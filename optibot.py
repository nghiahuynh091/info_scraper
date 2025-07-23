#!/usr/bin/env python3
"""
OptiBot - Simple assistant manager with timestamp-based updates
"""

from openai import OpenAI
from pathlib import Path
import time
import sys
import json
from datetime import datetime
from config import OPENAI_API_KEY, ASSISTANT_ID, VECTOR_STORE_ID

class OptiBotManager:
    def __init__(self, assistant_id=None, vector_store_id=None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant_id = assistant_id or ASSISTANT_ID
        self.vector_store_id = vector_store_id or VECTOR_STORE_ID
    
    def update_vector_store(self):
        """Update vector store using timestamp comparison"""
        if not self.vector_store_id:
            print("No vector store ID provided")
            return {"added": [], "updated": [], "skipped": []}
        
        print("Checking for updates...")
        
        # 1. Get local files with timestamps
        local_files = self._get_local_files()
        if not local_files:
            print("No articles found")
            return {"added": [], "updated": [], "skipped": []}
        
        # 2. Get last scrape time
        last_scrape_time = self._get_last_scrape_time()
        
        # 3. Find files that need updating
        files_to_update, file_categories = self._find_files_to_update(local_files, last_scrape_time)
        
        # Calculate counts for reporting
        total_files = len(local_files)
        files_updated = len(files_to_update)
        files_skipped = total_files - files_updated
        
        if not files_to_update:
            print("All articles are up to date")
            # Still save cache to update counts
            self._save_cache(local_files, 0, 0, total_files)
            return {
                "added": [],
                "updated": [], 
                "skipped": list(local_files.keys())
            }
        
        # 4. Upload files
        self._upload_files(files_to_update, local_files)
        
        # 5. Save updated cache with counts
        self._save_cache(local_files, files_updated, 0, files_skipped)
        
        print("Update completed successfully")
        
        return file_categories
    
    def _get_local_files(self):
        """Get local files with timestamp metadata"""
        local_files = {}
        articles_dir = Path("articles")
        
        if not articles_dir.exists():
            return {}
        
        markdown_files = [f for f in articles_dir.glob("*.md") if f.name != "README.md"]
        print(f"Found {len(markdown_files)} local articles")
        
        for file_path in markdown_files:
            created_at, updated_at = self._extract_timestamps(file_path)
            
            local_files[file_path.name] = {
                'path': str(file_path),
                'created_at': created_at,
                'updated_at': updated_at,
                'file_id': None
            }
        
        return local_files
    
    def _extract_timestamps(self, file_path):
        """Extract created_at and updated_at from frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                return None, None
                
            end_marker = content.find('---', 3)
            if end_marker == -1:
                return None, None
                
            frontmatter = content[3:end_marker]
            created_at = updated_at = None
            
            for line in frontmatter.split('\n'):
                line = line.strip()
                if line.startswith('created_at:'):
                    created_at = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('updated_at:'):
                    updated_at = line.split(':', 1)[1].strip().strip('"')
            
            return created_at, updated_at
            
        except Exception as e:
            print(f"Warning: Could not extract timestamps from {file_path}: {e}")
            return None, None
    
    def _get_last_scrape_time(self):
        """Get the last scrape time from cache"""
        cache_file = Path(".optibot_cache.json")
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            return cache.get('_metadata', {}).get('last_scrape_time')
        except Exception as e:
            print(f"Warning: Could not read cache: {e}")
            return None
    
    def _load_cache_data(self):
        """Load existing cache data"""
        cache_file = Path(".optibot_cache.json")
        
        if not cache_file.exists():
            return {}, {}, False
            
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            existing_files = set(key for key in cache.keys() if not key.startswith('_'))
            cached_file_data = {k: v for k, v in cache.items() if not k.startswith('_')}
            return existing_files, cached_file_data, True
        except:
            return {}, {}, False

    def _find_files_to_update(self, local_files, last_scrape_time):
        """Find files that need updating based on timestamps and missing files"""
        files_to_update = []
        file_categories = {"added": [], "updated": [], "skipped": []}
        
        print(f"Last scrape: {last_scrape_time or 'Never (will update all)'}")
        
        existing_files, cached_file_data, cache_exists = self._load_cache_data()
        
        # If no cache exists or cache is empty (first upload case)
        if not cache_exists or len(existing_files) == 0:
            print("No cached articles found - uploading all articles")
            for filename in local_files.keys():
                files_to_update.append(filename)
                file_categories["added"].append(filename)
                print(f"FIRST UPLOAD: {filename}")
            return files_to_update, file_categories
        
        for filename, file_info in local_files.items():
            created_at, updated_at = file_info['created_at'], file_info['updated_at']
            
            # Skip files without timestamps
            if not created_at or not updated_at:
                print(f"SKIP: {filename} (missing timestamps)")
                file_categories["skipped"].append(filename)
                continue
            
            # Check if this is a new file not in cache
            if filename not in existing_files:
                files_to_update.append(filename)
                file_categories["added"].append(filename)
                print(f"NEW FILE: {filename}")
                continue
            
            # Check if file exists in cache but has null file_id (needs re-upload)
            if cached_file_data[filename].get('file_id') is None:
                files_to_update.append(filename)
                file_categories["added"].append(filename)
                print(f"MISSING FILE_ID: {filename}")
                continue
            
            # Check timestamp-based updates
            if last_scrape_time:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    last_scrape_dt = datetime.fromisoformat(last_scrape_time.replace('Z', '+00:00'))
                    
                    if created_dt > last_scrape_dt:
                        files_to_update.append(filename)
                        file_categories["added"].append(filename)
                        print(f"NEW: {filename}")
                    elif updated_dt > last_scrape_dt:
                        files_to_update.append(filename)
                        file_categories["updated"].append(filename)
                        print(f"UPDATED: {filename}")
                    else:
                        file_categories["skipped"].append(filename)
                except Exception as e:
                    print(f"SKIP: {filename} (timestamp error: {e})")
                    file_categories["skipped"].append(filename)
            else:
                file_categories["skipped"].append(filename)
        
        return files_to_update, file_categories
    
    def _upload_files(self, files_to_update, local_files):
        """Upload files to vector store"""
        print(f"Uploading {len(files_to_update)} files...")
        
        file_ids = []
        
        for i, filename in enumerate(files_to_update, 1):
            file_path = Path(local_files[filename]['path'])
            
            try:
                with open(file_path, 'rb') as file:
                    uploaded_file = self.client.files.create(file=file, purpose='assistants')
                    local_files[filename]['file_id'] = uploaded_file.id
                    file_ids.append(uploaded_file.id)
                    print(f"  {i}/{len(files_to_update)}: {filename}")
                    
            except Exception as e:
                print(f"  Error uploading {filename}: {e}")
                continue
        
        if file_ids:
            print("Attaching files to vector store...")
            self.client.vector_stores.file_batches.create(
                vector_store_id=self.vector_store_id,
                file_ids=file_ids
            )
            print("Files uploaded successfully")
    
    def _save_cache(self, local_files, files_added=0, files_updated=0, files_skipped=0):
        """Save cache with current timestamp, preserving existing metadata and file_ids"""
        cache_file = Path(".optibot_cache.json")
        
        # Load existing cache data
        cache_data = {}
        existing_metadata = {}
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    existing_cache = json.load(f)
                cache_data = {k: v for k, v in existing_cache.items() if not k.startswith('_')}
                existing_metadata = existing_cache.get('_metadata', {})
            except:
                pass
        
        # Update with current local_files data, preserving existing file_ids
        for filename, file_info in local_files.items():
            if filename in cache_data and file_info['file_id'] is None:
                file_info['file_id'] = cache_data[filename].get('file_id')
            cache_data[filename] = file_info
        
        # Update metadata with counts
        cache_data['_metadata'] = {
            **existing_metadata,
            'last_upload_time': datetime.now().isoformat() + 'Z',
            'version': '2.0',
            'files_added': files_added,
            'files_updated': files_updated,
            'files_skipped': files_skipped
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"Cache saved with upload time: {cache_data['_metadata']['last_upload_time']}")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def test_assistant(self, question="How do I add a YouTube video?"):
        """Test the assistant"""
        if not self.assistant_id:
            print("No assistant ID provided")
            return
        
        print(f"Testing assistant with: {question}")
        
        try:
            thread = self.client.beta.threads.create()
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=question
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            while run.status in ['queued', 'in_progress']:
                time.sleep(2)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            response = messages.data[0].content[0].text.value
            
            print("\nOptiBot Response:")
            print(response)
            return response
            
        except Exception as e:
            print(f"Error testing assistant: {e}")
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python optibot.py [command]")
        print("Commands:")
        print("  update - Update vector store with articles")
        print("  test   - Test assistant with default question")
        return
    
    command = sys.argv[1]
    manager = OptiBotManager()
    
    if command == "update":
        manager.update_vector_store()
    elif command == "test":
        manager.test_assistant()
    else:
        print(f"Unknown command: {command}")
        print("Use 'update' or 'test'")

if __name__ == "__main__":
    main()
