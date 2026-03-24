# Migration Checklist — Clawith v1.7.0 → v1.7.1

**Date:** 24 mars 2026  
**Pour:** Guillaume  
**Statut:** ⏳ Prêt à exécuter (après validation)  
**Temps total:** 10-14 heures

---

## 🚦 GO/NO GO Decision

**Avant de commencer, cocher TOUTES les cases:**

- [ ] **Backup DB testé et vérifié** (taille > 0)
- [ ] **Staging environment prêt** (serveur + DB)
- [ ] **1 jour bloqué dans agenda** (10-14h)
- [ ] **Équipe disponible** (toi + leads si besoin)
- [ ] **Token GitHub sécurisé** (dans Infisical, PAS dans .env)
- [ ] **SSH configuré** (accès Hetzner/Coolify testé)
- [ ] **Rollback plan compris** (10-15 min)

**Si TOUTES les cases sont cochées:** → **GO** ✅  
**Sinon:** → **NO GO**, reporter l'upgrade

---

## 📋 Phase 0: Preparation (30 min)

### ✅ Backup DB (15 min)

```bash
cd /data/workspace/clawith-fork

# 1. Backup DB
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_pre_upgrade_$(date +%Y%m%d_%H%M%S).sql

# 2. Vérifier backup
ls -lh backup_pre_upgrade_*.sql
wc -l backup_pre_upgrade_*.sql
```

**Validation:**
- [ ] Fichier créé (taille > 0, ex: 10-100 MB)
- [ ] Lignes > 0 (ex: 5000+ lignes)
- [ ] Fichier stocké dans `/data/workspace/clawith-fork/backups/`

---

### ✅ Git Snapshot (5 min)

```bash
# 1. Créer tag de backup
git tag backup/pre-upgrade-$(date +%Y%m%d)
git push origin backup/pre-upgrade-$(date +%Y%m%d)

# 2. Noter commit hash
git rev-parse HEAD
```

**Validation:**
- [ ] Tag créé localement
- [ ] Tag pushé vers GitHub
- [ ] Visible sur https://github.com/lesmoires/Clawith/tags

---

### ✅ Créer Branches (10 min)

```bash
# 1. Vérifier branche actuelle
git status  # Doit être sur main

# 2. Créer develop (si pas existe)
git checkout -b develop
git push -u origin develop

# 3. Créer branche d'upgrade
git checkout -b feature/upgrade-1.7.1 develop
git push -u origin feature/upgrade-1.7.1
```

**Validation:**
- [ ] Branche `develop` créée et pushée
- [ ] Branche `feature/upgrade-1.7.1` créée et pushée
- [ ] Visible sur GitHub

---

### ✅ Backup Configs Custom (5 min)

```bash
# 1. Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# 2. Backup custom files
mkdir -p backups/custom
cp backend/app/tools/agentmail_tools.py backups/custom/
cp backend/app/skills/infisical_secrets.py backups/custom/
cp backend/app/tools/infisical_secret.py backups/custom/
cp backend/app/api/gateway.py backups/custom/

# 3. Vérifier
ls -lh backups/custom/
```

**Validation:**
- [ ] docker-compose.yml.backup créé
- [ ] 4 fichiers custom backupés
- [ ] Tailles correspondent aux originaux

---

## 🗄️ Phase 1: DB Migration (30 min)

### ✅ Run Migration (15 min)

```bash
# 1. Vérifier migration actuelle
docker exec clawith-backend-1 alembic current

# 2. Run migration
docker exec clawith-backend-1 alembic upgrade head

# 3. Vérifier résultat
docker exec clawith-backend-1 alembic current
```

**Validation:**
- [ ] Migration appliquée sans erreur
- [ ] Alembic current = `df3da9cf3b27` (head)

---

### ✅ Verify Schema (10 min)

```bash
# 1. Vérifier colonnes ajoutées
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c "\d entrypoints"

# 2. Vérifier tables
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
```

**Validation:**
- [ ] 20 colonnes ajoutées (voir DB_MIGRATION_PLAN.md)
- [ ] 1 table créée (si applicable)
- [ ] Pas d'erreurs SQL

---

### ✅ Test Critical Queries (5 min)

```bash
# 1. Test count
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT COUNT(*) FROM entrypoints;"

# 2. Test join
docker exec clawith-backend-postgres-1 psql -U clawith clawith -c \
  "SELECT e.*, a.name FROM entrypoints e JOIN agents a ON e.agent_id = a.id LIMIT 5;"
```

**Validation:**
- [ ] Queries retournent des résultats
- [ ] Pas d'erreurs SQL
- [ ] Performance normale (< 100ms)

---

## 🔀 Phase 2: Code Merge (6-8h)

### ✅ Fetch Upstream (5 min)

```bash
# 1. Fetch upstream tags
git fetch upstream --tags

# 2. Vérifier version
git log upstream/main --oneline | head -10

# 3. Voir différence
git log HEAD..upstream/main --oneline | wc -l
```

**Validation:**
- [ ] Upstream fetché
- [ ] ~88 commits de différence

---

### ✅ Merge Initial (15 min)

```bash
# 1. Merge upstream v1.7.1
git merge v1.7.1 --no-commit --no-ff

# 2. Voir conflits
git status --short | grep "^UU"
```

**Validation:**
- [ ] Merge initié
- [ ] ~33 fichiers en conflit listés

---

### ✅ Résoudre Conflits HIGH Risk (4-5h)

#### 🔴 `backend/app/main.py` (1-2h)

**Ouvrir le fichier et vérifier:**

```python
# Lignes 1-10: Imports
from loguru import logger  # ← Doit être présent
from app.core.logging_config import configure_logging, intercept_standard_logging  # ← Doit être présent
from app.core.middleware import TraceIdMiddleware  # ← Doit être présent

# Dans lifespan():
configure_logging()
intercept_standard_logging()
logger.info("[startup] Logging configured")

# Note: MCP stdio servers are now handled by Supergateway...
```

**Validation:**
- [ ] Logging upstream présent
- [ ] Supergateway comment préservé
- [ ] Python compile: `python -m py_compile backend/app/main.py`

---

#### 🔴 `backend/app/api/gateway.py` (2-3h)

**Ouvrir le fichier et vérifier:**

```python
# Imports
from loguru import logger  # ← Upstream logging

# Dans report_result():
if body.result and msg.sender_agent_id:
    # ... code Fork de création ChatSession/ChatMessage ...
    
    # WebSocket push
    try:
        from app.api.websocket import manager
        await manager.send_message(...)
        logger.info(f"[Gateway] WebSocket push to agent {sender_agent_id_str}")
    except Exception as e:
        logger.warning(f"[Gateway] WebSocket push failed: {e}")
```

**Validation:**
- [ ] Python compile
- [ ] WebSocket push code présent
- [ ] ChatMessage persistence présente
- [ ] Logging upstream utilisé

---

#### 🔴 `docker-compose.yml` (1h)

**Vérifier:**

```yaml
services:
  backend:
    build:
      args:  # ← Upstream
        CLAWITH_PIP_INDEX_URL: ${CLAWITH_PIP_INDEX_URL:-}
        CLAWITH_PIP_TRUSTED_HOST: ${CLAWITH_PIP_TRUSTED_HOST:-}
    environment:
      # Database (Fork)
      DATABASE_URL: postgresql+asyncpg://clawith:${POSTGRES_PASSWORD}@postgres:5432/clawith
      # Infisical (Fork)
      INFISICAL_HOST_URL: ${INFISICAL_HOST_URL:-}
      # AgentMail (Fork)
      AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
      # Logging (Upstream)
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

**Validation:**
- [ ] YAML valide: `docker compose config`
- [ ] Env vars custom présentes (INFISICAL, AGENTMAIL)
- [ ] Logging config upstream présente

---

#### 🔴 `backend/app/api/websocket.py` (1h)

**Vérifier:**

```python
from loguru import logger  # ← Upstream

# Tous les print() remplacés par logger.*
logger.info("...")  # au lieu de print("...")
```

**Validation:**
- [ ] Python compile
- [ ] logging import = loguru
- [ ] Pas de `print()` restants

---

### ✅ Résoudre Conflits MEDIUM Risk (2-3h)

#### 🟡 Services Logging (15 fichiers, 2h)

**Vérifier chaque fichier:**

```bash
# Pour chaque fichier dans backend/app/services/
grep "from loguru import logger" backend/app/services/*.py
```

**Validation:**
- [ ] 15 fichiers migrés vers loguru
- [ ] Tous compile OK
- [ ] Pas de `import logging` restants

---

#### 🟡 `backend/entrypoint.sh` (30 min)

**Vérifier:**

```bash
#!/bin/bash
set -e

# Alembic migrations
alembic upgrade head

# Data migrations
python3 -m app.scripts.migrate_schedules_to_triggers

# Custom MCP setup (Fork)
echo "[Entrypoint] Setting up Infisical MCP..."
if [ -n "$INFISICAL_HOST_URL" ]; then
  echo "[Entrypoint] Infisical MCP configured"
fi

# Start backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Validation:**
- [ ] Migrations upstream présentes
- [ ] MCP setup Fork présent
- [ ] Script exécutable: `chmod +x backend/entrypoint.sh`

---

#### 🟡 `backend/pyproject.toml` (15 min)

**Vérifier:**

```toml
[project]
dependencies = [
    "loguru>=0.7.0",  # ← Upstream
    # ... autres deps
]
```

**Validation:**
- [ ] loguru dans dependencies
- [ ] `pip install -e .` OK
- [ ] `from loguru import logger` fonctionne

---

### ✅ Conflits LOW Risk (1h)

- [ ] Frontend pages (8 fichiers)
- [ ] i18n files (traductions)
- [ ] VERSION files (bump à 1.7.1)
- [ ] README files (banner upstream)
- [ ] Scripts & configs

---

## 🔧 Phase 3: Features Custom (2-3h)

### ✅ Re-integrate AgentMail (30 min)

```bash
# 1. Vérifier dans docker-compose.yml
grep "AGENTMAIL_API_KEY" docker-compose.yml

# 2. Vérifier dans tools.py
grep "agentmail" backend/app/api/tools.py

# 3. Tester (après build)
curl http://localhost:8000/api/tools | jq '.[] | select(.name | contains("agentmail"))'
```

**Validation:**
- [ ] AGENTMAIL_API_KEY dans docker-compose.yml
- [ ] AgentMail tools dans tools.py
- [ ] Tools listés dans API

---

### ✅ Re-integrate Infisical MCP (30 min)

```bash
# 1. Vérifier dans docker-compose.yml
grep "INFISICAL" docker-compose.yml

# 2. Vérifier fichiers
ls backend/app/skills/infisical_secrets.py
ls backend/app/tools/infisical_secret.py

# 3. Tester (après build)
curl http://localhost:8000/api/skills | jq '.[] | select(.name | contains("infisical"))'
```

**Validation:**
- [ ] INFISICAL_* dans docker-compose.yml
- [ ] Fichiers Infisical présents
- [ ] Skills listés dans API

---

### ✅ Re-integrate Gateway API (1h)

```bash
# 1. Vérifier WebSocket push
grep "manager.send_message" backend/app/api/gateway.py

# 2. Vérifier ChatMessage
grep "ChatMessage" backend/app/api/gateway.py

# 3. Tester (après build)
curl -X POST http://localhost:8000/api/gateway/messages \
  -H "X-Api-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "content": "Test"}'
```

**Validation:**
- [ ] WebSocket push code présent
- [ ] ChatMessage persistence présente
- [ ] API Gateway répond

---

### ✅ Re-integrate Supergateway/LiteLLM (30 min)

**Option A: Garder Supergateway (actuel)**

```bash
# Vérifier dans docker-compose.yml
grep -A5 "supergateway:" docker-compose.yml
```

**Option B: Remplacer par LiteLLM (recommandé)**

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
- [ ] Service configuré
- [ ] Service démarre: `docker compose up -d litellm-mcp`
- [ ] Health check OK: `curl http://localhost:4000/health`

---

## 🧪 Phase 4: Testing (2-3h)

### ✅ Unit Tests (30 min)

```bash
# Backend
cd backend
pytest -xvs

# Frontend
cd frontend
npm test
```

**Validation:**
- [ ] Backend tests pass (100%)
- [ ] Frontend tests pass (100%)

---

### ✅ Integration Tests (1h)

**Checklist manuelle:**

- [ ] Login/Logout fonctionne
- [ ] Création agent fonctionne
- [ ] Chat avec agent → réponses OK
- [ ] **WebSocket temps réel** (ouvrir 2 onglets, envoyer message)
- [ ] **Gateway API agent-to-agent** (test avec 2 agents)
- [ ] **Supergateway MCP** (tester Infisical tool)
- [ ] **AgentMail tools** (send + receive email)
- [ ] **Infisical secrets** (get_secret)
- [ ] Upload fichier < 100MB
- [ ] Feishu org sync (si utilisé)

---

### ✅ E2E Tests (1h)

#### Scénario 1: Clawith Repair Sync

```bash
# 1. Agent A envoie message à Agent B
curl -X POST http://localhost:8000/api/gateway/messages \
  -H "X-Api-Key: agent-a-key" \
  -d '{"agent_id": 1, "content": "Hello from A"}'

# 2. Vérifier Agent B reçoit (WebSocket)
# → Ouvrir frontend Agent B, vérifier notification

# 3. Agent B reply
# → Vérifier Agent A reçoit notification
```

**Validation:**
- [ ] WebSocket push fonctionne
- [ ] ChatMessage persistence fonctionne
- [ ] Sync bidirectionnelle OK

---

#### Scénario 2: MCP Hetzner

```bash
# 1. Lister servers via MCP
# → Via frontend ou API

# 2. Créer server test
# → Vérifier sur Hetzner Console

# 3. Supprimer server test
```

**Validation:**
- [ ] MCP Hetzner connecté
- [ ] CRUD operations fonctionnent

---

#### Scénario 3: AgentMail

```bash
# 1. Send email
curl -X POST http://localhost:8000/api/tools/agentmail/send \
  -H "Authorization: Bearer <token>" \
  -d '{"to": "test@example.com", "subject": "Test", "body": "Hello"}'

# 2. Read email
# → Vérifier contenu reçu
```

**Validation:**
- [ ] Send email fonctionne
- [ ] Read email fonctionne

---

#### Scénario 4: Infisical

```bash
# 1. Get secret
curl http://localhost:8000/api/skills/infisical/get-secret \
  -H "Authorization: Bearer <token>" \
  -d '{"secret_name": "TEST_SECRET"}'

# 2. Vérifier valeur correcte
```

**Validation:**
- [ ] Get secret fonctionne
- [ ] Valeur correcte retournée

---

### ✅ Performance Tests (30 min)

```bash
# 1. API response time
curl -w "time_total: %{time_total}s\n" -o /dev/null -s http://localhost:8000/api/health

# 2. Load test (optionnel)
ab -n 1000 -c 10 http://localhost:8000/api/health
```

**Targets:**
- [ ] API response: < 0.5s
- [ ] Page load: < 3s
- [ ] WebSocket latency: < 100ms

---

## 🚀 Phase 5: Deployment (1h)

### ✅ Deploy to Staging (30 min)

```bash
# Sur serveur staging
cd /data/workspace/clawith-fork

# 1. Pull code
git pull origin feature/upgrade-1.7.1

# 2. Build
docker compose build

# 3. Deploy
docker compose up -d

# 4. Wait for health
sleep 30
docker compose ps

# 5. Check logs
docker compose logs backend --tail 50
```

**Validation:**
- [ ] Tous services healthy (docker compose ps)
- [ ] Logs propres (pas d'erreurs critiques)
- [ ] Frontend accessible: `curl http://staging.clawith.your-domain.com`

---

### ✅ Final Validation Staging (15 min)

**Checklist:**

- [ ] Login fonctionne
- [ ] Création agent fonctionne
- [ ] Chat fonctionne
- [ ] Features custom fonctionnent (AgentMail, Infisical, Gateway)
- [ ] Performance OK
- [ ] Pas d'erreurs dans logs

---

### ✅ Deploy to Production (15 min)

```bash
# Sur serveur production
cd /data/workspace/clawith-fork

# 1. Backup DB production
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_prod_$(date +%Y%m%d_%H%M%S).sql

# 2. Pull code (après merge feature → main)
git checkout main
git pull origin main

# 3. Build
docker compose build

# 4. Deploy
docker compose up -d

# 5. Wait for health
sleep 30
docker compose ps

# 6. Final check
curl http://localhost:8000/api/health
```

**Validation:**
- [ ] Backup DB production créé
- [ ] Tous services healthy
- [ ] Health check OK: `{"status":"ok","version":"1.7.1"}`
- [ ] Équipe notifiée

---

## 🔄 Rollback (Si Problème)

### ⚠️ Trigger Rollback Si:

- ❌ Backend ne démarre pas
- ❌ DB corrompue
- ❌ Features custom critiques broken
- ❌ Performance degradation > 50%
- ❌ Error rate > 10%

---

### 🚨 Rollback Steps (10-15 min)

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

**Validation:**
- [ ] Services redémarrés
- [ ] Health check OK
- [ ] Version = 1.7.0

---

## ✅ Post-Migration

### ✅ Feishu Migration (Si Applicable) (15 min)

```bash
docker exec clawith-backend-1 python3 -m app.scripts.cleanup_duplicate_feishu_users
```

---

### ✅ Monitoring Setup (30 min)

**Alerts à configurer:**

- [ ] Error rate > 1% → alert
- [ ] API latency > 1s → alert
- [ ] WebSocket disconnections → alert
- [ ] DB connections > 80% → alert

---

### ✅ Documentation Update (30 min)

**À mettre à jour:**

- [ ] `README.md` - Version badge → v1.7.1
- [ ] `RELEASE_NOTES.md` - Section v1.7.1
- [ ] Internal docs - Custom features list
- [ ] Team notification - Upgrade complete

---

### ✅ Cleanup (Après 7 jours) (15 min)

```bash
# 1. Archiver docs upgrade
mkdir -p docs/archive/upgrade-v1.7.1
mv UPGRADE_*.md MERGE_STRATEGY.md CONFLICT_MATRIX.md ROLLBACK_PLAN.md docs/archive/upgrade-v1.7.1/

# 2. Supprimer backups locaux (> 30 jours)
find backups/ -type f -mtime +30 -delete

# 3. Git cleanup
git branch -d feature/upgrade-1.7.1
git push origin --delete feature/upgrade-1.7.1
```

---

## 📊 Checklist Récapitulative

### Avant Migration

- [ ] GO/NO GO decision ✅
- [ ] Backup DB testé ✅
- [ ] Git snapshot ✅
- [ ] Branches créées ✅
- [ ] Configs backupées ✅

### Pendant Migration

- [ ] Phase 0: Preparation ✅
- [ ] Phase 1: DB Migration ✅
- [ ] Phase 2: Code Merge ✅
- [ ] Phase 3: Features Custom ✅
- [ ] Phase 4: Testing ✅
- [ ] Phase 5: Deployment ✅

### Après Migration

- [ ] All tests pass ✅
- [ ] MCP Hetzner works ✅
- [ ] Clawith Repair sync works ✅
- [ ] AgentMail works ✅
- [ ] Infisical works ✅
- [ ] No data loss ✅
- [ ] Documentation updated ✅
- [ ] Team notified ✅

---

## 📞 Contacts Urgence

| Rôle | Nom | Contact |
|------|-----|---------|
| **Validateur** | Guillaume | [Ton contact] |
| **Upgrade Lead** | [À assigner] | [Contact] |
| **MCP Lead** | [À assigner] | [Contact] |

---

## 💡 Notes pour Guillaume

**Si tu commences avant de dormir:**

1. **Phase 0-1** (1h): Backup + DB migration → **Safe to stop here**
2. **Phase 2** (6-8h): Code merge → **Nécessite concentration**
3. **Phase 3-5** (4-5h): Features + Tests + Deploy → **Peut attendre lendemain**

**Recommandation:**
- **Soir:** Phases 0-1 (Backup + DB)
- **Demain matin:** Phases 2-5 (Merge + Features + Tests + Deploy)

**Si quelque chose casse:**
- → Rollback (10-15 min)
- → Dors tranquille
- → Reprise demain

---

**Checklist créée par:** Migration Coordinator (Subagent)  
**Date:** 24 mars 2026  
**Statut:** ✅ Prêt à exécuter
