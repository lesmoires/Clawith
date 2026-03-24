# Master Migration Plan — Clawith v1.7.0 → v1.7.1

**Date:** 24 mars 2026  
**Coordination:** Migration Coordinator (Subagent)  
**Statut:** ⏳ En attente de validation Guillaume  
**Upstream:** dataelement/Clawith  
**Notre Fork:** lesmoires/Clawith

---

## 📊 Executive Summary

### Go/No Go Recommendation

**⚠️ GO avec precautions**

**Conditions préalables:**
1. ✅ Backup DB complet avant upgrade
2. ✅ Environnement de test/staging disponible
3. ✅ 1 jour bloqué pour l'upgrade + tests
4. ✅ Rollback plan testé et prêt
5. ✅ Équipe disponible pour support

**Si une condition n'est pas remplie:** → **No Go**, rester sur v1.7.0

---

### Total Effort Estimé

| Phase | Durée | Détails |
|-------|-------|---------|
| **Preparation** | 30 min | Backup, snapshot, branches |
| **DB Migration** | 30 min | Migration df3da9cf3b27 |
| **Code Merge** | 6-8h | Merge upstream + conflits |
| **Features Custom** | 2-3h | Réintégration features |
| **Testing** | 2-3h | Tests complets |
| **Deployment** | 1h | Staging + production |
| **TOTAL** | **10-14 heures** | ~1 jour bloqué |

---

### Risques Principaux

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Conflits logging (loguru)** | Moyen | Élevée | Merge manuel, tests |
| **Gateway API cassée** | Critique | Moyenne | Backup + tests sync |
| **Features custom perdues** | Critique | Faible | Checklist préservation |
| **DB migration échoue** | Élevé | Faible | Rollback DB prêt |
| **Performance degradation** | Moyen | Faible | Tests performance |

---

### Timeline

```
Jour 1 (8-10h):
├── Phase 0: Preparation (30 min)
├── Phase 1: DB Migration (30 min)
├── Phase 2: Code Merge (6-8h)
└── Phase 3: Features Custom (2-3h)

Jour 2 (4-6h):
├── Phase 4: Testing (2-3h)
└── Phase 5: Deployment (1h) + Buffer
```

---

## ✅ Pre-Requisites Checklist

**À valider AVANT de commencer:**

- [ ] **Backup DB testé**
  ```bash
  docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_$(date +%Y%m%d_%H%M%S).sql
  ls -lh backup_*.sql  # Taille > 0
  ```

- [ ] **Staging environment prêt**
  - [ ] Serveur de test disponible
  - [ ] DB de test configurée
  - [ ] DNS test configuré (optionnel)

- [ ] **Équipe disponible**
  - [ ] Guillaume (validation + urgence)
  - [ ] Upgrade Lead (merge)
  - [ ] MCP Lead (features MCP)

- [ ] **Token GitHub sécurisé**
  - [ ] Token dans Infisical/vault
  - [ ] **PAS dans .env ou code**
  - [ ] Remote URL nettoyée: `git remote set-url origin https://github.com/lesmoires/Clawith.git`

- [ ] **SSH configuré**
  - [ ] Clé SSH pour Hetzner/Coolify
  - [ ] Accès serveur testé
  - [ ] Docker Compose accessible

---

## 📋 Phase 0: Preparation (30 min)

### 0.1 Backup DB (15 min)

```bash
cd /data/workspace/clawith-fork

# Backup complet DB PostgreSQL
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_pre_upgrade_$(date +%Y%m%d_%H%M%S).sql

# Vérifier backup
ls -lh backup_pre_upgrade_*.sql
wc -l backup_pre_upgrade_*.sql  # Doit être > 0

# Optionnel: Backup cloud
# aws s3 cp backup_pre_upgrade_*.sql s3://moiria-backups/clawith/
```

**Validation:**
- [ ] Fichier créé (taille > 0)
- [ ] Contient CREATE TABLE
- [ ] Contient INSERT INTO

---

### 0.2 Git Snapshot (5 min)

```bash
# Créer tag de backup
git tag backup/pre-upgrade-$(date +%Y%m%d)
git push origin backup/pre-upgrade-$(date +%Y%m%d)

# Noter commit hash
git rev-parse HEAD > .backup_commit.txt
cat .backup_commit.txt
```

**Validation:**
- [ ] Tag créé localement
- [ ] Tag pushé vers remote
- [ ] Visible sur GitHub UI

---

### 0.3 Créer Branches (10 min)

```bash
# S'assurer d'être sur main
git checkout main
git pull origin main

# Créer branche develop (si pas existe)
git checkout -b develop
git push -u origin develop

# Créer branche d'upgrade
git checkout -b feature/upgrade-1.7.1 develop
```

**Validation:**
- [ ] Branche `develop` créée
- [ ] Branche `feature/upgrade-1.7.1` créée
- [ ] Branches pushées vers GitHub

---

### 0.4 Configs Custom Backup (5 min)

```bash
# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Backup env vars (si .env existe)
if [ -f .env ]; then
  cp .env .env.backup
fi

# Backup custom files
mkdir -p backups/custom
cp backend/app/tools/agentmail_tools.py backups/custom/
cp backend/app/skills/infisical_secrets.py backups/custom/
cp backend/app/tools/infisical_secret.py backups/custom/
cp backend/app/api/gateway.py backups/custom/
```

**Validation:**
- [ ] docker-compose.yml.backup créé
- [ ] 4 fichiers custom backupés

---

## 🗄️ Phase 1: DB Migration (30 min)

### 1.1 Run Migration (15 min)

**Migration:** `df3da9cf3b27_add_entrypoint_missing_columns.py`

```bash
# Vérifier si migration déjà appliquée
docker exec clawith-backend-1 alembic current

# Si migration pas appliquée:
docker exec clawith-backend-1 alembic upgrade head

# Vérifier résultat
docker exec clawith-backend-1 alembic current
# Doit afficher: df3da9cf3b27 (head)
```

**Validation:**
- [ ] Migration appliquée sans erreur
- [ ] Alembic current = df3da9cf3b27

---

### 1.2 Verify Schema (10 min)

```bash
# Vérifier colonnes ajoutées
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "\d entrypoints"

# Vérifier table créée (si applicable)
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
```

**Validation:**
- [ ] 20 colonnes ajoutées (voir DB_MIGRATION_PLAN.md)
- [ ] 1 table créée (si applicable)
- [ ] Pas d'erreurs SQL

---

### 1.3 Test Critical Queries (5 min)

```bash
# Test query sur table modifiée
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT COUNT(*) FROM entrypoints;"

# Test query avec jointures
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT e.*, a.name FROM entrypoints e JOIN agents a ON e.agent_id = a.id LIMIT 5;"
```

**Validation:**
- [ ] Queries retournent des résultats
- [ ] Pas d'erreurs SQL
- [ ] Performance normale (< 100ms)

---

## 🔀 Phase 2: Code Merge (6-8h)

### 2.1 Fetch Upstream (5 min)

```bash
# Fetch upstream tags
git fetch upstream --tags

# Vérifier version upstream
git log upstream/main --oneline | head -10

# Voir différence
git log HEAD..upstream/main --oneline | wc -l
# Doit afficher: ~88 commits
```

---

### 2.2 Merge Initial (15 min)

```bash
# Merge upstream v1.7.1
git merge v1.7.1 --no-commit --no-ff

# Voir conflits
git status --short | grep "^UU"
```

**Sortie attendue:** ~33 fichiers en conflit potentiel

---

### 2.3 Résoudre Conflits HIGH Risk (4-5h)

#### 🔴 Fichier 1: `backend/app/main.py` (1-2h)

**Conflit:** Upstream logging overhaul (loguru) vs Fork Supergateway comments

**Résolution:**
```python
# Imports (lignes 1-10)
from loguru import logger  # ← Upstream
from app.core.logging_config import configure_logging, intercept_standard_logging  # ← Upstream
from app.core.middleware import TraceIdMiddleware  # ← Upstream

# Dans lifespan()
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    intercept_standard_logging()
    logger.info("[startup] Logging configured")
    
    # Note: MCP stdio servers are now handled by Supergateway (docker-compose service)
    # No need for embedded MCP HTTP wrapper anymore
    
    # ... reste du code upstream
```

**Validation:**
- [ ] Python compile: `python -m py_compile backend/app/main.py`
- [ ] Logging configuré
- [ ] Supergateway comment préservé

---

#### 🔴 Fichier 2: `backend/app/api/gateway.py` (2-3h)

**Conflit:** Upstream logging vs Fork WebSocket + ChatMessage routing

**Résolution:**
```python
# Imports
from loguru import logger  # ← Upstream logging

# Dans report_result()
if body.result and msg.sender_agent_id:
    # ... code Fork de création ChatSession/ChatMessage ...
    
    # 3. Push WebSocket notification
    try:
        from app.api.websocket import manager
        await manager.send_message(sender_agent_id_str, {
            "type": "agent_reply",
            # ... payload ...
        })
        logger.info(f"[Gateway] WebSocket push to agent {sender_agent_id_str}")  # ← Upstream
    except Exception as e:
        logger.warning(f"[Gateway] WebSocket push failed: {e}")  # ← Upstream
```

**Validation:**
- [ ] Python compile
- [ ] WebSocket push fonctionne
- [ ] ChatMessage persistence fonctionne
- [ ] Logs avec trace IDs

---

#### 🔴 Fichier 3: `docker-compose.yml` (1h)

**Conflit:** Coolify env vars (Fork) vs Hardcoded (Upstream)

**Résolution (Fusion):**
```yaml
services:
  backend:
    build:
      context: ./backend
      args:  # ← Upstream
        CLAWITH_PIP_INDEX_URL: ${CLAWITH_PIP_INDEX_URL:-}
        CLAWITH_PIP_TRUSTED_HOST: ${CLAWITH_PIP_TRUSTED_HOST:-}
    environment:
      # Database (Fork - Coolify)
      DATABASE_URL: postgresql+asyncpg://clawith:${POSTGRES_PASSWORD}@postgres:5432/clawith
      REDIS_URL: redis://redis:6379/0
      # Secrets (Fork)
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      # Infisical MCP (Fork custom)
      INFISICAL_HOST_URL: ${INFISICAL_HOST_URL:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_ID: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}
      # AgentMail API (Fork custom)
      AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
      # Upstream configs
      DOCKER_NETWORK: clawith_network
      SS_CONFIG_FILE: /data/ss-nodes.json
    logging:  # ← Upstream
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

**Validation:**
- [ ] YAML valide: `docker compose config`
- [ ] Env vars custom présentes
- [ ] Logging config upstream présente

---

#### 🔴 Fichier 4: `backend/app/api/websocket.py` (1h)

**Conflit:** Upstream logging vs Fork custom logic

**Résolution:**
```python
from loguru import logger  # ← Upstream

# Remplacer tous les print() par logger.*
# print("...") → logger.info("...")
```

**Validation:**
- [ ] Python compile
- [ ] WebSocket connections OK
- [ ] Logs avec trace IDs

---

### 2.4 Résoudre Conflits MEDIUM Risk (2-3h)

#### 🟡 Services Logging (15 fichiers, 2h)

**Script de migration:**
```bash
#!/bin/bash
# migrate_logging.sh

FILES=(
  "backend/app/services/agent_context.py"
  "backend/app/services/agent_tools.py"
  "backend/app/services/feishu_ws.py"
  "backend/app/services/llm_client.py"
  "backend/app/services/mcp_client.py"
  # ... tous les services
)

for file in "${FILES[@]}"; do
  # Backup
  cp "$file" "$file.bak"
  
  # Replace imports
  sed -i 's/^import logging$/from loguru import logger/' "$file"
  sed -i 's/^logger = logging.getLogger(__name__)$/# Removed for loguru/' "$file"
  
  # Validate
  python -m py_compile "$file"
  if [ $? -ne 0 ]; then
    cp "$file.bak" "$file"
  else
    rm "$file.bak"
  fi
done
```

**Validation:**
- [ ] 15 fichiers migrés
- [ ] Tous compile OK
- [ ] Logs avec trace IDs

---

#### 🟡 `backend/entrypoint.sh` (30 min)

**Résolution:**
```bash
#!/bin/bash
set -e

# Alembic migrations (Upstream)
alembic upgrade head

# Data migrations (Upstream)
python3 -m app.scripts.migrate_schedules_to_triggers

# Custom MCP setup (Fork)
echo "[Entrypoint] Setting up Infisical MCP..."
if [ -n "$INFISICAL_HOST_URL" ]; then
  echo "[Entrypoint] Infisical MCP configured"
fi

if [ -n "$AGENTMAIL_API_KEY" ]; then
  echo "[Entrypoint] AgentMail API configured"
fi

# Start backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Validation:**
- [ ] Migrations run
- [ ] MCP setup OK
- [ ] Backend démarre

---

#### 🟡 `backend/pyproject.toml` (15 min)

**Ajouter:**
```toml
[project]
dependencies = [
    "loguru>=0.7.0",  # ← Upstream
    # ... autres deps
]
```

**Validation:**
- [ ] `pip install -e .` OK
- [ ] `from loguru import logger` fonctionne

---

### 2.5 Conflits LOW Risk (1h)

- [ ] Frontend pages (8 fichiers, 1h)
- [ ] i18n files (30 min)
- [ ] VERSION files (5 min)
- [ ] README files (30 min)
- [ ] Scripts & configs (30 min)

---

## 🔧 Phase 3: Features Custom (2-3h)

### 3.1 Re-integrate AgentMail (30 min)

**Vérifier:**
```bash
# Dans docker-compose.yml
grep -A2 "AGENTMAIL_API_KEY" docker-compose.yml

# Dans tools.py
grep -n "agentmail" backend/app/api/tools.py

# Tester API
curl http://localhost:8000/api/tools | jq '.[] | select(.name | contains("agentmail"))'
```

**Si manquant:**
```python
# backend/app/api/tools.py
from app.tools.agentmail_tools import (
    agentmail_list_inboxes,
    agentmail_create_inbox,
    agentmail_send_email,
    agentmail_read_email
)
# Register tools...
```

**Validation:**
- [ ] AgentMail tools listés
- [ ] Send/receive email testé

---

### 3.2 Re-integrate Infisical MCP (30 min)

**Vérifier:**
```bash
# Dans docker-compose.yml
grep "INFISICAL" docker-compose.yml

# Dans skills/
ls backend/app/skills/infisical_secrets.py
ls backend/app/tools/infisical_secret.py

# Tester
curl http://localhost:8000/api/skills | jq '.[] | select(.name | contains("infisical"))'
```

**Validation:**
- [ ] Infisical skills listés
- [ ] Get secret testé

---

### 3.3 Re-integrate Gateway API (1h)

**Vérifier:**
```bash
# WebSocket push
grep -n "manager.send_message" backend/app/api/gateway.py

# ChatMessage persistence
grep -n "ChatMessage" backend/app/api/gateway.py

# Tester sync
curl -X POST http://localhost:8000/api/gateway/messages \
  -H "X-Api-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "content": "Test"}'
```

**Validation:**
- [ ] WebSocket push fonctionne
- [ ] ChatMessage persistence fonctionne
- [ ] Sync Clawith Repair testé

---

### 3.4 Re-integrate Supergateway/LiteLLM (30 min)

**Option A: Garder Supergateway (actuel)**
```yaml
# docker-compose.yml
services:
  supergateway:
    image: node:18-alpine
    command: node /app/index.js
    # ... config actuelle
```

**Option B: Remplacer par LiteLLM (recommandé long terme)**
```yaml
services:
  litellm-mcp:
    image: ghcr.io/berriai/litellm:main
    command: ["--mcp"]
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - KIMI_KEY=${KIMI_KEY}
    ports:
      - "4000:4000"
```

**Validation:**
- [ ] Service démarre
- [ ] MCP calls fonctionnent

---

## 🧪 Phase 4: Testing (2-3h)

### 4.1 Unit Tests (30 min)

```bash
cd backend
pytest -xvs

# Frontend
cd frontend
npm test
```

**Validation:**
- [ ] Backend tests pass
- [ ] Frontend tests pass

---

### 4.2 Integration Tests (1h)

**Checklist:**
- [ ] Login/Logout fonctionne
- [ ] Création agent fonctionne
- [ ] Chat avec agent → réponses OK
- [ ] **WebSocket temps réel** (2 onglets)
- [ ] **Gateway API agent-to-agent**
- [ ] **Supergateway MCP** (Infisical)
- [ ] **AgentMail tools** (send/receive)
- [ ] **Infisical secrets** (get_secret)
- [ ] Upload fichier < 100MB
- [ ] Feishu org sync (si utilisé)

---

### 4.3 E2E Tests (1h)

**Scénarios critiques:**

1. **Clawith Repair Sync:**
```bash
# Agent A envoie message → Agent B reçoit → Reply → Agent A reçoit notification
# Vérifier WebSocket + ChatMessage persistence
```

2. **MCP Hetzner:**
```bash
# Créer server via MCP → Vérifier sur Hetzner Console
```

3. **AgentMail:**
```bash
# Send email → Vérifier reçu
# Read email → Vérifier contenu
```

4. **Infisical:**
```bash
# Get secret → Vérifier valeur correcte
```

---

### 4.4 Performance Tests (30 min)

```bash
# API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health

# curl-format.txt:
# time_total: %{time_total}\n

# Load test (optionnel)
ab -n 1000 -c 10 http://localhost:8000/api/health
```

**Targets:**
- [ ] API response: < 500ms
- [ ] Page load: < 3 sec
- [ ] WebSocket latency: < 100ms

---

## 🚀 Phase 5: Deployment (1h)

### 5.1 Deploy to Staging (30 min)

```bash
# Sur serveur staging
cd /data/workspace/clawith-fork

# Pull code
git pull origin feature/upgrade-1.7.1

# Build
docker compose build

# Deploy
docker compose up -d

# Wait for health
sleep 30
docker compose ps
```

**Validation:**
- [ ] Tous services healthy
- [ ] Logs propres
- [ ] Frontend accessible

---

### 5.2 Final Validation (15 min)

**Checklist:**
- [ ] Login fonctionne
- [ ] Création agent fonctionne
- [ ] Chat fonctionne
- [ ] Features custom fonctionnent
- [ ] Performance OK
- [ ] Pas d'erreurs dans logs

---

### 5.3 Deploy to Production (15 min)

```bash
# Sur serveur production
cd /data/workspace/clawith-fork

# Backup DB production
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_prod_$(date +%Y%m%d_%H%M%S).sql

# Pull code
git pull origin main  # Après merge de feature/upgrade-1.7.1

# Build
docker compose build

# Deploy
docker compose up -d

# Wait for health
sleep 30
docker compose ps

# Final check
curl http://localhost:8000/api/health
```

**Validation:**
- [ ] Backup DB créé
- [ ] Tous services healthy
- [ ] Health check OK
- [ ] Équipe notifiée

---

## 🔄 Rollback Plan

### Trigger Conditions

**Rollback si:**
- ❌ Backend ne démarre pas
- ❌ DB corrompue
- ❌ Features custom critiques broken
- ❌ Performance degradation > 50%
- ❌ Error rate > 10%

---

### Rollback Steps (10-15 min)

```bash
# 1. Stop services
docker compose down

# 2. Restore code
git checkout main
git reset --hard backup/pre-upgrade-$(date +%Y%m%d)

# 3. Restore DB
cat backup_pre_upgrade_*.sql | docker exec -i clawith-backend-postgres-1 psql -U clawith clawith

# 4. Restore configs
cp docker-compose.yml.backup docker-compose.yml

# 5. Restart
docker compose up -d

# 6. Verify
docker compose ps
curl http://localhost:8000/api/health
```

---

### Contacts Urgence

| Rôle | Nom | Contact |
|------|-----|---------|
| **Validateur** | Guillaume | [Contact] |
| **Upgrade Lead** | [À assigner] | [Contact] |
| **MCP Lead** | [À assigner] | [Contact] |

---

## ✅ Success Criteria

**À cocher APRÈS déploiement:**

- [ ] **All tests pass**
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] E2E tests

- [ ] **MCP Hetzner works**
  - [ ] Créer server
  - [ ] Lister servers
  - [ ] Supprimer server

- [ ] **Clawith Repair sync works**
  - [ ] WebSocket push
  - [ ] ChatMessage persistence
  - [ ] Agent-to-agent messaging

- [ ] **AgentMail works**
  - [ ] Send email
  - [ ] Read email
  - [ ] List inboxes

- [ ] **Infisical works**
  - [ ] Get secret
  - [ ] MCP integration

- [ ] **No data loss**
  - [ ] Agents count = avant upgrade
  - [ ] Chat sessions count = avant
  - [ ] Users count = avant

---

## 📊 Post-Migration Actions

### 7.1 Feishu Migration (Si Applicable)

```bash
docker exec clawith-backend-1 python3 -m app.scripts.cleanup_duplicate_feishu_users
```

---

### 7.2 Monitoring Setup

**Alerts à configurer:**
- [ ] Error rate > 1% → alert
- [ ] API latency > 1s → alert
- [ ] WebSocket disconnections → alert
- [ ] DB connections > 80% → alert

---

### 7.3 Documentation Update

**À mettre à jour:**
- [ ] `README.md` - Version badge
- [ ] `RELEASE_NOTES.md` - Section v1.7.1
- [ ] Internal docs - Custom features list
- [ ] Team notification - Upgrade complete

---

### 7.4 Cleanup

**Après 7 jours sans problème:**
```bash
# Supprimer documentation upgrade temporaire
mkdir -p docs/archive/upgrade-v1.7.1
mv UPGRADE_*.md MERGE_STRATEGY.md CONFLICT_MATRIX.md ROLLBACK_PLAN.md docs/archive/upgrade-v1.7.1/

# Supprimer backups locaux (> 30 jours)
find backups/ -type f -mtime +30 -delete

# Git cleanup
git branch -d feature/upgrade-1.7.1
git push origin --delete feature/upgrade-1.7.1
```

---

## 📈 Checklist Finale

**Avant de commencer:**
- [ ] Backup DB testé
- [ ] Staging environment prêt
- [ ] Équipe disponible
- [ ] Token GitHub sécurisé
- [ ] SSH configuré

**Pendant migration:**
- [ ] Phase 0: Preparation ✅
- [ ] Phase 1: DB Migration ✅
- [ ] Phase 2: Code Merge ✅
- [ ] Phase 3: Features Custom ✅
- [ ] Phase 4: Testing ✅
- [ ] Phase 5: Deployment ✅

**Après migration:**
- [ ] All tests pass ✅
- [ ] MCP Hetzner works ✅
- [ ] Clawith Repair sync works ✅
- [ ] AgentMail works ✅
- [ ] Infisical works ✅
- [ ] No data loss ✅
- [ ] Documentation updated ✅
- [ ] Team notified ✅

---

## 📞 Support

**En cas de questions:**
- Voir `MERGE_STRATEGY.md` pour détails techniques
- Voir `CONFLICT_MATRIX.md` pour conflits spécifiques
- Voir `ROLLBACK_PLAN.md` pour procédure d'urgence

**Escalation:**
- Guillaume (Président UPentreprise)
- Ranga (CTO)
- VirtualGX Team (DevOps)

---

**Plan créé par:** Migration Coordinator (Subagent)  
**Date:** 24 mars 2026  
**Statut:** ⏳ En attente de validation Guillaume
