# Fork Audit — Clawith Custom Developments

**Date:** 24 mars 2026  
**Audité par:** Claw (Code Audit Lead)  
**Repo:** /data/workspace/clawith-fork  
**Upstream:** dataelement/Clawith

---

## 📍 Fork Point

| Référence | Commit | Description |
|-----------|--------|-------------|
| **Upstream (dataelement/main)** | v1.7.1+ | Version actuelle upstream |
| **Notre version (HEAD)** | b8faa95bf6 | `fix: WebSocket push + ChatMessage for agent-to-agent Gateway replies` |
| **Divergence** | **~64 commits** | Nos développements custom |

---

## 🎯 Custom Features Identified

### 1. **Supergateway POC** ✅ Core
**Fichiers:**
- `docker-compose.yml` (service supergateway)
- `backend/app/main.py` (MCP HTTP wrapper comments)

**Description:** Service Node.js pour exposer Infisical MCP via HTTP/stdio
**Statut:** Actif en production
**Alignement upstream:** ⚠️ Partiel (upstream utilise une approche différente)

---

### 2. **AgentMail Integration** ✅ Core
**Fichiers:**
- `backend/app/tools/agentmail_tools.py` (10.9 KB)
- `backend/app/api/tools.py` (intégration API)
- `docker-compose.yml` (env var `AGENTMAIL_API_KEY`)

**Description:** Outils pour envoyer/recevoir des emails via AgentMail API
**Statut:** Actif, documenté
**Alignement upstream:** ❌ Non aligné (feature custom)

---

### 3. **Infisical MCP + Secrets** ✅ Core
**Fichiers:**
- `backend/app/skills/infisical_secrets.py` (5.3 KB)
- `backend/app/tools/infisical_secret.py` (3.6 KB)
- `docker-compose.yml` (env vars Infisical)

**Description:** Intégration Infisical pour gestion des secrets via MCP
**Statut:** Actif en production
**Alignement upstream:** ⚠️ Partiel (upstream a une approche différente)

---

### 4. **Gateway API Enhanced** ✅ Core
**Fichiers:**
- `backend/app/api/gateway.py` (29.8 KB, modifié)
- WebSocket push + ChatMessage pour replies agent-to-agent

**Description:** API Gateway avec support WebSocket pour synchronisation Clawith Repair
**Statut:** Actif, critique pour Clawith Repair sync
**Alignement upstream:** ⚠️ Modifié (ajouts custom)

---

### 5. **Feishu Integrations** ⚠️ À vérifier
**Fichiers:**
- `backend/app/api/feishu.py` (51.2 KB)
- `backend/app/services/feishu_service.py`
- `backend/app/services/feishu_ws.py`
- `frontend/public/feishu.*` (assets)

**Description:** Intégration Feishu (chat bot chinois, similaire Slack)
**Statut:** Présent, besoin de vérifier si activement utilisé
**Alignement upstream:** ✅ Aligné (upstream a aussi Feishu)

---

### 6. **Documentation Custom** ⚠️ À refactorer
**Fichiers:**
- `UPGRADE_ANALYSIS.md` (10 KB)
- `MERGE_STRATEGY.md` (19.8 KB)
- `CONFLICT_MATRIX.md` (14.2 KB)
- `ROLLBACK_PLAN.md` (12.8 KB)
- `UPGRADE_README.md` (4.7 KB)

**Description:** Documentation pour upgrade v1.7.0 → v1.7.1
**Statut:** Utile mais temporaire (post-merge)
**Alignement upstream:** N/A (interne au fork)

---

### 7. **Backend Custom Structure** ⚠️ À auditer
**Fichiers:**
- `backend/app/api/tools.py` (22 KB, modifié)
- `backend/app/main.py` (13.1 KB, modifié)
- `backend/app/config.py`

**Description:** Modifications backend pour supporter features custom
**Statut:** Actif
**Alignement upstream:** ⚠️ Partiellement divergent

---

### 8. **Docker Compose Config** ⚠️ À refactorer
**Fichiers:**
- `docker-compose.yml` (3.9 KB)

**Description:** Config Docker avec services custom (supergateway, coolify network)
**Statut:** Actif en production
**Alignement upstream:** ⚠️ Modifié (ajouts custom)

---

## 📊 Initial Assessment

### ✅ À Garder (Core Features)

| Feature | Priority | Justification |
|---------|----------|---------------|
| **AgentMail Integration** | P0 | Validé en prod, unique au fork |
| **Gateway API Enhanced** | P0 | Critique pour Clawith Repair sync |
| **Infisical MCP** | P0 | Validé en prod, gestion secrets |
| **Supergateway** | P1 | Utile mais peut être remplacé |

---

### ⚠️ À Refactorer

| Feature | Priority | Action |
|---------|----------|--------|
| **docker-compose.yml** | P1 | Nettoyer, aligner avec upstream |
| **backend/main.py** | P1 | Fusionner changements upstream |
| **backend/api/tools.py** | P1 | Intégrer AgentMail proprement |
| **Documentation upgrade** | P2 | Archive post-merge |

---

### ❌ À Supprimer (Obsolète)

| Feature | Priority | Justification |
|---------|----------|---------------|
| **dev_deploy_temp.tar.gz** (1.1 GB) | P0 | Fichier temporaire, inutile |
| **Documentation merge** (post-merge) | P2 | Archive ou supprimer |
| **Anciennes configs MCP** | P2 | Si remplacé par LiteLLM |

---

## 🔍 Prochaines Étapes

### Phase 2: Analyse de Pertinence (En cours)

Pour chaque feature, évaluer:
1. **Utilisé?** — Activement en production?
2. **Aligné upstream?** — Upstream a évolué dans la même direction?
3. **Documenté?** — Bien documenté?
4. **Testé?** — Ça marche vraiment?
5. **Dette technique?** — Code propre ou besoin refactor?

### Phase 3: Matrice de Pertinence

Produire `RELEVANCE_MATRIX.md` avec scoring détaillé.

### Phase 4: Plan de Nettoyage

Produire `CLEANUP_PLAN.md` avec:
- Files to keep: X
- Files to refactor: Y
- Files to delete: Z
- Backup checklist

---

## 📈 Métriques

| Métrique | Valeur |
|----------|--------|
| **Commits custom** | ~64 |
| **Fichiers modifiés** | ~10177 (renamed detection skipped) |
| **Features custom** | 8 |
| **Core features (P0)** | 4 |
| **Features à refactorer** | 4 |
| **Features à supprimer** | 3 |

---

## 📝 Notes

- **Gros fichier à supprimer:** `dev_deploy_temp.tar.gz` (1.1 GB)
- **Upstream correct:** dataelement/Clawith (pas openclaw/openclaw)
- **Version actuelle:** v1.7.0 fork custom
- **Cible upgrade:** v1.7.1 upstream

---

**Prochaine mise à jour:** RELEVANCE_MATRIX.md (analyse détaillée par feature)
