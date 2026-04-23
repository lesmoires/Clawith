---
name: clawith-skills-and-tools-seeder
description: Seed skills and MCP tools into Clawith platform. Use when: (1) deploying Clawith to a new instance, (2) adding new MCP servers/tools, (3) recovering from data loss, (4) syncing skills/tools after a migration. Handles: skills (DB + disk), tools (DB), agent tool assignments, MCP server registration in LiteLLM. Idempotent.
requires:
  env:
    - LITELLM_URL
    - LITELLM_API_KEY
---

# Clawith Skills & Tools Seeder

Automates seeding of skills and MCP tools into Clawith after a fresh deploy or data recovery. Idempotent - safe to run multiple times.

## What it seeds

### Skills (3 layers - all required)
1. **DB**: `skills` table (metadata: name, folder_name, description, category, icon)
2. **DB**: `skill_files` table (SKILL.md + references content)
3. **Disk**: Docker volume at `/var/lib/docker/volumes/{app}_agent_data/_data/{agent_id}/skills/<folder>/`

### MCP Tools (2 layers)
1. **DB**: `tools` table (name, type, mcp_server_name, mcp_server_url, display_name, description, parameters_schema, config, config_schema, category, icon, enabled, is_default, source)
2. **DB**: `agent_tools` table (agent_id, tool_id mapping with enabled flag)

### MCP Servers (1 layer)
1. **LiteLLM**: Registered via `POST /v1/mcp/server` API

## Usage

### Full seed
```bash
python3 seed_all.py \
  --db-url "postgresql://clawith:PASS@postgres:5432/clawith" \
  --agent-id "29ae0878-93a8-476d-9fb1-9786aaaa3902" \
  --litellm-url "https://litellm.moiria.com" \
  --litellm-key "sk-..." \
  --volume-path "/var/lib/docker/volumes/twcgssk04ckw4kgw0gcwcw48_agent_data/_data"
```

### Options
- `--skills-only` - Only seed skills
- `--tools-only` - Only seed MCP tools  
- `--mcp-server NAME` - Only seed tools for this MCP server
- `--dry-run` - Show SQL without executing

## Idempotency
- Skills: `ON CONFLICT (folder_name) DO NOTHING`
- Skill files: `ON CONFLICT (skill_id, path) DO NOTHING`
- Tools: `ON CONFLICT (name) DO NOTHING`
- Agent tools: `ON CONFLICT (agent_id, tool_id) DO UPDATE SET enabled = EXCLUDED.enabled`
