# Handoff Notes — Clawith Maintainer

**Date:** 2026-03-24  
**From:** Guillaume + Claw (subagents)  
**To:** Clawith Maintainer  
**Status:** ⏳ Pending agent creation

---

## 📋 Context

### Fork Clawith v1.7.0 → v1.7.1 in progress

Today, **5 subagents** worked on the Clawith fork migration and architecture:

1. **Upgrade Evaluator** — Full upgrade analysis (88 commits, 95 files)
2. **DB Analyst** — Database migration analysis
3. **Fork Audit Lead** — Fork cleanup and audit
4. **Git Workflow Architect** — Branching strategy and upstream sync
5. **Master Migration Coordinator** — Unified migration plan

### Clawith Maintainer Mission

You are the **guardian of the Clawith infrastructure** and the **fork maintenance coordinator**.

Your main responsibilities:
1. **Upstream Monitoring** — Watch `dataelement/Clawith` for new releases
2. **Fork Maintenance** — Manage branches, coordinate upstream merges
3. **Tools & Skills Distribution** — Maintain the central tool catalog
4. **Secret Management** — Manage Infisical access and secret rotation
5. **MCP Gateway Management** — Configure MCP servers in LiteLLM

---

## ✅ Knowledge Transferred

### 1. Upgrade Knowledge (16 reports)

**Files generated during v1.7.0 → v1.7.1 upgrade:**

| File | Description | Path |
|------|-------------|------|
| `UPGRADE_ANALYSIS.md` | Full upgrade analysis | `/data/workspace/clawith-fork/` |
| `CONFLICT_MATRIX.md` | Potential conflict matrix | `/data/workspace/clawith-fork/` |
| `MERGE_STRATEGY.md` | Detailed merge strategy | `/data/workspace/clawith-fork/` |
| `ROLLBACK_PLAN.md` | Complete rollback plan | `/data/workspace/clawith-fork/` |
| `MASTER_MIGRATION_PLAN.md` | Unified migration plan | `/data/workspace/clawith-fork/` |
| `MIGRATION_CHECKLIST.md` | Step-by-step checklist | `/data/workspace/clawith-fork/` |
| `BACKUP_CHECKLIST.md` | Backup checklist | `/data/workspace/clawith-fork/` |
| `BRANCHING_STRATEGY.md` | Git branching strategy | `/data/workspace/clawith-fork/` |
| `GIT_WORKFLOW_ANALYSIS_v1.md` | Git workflow analysis | `/data/workspace/clawith-fork/` |
| `IMPLEMENTATION_GUIDE.md` | Implementation guide | `/data/workspace/clawith-fork/` |
| `README_GIT_WORKFLOW.md` | Git workflow README | `/data/workspace/clawith-fork/` |
| `REPO_ARCHITECTURE.md` | Repo architecture | `/data/workspace/clawith-fork/` |
| `CLEANUP_PLAN.md` | Cleanup plan | `/data/workspace/clawith-fork/` |
| `FORK_AUDIT_SUMMARY.md` | Audit summary | `/data/workspace/clawith-fork/` |
| `RELEVANCE_MATRIX.md` | Relevance matrix | `/data/workspace/clawith-fork/` |
| `MIGRATION_SUMMARY_FOR_GUILLAUME.md` | Summary for Guillaume | `/data/workspace/clawith-fork/` |

**Key Learnings:**
- 88 upstream commits between v1.7.0 and v1.7.1
- 95 files changed
- 33 files with potential conflicts
- 4 HIGH risk conflicts: `main.py`, `gateway.py`, `docker-compose.yml`, `websocket.py`
- Strategy used: **Option B** (Fork + Feature Branches)
- Progressive merge via `feature/upgrade-1.7.1`
- 4 custom features must be preserved

**Lessons Learned (CRITICAL):**
- ✅ Backup DB before upgrade (CRITICAL)
- ✅ Git snapshot before merge (CRITICAL)
- ✅ Test custom features after merge (CRITICAL)
- ✅ Rollback plan ready (10-15 min)

---

### 2. MCP Knowledge

#### Hetzner MCP (via LiteLLM)

| Property | Value |
|----------|-------|
| **MCP Server** | `hetzner_cloud` |
| **MCP URL** | `https://litellm.moiria.com/mcp` |
| **API Key** | `[REDACTED - use Infisical]` (in Infisical: `/clawith/mcp/hetzner`) |
| **Tools** | 19 Hetzner tools registered |
| **Assigned Agents** | DevOps Moiria, Clawith Maintainer |
| **Status** | ✅ Production |

#### Infisical MCP (via Supergateway)

| Property | Value |
|----------|-------|
| **MCP URL** | `http://supergateway:8000/sse` |
| **Config** | `INFISICAL_HOST_URL`, `CLIENT_ID`, `CLIENT_SECRET`, `PROJECT_ID` |
| **Vault** | `/clawith/mcp/infisical` |
| **Tools** | 3 (get-secret, list-secrets, create-secret) |
| **Assigned Agents** | All agents |
| **Status** | ✅ Production |

#### LiteLLM MCP Gateway Config

| Property | Value |
|----------|-------|
| **URL** | `https://litellm.moiria.com/mcp` |
| **Config File** | `/data/coolify/services/wg0k80o88gcswco0ksgkkggc/litellm-config.yaml` |
| **Auth** | `Authorization: Bearer <key>` |

---

### 3. Git Workflow Knowledge

#### Remote Configuration

```bash
# origin: our fork
git remote -v
# origin  https://github.com/lesmoires/Clawith.git (fetch)
# origin  https://github.com/lesmoires/Clawith.git (push)

# upstream: parent
git remote add upstream https://github.com/dataelement/Clawith.git
git remote -v
# upstream  https://github.com/dataelement/Clawith.git (fetch)
# upstream  https://github.com/dataelement/Clawith.git (push)
```

#### Branches

| Branch | Usage | Protection |
|--------|-------|------------|
| `main` | Production | ✅ Protected |
| `develop` | Staging | ⚠️ Recommended |
| `feature/*` | Features in development | ❌ None |
| `hotfix/*` | Urgent fixes | ❌ None |
| `backup/*` | Snapshots before upgrades | ❌ None |

#### Upstream Sync Workflow

```bash
# 1. Fetch upstream
git fetch upstream --tags

# 2. Create feature branch
git checkout -b feature/upgrade-<version> develop

# 3. Merge upstream
git merge upstream/main

# 4. Resolve conflicts
# ... edit files ...
git add <files>
git commit -m "Resolve conflicts with upstream"

# 5. Push and PR
git push -u origin feature/upgrade-<version>
# → Create PR on GitHub
```

#### Token Security

- ⛔ **NEVER** put tokens in URLs
- ✅ **ALWAYS** use SSH or credential helper
- ✅ **ALWAYS** store tokens in Infisical only

---

### 4. Custom Features Registry

#### Core Features (P0 — Must be preserved)

| Feature | Files | Lines | Status |
|---------|-------|-------|--------|
| **AgentMail Integration** | `backend/app/tools/agentmail_tools.py` | 373 | ✅ Production |
| **Infisical MCP + Secrets** | `backend/app/skills/infisical_secrets.py`, `backend/app/tools/infisical_secret.py` | 764 | ✅ Production |
| **Gateway API Enhanced** | `backend/app/api/gateway.py` | 767 | ✅ Production (Clawith Repair sync) |
| **LiteLLM MCP Gateway** | `litellm-config.yaml` (Coolify) | - | ✅ Production (Hetzner MCP) |

#### Refactor Features (P1 — To improve)

| Feature | Status | Notes |
|---------|--------|-------|
| **Supergateway POC** | ⚠️ Replace with LiteLLM MCP Gateway | Legacy, to be deprecated |

---

## 📚 Registry Files Created

### 1. AGENTS_REGISTRY.md

**Path:** `/data/workspace/clawith-fork/AGENTS_REGISTRY.md`

**Content:**
- Registry of all Clawith agents
- Roles and responsibilities
- Assigned tools
- Infisical access
- MCP access

**Agents documented:**
- Clawith Maintainer (⏳ Pending creation)
- DevOps Moiria (✅ Active)
- Clawith Repair (✅ Active)

---

### 2. TOOLS_REGISTRY.md

**Path:** `/data/workspace/clawith-fork/TOOLS_REGISTRY.md`

**Content:**
- Core Tools (all agents)
- Custom Tools (AgentMail, Infisical, Gateway)
- MCP Tools (Hetzner, 19 tools)
- Tools Distribution Matrix
- New tool request workflow

---

### 3. MCP_REGISTRY.md

**Path:** `/data/workspace/clawith-fork/MCP_REGISTRY.md`

**Content:**
- LiteLLM MCP Gateway configuration
- Hetzner MCP (19 tools)
- Infisical MCP (3 tools)
- MCP Access Matrix
- Troubleshooting guide

---

### 4. INFISICAL_VAULTS.md

**Path:** `/data/workspace/clawith-fork/INFISICAL_VAULTS.md`

**Content:**
- Infisical vault structure
- Secrets per vault
- Vault Access Matrix
- Secret Rotation Policy
- Security Best Practices

**Vaults documented:**
- `/clawith/admin` — Admin credentials
- `/clawith/mcp` — MCP server credentials
- `/clawith/mcp/hetzner` — Hetzner API
- `/clawith/mcp/infisical` — Infisical MCP config
- `/clawith/mcp/agentmail` — AgentMail credentials
- `/clawith/gateway` — Gateway API keys
- `/clawith/agents/*` — Agent-specific secrets

---

## 🎯 Next Actions

### Priority 1 (Immediate)

1. **⏳ Create the Clawith Maintainer agent** in Clawith
   - Via UI: `https://agents.moiria.com`
   - Via API: `POST /api/agents/` (requires admin auth)
   - Role: "Infrastructure & Maintenance Guardian"

2. **⏳ Configure Infisical access**
   - Add Clawith Maintainer to vaults:
     - `/clawith/admin` (Full)
     - `/clawith/mcp` (Full)
     - `/clawith/agents/*` (Read)

3. **⏳ Configure MCP access**
   - Admin access on all MCP servers
   - Test Hetzner MCP connection
   - Test Infisical MCP connection

4. **⏳ Assign tools**
   - Core Tools: All
   - Custom Tools: All
   - MCP Tools: All

### Priority 2 (This week)

5. **⏳ Complete v1.7.1 migration** (if not already done)
   - Follow `MIGRATION_CHECKLIST.md`
   - Test custom features post-migration
   - Document in MEMORY.md

6. **⏳ Test the agent**
   ```bash
   curl -s -X POST https://agents.moiria.com/api/gateway/send-message \
     -H "X-Api-Key: oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs" \
     -H "Content-Type: application/json" \
     -d '{"target":"Clawith Maintainer","content":"Hello! Can you summarize your role and responsibilities?"}'
   ```

7. **⏳ Update registries**
   - Add agent UUID to `AGENTS_REGISTRY.md`
   - Add API key to `INFISICAL_VAULTS.md`

### Priority 3 (Ongoing)

8. **🔄 Monitor upstream for v1.7.2**
   - Watch `dataelement/Clawith` releases
   - Analyze changes
   - Recommend Go/No Go

9. **🔄 Onboard new agents as needed**
   - Create agents in Clawith
   - Configure access
   - Document in registries

10. **🔄 Maintain tools registry**
    - Validate new tools
    - Assign to agents
    - Document

11. **🔄 Audit Infisical access quarterly**
    - Review access
    - Rotate secrets
    - Update documentation

---

## 📞 Contacts

| Role | Name | Email |
|------|------|-------|
| **Project Owner** | Guillaume | guillaume.bleau@upentreprise.com |
| **Clawith Repair** | OpenClaw bridge agent | Via Gateway API |
| **DevOps Moiria** | DevOps agent | Via Gateway API |

---

## 🔑 API Keys & Access

### Gateway API

- **Base URL:** `https://agents.moiria.com/api/gateway/`
- **API Key:** `oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs`
- **Endpoints:**
  - `GET /poll` — Poll inbox
  - `POST /send-message` — Send a message
  - `POST /report` — Report a processed message

### Clawith Admin API (requires authentication)

- **Base URL:** `https://agents.moiria.com/api/`
- **Auth:** JWT Token (via login)
- **Endpoints:**
  - `POST /agents/` — Create an agent
  - `GET /agents/` — List agents
  - `GET /agents/templates` — List templates

---

## ✅ Validation Checklist

### Agent creation

- [ ] Clawith Maintainer agent created in Clawith
- [ ] Role well defined: "Infrastructure & Maintenance Guardian"
- [ ] API key generated and stored in Infisical
- [ ] Agent visible in the agent list

### Access configuration

- [ ] Infisical: Vault access configured
- [ ] MCP: Server access configured
- [ ] Tools: Core + Custom + MCP assigned

### Registry files

- [ ] `AGENTS_REGISTRY.md` created and up to date
- [ ] `TOOLS_REGISTRY.md` created and up to date
- [ ] `MCP_REGISTRY.md` created and up to date
- [ ] `INFISICAL_VAULTS.md` created and up to date

### Handoff

- [ ] This document completed
- [ ] Knowledge transfer validated
- [ ] First agent test successful
- [ ] Guillaume notified

---

## 🎉 Welcome Aboard, Clawith Maintainer!

You are now the guardian of the Clawith infrastructure. Your main missions:

1. **Keep the fork up to date** with upstream
2. **Preserve custom features** (AgentMail, Infisical, Gateway, MCP)
3. **Manage access and secrets** (Infisical, MCP)
4. **Document all changes** in the registries
5. **Recommend upgrades** (Go/No Go)

**Good luck!** 🚀

---

*Document created by: Claw (subagent)*  
*Date: 2026-03-24 11:40 UTC*  
*For: Guillaume + Clawith Maintainer*
