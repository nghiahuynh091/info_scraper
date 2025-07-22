#!/usr/bin/env python3
"""
Initial Setup - Create OptiBot Assistant and Vector Store
"""

from openai import OpenAI
from pathlib import Path
import time
from config import OPENAI_API_KEY

def create_initial_setup():
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    print("Creating initial OptiBot setup...")
    
    # Create vector store
    print("Creating vector store...")
    vector_store = client.vector_stores.create(name="OptiSigns Help Center")
    print(f"Vector store created: {vector_store.id}")
    
    # Find and upload articles
    markdown_files = [f for f in Path("articles").glob("*.md") if f.name != "README.md"]
    print(f"Found {len(markdown_files)} articles to upload")
    
    if markdown_files:
        file_ids = []
        for file_path in markdown_files:
            with open(file_path, 'rb') as file:
                uploaded_file = client.files.create(file=file, purpose='assistants')
                file_ids.append(uploaded_file.id)
        
        # Attach files to vector store
        client.vector_stores.file_batches.create(
            vector_store_id=vector_store.id,
            file_ids=file_ids
        )
        
        # Wait for processing
        print("Processing files...")
        while True:
            vs = client.vector_stores.retrieve(vector_store.id)
            if vs.file_counts.completed >= len(file_ids):
                break
            time.sleep(2)
        print(f"Uploaded {len(file_ids)} files to vector store")
    
    # Create assistant
    print("Creating assistant...")
    instructions = ("You are OptiBot, the customer-support bot for OptiSigns.com. "
                   "STRICT RULES: "
                   "1. Be helpful, factual, concise using ONLY uploaded documentation "
                   "2. Maximum 4 bullet points with specific steps "
                   "3. Then say 'For detailed steps, see:' "
                   "4. ALWAYS end with EXACTLY 3 lines in this format: "
                   "'Article URL: https://support.optisigns.com/hc/en-us/articles/...' "
                   "5. Use plain text 'Article URL:' - NO markdown links, NO footnotes "
                   "6. Find 3 different relevant articles from the knowledge base")
    
    assistant = client.assistants.create(
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
    print("\nSave these IDs for use with optibot.py")

if __name__ == "__main__":
    create_initial_setup()
