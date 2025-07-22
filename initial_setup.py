#!/usr/bin/env python3
"""
Initial Setup - Create OptiBot Assistant and Vector Store
"""

from openai import OpenAI
from pathlib import Path
import time
import json
import hashlib
import os
from config import OPENAI_API_KEY

def create_initial_setup():
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        print("Creating initial OptiBot setup...")
        
        # Create vector store
        print("Creating vector store...")
        vector_store = client.vector_stores.create(name="OptiSigns Help Center")
        print(f"Vector store created: {vector_store.id}")
        
        # Find and upload articles
        markdown_files = [f for f in Path("articles").glob("*.md") if f.name != "README.md"]
        print(f"Found {len(markdown_files)} articles to upload")
        
        if not markdown_files:
            print("No articles found in articles/ directory!")
            return
        
        if markdown_files:
            file_ids = []
            print("Uploading files...")
            for i, file_path in enumerate(markdown_files, 1):
                try:
                    with open(file_path, 'rb') as file:
                        uploaded_file = client.files.create(file=file, purpose='assistants')
                        file_ids.append(uploaded_file.id)
                        print(f"  {i}/{len(markdown_files)}: {file_path.name}")
                except Exception as e:
                    print(f"  Error uploading {file_path.name}: {e}")
                    continue
            
            if not file_ids:
                print("No files were successfully uploaded!")
                return
            
            # Attach files to vector store
            print("Attaching files to vector store...")
            client.vector_stores.file_batches.create(
                vector_store_id=vector_store.id,
                file_ids=file_ids
            )
            
            # Wait for processing with timeout
            print("Processing files...")
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                vs = client.vector_stores.retrieve(vector_store.id)
                completed = vs.file_counts.completed if vs.file_counts else 0
                total = len(file_ids)
                
                print(f"  Progress: {completed}/{total} files processed")
                
                if completed >= total:
                    break
                    
                time.sleep(3)
            else:
                print("Warning: File processing may not be complete (timeout reached)")
            
            print(f"Uploaded {len(file_ids)} files to vector store")
            
            # Create cache file so delta updates work correctly
            print("Creating file cache...")
            create_cache_file(markdown_files, file_ids)
            print("Cache file created successfully!")
        
        # Create assistant
        print("Creating assistant...")
        instructions = ("You are OptiBot, the customer-support bot for OptiSigns.com. "
                       "STRICT RULES: "
                       "1. Be helpful, factual, concise using ONLY uploaded documentation "
                       "2. Maximum 5 bullet points with information/steps, else link to the docs"
                       "3. Cite each reply with up to 3 article links in this format below, NO markdown links, NO footnotes: "
                       " 'Article URL: https://support.optisigns.com/hc/en-us/articles/...' "
                       "4. Find 3 different relevant articles from the knowledge base")
        
        assistant = client.beta.assistants.create(
            instructions=instructions,
            name="OptiBot",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            model="gpt-4o"
        )
        
        print(f"Assistant created: {assistant.id}")
        print("\nSetup complete!")
        print(f"Assistant ID: {assistant.id}")
        print(f"Vector Store ID: {vector_store.id}")
        
        # Update config.py with the new IDs
        print("\nUpdating config.py with new IDs...")
        update_config_file(assistant.id, vector_store.id)
        
        print("Configuration updated successfully!")
        print("You can now use: python optibot.py test")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        import traceback
        traceback.print_exc()

def get_file_hash(file_path):
    """Get MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_article_updated_at(file_path):
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

def create_cache_file(markdown_files, file_ids):
    """Create cache file with uploaded file information"""
    cache_data = {}
    
    for i, file_path in enumerate(markdown_files):
        if i < len(file_ids):  # Ensure we have a corresponding file_id
            file_hash = get_file_hash(file_path)
            article_updated_at = get_article_updated_at(file_path)
            file_mod_time = os.path.getmtime(file_path)
            
            cache_data[file_path.name] = {
                'hash': file_hash,
                'updated_at': article_updated_at,
                'mod_time': file_mod_time,
                'path': str(file_path),
                'file_id': file_ids[i]
            }
    
    # Save cache to file
    cache_file = Path(".optibot_cache.json")
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)

def update_config_file(assistant_id, vector_store_id):
    """Update config.py with the new assistant and vector store IDs"""
    config_path = Path("config.py")
    
    # Read current config or create new one
    if config_path.exists():
        with open(config_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = [f'OPENAI_API_KEY = "{OPENAI_API_KEY}"\n']
    
    # Remove existing ASSISTANT_ID and VECTOR_STORE_ID lines
    lines = [line for line in lines if not line.startswith(('ASSISTANT_ID', 'VECTOR_STORE_ID'))]
    
    # Add new IDs
    if not any('OptiBot Configuration' in line for line in lines):
        lines.append('\n# OptiBot Configuration\n')
    
    lines.append(f'ASSISTANT_ID = "{assistant_id}"\n')
    lines.append(f'VECTOR_STORE_ID = "{vector_store_id}"\n')
    
    # Write back to config.py
    with open(config_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    create_initial_setup()
