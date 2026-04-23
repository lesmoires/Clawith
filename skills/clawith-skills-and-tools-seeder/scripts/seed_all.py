#!/usr/bin/env python3
"""
Clawith Skills & Tools Seeder
==============================
Seeds ALL skills and ALL MCP tools into Clawith platform.
Idempotent — safe to run multiple times after deploy.

Usage:
  python3 seed_all.py \
    --db-url "postgresql://clawith:PASS@host:5432/clawith" \
    --agent-id "29ae0878-93a8-476d-9fb1-9786aaaa3902" \
    --litellm-url "https://litellm.moiria.com" \
    --litellm-key "sk-..." \
    --volume-path "/var/lib/docker/volumes/APPID_agent_data/_data"

Options:
  --skills-only     Only seed skills
  --tools-only      Only seed MCP tools
  --mcp-server NAME Only seed tools for this MCP server
  --agent-name NAME Seed for this agent (default: DevOps Moiria)
  --dry-run         Show SQL without executing
"""

import argparse
import json
import os
import sys
import uuid
import subprocess
from pathlib import Path

try:
    import httpx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

# ─── Config ────────────────────────────────────────────────────────
WORKSPACE_SKILLS = Path("/data/workspace/skills")
SCRIPT_DIR = Path(__file__).parent

# Agent presets
AGENT_PRESETS = {
    "devops-moiria": {
        "agent_id": "29ae0878-93a8-476d-9fb1-9786aaaa3902",
        "volume_path": "/var/lib/docker/volumes/twcgssk04ckw4kgw0gcwcw48_agent_data/_data",
        "skills": ["mcp-ssh-bridge", "hetzner", "coolify", "infisical-god", "mcp-vault-setup"],
    },
    "clawith-repair": {
        "agent_id": "a3b3eed5-6b31-4189-bc07-0af4acefa6ea",
        "volume_path": "/var/lib/docker/volumes/twcgssk04ckw4kgw0gcwcw48_agent_data/_data",
        "skills": ["clawith-skills-and-tools-seeder"],
    },
}


# ─── SQL helpers ───────────────────────────────────────────────────
def exec_sql(db_url: str, sql: str, dry_run: bool = False) -> bool:
    """Execute SQL via psql."""
    if dry_run:
        print(f"    SQL: {sql.rstrip(';')[:120]}...")
        return True
    
    parts = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    creds = parts.split("@")[0]
    host_db = parts.split("@")[1]
    user, password = (creds.split(":") if ":" in creds else (creds, ""))
    host, dbname = (host_db.split("/") if "/" in host_db else (host_db, ""))
    
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    
    result = subprocess.run(
        ["psql", f"postgresql://{user}@{host}/{dbname}", "-c", sql],
        capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        err = result.stderr.lower()
        if "duplicate" in err or "already exists" in err or "conflict" in err:
            return True  # Expected for upserts
        print(f"    ❌ SQL error: {result.stderr[:200]}")
        return False
    return True


# ─── Skills seeding ────────────────────────────────────────────────
def seed_skills(db_url: str, agent_id: str, volume_path: str, 
                skill_folders: list = None, dry_run: bool = False):
    """Seed skills into DB (skills + skill_files) AND Docker volume."""
    print(f"\n{'='*60}")
    print(f"  SEEDING SKILLS")
    print(f"{'='*60}")
    
    if skill_folders is None:
        # Auto-discover all skills in workspace
        skill_folders = [d.name for d in WORKSPACE_SKILLS.iterdir() 
                        if d.is_dir() and (d / "SKILL.md").exists()]
        print(f"  Auto-discovered {len(skill_folders)} skills in workspace")
    
    seeded = 0
    for folder_name in skill_folders:
        skill_dir = WORKSPACE_SKILLS / folder_name
        if not skill_dir.is_dir():
            print(f"\n  ⚠️  {folder_name}: directory not found")
            continue
        
        # Parse SKILL.md header
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            print(f"\n  ⚠️  {folder_name}: SKILL.md not found")
            continue
        
        content = skill_md.read_text()
        # Extract name from frontmatter
        name = folder_name.replace("-", " ").title()
        description = ""
        category = "custom"
        icon = "📋"
        
        for line in content.split("\n"):
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                description = line.split(":", 1)[1].strip()[:500]
            elif line.startswith("category:"):
                category = line.split(":", 1)[1].strip()
            elif line.startswith("icon:"):
                icon = line.split(":", 1)[1].strip()
        
        # Collect all files
        files = []
        for f in skill_dir.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                rel = str(f.relative_to(skill_dir))
                files.append({"path": rel, "content": f.read_text()})
        
        if not files:
            print(f"\n  ⚠️  {folder_name}: no files found")
            continue
        
        print(f"\n  📁 {folder_name} ({len(files)} files)")
        
        skill_id = str(uuid.uuid4())
        desc_escaped = description.replace("'", "''")
        
        # 1. INSERT into skills table
        sql = (
            f"INSERT INTO skills (id, name, folder_name, description, category, icon, is_builtin, is_default, created_at) "
            f"VALUES ('{skill_id}', '{name}', '{folder_name}', $$${desc_escaped}$$, '{category}', '{icon}', false, false, now()) "
            f"ON CONFLICT (folder_name) DO NOTHING;"
        )
        if exec_sql(db_url, sql, dry_run):
            print(f"    ✅ skills table")
            seeded += 1
        
        # 2. INSERT into skill_files table
        for f in files:
            file_id = str(uuid.uuid4())
            content_escaped = f["content"].replace("'", "''")
            sql = (
                f"INSERT INTO skill_files (id, skill_id, path, content) "
                f"VALUES ('{file_id}', '{skill_id}', '{f['path']}', $$${content_escaped}$$$) "
                f"ON CONFLICT (skill_id, path) DO NOTHING;"
            )
            exec_sql(db_url, sql, dry_run)
        
        # 3. Copy to Docker volume
        if volume_path:
            dest = Path(volume_path) / agent_id / "skills" / folder_name
            if dry_run:
                print(f"    📄 Would copy to: {dest}/")
            else:
                dest.mkdir(parents=True, exist_ok=True)
                for f in files:
                    file_path = dest / f["path"]
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(f["content"])
                    print(f"    ✅ disk: {f['path']}")
    
    print(f"\n  📊 Skills seeded: {seeded}/{len(skill_folders)}")
    return seeded


# ─── Tools seeding ─────────────────────────────────────────────────
def seed_tools_from_litellm(db_url: str, agent_id: str, litellm_url: str,
                             litellm_key: str, mcp_server_name: str = None,
                             dry_run: bool = False):
    """Fetch MCP tools from LiteLLM and seed into DB + agent_tools."""
    print(f"\n{'='*60}")
    print(f"  SEEDING MCP TOOLS FROM LITELLM")
    print(f"{'='*60}")
    
    # 1. Get MCP servers from LiteLLM
    resp = httpx.get(
        f"{litellm_url}/v1/mcp/server",
        headers={"Authorization": f"Bearer {litellm_key}"},
        timeout=30
    )
    if resp.status_code != 200:
        print(f"  ❌ Failed to get MCP servers: HTTP {resp.status_code}")
        return 0
    
    servers = resp.json()
    total_tools = 0
    total_new = 0
    
    for server in servers:
        name = server["server_name"]
        if mcp_server_name and name != mcp_server_name:
            continue
        
        server_id = server.get("server_id", server.get("id", ""))
        print(f"\n  🔌 {name} (server_id: {server_id[:12]}...)")
        
        # 2. Get tools list
        try:
            tools_resp = httpx.get(
                f"{litellm_url}/mcp-rest/tools/list",
                headers={"Authorization": f"Bearer {litellm_key}"},
                params={"server_id": server_id},
                timeout=60
            )
            if tools_resp.status_code != 200:
                print(f"    ⚠️  HTTP {tools_resp.status_code}")
                continue
            tools = tools_resp.json().get("tools", [])
            print(f"    Found {len(tools)} tools")
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
            continue
        
        # 3. Seed each tool
        for i, tool in enumerate(tools):
            tool_id = str(uuid.uuid4())
            tname = tool.get("name", "")
            tdesc = tool.get("description", "")[:1000].replace("'", "''")
            display = tname.replace("ssh_", "").replace("_", " ").title().replace("'", "''")
            schema = json.dumps(tool.get("inputSchema", {"type": "object", "properties": {}})).replace("'", "''")
            
            # INSERT tool
            sql = (
                f"INSERT INTO tools (id, name, type, mcp_server_name, mcp_server_url, "
                f"display_name, description, parameters_schema, config, config_schema, "
                f"category, icon, enabled, is_default, source, created_at, updated_at) "
                f"VALUES ('{tool_id}', '{tname}', 'mcp', '{name}', '{litellm_url}', "
                f"'{display}', $$${tdesc}$$, '{schema}', '{{}}', '{{}}', "
                f"'infrastructure', '🔐', true, false, 'mcp', now(), now()) "
                f"ON CONFLICT (name) DO NOTHING;"
            )
            if exec_sql(db_url, sql, dry_run):
                total_new += 1
            
            # INSERT agent_tool mapping
            at_id = str(uuid.uuid4())
            sql = (
                f"INSERT INTO agent_tools (id, agent_id, tool_id, enabled, config, source, created_at) "
                f"VALUES ('{at_id}', '{agent_id}', '{tool_id}', true, '{{}}', 'mcp', now()) "
                f"ON CONFLICT (agent_id, tool_id) DO UPDATE SET enabled = EXCLUDED.enabled;"
            )
            exec_sql(db_url, sql, dry_run)
            total_tools += 1
        
        print(f"    ✅ {len(tools)} tools processed")
    
    print(f"\n  📊 Total tools processed: {total_tools}")
    print(f"  📊 New tools inserted: {total_new}")
    return total_tools


# ─── MCP Server registration ──────────────────────────────────────
def register_mcp_servers(litellm_url: str, litellm_key: str, dry_run: bool = False):
    """Register MCP servers in LiteLLM if not already registered."""
    print(f"\n{'='*60}")
    print(f"  REGISTERING MCP SERVERS IN LITELLM")
    print(f"{'='*60}")
    
    # Check existing
    resp = httpx.get(
        f"{litellm_url}/v1/mcp/server",
        headers={"Authorization": f"Bearer {litellm_key}"},
        timeout=30
    )
    if resp.status_code != 200:
        print(f"  ❌ Failed: HTTP {resp.status_code}")
        return
    
    existing = {s["server_name"] for s in resp.json()}
    
    servers = [
        {
            "server_name": "mcp_ssh_bridge",
            "description": "mcp-ssh-bridge - 356 sysadmin tools (SSH, Docker, systemd, monitoring)",
            "transport": "stdio",
            "command": "/usr/local/bin/mcp-ssh-bridge",
            "args": ["serve"],
            "env": {"HOME": "/root"},
        },
        {
            "server_name": "coolify_mcp",
            "description": "Coolify PaaS - 38 tools (deploy, restart, logs, backups)",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@masonator/coolify-mcp"],
            "env": {
                "COOLIFY_BASE_URL": "https://coolify.moiria.com",
                "COOLIFY_ACCESS_TOKEN": "78b5dbdab7357293bd06eae18d8a6126274f81777cf7ac15147d740040127fed",
            },
        },
    ]
    
    for srv in servers:
        name = srv["server_name"]
        if name in existing:
            print(f"  ✅ {name}: already registered")
            continue
        
        if dry_run:
            print(f"  📝 Would register: {name}")
            continue
        
        resp = httpx.post(
            f"{litellm_url}/v1/mcp/server",
            headers={"Authorization": f"Bearer {litellm_key}", "Content-Type": "application/json"},
            json=srv,
            timeout=30
        )
        if resp.status_code in (200, 201, 400, 409):
            print(f"  ✅ {name}: registered")
        else:
            print(f"  ⚠️  {name}: HTTP {resp.status_code}")


# ─── Main ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Clawith Skills & Tools Seeder")
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--litellm-url", required=True)
    parser.add_argument("--litellm-key", required=True)
    parser.add_argument("--volume-path")
    parser.add_argument("--agent-name", default="devops-moiria", 
                       choices=list(AGENT_PRESETS.keys()),
                       help="Agent preset to use")
    parser.add_argument("--skills-only", action="store_true")
    parser.add_argument("--tools-only", action="store_true")
    parser.add_argument("--mcp-server", help="Only seed this MCP server")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    # Resolve preset
    preset = AGENT_PRESETS.get(args.agent_name, {})
    agent_id = args.agent_id or preset.get("agent_id")
    volume_path = args.volume_path or preset.get("volume_path", "")
    skill_folders = preset.get("skills")
    
    if not agent_id:
        print("❌ --agent-id required (or use --agent-name with a preset)")
        sys.exit(1)
    
    print(f"🌱 Clawith Skills & Tools Seeder")
    print(f"   Agent: {agent_id}")
    print(f"   Preset: {args.agent_name}")
    print(f"   LiteLLM: {args.litellm_url}")
    if args.dry_run:
        print("   *** DRY RUN ***")
    
    skills_count = 0
    if not args.tools_only:
        skills_count = seed_skills(
            args.db_url, agent_id, volume_path, 
            skill_folders=skill_folders, dry_run=args.dry_run
        )
    
    tools_count = 0
    if not args.skills_only:
        tools_count = seed_tools_from_litellm(
            args.db_url, agent_id, args.litellm_url, args.litellm_key,
            mcp_server_name=args.mcp_server, dry_run=args.dry_run
        )
    
    if not args.skills_only and not args.tools_only:
        register_mcp_servers(args.litellm_url, args.litellm_key, args.dry_run)
    
    print(f"\n{'='*60}")
    print(f"  ✅ DONE — Skills: {skills_count}, Tools: {tools_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
