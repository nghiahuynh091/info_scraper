#!/usr/bin/env python3
"""
Initial Setup - Create OptiBot Assistant and Vector Store only
File upload is handled by optibot.py
"""

from openai import OpenAI
from config import OPENAI_API_KEY

def create_initial_setup():
    """Create assistant and vector store only - no file upload"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        print("Creating initial OptiBot setup...")
        
        # Create vector store (empty)
        print("Creating vector store...")
        vector_store = client.vector_stores.create(name="OptiSigns Help Center")
        
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
        print("\nSetup complete!")
        print(f"Assistant ID: {assistant.id}")
        print(f"Vector Store ID: {vector_store.id}")
        



        print(f"Assistant created: {assistant.id}")
        
        # Update config file
        print("Updating configuration...")
        config_content = f'''OPENAI_API_KEY = "{OPENAI_API_KEY}"

# OptiBot Configuration
ASSISTANT_ID = "{assistant.id}"
VECTOR_STORE_ID = "{vector_store.id}"
'''
        
        with open('config.py', 'w') as f:
            f.write(config_content)
        
        print(f"Initial setup completed successfully!")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_initial_setup()