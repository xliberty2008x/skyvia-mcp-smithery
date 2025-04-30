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

## Troubleshooting

### "Server not initialized" Error

If you receive a "Server not initialized" error when trying to use the server tools, this typically indicates that the server did not properly initialize due to a missing or invalid API token. To resolve this:

1. Verify your Skyvia API token is valid and has the necessary permissions.
2. Make sure the `SKYVIA_API_TOKEN` environment variable is properly set:
   - For local testing, use `export SKYVIA_API_TOKEN="your-token-here"`
   - For Smithery deployment, ensure the token is correctly set in your Smithery profile

### Diagnosing Connection Issues

The repository includes a dedicated diagnostic script for testing connectivity:

```bash
# Set your API token
export SKYVIA_API_TOKEN="your-token-here"

# Optionally set your Smithery API key (if using a different one)
export SMITHERY_API_KEY="your-smithery-api-key"

# Run the diagnostic script
python test_smithery_connection.py
```

This script will:
- Test direct connection to a locally running server
- Test connection to the Smithery-deployed server
- Provide detailed logs and troubleshooting guidance
- Compare results to help isolate if the issue is with Smithery configuration or the server itself

### Common Issues

1. **Missing Dependencies**: Ensure you've installed all required packages with `pip install -r requirements.txt`
2. **Invalid API Token**: The token may be expired or have insufficient permissions
3. **Smithery Profile Issue**: If using Smithery, check that your profile has the correct configuration with the API token
4. **Networking Issues**: If behind a corporate firewall, check if websocket connections are allowed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
