#!/usr/bin/env python3
"""
Test script to verify OpenAI embedding call works.
"""
import sys
import asyncio
from backend.openai_handler import OpenAIHandler
from backend.config_manager import config_manager

def main():
    api_keys = config_manager.get_api_keys()
    if not api_keys.get('openai'):
        print('❌ No OpenAI API key found in environment.')
        return
    try:
        handler = OpenAIHandler(api_keys['openai'])
        print('OpenAI handler initialized successfully.')
        result = asyncio.run(handler.get_embedding('Test embedding for OpenAI API'))
        if result:
            print('✅ Embedding call succeeded!')
            print('Embedding length:', len(result))
            print('First 5 values:', result[:5])
        else:
            print('❌ Embedding call returned no result.')
    except Exception as e:
        print(f'❌ Exception during embedding call: {e}')

if __name__ == "__main__":
    main()