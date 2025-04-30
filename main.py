#!/usr/bin/env python3
"""
Skyvia MCP Server - Provides tools for interacting with Skyvia API
"""

import os
import sys
import json
import logging
import requests
# Removed argparse import
from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("skyvia-mcp")

# Constants
BASE_URL = "https://api.skyvia.com"
API_VERSION = "v1"

# Custom exceptions
class SkyviaAPIError(Exception):
    """Exception raised for errors in the Skyvia API responses."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Skyvia API Error ({status_code}): {message}")


@dataclass
class SkyviaClient:
    """Client for interacting with the Skyvia API."""
    api_token: str
    
    def __post_init__(self):
        if not self.api_token:
            raise ValueError("API token is required")
        
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }
    
    def _make_request(self, method: str, path: str, params: Dict = None, data: Dict = None) -> Any:
        """Make a request to the Skyvia API."""
        url = f"{BASE_URL}/{API_VERSION}/{path}"
        logger.info(f"Making {method} request to {url}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            
            # Handle non-200 responses
            if response.status_code != 200:
                error_message = response.text
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                except json.JSONDecodeError:
                    pass
                
                # Handle 204 No Content specifically (common for 'get_active_...' or 'get_schedule')
                if response.status_code == 204:
                    logger.info(f"Received 204 No Content for {method} {url}. Returning None.")
                    return None 
                    
                raise SkyviaAPIError(response.status_code, error_message)
            
            # Return the JSON data if available, otherwise None for empty success responses (like 200 OK with no body)
            if response.text and response.headers.get('Content-Type', '').startswith('application/json'):
                return response.json()
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error making request: {str(e)}")
            raise SkyviaAPIError(500, str(e))
    
    # Workspace methods
    def list_workspaces(self) -> List[Dict]:
        """List all workspaces."""
        return self._make_request("GET", "workspaces")
    
    def get_workspace(self, workspace_id: int) -> Dict:
        """Get details for a specific workspace."""
        return self._make_request("GET", f"workspaces/{workspace_id}")
    
    # Connection methods
    def list_connections(self, workspace_id: int, skip: int = 0, take: int = 20) -> Dict:
        """List connections in a workspace."""
        params = {"skip": skip, "take": take}
        return self._make_request("GET", f"workspaces/{workspace_id}/connections", params=params)
    
    def get_connection_details(self, workspace_id: int, connection_id: int) -> Dict:
        """Get details for a specific connection."""
        return self._make_request("GET", f"workspaces/{workspace_id}/connections/{connection_id}")
    
    def test_connection(self, workspace_id: int, connection_id: int) -> Dict:
        """Test a connection."""
        return self._make_request("POST", f"workspaces/{workspace_id}/connections/{connection_id}/test")
    
    # Integration methods
    def list_integrations(self, workspace_id: int, skip: int = 0, take: int = 20) -> Dict:
        """List integrations in a workspace."""
        params = {"skip": skip, "take": take}
        return self._make_request("GET", f"workspaces/{workspace_id}/integrations", params=params)
    
    def get_integration(self, workspace_id: int, integration_id: int) -> Dict:
        """Get details for a specific integration."""
        return self._make_request("GET", f"workspaces/{workspace_id}/integrations/{integration_id}")
    
    def run_integration(self, workspace_id: int, integration_id: int) -> Dict:
        """Run an integration."""
        return self._make_request("POST", f"workspaces/{workspace_id}/integrations/{integration_id}/executions")

    def get_integration_executions(self, workspace_id: int, integration_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None, failed: Optional[bool] = None, skip: int = 0, take: int = 20, sort_order: str = 'asc', sort_by: str = 'startDate') -> Dict:
        """Get finished execution history for an integration."""
        params = {
            "startDate": start_date, "endDate": end_date, "failed": failed,
            "skip": skip, "take": take, "sortOrder": sort_order, "sortBy": sort_by
        }
        params = {k: v for k, v in params.items() if v is not None} # Remove None values
        return self._make_request("GET", f"workspaces/{workspace_id}/integrations/{integration_id}/executions", params=params)

    def get_integration_execution_details(self, workspace_id: int, integration_id: int, execution_id: int) -> Dict:
        """Get details of a specific finished integration execution."""
        return self._make_request("GET", f"workspaces/{workspace_id}/integrations/{integration_id}/executions/{execution_id}")

    def get_active_integration_execution(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Get the state of the currently active integration execution."""
        try:
            return self._make_request("GET", f"workspaces/{workspace_id}/integrations/{integration_id}/executions/active")
        except SkyviaAPIError as e:
            # Skyvia API might return 404 if no active run, handle gracefully
            if e.status_code == 404:
                 logger.info(f"No active execution found for integration {integration_id} in workspace {workspace_id}.")
                 return None # Or return a specific message indicating no active run
            raise e # Re-raise other errors

    def cancel_integration(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Cancel an active integration execution."""
        return self._make_request("POST", f"workspaces/{workspace_id}/integrations/{integration_id}/executions/cancel")

    def kill_integration(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Forcefully stop (kill) an active integration execution."""
        return self._make_request("POST", f"workspaces/{workspace_id}/integrations/{integration_id}/executions/kill")

    def get_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Get the schedule status for an integration."""
        return self._make_request("GET", f"workspaces/{workspace_id}/integrations/{integration_id}/schedule")

    def enable_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Enable the schedule for an integration."""
        return self._make_request("POST", f"workspaces/{workspace_id}/integrations/{integration_id}/schedule/enable")

    def disable_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Disable the schedule for an integration."""
        return self._make_request("POST", f"workspaces/{workspace_id}/integrations/{integration_id}/schedule/disable")


class MCPServer:
    """Skyvia MCP Server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None  # Will be initialized during startup
        
        # Register tools
        self.tools = {
            "list_workspaces": self.list_workspaces,
            "get_workspace": self.get_workspace,
            "list_connections": self.list_connections,
            "get_connection_details": self.get_connection_details,
            "test_connection": self.test_connection,
            "list_integrations": self.list_integrations,
            "get_integration": self.get_integration,
            "run_integration": self.run_integration,
            "get_integration_executions": self.get_integration_executions,
            "get_integration_execution_details": self.get_integration_execution_details,
            "get_active_integration_execution": self.get_active_integration_execution,
            "cancel_integration": self.cancel_integration,
            "kill_integration": self.kill_integration,
            "get_integration_schedule": self.get_integration_schedule,
            "enable_integration_schedule": self.enable_integration_schedule,
            "disable_integration_schedule": self.disable_integration_schedule,
        }

        # Tool schemas
        self.schemas = {
            "list_workspaces": {
                "type": "object",
                "properties": {},
                "title": "list_workspacesArguments"
            },
            "get_workspace": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The unique identifier for the workspace.",
                        "title": "Workspace Id",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id"],
                "title": "get_workspaceArguments"
            },
            "list_connections": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the connections.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "skip": {
                        "default": 0,
                        "description": "Number of connections to skip (for pagination). Must be >= 0.",
                        "minimum": 0,
                        "title": "Skip",
                        "type": "integer"
                    },
                    "take": {
                        "default": 20,
                        "description": "Number of connections to return (for pagination). Must be between 1 and 200.",
                        "maximum": 200,
                        "minimum": 1,
                        "title": "Take",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id"],
                "title": "list_connectionsArguments"
            },
            "get_connection_details": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the connection.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "connection_id": {
                        "description": "The ID of the connection to retrieve details for.",
                        "title": "Connection Id",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id", "connection_id"],
                "title": "get_connection_detailsArguments"
            },
            "test_connection": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the connection.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "connection_id": {
                        "description": "The ID of the connection to test.",
                        "title": "Connection Id",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id", "connection_id"],
                "title": "test_connectionArguments"
            },
            "list_integrations": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the integrations.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "skip": {
                        "default": 0,
                        "description": "Number of integrations to skip (for pagination). Must be >= 0.",
                        "minimum": 0,
                        "title": "Skip",
                        "type": "integer"
                    },
                    "take": {
                        "default": 20,
                        "description": "Number of integrations to return (for pagination). Must be between 1 and 200.",
                        "maximum": 200,
                        "minimum": 1,
                        "title": "Take",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id"],
                "title": "list_integrationsArguments"
            },
            "get_integration": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the integration.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "integration_id": {
                        "description": "The ID of the integration package to retrieve.",
                        "title": "Integration Id",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "get_integrationArguments"
            },
            "run_integration": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "description": "The ID of the workspace containing the integration.",
                        "title": "Workspace Id",
                        "type": "integer"
                    },
                    "integration_id": {
                        "description": "The ID of the integration package to run.",
                        "title": "Integration Id",
                        "type": "integer"
                    }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "run_integrationArguments"
            },
            "get_integration_executions": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" },
                    "start_date": { "type": "string", "format": "date-time", "description": "Optional start date filter (ISO 8601 format)", "nullable": True },
                    "end_date": { "type": "string", "format": "date-time", "description": "Optional end date filter (ISO 8601 format)", "nullable": True },
                    "failed": { "type": "boolean", "description": "Optional filter for failed status", "nullable": True },
                    "skip": { "type": "integer", "default": 0, "minimum": 0, "description": "Items to skip" },
                    "take": { "type": "integer", "default": 20, "minimum": 1, "maximum": 200, "description": "Items to take" },
                    "sort_order": { "type": "string", "default": "asc", "enum": ["asc", "desc"], "description": "Sort order" },
                    "sort_by": { "type": "string", "default": "startDate", "enum": ["startDate", "runId"], "description": "Field to sort by" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "get_integration_executionsArguments"
            },
            "get_integration_execution_details": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" },
                    "execution_id": { "type": "integer", "description": "Execution ID" }
                },
                "required": ["workspace_id", "integration_id", "execution_id"],
                "title": "get_integration_execution_detailsArguments"
            },
            "get_active_integration_execution": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "get_active_integration_executionArguments"
            },
            "cancel_integration": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "cancel_integrationArguments"
            },
            "kill_integration": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "kill_integrationArguments"
            },
            "get_integration_schedule": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "get_integration_scheduleArguments"
            },
            "enable_integration_schedule": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "enable_integration_scheduleArguments"
            },
            "disable_integration_schedule": {
                "type": "object",
                "properties": {
                    "workspace_id": { "type": "integer", "description": "Workspace ID" },
                    "integration_id": { "type": "integer", "description": "Integration ID" }
                },
                "required": ["workspace_id", "integration_id"],
                "title": "disable_integration_scheduleArguments"
            }
        }

    def initialize(self) -> Dict:
        """Initialize the MCP server."""
        # Get API token from environment
        api_token = os.environ.get("SKYVIA_API_TOKEN")
        if not api_token:
            logger.error("SKYVIA_API_TOKEN environment variable is not set")
            return {"error": "API token is not set"}

        try:
            self.client = SkyviaClient(api_token)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error initializing client: {str(e)}")
            return {"error": str(e)}
    
    def handle_request(self, request: Dict) -> Dict:
        """Handle an MCP request."""
        try:
            request_id = request.get("id", "unknown")
            client_id = request.get("clientId", "unknown")
            
            # Handle different request types
            if request.get("type") == "initialize":
                return self._create_response(request_id, client_id, self.initialize())
            
            elif request.get("type") == "tools/list":
                tools_list = [{"name": name, "schema": schema} for name, schema in self.schemas.items()]
                return self._create_response(request_id, client_id, tools_list)
            
            elif request.get("type") == "tools/use":
                tool_name = request.get("name")
                tool_args = request.get("arguments", {})

                # --- START ADDED CHECK ---
                # Check if client was initialized *before* trying to use it
                if not self.client:
                    # Return an MCP error response if the client wasn't set up (likely due to initialization failure)
                    return self._create_error_response(request_id, client_id, 
                                                       "Server not properly initialized. Check API token or server logs.", 
                                                       error_code=503) # 503 Service Unavailable is appropriate
                # --- END ADDED CHECK ---
                
                if tool_name not in self.tools:
                    return self._create_error_response(request_id, client_id, f"Unknown tool: {tool_name}")
                
                # Now it's safe to assume self.client exists
                result = self.tools[tool_name](**tool_args) 
                return self._create_response(request_id, client_id, result)
            
            # Handle unknown request types
            return self._create_error_response(request_id, client_id, f"Unknown request type: {request.get('type')}")
            
        except SkyviaAPIError as e:
            return self._create_error_response(request.get("id", "unknown"), request.get("clientId", "unknown"), 
                                              f"Skyvia API Error: {e.message}", error_code=e.status_code)
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return self._create_error_response(request.get("id", "unknown"), request.get("clientId", "unknown"), 
                                              f"Error handling request: {str(e)}")
    
    def _create_response(self, request_id: str, client_id: str, data: Any) -> Dict:
        """Create a successful response."""
        return {
            "id": request_id,
            "clientId": client_id,
            "type": "response",
            "data": data
        }
    
    def _create_error_response(self, request_id: str, client_id: str, message: str, error_code: int = 500) -> Dict:
        """Create an error response."""
        return {
            "id": request_id,
            "clientId": client_id,
            "type": "error",
            "error": {
                "code": error_code,
                "message": message
            }
        }
    
    # Tool implementations
    def list_workspaces(self) -> List[Dict]:
        """
        Retrieves a list of all workspaces available to the user account.

        Returns:
            A list of workspace objects containing id, name, and isPersonal flag.

        Raises:
            SkyviaAPIError: If the API request fails.
        """
        return self.client.list_workspaces()
    
    def get_workspace(self, workspace_id: int) -> Dict:
        """
        Retrieves details for a specific workspace.

        Args:
            workspace_id: The ID of the workspace to retrieve.

        Returns:
            A workspace object containing id, name, and isPersonal flag.

        Raises:
            SkyviaAPIError: If the API request fails (e.g., workspace not found).
        """
        return self.client.get_workspace(workspace_id)
    
    def list_connections(self, workspace_id: int, skip: int = 0, take: int = 20) -> Dict:
        """
        Retrieves a list of connections within a specific workspace.

        Args:
            workspace_id: The ID of the target workspace.
            skip: Items to skip (default 0).
            take: Items to take (default 20, max 200).

        Returns:
            An object containing a list of connection DTOs and a 'hasMore' flag for pagination.

        Raises:
            SkyviaAPIError: If the API request fails.
        """
        return self.client.list_connections(workspace_id, skip, take)
    
    def get_connection_details(self, workspace_id: int, connection_id: int) -> Dict:
        """
        Retrieves detailed information for a specific connection within a workspace.

        Args:
            workspace_id: The ID of the target workspace.
            connection_id: The ID of the target connection.

        Returns:
            A ConnectionDetailsDto object with detailed connection information.

        Raises:
            SkyviaAPIError: If the API request fails (e.g., connection not found).
        """
        return self.client.get_connection_details(workspace_id, connection_id)
    
    def test_connection(self, workspace_id: int, connection_id: int) -> Dict:
        """
        Tests the specified connection within a workspace.

        Args:
            workspace_id: The ID of the target workspace.
            connection_id: The ID of the target connection to test.

        Returns:
            An ApiResult object, typically containing a success or failure message.

        Raises:
            SkyviaAPIError: If the API request fails or the test itself indicates an error.
        """
        return self.client.test_connection(workspace_id, connection_id)
    
    def list_integrations(self, workspace_id: int, skip: int = 0, take: int = 20) -> Dict:
        """
        Retrieves a list of integration packages within a specific workspace.

        Args:
            workspace_id: The ID of the target workspace.
            skip: Items to skip (default 0).
            take: Items to take (default 20, max 200).

        Returns:
            An object containing a list of integration DTOs and a 'hasMore' flag for pagination.

        Raises:
            SkyviaAPIError: If the API request fails.
        """
        return self.client.list_integrations(workspace_id, skip, take)
    
    def get_integration(self, workspace_id: int, integration_id: int) -> Dict:
        """
        Retrieves details for a specific integration package within a workspace.

        Args:
            workspace_id: The ID of the target workspace.
            integration_id: The ID of the target integration package.

        Returns:
            An IntegrationDto object with integration package details.

        Raises:
            SkyviaAPIError: If the API request fails (e.g., integration not found).
        """
        return self.client.get_integration(workspace_id, integration_id)
    
    def run_integration(self, workspace_id: int, integration_id: int) -> Dict:
        """
        Starts an execution run for the specified integration package.

        Args:
            workspace_id: The ID of the target workspace.
            integration_id: The ID of the target integration package to execute.

        Returns:
            An IntegrationExecutionLogDto object representing the initiated run (often shows 'Queued' or 'New' state initially).

        Raises:
            SkyviaAPIError: If the API request fails (e.g., integration not found, invalid state).
        """
        return self.client.run_integration(workspace_id, integration_id)

    def get_integration_executions(self, workspace_id: int, integration_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None, failed: Optional[bool] = None, skip: int = 0, take: int = 20, sort_order: str = 'asc', sort_by: str = 'startDate') -> Dict:
        """Retrieves finished execution history for a specific integration."""
        return self.client.get_integration_executions(workspace_id, integration_id, start_date, end_date, failed, skip, take, sort_order, sort_by)

    def get_integration_execution_details(self, workspace_id: int, integration_id: int, execution_id: int) -> Dict:
        """Retrieves details for a specific finished integration execution."""
        return self.client.get_integration_execution_details(workspace_id, integration_id, execution_id)

    def get_active_integration_execution(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Retrieves the state of the currently active execution for a specific integration."""
        return self.client.get_active_integration_execution(workspace_id, integration_id)

    def cancel_integration(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Cancels an active integration execution."""
        return self.client.cancel_integration(workspace_id, integration_id)

    def kill_integration(self, workspace_id: int, integration_id: int) -> Optional[Dict]:
        """Forcefully stops (kills) an active integration execution."""
        return self.client.kill_integration(workspace_id, integration_id)

    def get_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Retrieves the schedule status for a specific integration."""
        return self.client.get_integration_schedule(workspace_id, integration_id)

    def enable_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Enables the schedule for the specified integration."""
        return self.client.enable_integration_schedule(workspace_id, integration_id)

    def disable_integration_schedule(self, workspace_id: int, integration_id: int) -> Dict:
        """Disables the schedule for the specified integration."""
        return self.client.disable_integration_schedule(workspace_id, integration_id)


def main(): # Removed argument
    """Main entry point for the MCP server."""
    server = MCPServer()

    # Initialize the server (uses environment variable)
    init_result = server.initialize()
    if init_result.get("error"):
        # Log the error but continue to process MCP requests
        # MCP standard requires handling initialize/list even if client setup fails
        logger.error(f"Initialization failed: {init_result['error']}")
        # Optionally, we could exit here if initialization is absolutely critical
        # sys.exit(1)

    # Process input lines (MCP messages)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            
            # Write response to stdout
            json_response = json.dumps(response)
            sys.stdout.write(json_response + "\n")
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {line}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    # Removed argument parsing
    main()
