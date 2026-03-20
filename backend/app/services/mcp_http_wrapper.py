"""
MCP HTTP Wrapper - Exposes stdio MCP servers as HTTP/SSE endpoints.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import subprocess
import threading
import queue
import uuid

app = FastAPI(title="MCP HTTP Wrapper")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_mcp_process: Optional[subprocess.Popen] = None
_mcp_queue: queue.Queue = queue.Queue()
_request_counter = 0
_response_cache: Dict[str, Any] = {}


def get_infisical_env() -> Dict[str, str]:
    """Get Infisical environment variables."""
    return {
        "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "INFISICAL_HOST_URL": os.environ.get("INFISICAL_HOST_URL", "https://app.infisical.com"),
        "INFISICAL_UNIVERSAL_AUTH_CLIENT_ID": os.environ.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_ID", ""),
        "INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET": os.environ.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET", ""),
    }


def start_mcp_process():
    """Start MCP stdio process in a thread."""
    global _mcp_process
    
    if _mcp_process is not None:
        return
    
    env = get_infisical_env()
    print(f"🚀 Starting MCP HTTP Wrapper", file=sys.stderr)
    print(f"   INFISICAL_HOST_URL: {env['INFISICAL_HOST_URL']}", file=sys.stderr)
    print(f"   Client ID: {env['INFISICAL_UNIVERSAL_AUTH_CLIENT_ID'][:20]}...", file=sys.stderr)
    
    try:
        _mcp_process = subprocess.Popen(
            ["npx", "-y", "@infisical/mcp"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print(f"✓ MCP process started (PID: {_mcp_process.pid})", file=sys.stderr)
        
        # Start stdout reader thread
        def read_stdout():
            for line in _mcp_process.stdout:
                _mcp_queue.put(line)
        
        reader_thread = threading.Thread(target=read_stdout, daemon=True)
        reader_thread.start()
        
    except Exception as e:
        print(f"✗ Failed to start MCP process: {e}", file=sys.stderr)


def send_mcp_request(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send JSON-RPC request to MCP process."""
    global _request_counter
    
    if _mcp_process is None:
        start_mcp_process()
        import time
        time.sleep(2)  # Wait for process to start
    
    if _mcp_process is None or _mcp_process.poll() is not None:
        return {"error": "MCP process not running"}
    
    # Build request
    _request_counter += 1
    request = {
        "jsonrpc": "2.0",
        "id": _request_counter,
        "method": method,
        "params": params or {}
    }
    
    # Send request
    request_json = json.dumps(request) + "\n"
    print(f"→ Sending: {request_json.strip()}", file=sys.stderr)
    _mcp_process.stdin.write(request_json)
    _mcp_process.stdin.flush()
    
    # Wait for response (timeout 30s)
    try:
        response_line = _mcp_queue.get(timeout=30)
        response = json.loads(response_line)
        print(f"← Received: {json.dumps(response, indent=2)[:500]}", file=sys.stderr)
        return response
    except queue.Empty:
        return {"error": "Timeout waiting for MCP response"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}"}


@app.get("/health")
@app.post("/health")
async def health_check():
    """Health check endpoint."""
    is_running = _mcp_process is not None and _mcp_process.poll() is None
    return {"status": "healthy", "mcp_connected": is_running}


@app.get("/mcp/sse")
@app.post("/mcp/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP messages."""
    async def event_generator():
        while True:
            try:
                line = _mcp_queue.get(timeout=60)
                yield f"data: {line}\n\n"
            except queue.Empty:
                yield ": heartbeat\n\n"
            except Exception as e:
                print(f"SSE error: {e}", file=sys.stderr)
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/mcp/messages")
async def messages_endpoint(request: Request):
    """POST endpoint for sending MCP JSON-RPC requests."""
    try:
        body = await request.json()
        
        # Send via MCP process
        if _mcp_process is None:
            start_mcp_process()
        
        request_json = json.dumps(body) + "\n"
        _mcp_process.stdin.write(request_json)
        _mcp_process.stdin.flush()
        
        return JSONResponse({"status": "sent", "id": body.get("id")})
    except Exception as e:
        print(f"Message error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/mcp/call")
async def call_tool(request: Request):
    """Direct tool call endpoint."""
    try:
        body = await request.json()
        result = send_mcp_request(
            body.get("method", "tools/call"),
            body.get("params", {})
        )
        return JSONResponse(result)
    except Exception as e:
        print(f"Call tool error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/mcp/tools")
@app.post("/mcp/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        result = send_mcp_request("tools/list", {})
        if "error" in result:
            return JSONResponse(result, status_code=500)
        return JSONResponse(result.get("result", {}))
    except Exception as e:
        print(f"List tools error: {e}", file=sys.stderr)
        return JSONResponse({"error": str(e)}, status_code=500)


# Start MCP process on module load
start_mcp_process()
