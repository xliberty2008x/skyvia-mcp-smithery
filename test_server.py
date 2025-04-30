#!/usr/bin/env python3
"""
Test script for Skyvia MCP Server
"""

import os
import json
import sys
import subprocess
import time
import threading
from typing import Dict, Any, List

# Simulate an MCP client
class MockMCPClient:
    def __init__(self, server_process):
        self.server_process = server_process
        self.request_id = 1
    
    def send_request(self, request_type: str, **kwargs) -> Dict:
        """Send a request to the MCP server and get the response."""
        request = {
            "id": str(self.request_id),
            "clientId": "test-client",
            "type": request_type,
            **kwargs
        }
        self.request_id += 1
        
        # Send the request to the server's stdin
        self.server_process.stdin.write(json.dumps(request) + "\n")
        self.server_process.stdin.flush()
        
        # Read the response from stdout
        response_line = self.server_process.stdout.readline().strip()
        if not response_line:
            return {"error": "No response received"}
        
        try:
            return json.loads(response_line)
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON response: {response_line}"}
    
    def initialize(self) -> Dict:
        """Initialize the MCP server."""
        return self.send_request("initialize")
    
    def list_tools(self) -> Dict:
        """List available tools."""
        return self.send_request("tools/list")
    
    def use_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Use a specific tool."""
        return self.send_request("tools/use", name=tool_name, arguments=arguments)


def run_test(api_token: str):
    """Run tests for the Skyvia MCP server."""
    # Set the API token environment variable for the server process
    env = os.environ.copy()
    env["SKYVIA_API_TOKEN"] = api_token

    # Start the server process
    server_process = subprocess.Popen(
        ["python", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line-buffered
        env=env
    )

    # Start a thread to read stderr and print it
    def print_stderr():
        for line in server_process.stderr:
            print(f"SERVER LOG: {line.strip()}")
    
    stderr_thread = threading.Thread(target=print_stderr, daemon=True)
    stderr_thread.start()
    
    try:
        # Create a client
        client = MockMCPClient(server_process)
        
        # Test initialization
        print("\n--- Testing Initialization ---")
        init_response = client.initialize()
        print(f"Initialization Response: {json.dumps(init_response, indent=2)}")
        
        # Test listing tools
        print("\n--- Testing Tools Listing ---")
        tools_response = client.list_tools()
        print(f"Tools Response: {json.dumps(tools_response, indent=2)}")
        
        # Note: The following tests would normally be performed against a real Skyvia API
        # We're just demonstrating the structure here
        
        # Test list_workspaces (this will fail without a real API token)
        print(f"Tools Response: {json.dumps(tools_response, indent=2)}")

        # --- Tool Usage Tests (Requires REAL API Token & Valid IDs) ---
        # These tests assume you have a valid workspace and integration ID.
        # Get values from environment variables if available
        WORKSPACE_ID = int(os.environ.get("TEST_WORKSPACE_ID", "171381"))  # Default to placeholder
        INTEGRATION_ID = int(os.environ.get("TEST_INTEGRATION_ID", "270715"))  # Default to placeholder
        EXECUTION_ID = 1  # Placeholder, will be updated if possible from get_integration_executions

        print(f"\n--- Using Workspace ID: {WORKSPACE_ID}, Integration ID: {INTEGRATION_ID} ---")
        
        # Check if environment variables are set for testing
        if "TEST_WORKSPACE_ID" not in os.environ or "TEST_INTEGRATION_ID" not in os.environ:
            print("\nWARNING: For full testing, set TEST_WORKSPACE_ID and TEST_INTEGRATION_ID environment variables")

        # Test list_integrations
        print("\n--- Testing list_integrations ---")
        list_int_resp = client.use_tool("list_integrations", {"workspace_id": WORKSPACE_ID})
        print(f"List Integrations Response: {json.dumps(list_int_resp, indent=2)}")

        # Test get_integration
        print("\n--- Testing get_integration ---")
        get_int_resp = client.use_tool("get_integration", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        print(f"Get Integration Response: {json.dumps(get_int_resp, indent=2)}")

        # Test get_integration_executions
        print("\n--- Testing get_integration_executions ---")
        get_exec_resp = client.use_tool("get_integration_executions", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID, "take": 5})
        print(f"Get Executions Response: {json.dumps(get_exec_resp, indent=2)}")
        # Extract a real execution ID if possible for the details test
        if get_exec_resp.get("data") and get_exec_resp["data"].get("data"):
             try:
                 EXECUTION_ID = get_exec_resp["data"]["data"][0]["runId"]
                 print(f"Using Execution ID {EXECUTION_ID} for details test.")
             except (IndexError, KeyError):
                 print("Could not extract a valid Execution ID from the response.")


        # Test get_integration_execution_details (conditional)
        if EXECUTION_ID > 1: # Only run if we potentially got a valid ID
             print("\n--- Testing get_integration_execution_details ---")
             get_exec_details_resp = client.use_tool("get_integration_execution_details", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID, "execution_id": EXECUTION_ID})
             print(f"Get Execution Details Response: {json.dumps(get_exec_details_resp, indent=2)}")
        else:
             print("\n--- Skipping get_integration_execution_details (No valid Execution ID found) ---")


        # Test get_active_integration_execution
        print("\n--- Testing get_active_integration_execution ---")
        get_active_resp = client.use_tool("get_active_integration_execution", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        print(f"Get Active Execution Response: {json.dumps(get_active_resp, indent=2)}")

        # Test get_integration_schedule
        print("\n--- Testing get_integration_schedule ---")
        get_sched_resp = client.use_tool("get_integration_schedule", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        print(f"Get Schedule Response: {json.dumps(get_sched_resp, indent=2)}")

        # Example: Disable schedule (use enable/disable cautiously)
        # print("\n--- Testing disable_integration_schedule ---")
        # disable_sched_resp = client.use_tool("disable_integration_schedule", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        # print(f"Disable Schedule Response: {json.dumps(disable_sched_resp, indent=2)}")
        # time.sleep(1) # Allow time for state change
        # print("\n--- Testing enable_integration_schedule ---")
        # enable_sched_resp = client.use_tool("enable_integration_schedule", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        # print(f"Enable Schedule Response: {json.dumps(enable_sched_resp, indent=2)}")

        # Example: Run integration (use cautiously - may have side effects)
        # print("\n--- Testing run_integration ---")
        # run_resp = client.use_tool("run_integration", {"workspace_id": WORKSPACE_ID, "integration_id": INTEGRATION_ID})
        # print(f"Run Integration Response: {json.dumps(run_resp, indent=2)}")

        print("\n--- Testing completed ---")
        print("NOTE: Some tests (run, cancel, kill, schedule changes) might be commented out for safety.")
        print("Uncomment and adjust IDs as needed for full testing.")

    finally:
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=5)


if __name__ == "__main__":
    real_api_token = os.environ.get("REAL_SKYVIA_API_TOKEN")
    if not real_api_token:
        print("Error: REAL_SKYVIA_API_TOKEN environment variable not set.")
        print("Please set it to your actual Skyvia API token to run live tests.")
        # Fallback to dummy token for basic checks if needed, but live tests will fail
        # real_api_token = "dummy-token-live-tests-will-fail"
        sys.exit(1) # Exit if no real token is provided

    print(f"Using API Token: ...{real_api_token[-4:]}") # Print last 4 chars for confirmation
    run_test(real_api_token)
