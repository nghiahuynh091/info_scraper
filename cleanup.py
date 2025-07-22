#!/usr/bin/env python3
"""
Cleanup - Delete assistants and vector stores
"""

from openai import OpenAI
import sys
from config import OPENAI_API_KEY

def list_all():
    """List all assistants and vector stores"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    print("Listing all resources...")
    print("\n=== ASSISTANTS ===")
    
    # List all assistants
    assistants = client.beta.assistants.list(limit=50)
    if assistants.data:
        for assistant in assistants.data:
            print(f"ID: {assistant.id}")
            print(f"Name: {assistant.name}")
            print(f"Created: {assistant.created_at}")
            print(f"Model: {assistant.model}")
            print("-" * 40)
    else:
        print("No assistants found")
    
    print("\n=== VECTOR STORES ===")
    
    # List all vector stores
    stores = client.vector_stores.list(limit=50)
    if stores.data:
        for store in stores.data:
            print(f"ID: {store.id}")
            print(f"Name: {store.name}")
            print(f"Created: {store.created_at}")
            print(f"File counts: {store.file_counts.total if store.file_counts else 'N/A'}")
            print("-" * 40)
    else:
        print("No vector stores found")
    
    print("\n=== UPLOADED FILES ===")
    
    # List all files
    try:
        all_files = []
        has_more = True
        after = None
        
        while has_more:
            if after:
                files = client.files.list(limit=100, after=after)
            else:
                files = client.files.list(limit=100)
            
            all_files.extend(files.data)
            has_more = files.has_more
            if has_more and files.data:
                after = files.data[-1].id
        
        if all_files:
            total_size = 0
            print(f"Found {len(all_files)} files:")
            for file in all_files:
                size_kb = file.bytes / 1024 if file.bytes else 0
                total_size += size_kb
                print(f"ID: {file.id}")
                print(f"Name: {file.filename}")
                print(f"Size: {size_kb:.1f} KB")
                print(f"Purpose: {file.purpose}")
                print(f"Created: {file.created_at}")
                print("-" * 40)
            print(f"Total storage used: {total_size:.1f} KB ({total_size/1024:.2f} MB)")
        else:
            print("No files found")
    except Exception as e:
        print(f"Error listing files: {e}")

def clean_all():
    """Delete all assistants and vector stores"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    print("Cleaning all resources...")
    
    # Delete all assistants
    assistants = client.beta.assistants.list(limit=50)
    for assistant in assistants.data:
        try:
            client.beta.assistants.delete(assistant.id)
            print(f"Deleted assistant: {assistant.id} ({assistant.name})")
        except Exception as e:
            print(f"Error deleting assistant {assistant.id}: {e}")
    
    # Delete all vector stores
    stores = client.vector_stores.list(limit=50)
    for store in stores.data:
        try:
            client.vector_stores.delete(store.id)
            print(f"Deleted vector store: {store.id} ({store.name})")
        except Exception as e:
            print(f"Error deleting vector store {store.id}: {e}")
    
    # Delete all files
    print("Deleting uploaded files...")
    try:
        all_files = []
        has_more = True
        after = None
        
        # Get all files with pagination
        while has_more:
            if after:
                files = client.files.list(limit=100, after=after)
            else:
                files = client.files.list(limit=100)
            
            all_files.extend(files.data)
            has_more = files.has_more
            if has_more and files.data:
                after = files.data[-1].id
        
        print(f"Found {len(all_files)} files to delete")
        
        for file in all_files:
            try:
                client.files.delete(file.id)
                print(f"Deleted file: {file.id} ({file.filename})")
            except Exception as e:
                print(f"Error deleting file {file.id}: {e}")
                
    except Exception as e:
        print(f"Error listing files: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python cleanup.py [list|all]")
        print("  list - List all assistants and vector stores")
        print("  all  - Delete all assistants and vector stores")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_all()
    elif command == "all":
        clean_all()
    else:
        print(f"Unknown command: {command}")
        print("Use 'list' or 'all'")

if __name__ == "__main__":
    main()
