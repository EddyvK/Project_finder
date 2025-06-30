"""Test script for the streaming scan endpoint."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import aiohttp
import json
import logging
from logger_config import setup_logging
from main import app
from fastapi.testclient import TestClient

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_streaming_scan():
    """Test the streaming scan endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            # Test the streaming endpoint
            async with session.post(
                "http://localhost:8000/api/scan/stream/8",  # time_range as path parameter
                headers={"Accept": "text/event-stream"}
            ) as response:

                print(f"Response status: {response.status}")

                if response.status == 200:
                    print("Streaming response received:")

                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_type = data.get('type')

                            if event_type == 'start':
                                print(f"🚀 {data.get('message')}")
                            elif event_type == 'website_start':
                                print(f"🌐 Starting scan for: {data.get('website')}")
                            elif event_type == 'project':
                                project = data.get('data', {})
                                print(f"✅ Found project: {project.get('title', 'Unknown')} (ID: {project.get('id')})")
                            elif event_type == 'project_updated':
                                project = data.get('data', {})
                                print(f"🔄 Updated project: {project.get('title', 'Unknown')} with requirements")
                            elif event_type == 'website_complete':
                                print(f"✅ Completed scan for {data.get('website')}: {data.get('projects')} projects")
                            elif event_type == 'complete':
                                print(f"🎉 Scan completed! Total projects: {data.get('total_projects')}")
                            elif event_type == 'error':
                                print(f"❌ Error: {data.get('message')}")
                else:
                    print(f"Error: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")

    except Exception as e:
        logger.error(f"Error testing streaming scan: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_streaming_scan())