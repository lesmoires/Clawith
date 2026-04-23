---
name: clawith-skills-and-tools-seeder
description: Seed ALL skills and ALL MCP tools into Clawith platform. Use when: (1) deploying Clawith to a new instance, (2) adding new MCP servers/tools, (3) recovering from data loss, (4) syncing skills/tools after a migration. Handles: skills (DB + disk + volume), tools (DB + agent mapping), MCP server registration. Idempotent. Auto-discovers skills from workspace.
requires:
  env:
    - LITELLM_URL
    - LITELLM_API_KEY
---

# Clawith Skills & Tools Seeder

Automates seeding of ALL skills and ALL MCP tools into Clawith after a fresh deploy or data recovery. Idempotent — safe to run multiple times.

## Lessons learned (why this exists)

### Mistake #1: Skills in DB but not on disk
Skills were inserted into `skills` and `skill_files` tables, but the Docker volume wasn't updated. The frontend reads from the volume, so skills didn't appear in UI.

**Fix:** Seeder writes to BOTH DB AND Docker volume.

### Mistake #2: Tools created but not mapped
Tools were inserted into `tools` table but not into `agent_tools`. Agent couldn't see them.

**Fix:** Seeder inserts into BOTH `tools` AND `agent_tools` in one pass.

### Mistake #3: MCP server in config but not registered
LiteLLM config had `mcp_servers` section but server wasn't registered via API. Tools weren't discoverable.

**Fix:** Seeder registers MCP servers via `POST /v1/mcp/server` API.

## What it seeds

### Skills (3 layers — ALL required)
1. **DB**: `skills` table (`ON CONFLICT (folder_name) DO NOTHING`)
2. **DB**: `skill_files` table (`ON CONFLICT (skill_id, path) DO NOTHING`)
3. **Disk**: Docker volume `...agent_data/{agent_id}/skills/<folder>/`

### MCP Tools (2 layers)
1. **DB**: `tools` table (`ON CONFLICT (name) DO NOTHING`)
2. **DB**: `agent_tools` table (`ON CONFLICT (agent_id, tool_id) DO UPDATE SET enabled = EXCLUDED.enabled`)

### MCP Servers (1 layer)
1. **LiteLLM**: Registered via `POST /v1/mcp/server` (skips if already exists)

## Usage

### For DevOps Moiria (full seed)
```bash
python3 seed_all.py \
  --agent-name devops-moiria \
  --db-url "postgresql://clawith:PASS@postgres:5432/clawith" \
  --litellm-url "https://litellm.moiria.com" \
  --litellm-key "sk-..."
```

### For a specific agent
```bash
python3 seed_all.py \
  --agent-id "<uuid>" \
  --volume-path "/var/lib/docker/volumes/APPID_agent_data/_data" \
  --db-url "postgresql://clawith:PASS@postgres:5432/clawith" \
  --litellm-url "https://litellm.moiria.com" \
  --litellm-key "sk-..."
```

### Options
- `--agent-name devops-moiria|clawith-repair` — Use preset config
- `--skills-only` — Only seed skills
- `--tools-only` — Only seed MCP tools
- `--mcp-server NAME` — Only seed tools for this MCP server
- `--dry-run` — Show what would be done without executing

## How it works

### Skills
1. Auto-discovers skills from `/data/workspace/skills/<folder>/` (or uses preset list)
2. Parses SKILL.md frontmatter for name/description/category/icon
3. Inserts into `skills` table
4. Inserts all files into `skill_files` table
5. Copies files to Docker volume

### Tools
1. Queries LiteLLM `/v1/mcp/server` to get registered MCP servers
2. For each server, calls `/mcp-rest/tools/list` to get tool schemas
3. Inserts tools into `tools` table (ON CONFLICT DO NOTHING)
4. Maps ALL tools to target agent in `agent_tools` (ON CONFLICT DO UPDATE)

### MCP Servers
1. Checks existing servers via GET /v1/mcp/server
2. Registers missing servers via POST /v1/mcp/server

## Idempotency guarantees
- Skills: `ON CONFLICT (folder_name) DO NOTHING`
- Skill files: `ON CONFLICT (skill_id, path) DO NOTHING`
- Tools: `ON CONFLICT (name) DO NOTHING`
- Agent tools: `ON CONFLICT (agent_id, tool_id) DO UPDATE SET enabled = EXCLUDED.enabled`
- MCP servers: Skips if already registered

## Agent presets

### devops-moiria
- Agent: `29ae0878-93a8-476d-9fb1-9786aaaa3902`
- Skills: mcp-ssh-bridge, hetzner, coolify, infisical-god, mcp-vault-setup
- Volume: `/var/lib/docker/volumes/twcgssk04ckw4kgw0gcwcw48_agent_data/_data`

### clawith-repair
- Agent: `a3b3eed5-6b31-4189-bc07-0af4acefa6ea`
- Skills: clawith-skills-and-tools-seeder
