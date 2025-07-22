#!/usr/bin/env python3
"""
OptiBot - Simple assistant manager with specific IDs
"""

from openai import OpenAI
from pathlib import Path
import time
import sys
import json
import hashlib
import os
from config import OPENAI_API_KEY, ASSISTANT_ID, VECTOR_STORE_ID

class OptiBotManager:
    def __init__(self, assistant_id=None, vector_store_id=None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant_id = assistant_id or ASSISTANT_ID
        self.vector_store_id = vector_store_id or VECTOR_STORE_ID
    
    def update_vector_store(self):
        """Update vector store with only new or modified articles"""
        if not self.vector_store_id:
            print("No vector store ID provided")
            return
        
        print("Checking for new/updated articles...")
        
        # Find articles
        markdown_files = [f for f in Path("articles").glob("*.md") if f.name != "README.md"]
        print(f"Found {len(markdown_files)} articles in total")
        
        if not markdown_files:
            print("No articles found to process")
            return
        
        # Load existing file cache
        cache_file = Path(".optibot_cache.json")
        file_cache = self._load_file_cache(cache_file)
        
        # Find files that need updating
        files_to_update = []
        current_files = {}
        
        for file_path in markdown_files:
            file_hash = self._get_file_hash(file_path)
            article_updated_at = self._get_article_updated_at(file_path)
            file_mod_time = os.path.getmtime(file_path)
            
            current_files[file_path.name] = {
                'hash': file_hash,
                'updated_at': article_updated_at,
                'mod_time': file_mod_time,
                'path': str(file_path)
            }
            
            # Check if file is new or modified (using hash AND updated_at)
            if (file_path.name not in file_cache or 
                file_cache[file_path.name]['hash'] != file_hash or
                file_cache[file_path.name].get('updated_at') != article_updated_at):
                files_to_update.append(file_path)
        
        if not files_to_update:
            print("✅ All articles are up to date - no changes detected")
            return
        
        print(f"📝 Found {len(files_to_update)} files to update:")
        for file_path in files_to_update:
            status = "NEW" if file_path.name not in file_cache else "MODIFIED"
            print(f"  - {file_path.name} ({status})")
        
        # Remove old versions of modified files from vector store
        self._remove_old_files(file_cache, files_to_update)
        
        # Upload new/modified files
        file_ids = []
        print("\nUploading files...")
        for i, file_path in enumerate(files_to_update, 1):
            try:
                with open(file_path, 'rb') as file:
                    uploaded_file = self.client.files.create(file=file, purpose='assistants')
                    file_ids.append(uploaded_file.id)
                    print(f"  {i}/{len(files_to_update)}: {file_path.name}")
                    
                    # Update cache with new file info
                    current_files[file_path.name]['file_id'] = uploaded_file.id
            except Exception as e:
                print(f"  Error uploading {file_path.name}: {e}")
                continue
        
        if not file_ids:
            print("❌ No files were successfully uploaded")
            return
        
        # Attach files to vector store
        print("Attaching files to vector store...")
        self.client.vector_stores.file_batches.create(
            vector_store_id=self.vector_store_id,
            file_ids=file_ids
        )
        
        # Wait for processing
        print("Processing files...")
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            vs = self.client.vector_stores.retrieve(self.vector_store_id)
            completed = vs.file_counts.completed if vs.file_counts else 0
            
            if completed >= len(file_ids):
                break
            time.sleep(2)
        else:
            print("⚠️ Warning: File processing may not be complete (timeout reached)")
        
        # Save updated cache
        self._save_file_cache(cache_file, current_files)
        
        print(f"✅ Successfully updated vector store with {len(file_ids)} files")
    
    def _get_file_hash(self, file_path):
        """Get MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_article_updated_at(self, file_path):
        """Extract updated_at timestamp from article frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for frontmatter between --- markers
            if content.startswith('---'):
                end_marker = content.find('---', 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker]
                    for line in frontmatter.split('\n'):
                        if line.strip().startswith('updated_at:'):
                            # Extract the timestamp (remove quotes if present)
                            updated_at = line.split(':', 1)[1].strip().strip('"')
                            return updated_at
            return None
        except Exception as e:
            print(f"⚠️ Warning: Could not extract updated_at from {file_path}: {e}")
            return None
    
    def _load_file_cache(self, cache_file):
        """Load file cache from disk"""
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not load cache file: {e}")
        return {}
    
    def _save_file_cache(self, cache_file, file_cache):
        """Save file cache to disk"""
        try:
            with open(cache_file, 'w') as f:
                json.dump(file_cache, f, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Could not save cache file: {e}")
    
    def _remove_old_files(self, file_cache, files_to_update):
        """Remove old versions of modified files from vector store"""
        files_to_remove = []
        
        for file_path in files_to_update:
            filename = file_path.name
            if filename in file_cache and 'file_id' in file_cache[filename]:
                files_to_remove.append(file_cache[filename]['file_id'])
        
        if files_to_remove:
            print(f"🗑️ Removing {len(files_to_remove)} old file versions...")
            for file_id in files_to_remove:
                try:
                    self.client.files.delete(file_id)
                    print(f"  Removed old file: {file_id}")
                except Exception as e:
                    print(f"  Warning: Could not remove file {file_id}: {e}")
    
    def test_assistant(self, question="How do I add a YouTube video?"):
        """Test the assistant"""
        if not self.assistant_id:
            print("No assistant ID provided")
            return
        
        print(f"Testing assistant with: {question}")
        
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python optibot.py [command] [optional: assistant_id] [optional: vector_store_id]")
        print("Commands:")
        print("  update - Update vector store with articles")
        print("  test   - Test assistant with default question")
        print("\nExamples:")
        print("  python optibot.py test")
        print("  python optibot.py update")
        print("  python optibot.py test custom_asst_id custom_vs_id  # Override default IDs")
        return
    
    command = sys.argv[1]
    assistant_id = sys.argv[2] if len(sys.argv) > 2 else None
    vector_store_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    manager = OptiBotManager(assistant_id, vector_store_id)
    
    if command == "update":
        manager.update_vector_store()
    elif command == "test":
        manager.test_assistant()
    else:
        print(f"Unknown command: {command}")
        print("Use 'test' or 'update'")

if __name__ == "__main__":
    main()
