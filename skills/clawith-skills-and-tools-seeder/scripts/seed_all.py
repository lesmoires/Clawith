#!/usr/bin/env python3
"""Clawith Skills & Tools Seeder - see SKILL.md for usage."""
import argparse, json, os, sys, uuid, subprocess
from pathlib import Path

try:
    import httpx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

WORKSPACE_SKILLS = Path("/data/workspace/skills")

def exec_sql(db_url, sql, dry_run=False):
    if dry_run:
        print(sql.rstrip(";")); return True
    parts = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    creds, host_db = parts.split("@")[0], parts.split("@")[1]
    user, password = (creds.split(":") if ":" in creds else (creds, ""))
    host, dbname = (host_db.split("/") if "/" in host_db else (host_db, ""))
    env = os.environ.copy(); env["PGPASSWORD"] = password
    result = subprocess.run(["psql", f"postgresql://{user}@{host}/{dbname}", "-c", sql],
                           capture_output=True, text=True, env=env)
    if result.returncode != 0 and "duplicate" not in result.stderr.lower() and "already exists" not in result.stderr.lower():
        print(f"  SQL error: {result.stderr[:200]}"); return False
    return True

def seed_skills(db_url, agent_id, volume_path, dry_run=False):
    print(f"\n{'='*60}\n  SEEDING SKILLS\n{'='*60}")
    skill_defs = {
        "mcp-ssh-bridge": {"name": "MCP SSH Bridge", "description": "Remote infrastructure management via SSH - 356 tools", "category": "infrastructure", "icon": "🔐"},
    }
    for folder, info in skill_defs.items():
        skill_dir = WORKSPACE_SKILLS / folder
        if not skill_dir.is_dir():
            print(f"\n  ⚠️  {folder}: not found in workspace"); continue
        files = [{"path": str(f.relative_to(skill_dir)), "content": f.read_text()} for f in skill_dir.rglob("*") if f.is_file()]
        if not files:
            print(f"\n  ⚠️  {folder}: no files"); continue
        print(f"\n  📁 {folder} ({len(files)} files)")
        skill_id = str(uuid.uuid4())
        desc = info["description"].replace("'", "''")
        exec_sql(db_url, f"INSERT INTO skills (id, name, folder_name, description, category, icon, is_builtin, is_default, created_at) VALUES ('{skill_id}', '{info['name']}', '{folder}', $$${desc}$$, '{info['category']}', '{info['icon']}', false, false, now()) ON CONFLICT (folder_name) DO NOTHING;", dry_run)
        for f in files:
            file_id = str(uuid.uuid4())
            content = f["content"].replace("'", "''")
            exec_sql(db_url, f"INSERT INTO skill_files (id, skill_id, path, content) VALUES ('{file_id}', '{skill_id}', '{f['path']}', $$${content}$$$) ON CONFLICT (skill_id, path) DO NOTHING;", dry_run)
        if volume_path:
            dest = Path(volume_path) / agent_id / "skills" / folder
            if dry_run:
                print(f"    📄 Would copy to: {dest}/")
            else:
                dest.mkdir(parents=True, exist_ok=True)
                for f in files:
                    fp = dest / f["path"]; fp.parent.mkdir(parents=True, exist_ok=True); fp.write_text(f["content"])
                    print(f"    ✅ {fp}")

def seed_tools(db_url, agent_id, litellm_url, litellm_key, mcp_server=None, dry_run=False):
    print(f"\n{'='*60}\n  SEEDING MCP TOOLS FROM LITELLM\n{'='*60}")
    resp = httpx.get(f"{litellm_url}/v1/mcp/server", headers={"Authorization": f"Bearer {litellm_key}"}, timeout=30)
    if resp.status_code != 200:
        print(f"  ❌ Failed: HTTP {resp.status_code}"); return
    servers = resp.json(); total = 0
    for srv in servers:
        name = srv["server_name"]
        if mcp_server and name != mcp_server: continue
        sid = srv.get("server_id", srv.get("id", ""))
        print(f"\n  🔌 {name} ({sid[:12]}...)")
        tools_resp = httpx.get(f"{litellm_url}/mcp-rest/tools/list", headers={"Authorization": f"Bearer {litellm_key}"}, params={"server_id": sid}, timeout=60)
        if tools_resp.status_code != 200:
            print(f"    ⚠️  HTTP {tools_resp.status_code}"); continue
        tools = tools_resp.json().get("tools", []); print(f"    Found {len(tools)} tools")
        for i, tool in enumerate(tools):
            tid = str(uuid.uuid4()); tn = tool.get("name", "")
            td = tool.get("description", "")[:1000].replace("'", "''")
            dn = tn.replace("ssh_", "").replace("_", " ").title().replace("'", "''")
            schema = json.dumps(tool.get("inputSchema", {"type": "object", "properties": {}})).replace("'", "''")
            exec_sql(db_url, f"INSERT INTO tools (id, name, type, mcp_server_name, mcp_server_url, display_name, description, parameters_schema, config, config_schema, category, icon, enabled, is_default, source, created_at, updated_at) VALUES ('{tid}', '{tn}', 'mcp', '{name}', '{litellm_url}', '{dn}', $$${td}$$, '{schema}', '{{}}', '{{}}', 'infrastructure', '🔐', true, false, 'mcp', now(), now()) ON CONFLICT (name) DO NOTHING;", dry_run)
            aid = str(uuid.uuid4())
            exec_sql(db_url, f"INSERT INTO agent_tools (id, agent_id, tool_id, enabled, config, source, created_at) VALUES ('{aid}', '{agent_id}', '{tid}', true, '{{}}', 'mcp', now()) ON CONFLICT (agent_id, tool_id) DO UPDATE SET enabled = EXCLUDED.enabled;", dry_run)
            total += 1
        print(f"    ✅ {len(tools)} tools seeded")
    print(f"\n  📊 Total: {total}")

def register_mcp(litellm_url, litellm_key, dry_run=False):
    print(f"\n{'='*60}\n  REGISTERING MCP SERVERS\n{'='*60}")
    srv = {"server_name": "mcp_ssh_bridge", "description": "mcp-ssh-bridge - 356 sysadmin tools", "transport": "stdio", "command": "/usr/local/bin/mcp-ssh-bridge", "args": ["serve"], "env": {"HOME": "/root"}}
    if dry_run:
        print(f"  📝 Would register: {srv['server_name']}"); return
    resp = httpx.post(f"{litellm_url}/v1/mcp/server", headers={"Authorization": f"Bearer {litellm_key}", "Content-Type": "application/json"}, json=srv, timeout=30)
    print(f"  {'✅' if resp.status_code in (200,201,400,409) else '⚠️'}  {srv['server_name']}: HTTP {resp.status_code}")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--db-url", required=True); p.add_argument("--agent-id", required=True)
    p.add_argument("--litellm-url", required=True); p.add_argument("--litellm-key", required=True)
    p.add_argument("--volume-path"); p.add_argument("--skills-only", action="store_true"); p.add_argument("--tools-only", action="store_true")
    p.add_argument("--mcp-server"); p.add_argument("--dry-run", action="store_true"); args = p.parse_args()
    print(f"🌱 Clawith Seeder | Agent: {args.agent_id} | LiteLLM: {args.litellm_url}")
    if args.dry_run: print("   *** DRY RUN ***")
    if not args.tools_only: seed_skills(args.db_url, args.agent_id, args.volume_path or "", args.dry_run)
    if not args.skills_only: seed_tools(args.db_url, args.agent_id, args.litellm_url, args.litellm_key, args.mcp_server, args.dry_run)
    register_mcp(args.litellm_url, args.litellm_key, args.dry_run)
    print("\n✅ Done")

if __name__ == "__main__": main()
