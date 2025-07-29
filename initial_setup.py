#!/usr/bin/env python3

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def create_initial_setup():
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        print("Creating initial ChatBot setup...")
        
        print("Creating vector store...")
        vector_store = client.vector_stores.create(name="Help Center")
        
        print("Creating assistant...")
        instructions = os.getenv('ASSISTANT_INSTRUCTIONS')
        
        assistant = client.beta.assistants.create(
            instructions=instructions,
            name="ChatBot",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            model="gpt-4o"
        )
        print("\nSetup complete!")
        print(f"Assistant ID: {assistant.id}")
        print(f"Vector Store ID: {vector_store.id}")
        

        # Update .env file
        print("Updating configuration (.evn)... ")
        env_lines = []

        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()

        env_lines = [line for line in env_lines 
                     if not line.startswith('OPENAI_API_KEY=') 
                     and not line.startswith('ASSISTANT_ID=') 
                     and not line.startswith('VECTOR_STORE_ID=')
                     and not line.startswith('ASSISTANT_INSTRUCTIONS=')]

        env_lines.append(f'OPENAI_API_KEY={OPENAI_API_KEY}\n')
        env_lines.append(f'ASSISTANT_ID={assistant.id}\n')
        env_lines.append(f'VECTOR_STORE_ID={vector_store.id}\n')

        safe_instructions = instructions.replace('\n', ' ').replace('"', '\"').replace("'", "''")
        env_lines.append(f'ASSISTANT_INSTRUCTIONS={safe_instructions}\n')
       
        with open('.env', 'w') as f:
            f.writelines(env_lines)
        print(".env file updated successfully!")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_initial_setup()