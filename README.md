# Skyvia MCP Server

A Model Context Protocol (MCP) server for interacting with the Skyvia API, focusing on integration-related endpoints.

## Overview

This MCP server provides tools to interact with the Skyvia API, allowing you to:

- Manage workspaces
- Manage connections
- List, view, and run integrations
- And more

The server is designed to be deployed on Smithery for easy access via WebSocket connections.

## Tools

### Workspace Tools
- `list_workspaces`: Retrieve all available workspaces
- `get_workspace`: Get details about a specific workspace

### Connection Tools
- `list_connections`: List connections in a workspace
- `get_connection_details`: Get details about a specific connection
- `test_connection`: Test a connection

### Integration Tools
- `list_integrations`: List integrations in a workspace
- `get_integration`: Get details about a specific integration
- `run_integration`: Execute an integration

## Deployment

### Prerequisites
- Docker installed on your local machine
- Access to Smithery deployment
- Skyvia API token

### Local Testing

To test the MCP server locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   export SKYVIA_API_TOKEN="your-api-token-here"
   ```

3. Run the server:
   ```
   python main.py
   ```

4. Use an MCP client like MCP Inspector to test:
   ```
   npx @modelcontextprotocol/inspector python main.py
   ```

### Smithery Deployment

1. Add the server to Smithery
2. Configure the server with your Skyvia API token
3. Deploy and test the server through Smithery's interface

## Configuration

The server requires a Skyvia API token to authenticate with the Skyvia API. This token should be provided via the `SKYVIA_API_TOKEN` environment variable.

## Usage Examples

Here's how to use some of the tools:

### List Workspaces

```javascript
// Example MCP client code
const result = await client.useToolWithMCP("list_workspaces", {});
console.log(result);
```

### List Integrations

```javascript
// Example MCP client code
const result = await client.useToolWithMCP("list_integrations", {
  workspace_id: 123 // Replace with your workspace ID
});
console.log(result);
```

### Run an Integration

```javascript
// Example MCP client code
const result = await client.useToolWithMCP("run_integration", {
  workspace_id: 123, // Replace with your workspace ID
  integration_id: 456 // Replace with your integration ID
});
console.log(result);
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
