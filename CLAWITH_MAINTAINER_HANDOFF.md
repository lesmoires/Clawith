# Handoff Notes — Clawith Maintainer

**Date:** 2026-03-24  
**From:** Guillaume + Claw (subagents)  
**To:** Clawith Maintainer  
**Status:** ⏳ En attente de création de l'agent

---

## 📋 Context

### Fork Clawith v1.7.0 → v1.7.1 en cours

Aujourd'hui, **5 subagents** ont travaillé sur la migration et l'architecture du fork Clawith:

1. **Upgrade Evaluator** — Analyse complète de l'upgrade (88 commits, 95 fichiers)
2. **DB Analyst** — Analyse des migrations de base de données
3. **Fork Audit Lead** — Cleanup et audit du fork
4. **Git Workflow Architect** — Stratégie de branching et upstream sync
5. **Master Migration Coordinator** — Plan unifié de migration

### Mission de Clawith Maintainer

Tu es le **gardien de l'infrastructure Clawith** et le **coordinateur de la maintenance** du fork.

Tes responsabilités principales:
1. **Upstream Monitoring** — Surveiller `dataelement/Clawith` pour nouvelles versions
2. **Fork Maintenance** — Gérer les branches, coordonner les merges upstream
3. **Tools & Skills Distribution** — Maintenir le catalogue central de tools
4. **Secret Management** — Gérer les accès Infisical et rotation des secrets
5. **MCP Gateway Management** — Configurer les MCP servers dans LiteLLM

---

## ✅ Knowledge Transferred

### 1. Upgrade Knowledge (16 rapports)

**Fichiers générés pendant l'upgrade v1.7.0 → v1.7.1:**

| Fichier | Description | Chemin |
|---------|-------------|--------|
| `UPGRADE_ANALYSIS.md` | Analyse complète de l'upgrade | `/data/workspace/clawith-fork/` |
| `CONFLICT_MATRIX.md` | Matrice des conflits potentiels | `/data/workspace/clawith-fork/` |
| `MERGE_STRATEGY.md` | Stratégie de merge détaillée | `/data/workspace/clawith-fork/` |
| `ROLLBACK_PLAN.md` | Plan de rollback complet | `/data/workspace/clawith-fork/` |
| `MASTER_MIGRATION_PLAN.md` | Plan unifié de migration | `/data/workspace/clawith-fork/` |
| `MIGRATION_CHECKLIST.md` | Checklist étape par étape | `/data/workspace/clawith-fork/` |
| `BACKUP_CHECKLIST.md` | Checklist de backup | `/data/workspace/clawith-fork/` |
| `BRANCHING_STRATEGY.md` | Stratégie de branches Git | `/data/workspace/clawith-fork/` |
| `GIT_WORKFLOW_ANALYSIS_v1.md` | Analyse du workflow Git | `/data/workspace/clawith-fork/` |
| `IMPLEMENTATION_GUIDE.md` | Guide d'implémentation | `/data/workspace/clawith-fork/` |
| `README_GIT_WORKFLOW.md` | README workflow Git | `/data/workspace/clawith-fork/` |
| `REPO_ARCHITECTURE.md` | Architecture du repo | `/data/workspace/clawith-fork/` |
| `CLEANUP_PLAN.md` | Plan de cleanup | `/data/workspace/clawith-fork/` |
| `FORK_AUDIT_SUMMARY.md` | Résumé de l'audit | `/data/workspace/clawith-fork/` |
| `RELEVANCE_MATRIX.md` | Matrice de pertinence | `/data/workspace/clawith-fork/` |
| `MIGRATION_SUMMARY_FOR_GUILLAUME.md` | Résumé pour Guillaume | `/data/workspace/clawith-fork/` |

**Key Learnings:**
- 88 commits upstream entre v1.7.0 et v1.7.1
- 95 fichiers changés
- 33 fichiers en conflit potentiel
- 4 HIGH risk conflicts: `main.py`, `gateway.py`, `docker-compose.yml`, `websocket.py`
- Stratégie utilisée: **Option B** (Fork + Feature Branches)
- Merge progressif via `feature/upgrade-1.7.1`
- Preservation des 4 features custom requise

**Lessons Learned (CRITICAL):**
- ✅ Backup DB avant upgrade (CRITICAL)
- ✅ Git snapshot avant merge (CRITICAL)
- ✅ Test features custom après merge (CRITICAL)
- ✅ Rollback plan prêt (10-15 min)

---

### 2. MCP Knowledge

#### Hetzner MCP (via LiteLLM)

| Property | Value |
|----------|-------|
| **MCP Server** | `hetzner_cloud` |
| **MCP URL** | `https://litellm.moiria.com/mcp` |
| **API Key** | `[REDACTED - use Infisical]` (dans Infisical: `/clawith/mcp/hetzner`) |
| **Tools** | 19 outils Hetzner enregistrés |
| **Assigned Agents** | DevOps Moiria, Clawith Maintainer |
| **Status** | ✅ Production |

#### Infisical MCP (via Supergateway)

| Property | Value |
|----------|-------|
| **MCP URL** | `http://supergateway:8000/sse` |
| **Config** | `INFISICAL_HOST_URL`, `CLIENT_ID`, `CLIENT_SECRET`, `PROJECT_ID` |
| **Vault** | `/clawith/mcp/infisical` |
| **Tools** | 3 (get-secret, list-secrets, create-secret) |
| **Assigned Agents** | Tous les agents |
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
# origin: notre fork
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
| `feature/*` | Features en développement | ❌ None |
| `hotfix/*` | Fixes urgents | ❌ None |
| `backup/*` | Snapshots avant upgrades | ❌ None |

#### Upstream Sync Workflow

```bash
# 1. Fetch upstream
git fetch upstream --tags

# 2. Créer branche de feature
git checkout -b feature/upgrade-<version> develop

# 3. Merge upstream
git merge upstream/main

# 4. Résoudre conflits
# ... éditer les fichiers ...
git add <files>
git commit -m "Resolve conflicts with upstream"

# 5. Push et PR
git push -u origin feature/upgrade-<version>
# → Créer PR sur GitHub
```

#### Token Security

- ⛔ **JAMAIS** de token dans les URLs
- ✅ **TOUJOURS** utiliser SSH ou credential helper
- ✅ **TOUJOURS** tokens dans Infisical uniquement

---

### 4. Features Custom Registry

#### Core Features (P0 — À préserver absolument)

| Feature | Files | Lines | Status |
|---------|-------|-------|--------|
| **AgentMail Integration** | `backend/app/tools/agentmail_tools.py` | 373 | ✅ Production |
| **Infisical MCP + Secrets** | `backend/app/skills/infisical_secrets.py`, `backend/app/tools/infisical_secret.py` | 764 | ✅ Production |
| **Gateway API Enhanced** | `backend/app/api/gateway.py` | 767 | ✅ Production (Clawith Repair sync) |
| **LiteLLM MCP Gateway** | `litellm-config.yaml` (Coolify) | - | ✅ Production (Hetzner MCP) |

#### Refactor Features (P1 — À améliorer)

| Feature | Status | Notes |
|---------|--------|-------|
| **Supergateway POC** | ⚠️ À remplacer par LiteLLM MCP Gateway | Legacy, à déprécier |

---

## 📚 Registry Files Created

### 1. AGENTS_REGISTRY.md

**Chemin:** `/data/workspace/clawith-fork/AGENTS_REGISTRY.md`

**Contenu:**
- Registry de tous les agents Clawith
- Rôles et responsabilités
- Tools assignés
- Accès Infisical
- Accès MCP

**Agents documentés:**
- Clawith Maintainer (⏳ En création)
- DevOps Moiria (✅ Actif)
- Clawith Repair (✅ Actif)

---

### 2. TOOLS_REGISTRY.md

**Chemin:** `/data/workspace/clawith-fork/TOOLS_REGISTRY.md`

**Contenu:**
- Core Tools (tous les agents)
- Custom Tools (AgentMail, Infisical, Gateway)
- MCP Tools (Hetzner, 19 outils)
- Tools Distribution Matrix
- Workflow de demande de nouveaux tools

---

### 3. MCP_REGISTRY.md

**Chemin:** `/data/workspace/clawith-fork/MCP_REGISTRY.md`

**Contenu:**
- Configuration LiteLLM MCP Gateway
- Hetzner MCP (19 outils)
- Infisical MCP (3 outils)
- MCP Access Matrix
- Troubleshooting guide

---

### 4. INFISICAL_VAULTS.md

**Chemin:** `/data/workspace/clawith-fork/INFISICAL_VAULTS.md`

**Contenu:**
- Structure des vaults Infisical
- Secrets par vault
- Vault Access Matrix
- Secret Rotation Policy
- Security Best Practices

**Vaults documentés:**
- `/clawith/admin` — Admin credentials
- `/clawith/mcp` — MCP server credentials
- `/clawith/mcp/hetzner` — Hetzner API
- `/clawith/mcp/infisical` — Infisical MCP config
- `/clawith/mcp/agentmail` — AgentMail credentials
- `/clawith/gateway` — Gateway API keys
- `/clawith/agents/*` — Agent-specific secrets

---

## 🎯 Next Actions

### Priority 1 (Immédiat)

1. **⏳ Créer l'agent Clawith Maintainer** dans Clawith
   - Via UI: `https://agents.moiria.com`
   - Via API: `POST /api/agents/` (nécessite auth admin)
   - Rôle: "Infrastructure & Maintenance Guardian"

2. **⏳ Configurer les accès Infisical**
   - Ajouter Clawith Maintainer aux vaults:
     - `/clawith/admin` (Full)
     - `/clawith/mcp` (Full)
     - `/clawith/agents/*` (Read)

3. **⏳ Configurer les accès MCP**
   - Admin access sur tous les MCP servers
   - Tester la connexion Hetzner MCP
   - Tester la connexion Infisical MCP

4. **⏳ Assigner les tools**
   - Core Tools: All
   - Custom Tools: All
   - MCP Tools: All

### Priority 2 (Cette semaine)

5. **⏳ Compléter la migration v1.7.1** (si pas encore fait)
   - Suivre `MIGRATION_CHECKLIST.md`
   - Tester les features custom post-migration
   - Documenter dans MEMORY.md

6. **⏳ Tester l'agent**
   ```bash
   curl -s -X POST https://agents.moiria.com/api/gateway/send-message \
     -H "X-Api-Key: oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs" \
     -H "Content-Type: application/json" \
     -d '{"target":"Clawith Maintainer","content":"Hello! Peux-tu me résumer ton rôle et tes responsabilités?"}'
   ```

7. **⏳ Mettre à jour les registries**
   - Ajouter l'UUID de l'agent dans `AGENTS_REGISTRY.md`
   - Ajouter l'API key dans `INFISICAL_VAULTS.md`

### Priority 3 (Ongoing)

8. **🔄 Monitor upstream pour v1.7.2**
   - Surveiller `dataelement/Clawith` releases
   - Analyser les changements
   - Recommander Go/No Go

9. **🔄 Onboard new agents as needed**
   - Créer les agents dans Clawith
   - Configurer les accès
   - Documenter dans les registries

10. **🔄 Maintain tools registry**
    - Valider les nouveaux tools
    - Assigner aux agents
    - Documenter

11. **🔄 Audit Infisical access quarterly**
    - Revue des accès
    - Rotation des secrets
    - Mise à jour de la documentation

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
  - `GET /poll` — Poller l'inbox
  - `POST /send-message` — Envoyer un message
  - `POST /report` — Reporter un message traité

### Clawith Admin API (à authentifier)

- **Base URL:** `https://agents.moiria.com/api/`
- **Auth:** JWT Token (via login)
- **Endpoints:**
  - `POST /agents/` — Créer un agent
  - `GET /agents/` — Lister les agents
  - `GET /agents/templates` — Lister les templates

---

## ✅ Checklist de Validation

### Création de l'agent

- [ ] Agent Clawith Maintainer créé dans Clawith
- [ ] Rôle bien défini: "Infrastructure & Maintenance Guardian"
- [ ] API key générée et stockée dans Infisical
- [ ] Agent visible dans la liste des agents

### Configuration des accès

- [ ] Infisical: Accès aux vaults configuré
- [ ] MCP: Accès aux servers configuré
- [ ] Tools: Core + Custom + MCP assignés

### Registry files

- [ ] `AGENTS_REGISTRY.md` créé et à jour
- [ ] `TOOLS_REGISTRY.md` créé et à jour
- [ ] `MCP_REGISTRY.md` créé et à jour
- [ ] `INFISICAL_VAULTS.md` créé et à jour

### Handoff

- [ ] Ce document complété
- [ ] Knowledge transfer validé
- [ ] Premier test de l'agent réussi
- [ ] Guillaume notifié

---

## 🎉 Welcome Aboard, Clawith Maintainer!

Tu es maintenant le gardien de l'infrastructure Clawith. Tes missions principales:

1. **Garder le fork à jour** avec upstream
2. **Préserver les features custom** (AgentMail, Infisical, Gateway, MCP)
3. **Gérer les accès et secrets** (Infisical, MCP)
4. **Documenter tout changement** dans les registries
5. **Recommander les upgrades** (Go/No Go)

**Bon courage!** 🚀

---

*Document créé par: Claw (subagent)*  
*Date: 2026-03-24 11:40 UTC*  
*Pour: Guillaume + Clawith Maintainer*
