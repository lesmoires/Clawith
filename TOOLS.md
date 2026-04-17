# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## 🚨 CLAWITH REPAIR MODE - ACTIVE (2026-04-07 10:35 UTC)

**See:** `MISSION_CLAWITH_HYPERACTIVITY.md` for operational doctrine

---

## ⚠️ CRITICAL SAFETY RULES (2026-04-17 Incident)

**After incident 2026-04-17 where 10 hours of work were lost:**

### NEVER Execute Without Backup

```bash
# ❌ NEVER run these without backup first:
rm -rf /data/coolify/applications/*/backend/agent_data
rm -rf /data/agents/
mv /data/coolify/applications/*/backend/agent_data

# ✅ ALWAYS backup first:
/data/workspace/scripts/backup-agent-data.sh AVANT_INTERVENTION
```

### Backup Locations

| Type | Location |
|------|----------|
| Agent Data | `/data/backups/agent_data_backup_*.tar.gz` |
| Database | `/data/backups/db_backup_*.sql.gz` |
| Manual Backups | `/data/backups/*_MANUAL.tar.gz` |

### Emergency Restore

See: `EMERGENCY_BACKUP_REFERENCE.md` — Keep this printed/accessible.

### Incident Report

See: `memory/INCIDENT_2026-04-17_CRITICAL_DATA_LOSS.md` — Full post-mortem.

### GitHub PAT
```
GITHUB_TOKEN=[REDACTED - Use Infisical]
```
**Scope:** Clawith repo access for debugging  
**⚠️ Security:** Move to Infisical when possible

### Clawith Gateway API
```
CLAWITH_API_KEY=oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs
Endpoint: https://agents.moiria.com/api/gateway/
```

### Active Monitoring
- **Status:** ✅ ENABLED (cron cleared, manual polling active)
- **Action:** Poll Clawith inbox → Alert on new messages

---

## 🔐 SECURITY BOUNDARY (CRITICAL)

**Clawith GitHub Fork = PUBLIC**

| Safe to Commit | NEVER Commit |
|----------------|--------------|
| Bug fixes in core code | Agent constitutions (soul.md) |
| Tool schema changes | API keys, tokens, passwords |
| MCP server configs (no tokens) | Company secrets |
| Skill definitions | Env vars (use Coolify .env) |
| Feature additions | Database contents |

**Secrets stay in:** Infisical, Coolify .env files, PostgreSQL, agent workspaces

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

---

## 🌍 Infrastructure (Clawith/Moiria)

### SSH
- **moiria-claw** → 46.225.220.208, user: root, key: env `HETZNER_SSH_KEY_BASE64`
- **Server Type:** Hetzner CPX42 (8 vCPU, 16GB RAM, 320GB NVMe)
- **Upgraded:** 2026-03-27 (was cpx32: 4 vCPU, 8GB RAM)

### Coolify
- **URL:** https://coolify.moiria.com
- **API:** `[REDACTED]` (Infisical: `COOLIFY_API_KEY`)

### Services
| Service | URL | Notes |
|---------|-----|-------|
| Clawith | agents.moiria.com | Main agent platform |
| LiteLLM | litellm.moiria.com | MCP proxy (Hetzner) |
| Infisical | secrets.moiria.com | Secrets vault |

### API Keys
- **Clawith Gateway:** `[REDACTED]` (Infisical: `CLAWITH_GATEWAY_KEY`)
- **LiteLLM:** `[REDACTED]` (Infisical: `LITELLMAPIKEY`)
- **Hetzner:** `[REDACTED]` (Infisical: `HETZNERAPIKEY`)

---

## 📦 MCP Servers (2026-04-07 - REPAIR MODE)

**Config:** `/data/workspace/config/mcporter.json`

| Server | Tools | Status |
|--------|-------|--------|
| **hetzner** | 104 | ✅ Production |
| **agentmail** | 11 | ✅ Production |

**Hetzner Tools:** list_servers, get_server, get_metrics, power_on/off, reboot, shutdown, create_server, list_locations, list_actions

---

## 🔐 Infisical Secrets (2026-03-28 Status)

**Project**: `clawith` (af441074-e1b8-462a-8157-c47a05f5ec65)  
**Environment**: `prod`

### ✅ Working Tools

| Tool | Method | Status |
|------|--------|--------|
| `mcp_list-secrets` | MCP | ✅ Returns all secrets with values |

### ❌ Broken Tools (Awaiting Fixes)

| Tool | Method | Issue | Fix |
|------|--------|-------|-----|
| `getinfisicalsecret` | Built-in | Missing `import httpx` | PR ready |
| `mcp_get-secret` | MCP | SDK Bug #1190 | SDK upgrade needed |

### 📋 Available Secrets (5 total)

1. `AGENTMAILAPIKEY`
2. `SMITHERYAPIKEY`
3. `HETZNERAPIKEY`
4. `LITELLMAPIKEY`
5. `GITHUB_TOKEN`

### 🎯 Recommended Pattern

```python
# Use list-secrets as primary method (already working)
secrets = mcp_list-secrets(project="clawith", environment="prod")
# Parse and cache in agent context
# Access needed secrets from cached results
```

**Why**: Single call returns all values, no dependency on broken get-secret tools.

### 🔧 Fixes In Flight

- **PR**: `PR_INFISICAL_HTTPX_FIX.md` (ready to submit)
- **MCP SDK**: Upgrade v1.12.0 → v1.26.0 (escalated 60+ hours)
- **Cleanup Plan**: `INFISICAL_CLEANUP_PLAN.md`

---

## 📧 AgentMail MCP (2026-03-29 — FIXÉ)

**Statut:** ✅ **Opérationnel** — Serveur MCP officiel `agentmail-mcp` configuré

### Configuration
- **Fichier:** `config/mcporter.json`
- **Commande:** `npx -y agentmail-mcp`
- **Auth:** Variable d'environnement `AGENTMAIL_API_KEY`

### Outils Disponibles (11 outils)
| Outil | Statut |
|-------|--------|
| `list_inboxes` | ✅ |
| `get_inbox` | ✅ |
| `create_inbox` | ✅ |
| `delete_inbox` | ✅ |
| `list_threads` | ✅ |
| `get_thread` | ✅ |
| **`get_attachment`** | ✅ **FIXÉ** |
| `send_message` | ✅ |
| `reply_to_message` | ✅ |
| `forward_message` | ✅ |
| `update_message` | ✅ |

### Inboxes Actives
- `conver.thesis@agentmail.to` (Conver Thesis)
- `elias.bridge@agentmail.to` (Elias Bridge)
- `geo.presence@agentmail.to` (Geo Presence)

### Attachments Downloadés (2026-03-29)
**Dossier:** `due_diligence/storyline/`
- ✅ 01_Lettre_revision_taux.pdf (701K)
- ✅ 02_Tableau_salaire.xlsx (25K)
- ✅ 03_EBITDA.xlsx (32K)
- ✅ 04_Concentration_clients.xlsx (18K)
- ✅ 05_Sous-traitance.xlsx (45K)
- ✅ 06_Certificat_constitution.pdf (9.0M)
- ✅ 07_Convention_actionnaires.pdf (796K)
- ✅ 08_Donation_vente_actions.pdf (3.0M)

**Total:** 8 fichiers, ~14MB

---

## ☁️ Hetzner MCP (2026-03-30 — PRODUCTION)

**Statut:** ✅ **Opérationnel** — Serveur MCP `@lazyants/hetzner-mcp-server` via LiteLLM

### Architecture
```
Infisical (HETZNERAPIKEY) → Coolify (Env Var) → LiteLLM (MCP Server) → Clawith Backend → Agent
```

### Configuration
- **LiteLLM Config:** `/data/coolify/services/.../litellm-config.yaml`
- **MCP Server:** `hetzner_cloud` (stdio transport)
- **Command:** `npx -y @lazyants/hetzner-mcp-server`
- **Auth:** `HETZNER_API_TOKEN: os.environ/HETZNER_API_KEY`
- **API Key:** `[REDACTED]` (Infisical: `HETZNERAPIKEY` → Coolify: `HETZNER_API_KEY`)

### Outils Disponibles (10 outils)
| Outil | Catégorie | Usage |
|-------|-----------|-------|
| `hetzner_list_servers` | infrastructure | Lister tous les serveurs |
| `hetzner_get_server` | infrastructure | Détails d'un serveur |
| `hetzner_get_server_metrics` | infrastructure | Métriques (CPU, RAM, disk) |
| `hetzner_list_locations` | infrastructure | Datacenters disponibles |
| `hetzner_list_server_actions` | infrastructure | Actions en cours/passées |
| `hetzner_create_server` | infrastructure | Créer un nouveau serveur |
| `hetzner_power_on` | infrastructure | Allumer un serveur |
| `hetzner_power_off` | ⚠️ DESTRUCTIVE | Éteindre un serveur |
| `hetzner_shutdown` | ⚠️ DESTRUCTIVE | Arrêt d'urgence |
| `hetzner_reboot` | ⚠️ DESTRUCTIVE | Redémarrer |

### Gouvernance (CRITICAL)

**Two-Layer Model:**
| Agent | Rôle | Permissions |
|-------|------|-------------|
| **DevOps Moiria** | Operations | Read-only ✅ / Destructive ⚠️ (Guillaume approval required) |
| **Clawith Maintainer** | Oversight | All ops ✅ (logged for audit) |

**Protected Servers:**
- `moiria-claw` → DevOps Moiria host (self-destruction risk)
- `moiria-coolify` → Coolify host (deployment management)

**Destructive Operations Requiring Guillaume Approval:**
- `hetzner_power_off`, `hetzner_shutdown`, `hetzner_reboot`
- Any operation on protected servers

**Rationale:** DevOps Moiria runs ON moiria-claw. Destructive ops = potential self-destruction. Guillaume must approve to prevent accidental outages.

### Agents Équipés
| Agent | Tools | Usage |
|-------|-------|-------|
| DevOps Moiria | 10/10 | Infrastructure monitoring + ops |
| Clawith Maintainer | 10/10 | Oversight + rollback coordination |

### Rollback / Disaster Recovery
- **Claw (Clawith Repair)** lives on DIFFERENT server → safe for rollback coordination
- If moiria-claw goes down, Claw can intervene and restore
- Future: Branch logic for HA (not yet implemented)

### MCP Config Export
- **File:** `/data/workspace/mcp_hetzner_config.json`
- **Pattern:** Same as AgentMail MCP (see `LITELLM_MCP_DEPLOYMENT_GUIDE.md`)

---

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
