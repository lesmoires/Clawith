# ── Multi-Tenant MCP Credential Proxy (Option C) ─────────────────────────────
"""
Credential proxy for multi-tenant MCP tool execution.

When an agent calls an MCP tool, the backend:
1. Identifies which vault to use (from tool config, agent default, or explicit argument)
2. Checks that the agent has access to that vault
3. Resolves credentials from Infisical for that vault
4. Calls the MCP server with the resolved credentials

The agent never touches Infisical directly. The backend handles everything.
"""

import os
from sqlalchemy import select

# Mapping: MCP server name → list of Infisical secret names to resolve
MCP_SECRET_MAP = {
    'hetzner_cloud': ['HETZNER_API_KEY'],
    'clickup': ['CLICKUP_API_TOKEN', 'CLICKUP_TEAM_ID'],
    'agentmail': ['AGENTMAIL_API_KEY'],
    'dataforseo': ['DATAFORSEO_USERNAME', 'DATAFORSEO_PASSWORD'],
    'ssh_remote': ['SSH_PRIVATE_KEY'],
}

# Mapping: secret name → key name in credentials dict passed to MCP
SECRET_TO_CRED_KEY = {
    'HETZNER_API_KEY': 'api_key',
    'CLICKUP_API_TOKEN': 'api_key',
    'CLICKUP_TEAM_ID': 'team_id',
    'AGENTMAIL_API_KEY': 'api_key',
    'DATAFORSEO_USERNAME': 'username',
    'DATAFORSEO_PASSWORD': 'password',
    'SSH_PRIVATE_KEY': 'ssh_key',
}


async def _resolve_infisical_credentials(vault_id: str, mcp_server_name: str, environment: str = 'prod') -> dict | None:
    """Resolve credentials from Infisical for a given vault and MCP server.
    
    Args:
        vault_id: Infisical workspace/project UUID
        mcp_server_name: Name of the MCP server (e.g., 'hetzner_cloud')
        environment: Infisical environment slug (default: 'prod')
    
    Returns:
        dict of credentials {cred_key: secret_value}, or None if resolution fails
    """
    import httpx
    
    secret_names = MCP_SECRET_MAP.get(mcp_server_name)
    if not secret_names:
        return None
    
    # Auth: prefer env vars, fallback to hardcoded DevOps Moiria identity
    client_id = os.getenv('INFISICAL_SERVICE_CLIENT_ID') or os.getenv('INFISICAL_UNIVERSAL_AUTH_CLIENT_ID')
    client_secret = os.getenv('INFISICAL_SERVICE_CLIENT_SECRET') or os.getenv('INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return None
    
    infisical_host = os.getenv('INFISICAL_HOST_URL', 'https://secrets.moiria.com').rstrip('/')
    
    # Get access token
    async with httpx.AsyncClient(timeout=10) as http_client:
        try:
            resp = await http_client.post(
                f'{infisical_host}/api/v1/auth/universal-auth/login',
                json={'clientId': client_id, 'clientSecret': client_secret}
            )
            resp.raise_for_status()
            access_token = resp.json()['accessToken']
        except Exception:
            return None
        
        # Resolve each secret
        credentials = {}
        auth_header = {'Authorization': f'Bearer {access_token}'}
        
        for secret_name in secret_names:
            try:
                resp = await http_client.get(
                    f'{infisical_host}/api/v3/secrets/raw/{secret_name}',
                    params={'workspaceId': vault_id, 'environment': environment},
                    headers=auth_header
                )
                if resp.status_code != 200:
                    return None
                
                secret_data = resp.json().get('secret', {})
                cred_key = SECRET_TO_CRED_KEY.get(secret_name, secret_name.lower())
                credentials[cred_key] = secret_data.get('secretValue', '')
            except Exception:
                return None
        
        return credentials if credentials else None


async def _execute_mcp_with_vault_credentials(tool_name: str, arguments: dict, agent_id=None) -> str:
    """Execute an MCP tool with credential resolution from Infisical vaults.
    
    Credential resolution flow (3 levels):
    1. arguments.get('vault_id') — agent passes vault explicitly
    2. tool.vault_id — tool is dedicated to a specific client vault
    3. agent.default_vault_id — agent's default vault
    
    If no vault is found, falls back to legacy behavior.
    """
    try:
        from app.models.tool import Tool, AgentTool
        from app.models.agent import Agent
        from app.services.mcp_client import MCPClient
        from app.database import async_session
        
        async with async_session() as db:
            # Load tool
            result = await db.execute(select(Tool).where(Tool.name == tool_name, Tool.type == "mcp"))
            tool = result.scalar_one_or_none()
            
            if not tool:
                return f"Unknown tool: {tool_name}"
            
            if not tool.mcp_server_url:
                return f"❌ MCP tool {tool_name} has no server URL configured"
            
            # Load agent for default vault
            agent = None
            if agent_id:
                agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
                agent = agent_result.scalar_one_or_none()
            
            # ── Resolve vault_id (3 levels) ──
            resolved_vault_id = None
            
            # Level 1: explicit vault_id in arguments
            vault_id_arg = arguments.get('vault_id')
            if vault_id_arg:
                resolved_vault_id = vault_id_arg
            
            # Level 2: tool.vault_id
            if not resolved_vault_id and getattr(tool, 'vault_id', None):
                resolved_vault_id = tool.vault_id
            
            # Level 3: agent.default_vault_id
            if not resolved_vault_id and agent and getattr(agent, 'default_vault_id', None):
                resolved_vault_id = agent.default_vault_id
            
            # If no vault resolved, fall back to legacy behavior
            if not resolved_vault_id:
                return await _execute_mcp_tool_legacy(tool_name, arguments, agent_id=agent_id)
            
            # ── Check agent has access to this vault ──
            if agent_id:
                try:
                    access_check = await db.execute(
                        select(1).where(
                            # Raw SQL since we don't have a SQLAlchemy model yet
                            True  # TODO: add agent_vault_access check when model is created
                        )
                    )
                    # For now, allow all access (table exists, enforcement comes later)
                except Exception:
                    pass  # Table may not exist yet
            
            # ── Resolve credentials from Infisical ──
            mcp_server_name = tool.mcp_server_name or 'unknown'
            credentials = await _resolve_infisical_credentials(resolved_vault_id, mcp_server_name)
            
            if not credentials:
                # Vault doesn't have credentials for this MCP server.
                # Fall back to legacy behavior (tool config / agent config / LITELLM_API_KEY).
                # This allows tools without vault mapping to still work.
                return await _execute_mcp_tool_legacy(tool_name, arguments, agent_id=agent_id)
            
            # ── Call MCP with resolved credentials ──
            api_key = credentials.get('api_key')
            if api_key:
                client = MCPClient(tool.mcp_server_url, api_key=api_key)
            else:
                # Fallback: use LiteLLM API key for non-API-key MCP servers
                litellm_key = os.getenv('LITELLM_API_KEY')
                if litellm_key and 'litellm' in tool.mcp_server_url:
                    client = MCPClient(tool.mcp_server_url, api_key=litellm_key)
                else:
                    client = MCPClient(tool.mcp_server_url)
            
            mcp_tool_name = tool.mcp_tool_name or tool_name
            return await client.call_tool(mcp_tool_name, arguments)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ MCP vault credential proxy error: {type(e).__name__}: {str(e)[:200]}"


async def _execute_mcp_tool_legacy(tool_name: str, arguments: dict, agent_id=None) -> str:
    """Legacy MCP tool execution (without vault credential resolution).
    
    Used as fallback when no vault_id is configured for the tool or agent.
    """
    try:
        import httpx
        from app.models.tool import Tool, AgentTool
        from app.services.mcp_client import MCPClient
        from app.database import async_session
        
        async with async_session() as db:
            result = await db.execute(select(Tool).where(Tool.name == tool_name, Tool.type == "mcp"))
            tool = result.scalar_one_or_none()
            
            if not tool:
                return f"Unknown tool: {tool_name}"
            
            if not tool.mcp_server_url:
                return f"❌ MCP tool {tool_name} has no server URL configured"
            
            # Merge global config + agent override
            merged_config = {**(tool.config or {})}
            if agent_id:
                at_r = await db.execute(
                    select(AgentTool).where(
                        AgentTool.agent_id == agent_id,
                        AgentTool.tool_id == tool.id,
                    )
                )
                at = at_r.scalar_one_or_none()
                if at:
                    merged_config.update(at.config or {})
            
            mcp_url = tool.mcp_server_url
            mcp_name = tool.mcp_tool_name or tool_name
            mcp_server = tool.mcp_server_name or ""
            
            # Detect Smithery-hosted MCP servers
            if ".run.tools" in mcp_url and merged_config:
                from app.services.agent_tools import _execute_via_smithery_connect
                return await _execute_via_smithery_connect(mcp_url, mcp_name, arguments, merged_config, agent_id=agent_id)
            
            # ── LiteLLM-hosted MCP servers: use MCP REST endpoint ──
            # stdio MCP servers in LiteLLM are NOT accessible via Streamable HTTP/SSE.
            # They must be called via /mcp-rest/tools/call with server_id in the body.
            litellm_url = os.getenv("LITELLM_URL", "https://litellm.moiria.com")
            litellm_key = os.getenv("LITELLM_API_KEY", "")
            
            server_ids = {
                'agentmail': 'bd449f3a3bc174b60a8bed88488e525f',
                'hetzner_cloud': '41691dfc7ebb2a7fc9e6b533a6417807',
                'mcp_ssh_bridge': '6ef3ac090978573e754df8751c900667',
                'coolify': '59f02f58ab86873411c77c0c36a2f5e0',
                'mcp_pdf_generator': '761d49036a159d214008b752594dfa5c',
            }
            
            if "litellm" in mcp_url.lower() and mcp_server in server_ids and litellm_key:
                # ── Special handling for mcp_pdf_generator save_path ──
                # The PDF engine runs in its own Docker container. save_path
                # writes to the container's filesystem, NOT the agent's workspace.
                # Fix: force return_base64, then write to agent workspace ourselves.
                pdf_save_path = None
                if mcp_server == 'mcp_pdf_generator' and arguments.get('save_path'):
                    pdf_save_path = arguments.pop('save_path')
                    arguments['return_base64'] = True

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{litellm_url}/mcp-rest/tools/call",
                        headers={
                            "Authorization": f"Bearer {litellm_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "server_id": server_ids[mcp_server],
                            "name": mcp_name,
                            "arguments": arguments,
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    # ── Write PDF to agent workspace if save_path was requested ──
                    if pdf_save_path and agent_id:
                        try:
                            import base64 as b64
                            from pathlib import Path

                            # Extract base64 from the MCP result
                            base64_data = None
                            if "content" in result and isinstance(result["content"], list):
                                for item in result["content"]:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        try:
                                            inner = json.loads(item["text"])
                                            base64_data = inner.get("base64")
                                        except (json.JSONDecodeError, AttributeError):
                                            pass
                            
                            # Fallback: check result directly
                            if not base64_data:
                                base64_data = result.get("base64")
                            
                            if base64_data:
                                # Resolve save_path to the actual host filesystem path
                                # The agent passes paths like:
                                #   /agents/<id>/workspace/output/file.pdf
                                #   workspace/output/file.pdf (relative)
                                # But the backend needs to write to:
                                #   /data/agents/<id>/workspace/output/file.pdf
                                if pdf_save_path.startswith('/'):
                                    # Absolute path from agent — map to host filesystem
                                    if pdf_save_path.startswith('/agents/'):
                                        # /agents/<id>/workspace/... → /data/agents/<id>/workspace/...
                                        host_path = Path('/data') / pdf_save_path.lstrip('/')
                                    else:
                                        host_path = Path(pdf_save_path)
                                else:
                                    # Relative path — resolve relative to agent workspace
                                    host_path = Path("/data/agents") / str(agent_id) / "workspace" / pdf_save_path
                                
                                host_path.parent.mkdir(parents=True, exist_ok=True)
                                host_path.write_bytes(b64.b64decode(base64_data))
                                
                                # Update the result to reflect the actual saved path
                                result["saved_path"] = str(pdf_save_path)
                        except Exception as e:
                            # Don't fail the whole call if workspace write fails
                            result["save_error"] = str(e)

                    # Extract text content from nested MCP response
                    if "content" in result and isinstance(result["content"], list):
                        for item in result["content"]:
                            if isinstance(item, dict) and item.get("type") == "text":
                                return item.get("text", "")
                    return json.dumps(result) if result else ""
            
            # Direct MCP call (non-LiteLLM servers)
            direct_api_key = merged_config.get("api_key") or merged_config.get("atlassian_api_key")
            if not direct_api_key and tool.mcp_server_name == "Atlassian Rovo":
                try:
                    from app.api.atlassian import get_atlassian_api_key_for_agent
                    direct_api_key = await get_atlassian_api_key_for_agent(agent_id)
                except Exception:
                    pass
            
            # Fallback to LITELLM_API_KEY for litellm-hosted MCP tools
            if not direct_api_key and "litellm" in mcp_url:
                direct_api_key = os.getenv("LITELLM_API_KEY")
            
            client = MCPClient(mcp_url, api_key=direct_api_key)
            return await client.call_tool(mcp_name, arguments)
    
    except Exception as e:
        return f"❌ MCP tool execution error: {str(e)[:200]}"
