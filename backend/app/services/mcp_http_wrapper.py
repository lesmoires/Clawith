"""
MCP HTTP Wrapper - Exposes stdio MCP servers as HTTP/SSE endpoints.

Usage:
    python mcp_http_wrapper.py --command npx --args "-y,@infisical/mcp" --port 8888

Environment variables for @infisical/mcp:
    INFISICAL_HOST_URL
    INFISICAL_UNIVERSAL_AUTH_CLIENT_ID
    INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET
"""

import asyncio
import json
import os
import sys
import argparse
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.shared.message import SessionMessage
import uuid

app = FastAPI(title="MCP HTTP Wrapper")

# Global state
_mcp_streams: Optional[tuple] = None
_mcp_process: Optional[Any] = None
_request_counter = 0


def get_env_with_prefix(prefix: str = "") -> Dict[str, str]:
    """Get environment variables, optionally filtered by prefix."""
    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}
    return env


async def get_mcp_streams(command: str, args: list[str], env: Dict[str, str]):
    """Initialize or return existing MCP stdio streams."""
    global _mcp_streams, _mcp_process
    
    if _mcp_streams is None:
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **env}
        )
        _mcp_streams = await stdio_client(server_params).__aenter__()
        print(f"✓ MCP server started: {command} {' '.join(args)}", file=sys.stderr)
    
    return _mcp_streams


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mcp_connected": _mcp_streams is not None}


@app.get("/mcp/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP messages."""
    async def event_generator():
        read_stream, _ = _mcp_streams
        
        try:
            async for message in read_stream:
                if isinstance(message, SessionMessage):
                    data = message.message.model_dump_json(by_alias=True)
                    yield f"data: {data}\n\n"
        except Exception as e:
            print(f"SSE error: {e}", file=sys.stderr)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/mcp/messages")
async def messages_endpoint(request: Request):
    """POST endpoint for sending MCP JSON-RPC requests."""
    global _request_counter
    
    try:
        body = await request.json()
        _, write_stream = _mcp_streams
        
        # Add request ID if not present
        if "id" not in body:
            _request_counter += 1
            body["id"] = _request_counter
        
        # Send via stdio
        await write_stream.send(SessionMessage(message=body))
        
        return JSONResponse({"status": "sent", "id": body.get("id")})
    except Exception as e:
        print(f"Message error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/mcp/call")
async def call_tool(request: Request):
    """Direct tool call endpoint (simpler for testing)."""
    try:
        body = await request.json()
        read_stream, write_stream = _mcp_streams
        
        # Build JSON-RPC request
        request_id = str(uuid.uuid4())
        rpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": body.get("method", "tools/call"),
            "params": body.get("params", {})
        }
        
        # Send request
        await write_stream.send(SessionMessage(message=rpc_request))
        
        # Wait for response (timeout 30s)
        async with asyncio.timeout(30):
            async for message in read_stream:
                if isinstance(message, SessionMessage):
                    response = message.message.model_dump()
                    if response.get("id") == request_id:
                        return JSONResponse(response)
        
        return JSONResponse({"error": "Timeout waiting for response"}, status_code=504)
    except Exception as e:
        print(f"Call tool error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        read_stream, write_stream = _mcp_streams
        
        # Send tools/list request
        request_id = str(uuid.uuid4())
        rpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list",
            "params": {}
        }
        
        await write_stream.send(SessionMessage(message=rpc_request))
        
        # Wait for response
        async with asyncio.timeout(10):
            async for message in read_stream:
                if isinstance(message, SessionMessage):
                    response = message.message.model_dump()
                    if response.get("id") == request_id:
                        return JSONResponse(response.get("result", {}))
        
        return JSONResponse({"error": "Timeout"}, status_code=504)
    except Exception as e:
        print(f"List tools error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


def main():
    parser = argparse.ArgumentParser(description="MCP HTTP Wrapper")
    parser.add_argument("--command", default="npx", help="Command to run (default: npx)")
    parser.add_argument("--args", default="-y,@infisical/mcp", help="Arguments (comma-separated)")
    parser.add_argument("--port", type=int, default=8888, help="HTTP port (default: 8888)")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    # Parse args
    cmd_args = args.args.split(",") if args.args else []
    
    print(f"🚀 Starting MCP HTTP Wrapper", file=sys.stderr)
    print(f"   Command: {args.command}", file=sys.stderr)
    print(f"   Args: {cmd_args}", file=sys.stderr)
    print(f"   Port: {args.port}", file=sys.stderr)
    print(f"   Infisical URL: {os.environ.get('INFISICAL_HOST_URL', 'not set')}", file=sys.stderr)
    
    # Start wrapper
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
