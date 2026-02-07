# WikiMed MCP Server

## Introduction

WikiMed MCP Server is a Model Context Protocol (MCP) server that provides a standardized interface for interacting with the WikiMed medical management system. It exposes various medical appointment and patient management functions through MCP tools, enabling AI agents and applications to seamlessly integrate with WikiMed's API.

This server handles:

- Doctor information and search
- Appointment scheduling and management
- Patient record lookup
- Financial reports (invoices, daily income)
- System administration tasks

The server supports both streamable HTTP transport for production deployments and standard I/O for local development and testing.

## Directory Structure

```
mcp-server-qs/
├── server/                 # Main server package
│   ├── __init__.py        # Package initialization, exports mcp instance
│   ├── __main__.py        # Entry point for running as module
│   └── app.py             # Core server implementation with MCP tools
├── __pycache__/           # Python bytecode cache
├── Dockerfile             # Docker container configuration
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependency versions
└── README.md              # This documentation file
```

## Dependencies

### Python Version

- **Python 3.13 or higher** (required)

### Core Dependencies

The project uses the following Python packages (defined in `pyproject.toml`):

- **mcp[cli,rich,ws]** (>=1.26.0) - Model Context Protocol SDK with CLI, Rich terminal formatting, and WebSocket support
- **trio** (>=0.32.0) - Async I/O framework
- **xmltodict** (>=1.0.2) - XML to dictionary parser for API responses
- **httpx** - Async HTTP client (installed as MCP dependency)

### Development Tools

- **uv** - Fast Python package installer and resolver (recommended for development)

## Installation

### Prerequisites

1. Install Python 3.13 or higher
2. (Optional but recommended) Install `uv` for faster dependency management:
   ```powershell
   pip install uv
   ```

### Local Installation

1. Clone the repository:

   ```powershell
   git clone <repository-url>
   cd mcp-server-qs
   ```

2. Install dependencies using uv (recommended):

   ```powershell
   uv sync
   ```

   Or using pip:

   ```powershell
   pip install -e .
   ```

## Running the Server

### Option 1: Run Locally (Development)

#### Using uv (recommended):

```powershell
uv run python -m server --host 0.0.0.0 --port 8000 --transport streamable-http
```

#### Using standard Python:

```powershell
python -m server --host 0.0.0.0 --port 8000 --transport streamable-http
```

#### Command-line Arguments:

- `--host`: Host address to bind (default: `0.0.0.0`)
- `--port`: Port number (default: `8000`)
- `--transport`: Transport protocol (options: `streamable-http`, `stdio`; default: `streamable-http`)

#### For stdio transport (used by MCP clients like Claude Desktop):

```powershell
uv run python -m server --transport stdio
```

### Option 2: Run with Docker

#### Build the Docker Image:

```powershell
docker build -t wikimed-mcp-server:latest .
```

#### Run the Container:

```powershell
docker run -p 8000:8000 wikimed-mcp-server:latest
```

The server will be accessible at `http://localhost:8000`.

#### Custom Configuration:

```powershell
docker run -p 3005:8000 wikimed-mcp-server:latest
```

This maps the container's port 8000 to your host's port 3005.

## Testing the Server

### Option 1: Using Claude Desktop (Recommended)

1. **Configure Claude Desktop** to use your MCP server by adding to the configuration file:

   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "wikimed": {
         "command": "uv",
         "args": ["run", "python", "-m", "server", "--transport", "stdio"],
         "cwd": "c:\\dev\\mcp-server-qs"
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Test the server** by asking Claude:
   - "List all available tools from the WikiMed server"
   - "Get WikiMed system information"
   - "List all doctors"

### Option 2: Using VS Code with MCP Extension

1. **Install the MCP Inspector extension** in VS Code (search for "MCP" in extensions)

2. **Configure the server** in VS Code settings or use the MCP Inspector UI

3. **Connect to the server** at `http://localhost:8000` (for HTTP transport)

### Option 3: Using MCP Inspector (Command Line)

```powershell
npx @modelcontextprotocol/inspector uv run python -m server --transport stdio
```

This will launch a web interface where you can:

- View all available tools
- Test tool invocations
- See request/response logs

### Option 4: Manual HTTP Testing

If running with `streamable-http` transport, you can test using curl or Postman:

```powershell
# Test server health
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools
```

### Verify Server is Working

Look for successful responses:

- **Stdio transport**: Check terminal logs for "WikiMed MCP Server" initialization
- **HTTP transport**: Server should respond to health checks and tool listings
- **Tool execution**: Test a simple tool like `get_wikimed_info` to verify API connectivity

## Code Structure

### Core Components

#### `server/app.py` - Main Server Implementation

**Configuration Management:**

- `client_configs` (dict): In-memory storage for client-specific WikiMed credentials
- `get_client_config(client_id)`: Retrieves config for a client, falls back to default hardcoded values

**Utility Functions:**

- `convert_xml_to_json(xml_data)`: Converts WikiMed XML responses to JSON
- `make_wikimed_request(params, client_id)`: Handles HTTP requests to WikiMed API with error handling

**MCP Tools (Functions exposed to AI agents):**

1. **Configuration:**

   - `configure_client`: Set up client credentials (base_url, hcode)

2. **System Information:**

   - `get_wikimed_info`: Retrieve system info (MType: 100)
   - `restart_service`: Restart WikiMed service (MType: 1300)

3. **Doctor Management:**

   - `list_doctors`: Get all doctors (MType: 500)
   - `find_doctor_by_name`: Search by name with fuzzy matching (MType: 600)
   - `find_doctor_by_code`: Search by doctor code (MType: 600)

4. **Appointment Management:**

   - `create_appointment`: Schedule new appointment (MType: 700)
   - `find_nearest_slot`: Find available time slots (MType: 800)
   - `confirm_appointment`: Confirm/cancel/update appointment (MType: 900)
   - `get_appointment`: Retrieve appointment details (MType: 910)
   - `list_appointments`: Get appointments by date (MType: 1000)

5. **Patient Management:**

   - `search_patient`: Find patient by file number, phone, or social ID (MType: 1100)

6. **Financial Reports:**
   - `get_patient_invoice`: Get patient billing summary (MType: 1200)
   - `get_daily_income`: Get daily income report (MType: 1200)

#### `server/__init__.py`

Exports the MCP instance for use by other modules.

#### `server/__main__.py`

Entry point that runs the server when executed as a module.

## Dynamic Client Configuration

### Current Issue

Currently, client configurations (base_url and hcode) are **hardcoded** in the `get_client_config` function:

```python
def get_client_config(client_id: str = "") -> dict:
    """Get client configuration by ID"""
    if not client_id or client_id not in client_configs:
        return {"base_url": "http://edrak1.selfip.com:64384", "hcode": "13745064"}
    return client_configs[client_id]
```

This means all clients without specific configurations use the same default credentials, which is not ideal for multi-tenant deployments.

### Solution: Dynamic Configuration via MCP Resources

MCP provides a **Resources** feature that allows servers to request configuration from the client at session initialization. Here's how to implement it:

#### Step 1: Add MCP Resource Handler

Add this code to `server/app.py`:

```python
@mcp.resource("config://client")
async def get_client_configuration() -> str:
    """
    Resource that agents should provide with client configuration.
    The agent/client should provide a JSON with: base_url and hcode
    """
    return json.dumps({
        "schema": {
            "base_url": "string (required) - WikiMed API base URL",
            "hcode": "string (required) - Hospital/clinic code"
        },
        "example": {
            "base_url": "http://edrak1.selfip.com:64384",
            "hcode": "13745064"
        }
    })
```

#### Step 2: Update Client Configuration Logic

Modify the initialization to request config from the client:

```python
# At the top of app.py, add:
from mcp.server.session import ServerSession

# Global to store session-specific configs
session_configs = {}

@mcp.on_session_start()
async def on_session_start(session: ServerSession):
    """Called when a new MCP session starts"""
    session_id = id(session)

    # Request configuration from the client
    try:
        # Client should provide this resource
        config_data = await session.read_resource("config://wikimed-credentials")
        config = json.loads(config_data)

        if "base_url" in config and "hcode" in config:
            session_configs[session_id] = config
            logger.info(f"Session {session_id} configured with custom credentials")
        else:
            logger.warning(f"Session {session_id} missing required config fields")
    except Exception as e:
        logger.warning(f"Could not load config for session {session_id}: {e}")
        logger.info("Using default configuration")

@mcp.on_session_end()
async def on_session_end(session: ServerSession):
    """Clean up session config when session ends"""
    session_id = id(session)
    if session_id in session_configs:
        del session_configs[session_id]
        logger.info(f"Cleaned up config for session {session_id}")
```

#### Step 3: Update get_client_config

```python
def get_client_config(session_id: str = None) -> dict:
    """Get client configuration by session ID"""
    if session_id and session_id in session_configs:
        return session_configs[session_id]

    # Fallback to default (for backwards compatibility)
    logger.warning("Using default hardcoded configuration")
    return {"base_url": "http://edrak1.selfip.com:64384", "hcode": "13745064"}
```

#### Step 4: Pass Session Context to Tools

Update all tool functions to accept and pass session context:

```python
@mcp.tool()
async def list_doctors(session: ServerSession) -> str:
    """Get list of all doctors"""
    session_id = id(session)
    params = {"MType": "500"}
    return await make_wikimed_request(params, session_id)
```

#### Step 5: Client-Side Configuration

When connecting to the MCP server, clients (like Claude Desktop) need to provide the resource:

**claude_desktop_config.json:**

```json
{
  "mcpServers": {
    "wikimed": {
      "command": "uv",
      "args": ["run", "python", "-m", "server", "--transport", "stdio"],
      "cwd": "c:\\dev\\mcp-server-qs",
      "env": {
        "WIKIMED_BASE_URL": "http://your-server.com:64384",
        "WIKIMED_HCODE": "your-hcode"
      }
    }
  }
}
```

Then read from environment variables in the server:

```python
import os

def get_default_config() -> dict:
    """Get configuration from environment variables or hardcoded defaults"""
    return {
        "base_url": os.getenv("WIKIMED_BASE_URL", "http://edrak1.selfip.com:64384"),
        "hcode": os.getenv("WIKIMED_HCODE", "13745064")
    }
```

### Alternative: Environment Variables (Simpler)

For a simpler approach without MCP Resources:

1. **Read from environment variables** at startup
2. **Allow clients to set env vars** in their MCP client configuration
3. **Each server instance** uses its own environment-provided credentials

This is simpler but requires restarting the server for config changes.

## API Reference

All tools accept a `client_id` parameter for client-specific configuration. Dates should be in `DD/MM/YYYY` format, times in `HH:MM` format.

For detailed API parameters and responses, refer to the WikiMed API documentation or inspect tool definitions in `server/app.py`.

## Logging

The server logs to stderr with INFO level by default. Logs include:

- Server initialization
- Client configuration changes
- HTTP request successes/failures
- XML parsing errors
- Session lifecycle events

## License

[Specify your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]
