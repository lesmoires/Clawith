# LiteLLM MCP Deployment Guide

**Version:** 1.0  
**Date:** 2026-03-29  
**Author:** Clawith Repair  
**Status:** ✅ Production Tested (AgentMail MCP)

---

## 📖 OVERVIEW

This guide documents the complete pattern for deploying MCP (Model Context Protocol) servers to Clawith via LiteLLM proxy.

**Tested With:** AgentMail MCP (`agentmail-mcp`)  
**Next In Line:** Hetzner Cloud MCP (`@lazyants/hetzner-mcp-server`)

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFISICAL (Single Source of Truth)           │
│  Project: clawith (prod)                                        │
│  Secrets: AGENTMAIL_API_KEY, HETZNER_API_KEY, etc.              │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (manual sync)
┌─────────────────────────────────────────────────────────────────┐
│                    COOLIFY ENVIRONMENT VARIABLES                │
│  Service: LiteLLM (litellm.moiria.com)                          │
│  Env Vars: AGENTMAIL_API_KEY, HETZNER_API_KEY, etc.             │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (injected at runtime)
┌─────────────────────────────────────────────────────────────────┐
│                    LITEllM CONTAINER                            │
│  File: /app/config.yaml                                         │
│  Config: AGENTMAIL_API_KEY: os.environ/AGENTMAIL_API_KEY        │
│                                                                 │
│  MCP Server: agentmail-mcp (npx process)                        │
│  Reads: process.env.AGENTMAIL_API_KEY                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (MCP REST endpoint)
┌─────────────────────────────────────────────────────────────────┐
│                    LITEllM MCP REST API                         │
│  Endpoint: POST /mcp-rest/tools/call                            │
│  Payload: { server_id, name, arguments }                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (HTTP call)
┌─────────────────────────────────────────────────────────────────┐
│                    CLAWITH BACKEND                              │
│  File: backend/app/services/agent_tools.py                      │
│  Function: _litellm_mcp_call()                                  │
│  URL: https://litellm.moiria.com                                │
│  Key: LITELLM_API_KEY                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (tool call)
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT (Conver Thesis, Geo Presence, etc.)    │
│  Call: agentmail_inbox_lite(inboxId='...')                      │
│  NEVER sees API keys!                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 DEPLOYMENT CHECKLIST

### Phase 1: Infisical (Single Source of Truth)

| Step | Action | Command/Notes |
|------|--------|---------------|
| 1.1 | Create secret in Infisical | `AGENTMAIL_API_KEY`, `HETZNER_API_KEY`, etc. |
| 1.2 | Note secret value | Copy for Coolify sync |
| 1.3 | Document secret | Add to Infisical description |

**Important:** Infisical is the **single source of truth**. All API keys live here first.

---

### Phase 2: Coolify Environment Variables

| Step | Action | Command/Notes |
|------|--------|---------------|
| 2.1 | Go to Coolify UI | https://coolify.moiria.com |
| 2.2 | Find LiteLLM service | `litellm-wg0k80o88gcswco0ksgkkggc` |
| 2.3 | Add environment variable | `AGENTMAIL_API_KEY=<value from Infisical>` |
| 2.4 | Save | Do NOT commit to git |

**Security Rule:** Secrets live in Coolify env vars, NEVER in git.

---

### Phase 3: LiteLLM Configuration

| Step | Action | File/Notes |
|------|--------|------------|
| 3.1 | Edit config.yaml | `/app/config.yaml` in LiteLLM container |
| 3.2 | Add MCP server config | See template below |
| 3.3 | Use `os.environ/` reference | Never hardcode values |
| 3.4 | Redeploy LiteLLM | Via Coolify UI or `docker restart` |

**Config Template:**
```yaml
mcp_servers:
  agentmail:
    transport: stdio
    command: npx
    args:
      - -y
      - agentmail-mcp
    env:
      AGENTMAIL_API_KEY: os.environ/AGENTMAIL_API_KEY
    description: 'AgentMail.to - Email sending and receiving'

  hetzner_cloud:
    transport: stdio
    command: npx
    args:
      - -y
      - '@lazyants/hetzner-mcp-server'
    env:
      HETZNER_API_TOKEN: $HETZNER_API_KEY
    description: 'Hetzner Cloud - Server management'
```

---

### Phase 4: Clawith Backend — Code Changes

| Step | Action | File |
|------|--------|------|
| 4.1 | Add tool schemas to `AGENT_TOOLS` | `backend/app/services/agent_tools.py` |
| 4.2 | Add handler calls in `execute_tool()` | Same file |
| 4.3 | Add handler functions | Same file (end of file) |
| 4.4 | Commit + Push to git | `main` branch |
| 4.5 | Deploy backend | Via Coolify |

**Code Template — Tool Schema:**
```python
{
    "type": "function",
    "function": {
        "name": "agentmail_inbox_lite",
        "description": "List threads in a specific inbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "inboxId": {
                    "type": "string",
                    "description": "Email address of the inbox"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max threads to return",
                    "default": 10
                }
            },
            "required": ["inboxId"]
        }
    }
}
```

**Code Template — Handler Function:**
```python
async def _agentmail_inbox_lite(agent_id: uuid.UUID, arguments: dict) -> str:
    """List inbox via LiteLLM AgentMail MCP."""
    return await _litellm_mcp_call(agent_id, 'agentmail', 'list_threads', arguments)
```

**Code Template — Generic MCP Caller:**
```python
async def _litellm_mcp_call(agent_id: uuid.UUID, mcp_server: str, mcp_method: str, arguments: dict) -> str:
    """Generic LiteLLM MCP tool executor via REST API."""
    import httpx
    import json
    
    litellm_url = os.getenv('LITELLM_URL', 'https://litellm.moiria.com')
    litellm_key = os.getenv('LITELLM_API_KEY', 'REDACTED - use Infisical')
    
    # Map server name to server_id (get from LiteLLM UI or API)
    server_ids = {
        'agentmail': 'bd449f3a3bc174b60a8bed88488e525f',
        'hetzner_cloud': '41691dfc7ebb2a7fc9e6b533a6417807'
    }
    server_id = server_ids.get(mcp_server, mcp_server)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f'{litellm_url}/mcp-rest/tools/call',
                headers={
                    'Authorization': f'Bearer {litellm_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'server_id': server_id,
                    'name': mcp_method,
                    'arguments': arguments
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract text content from response
            if 'content' in result and isinstance(result['content'], list):
                for item in result['content']:
                    if isinstance(item, dict) and 'text' in item:
                        text_content = item['text']
                        try:
                            parsed = json.loads(text_content)
                            return json.dumps(parsed, indent=2)
                        except Exception as e:
                            return f'Parse error: {str(e)} - Content: {text_content[:200]}'
            if 'result' in result:
                return str(result['result'])
            return f'Error: Empty response from MCP server.'
                
    except httpx.HTTPError as e:
        return f'Error: LiteLLM MCP call failed - {str(e)[:100]}'
    except Exception as e:
        return f'Error: {str(e)[:100]}'
```

---

### Phase 5: Database — Tool Definitions

| Step | Action | SQL |
|------|--------|-----|
| 5.1 | Insert tool into `tools` table | See template below |
| 5.2 | Set `parameters_schema` | **CRITICAL** — Must match code |
| 5.3 | Set `type` = 'builtin' | For LiteLLM-backed tools |
| 5.4 | Set `enabled` = true | Activate tool |

**SQL Template:**
```sql
-- Insert tool definition
INSERT INTO tools (id, name, display_name, description, type, category, icon, parameters_schema, config, config_schema, enabled, is_default, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'agentmail_inbox_lite',
  'List Inbox Threads',
  'List threads in a specific inbox. Returns thread metadata including sender, subject, timestamp.',
  'builtin',
  'communication',
  '📬',
  '{"type":"object","required":["inboxId"],"properties":{"inboxId":{"type":"string","description":"Email address of the inbox"},"limit":{"type":"integer","description":"Max threads to return","default":10}}}'::json,
  '{}'::json,
  '{}'::json,
  true,
  false,
  NOW(),
  NOW()
);

-- Get the tool_id (for assignment)
SELECT id FROM tools WHERE name = 'agentmail_inbox_lite';
```

**⚠️ CRITICAL:** `parameters_schema` MUST match the schema in `AGENT_TOOLS` (Phase 4). If they don't match, the LLM will send wrong parameters → MCP validation error.

---

### Phase 6: Database — Agent Assignments

| Step | Action | SQL |
|------|--------|-----|
| 6.1 | Find agent ID | `SELECT id FROM agents WHERE name = '...';` |
| 6.2 | Find tool ID | `SELECT id FROM tools WHERE name = '...';` |
| 6.3 | Insert into `agent_tools` | See template below |
| 6.4 | Set `enabled` = true | Activate for agent |

**SQL Template:**
```sql
-- Assign tool to agent
INSERT INTO agent_tools (id, agent_id, tool_id, enabled, config, source, created_at)
VALUES (
  gen_random_uuid(),
  'ccc2ba97-6dc3-466f-8558-8695c6264e16',  -- Conver Thesis
  '<tool_id_from_phase_5>',
  true,
  '{}',
  'system',
  NOW()
);

-- Verify assignment
SELECT t.name, a.name as agent
FROM tools t
JOIN agent_tools at ON t.id = at.tool_id
JOIN agents a ON at.agent_id = a.id
WHERE t.name LIKE '%agentmail%';
```

---

### Phase 7: Testing & Validation

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | List tools (agent side) | Tool appears in agent's tool list |
| 7.2 | Call tool with valid params | Success response |
| 7.3 | Call tool with invalid params | Validation error (not crash) |
| 7.4 | Check backend logs | No errors |
| 7.5 | Check LiteLLM logs | MCP call successful |

**Test Command (via agent):**
```
agentmail_inbox_lite with:
- inboxId: 'conver.thesis@agentmail.to'
- limit: 5
```

**Expected Response:**
```json
{
  "count": 2,
  "threads": [...]
}
```

---

## 🐛 TROUBLESHOOTING

### Error: "Unknown tool: agentmail_*"

**Cause:** Tool not in `AGENT_TOOLS` array or not assigned in DB.

**Fix:**
1. Check `backend/app/services/agent_tools.py` — schema present?
2. Check DB — tool exists in `tools` table?
3. Check DB — tool assigned in `agent_tools` table?

---

### Error: "Input validation error: Invalid arguments for tool"

**Cause:** `tools.parameters_schema` in DB doesn't match what LLM sends.

**Fix:**
1. Check `tools.parameters_schema` in DB
2. Check `AGENT_TOOLS` schema in code
3. They MUST match exactly (required fields, types, etc.)

**Example Mismatch:**
```sql
-- DB says:
{"required": [], "properties": {}}

-- But MCP expects:
{"required": ["inboxId"], "properties": {"inboxId": {"type": "string"}}}
```

**Solution:** Update DB:
```sql
UPDATE tools 
SET parameters_schema = '{"type":"object","required":["inboxId"],"properties":{"inboxId":{"type":"string"}}}'::json 
WHERE name = 'agentmail_inbox_lite';
```

---

### Error: "403 Forbidden" from AgentMail API

**Cause:** API key revoked or wrong key in Coolify.

**Fix:**
1. Check Infisical for correct key
2. Update Coolify env var
3. Restart LiteLLM container

**Verification:**
```bash
curl -X GET "https://api.agentmail.to/v0/inboxes" \
  -H "Authorization: Bearer <key_from_coolify>"
# Expected: {"count": 3, "inboxes": [...]}
```

---

### Error: "No content in attachment response"

**Cause:** MCP returns `downloadUrl`, code expects `content` (base64).

**Fix:** Update handler to fetch from URL:
```python
download_url = attachment_data.get('downloadUrl', '')
if download_url:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(download_url)
        file_content = response.content
```

---

### Error: "unsupported operand type(s) for /: 'PosixPath' and 'UUID'"

**Cause:** UUID not converted to string in path concatenation.

**Fix:**
```python
# Wrong
workspace_path = WORKSPACE_ROOT / agent_id / 'workspace' / save_path

# Correct
workspace_path = WORKSPACE_ROOT / str(agent_id) / 'workspace' / save_path
```

---

## 📚 LESSONS LEARNED (AgentMail MCP Deployment)

### What Went Wrong

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Tools not working | `tools.parameters_schema` was empty `{}` in DB | UPDATE all 12 tools |
| 403 Forbidden | Coolify had old/revoked API key | Sync from Infisical |
| UUID error | Path concatenation bug | `str(agent_id)` |
| Attachment download fail | MCP returns URL, not base64 | Fetch from URL |

### What Went Right

| Success | Why |
|---------|-----|
| LiteLLM MCP proxy | Clean separation of concerns |
| `os.environ/` pattern | Secrets never in git |
| `_litellm_mcp_call()` generic handler | Reusable for all MCPs |
| Infisical as single source | Easy rotation, audit trail |

---

## 🚀 NEXT MCP — HETZNER CLOUD

**Planned:** Hetzner Cloud MCP for DevOps Moiria agent.

**Steps:**
1. ✅ Add `HETZNER_API_KEY` to Infisical (already done)
2. ⏳ Sync to Coolify LiteLLM env vars
3. ⏳ Add to LiteLLM `config.yaml`
4. ⏳ Add 5 tool schemas to `AGENT_TOOLS`
5. ⏳ Add handlers to `agent_tools.py`
6. ⏳ Insert into DB `tools` table
7. ⏳ Assign to DevOps Moiria agent
8. ⏳ Test all 5 tools

**Estimated Time:** 30-45 minutes (now that pattern is documented)

---

## 📞 CONTACT

**For Issues:** @guillaume (Clawith Maintainer)  
**Documentation:** `/data/workspace/LITELLM_MCP_DEPLOYMENT_GUIDE.md`  
**Git Repo:** https://github.com/lesmoires/Clawith

---

**Last Updated:** 2026-03-29  
**Version:** 1.0 (Production Tested)
