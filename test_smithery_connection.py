#!/usr/bin/env python3
"""
Test script for Skyvia MCP Server hosted on Smithery
This script tests connection to a Smithery-hosted MCP server
with detailed error logging
"""

import os
import sys
import json
import base64
import asyncio
import logging
from urllib.parse import quote

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("smithery-test")

# Import MCP client library (install with pip install mcp-client if needed)
try:
    import mcp
    from mcp.client.websocket import websocket_client
except ImportError:
    logger.error("MCP client library not found. Install with 'pip install mcp-client'")
    sys.exit(1)

async def test_smithery_connection(skyvia_api_token, smithery_api_key):
    """Test connection to Smithery-hosted Skyvia MCP server"""
    
    # Configuration for the Skyvia MCP server
    config = {
        "skyvia_api_token": skyvia_api_token
    }
    
    # Encode config in base64
    config_json = json.dumps(config)
    logger.debug(f"Config (sanitized): {json.dumps({**config, 'skyvia_api_token': '***'})}")
    config_b64 = base64.b64encode(config_json.encode()).decode('utf-8')
    
    # Create server URL
    url = f"wss://server.smithery.ai/@xliberty2008x/skyvia-mcp-smithery/ws?config={config_b64}&api_key={smithery_api_key}"
    logger.info(f"Connecting to Smithery (token and key sanitized): wss://server.smithery.ai/@xliberty2008x/skyvia-mcp-smithery/ws?config=***&api_key=***")
    
    try:
        # Connect to the server using websocket client
        logger.info("Establishing websocket connection...")
        async with websocket_client(url) as streams:
            logger.info("Websocket connection established successfully")
            
            # Create MCP client session
            logger.info("Creating MCP client session...")
            async with mcp.ClientSession(*streams) as session:
                # Initialize the connection
                logger.info("Initializing MCP session...")
                try:
                    await session.initialize()
                    logger.info("✓ Session initialized successfully")
                except Exception as e:
                    logger.error(f"✗ Session initialization failed: {str(e)}")
                    raise
                
                # List available tools
                logger.info("Requesting tool list...")
                try:
                    tools_result = await session.list_tools()
                    tool_names = [t.name for t in tools_result.tools]
                    logger.info(f"✓ Available tools: {', '.join(tool_names)}")
                except Exception as e:
                    logger.error(f"✗ Failed to list tools: {str(e)}")
                    raise
                
                # Test a specific tool if available
                if tool_names and "list_workspaces" in tool_names:
                    logger.info("Testing list_workspaces tool...")
                    try:
                        workspace_result = await session.call_tool("list_workspaces", arguments={})
                        logger.info(f"✓ list_workspaces call successful")
                        logger.debug(f"Workspaces result: {workspace_result}")
                    except Exception as e:
                        logger.error(f"✗ Failed to call list_workspaces: {str(e)}")
                        raise
                else:
                    logger.warning("list_workspaces tool not available, skipping tool testing")
                
                logger.info("All tests completed successfully!")
                return True
                
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_direct_connection(skyvia_api_token):
    """For comparison, test a direct local connection to the MCP server"""
    
    import subprocess
    import time
    
    # Start the server in a separate process with the API token
    env = os.environ.copy()
    env["SKYVIA_API_TOKEN"] = skyvia_api_token
    
    logger.info("Starting local MCP server process...")
    server_process = subprocess.Popen(
        ["python", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Give the server a moment to start up
    time.sleep(2)
    
    # Simple test message
    test_message = {
        "id": "1",
        "clientId": "test-client",
        "type": "initialize"
    }
    
    logger.info("Sending initialize request to local server...")
    server_process.stdin.write(json.dumps(test_message) + "\n")
    server_process.stdin.flush()
    
    # Read the response
    response_line = server_process.stdout.readline().strip()
    logger.info(f"Local server initialize response: {response_line}")
    
    # Clean up
    logger.info("Terminating local server process...")
    server_process.terminate()
    server_process.wait(timeout=5)
    
    return "success" in response_line.lower()

async def main():
    """Main entry point"""
    
    # Get required credentials
    skyvia_api_token = os.environ.get("SKYVIA_API_TOKEN")
    # Use the specific Smithery API key that's been confirmed to work
    smithery_api_key = os.environ.get("SMITHERY_API_KEY", "473af8b4-8a68-462c-a688-033d53a21509")
    
    if not skyvia_api_token:
        logger.error("SKYVIA_API_TOKEN environment variable not set")
        logger.error("Set it to your Skyvia API token before running this script")
        return
    
    logger.info("=== TESTING SMITHERY CONNECTION ===")
    smithery_success = await test_smithery_connection(skyvia_api_token, smithery_api_key)
    
    # If Smithery test fails, try a direct connection for comparison
    if not smithery_success:
        logger.info("\n=== TESTING DIRECT LOCAL CONNECTION FOR COMPARISON ===")
        direct_success = await test_direct_connection(skyvia_api_token)
        
        if direct_success:
            logger.info("✓ Direct connection succeeded but Smithery connection failed")
            logger.info("This suggests the issue is with the Smithery deployment, not your server code")
        else:
            logger.info("✗ Both Smithery and direct connections failed")
            logger.info("This suggests the issue might be with your server code or API token")
    
    logger.info("\n=== TROUBLESHOOTING NEXT STEPS ===")
    logger.info("1. Verify you're using a valid Skyvia API token")
    logger.info("2. Check if your Smithery profile has the correct configuration")
    logger.info("3. Make sure the server properly checks for initialization before processing tool requests")
    logger.info("4. Check the Smithery logs for any server-side errors")

if __name__ == "__main__":
    asyncio.run(main())
