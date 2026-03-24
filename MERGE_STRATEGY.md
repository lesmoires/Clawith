# Merge Strategy: Clawith v1.7.0 → v1.7.1

**Date:** 24 mars 2026  
**Niveau:** Step-by-step guide  
**Temps estimé:** 6-8 heures

---

## 📋 Prérequis

### Avant de Commencer

- [ ] **Backup DB complet:**
  ```bash
  docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Snapshot VM/serveur** (si applicable)

- [ ] **Git setup:**
  ```bash
  cd /data/workspace/clawith-fork
  git remote add dataelement https://github.com/dataelement/Clawith.git  # si pas déjà fait
  git fetch dataelement --tags
  ```

- [ ] **Branche de travail:**
  ```bash
  git checkout -b upgrade/v1.7.1
  ```

- [ ] **Environnement de test** prêt (staging ou local)

- [ ] **Équipe notifiée** (downtime potentiel)

---

## 🚀 Étape 1: Merge Initial (30 min)

### 1.1 Merge Upstream v1.7.1

```bash
# Vérifier version actuelle
cat backend/VERSION  # Doit afficher: 1.7.0

# Merge upstream v1.7.1
git merge v1.7.1 --no-commit --no-ff
```

### 1.2 Voir Conflits

```bash
# Lister fichiers en conflit
git status --short | grep "^UU"

# Ou lister tous les fichiers changés
git diff --name-only HEAD v1.7.1
```

**Sortie attendue:** ~33 fichiers en conflit potentiel

---

## 🔴 Étape 2: Résoudre Conflits Critiques (4-5h)

### 2.1 `backend/app/main.py` (1-2h)

**Commande:**
```bash
git checkout --ours backend/app/main.py  # Garder version fork
```

**Éditer le fichier:**
```python
# Lignes 1-10: Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger  # ← AJOUTER (upstream)

from app.config import get_settings
from app.core.events import close_redis
from app.core.logging_config import configure_logging, intercept_standard_logging  # ← AJOUTER (upstream)
from app.core.middleware import TraceIdMiddleware  # ← AJOUTER (upstream)

# ... dans lifespan() ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Configure logging first (upstream)
    configure_logging()
    intercept_standard_logging()
    logger.info("[startup] Logging configured")
    
    # Note: MCP stdio servers are now handled by Supergateway (docker-compose service)
    # No need for embedded MCP HTTP wrapper anymore (fork)
    
    # ... reste du code upstream ...
```

**Validation:**
```bash
python -m py_compile backend/app/main.py
```

---

### 2.2 `backend/app/api/gateway.py` (2-3h)

**Commande:**
```bash
git checkout --ours backend/app/api/gateway.py  # Garder version fork
```

**Éditer le fichier:**

**Section imports (lignes 1-20):**
```python
# Remplacer:
import logging
logger = logging.getLogger(__name__)

# Par:
from loguru import logger  # ← Upstream logging
```

**Section `report_result()` (lignes ~220-350):**
```python
async def report_result(
    # ... params ...
):
    """OpenClaw agent reports the result of a processed message."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-Api-Key header")
    logger.info(f"[Gateway] report called, key_prefix={x_api_key[:8]}..., msg_id={body.message_id}")  # ← Upstream logging
    
    # ... validation code ...
    
    # If the original message was from another agent (OpenClaw-to-OpenClaw),
    # write the reply back as a gateway_message for the sender agent to poll
    # AND push WebSocket notification + save as ChatMessage for real-time UX
    if body.result and msg.sender_agent_id:
        async with async_session() as reply_db:
            conv_id = msg.conversation_id or f"gw_agent_{msg.sender_agent_id}_{agent.id}"
            
            # 1. Write reply to gateway_messages (for polling)
            gw_reply = GatewayMessage(
                agent_id=msg.sender_agent_id,
                sender_agent_id=agent.id,
                content=body.result,
                conversation_id=conv_id,
            )
            reply_db.add(gw_reply)
            
            # 2. Save as ChatMessage in target agent's conversation (for history + UI)
            from app.models.audit import ChatMessage
            from app.models.chat_session import ChatSession
            from app.models.participant import Participant
            import uuid as _uuid
            
            # Find or create ChatSession for this agent pair
            _ns = _uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
            sorted_ids = sorted([str(msg.sender_agent_id), str(agent.id)])
            session_uuid = _uuid.uuid5(_ns, f"{sorted_ids[0]}_{sorted_ids[1]}")
            
            existing_session = await reply_db.execute(
                select(ChatSession).where(ChatSession.id == session_uuid)
            )
            session = existing_session.scalar_one_or_none()
            if not session:
                # Load sender agent to get creator_id
                from app.models.agent import Agent as AgentModel
                sender_result = await reply_db.execute(
                    select(AgentModel).where(AgentModel.id == msg.sender_agent_id)
                )
                sender_agent = sender_result.scalar_one_or_none()
                
                session = ChatSession(
                    id=session_uuid,
                    agent_id=msg.sender_agent_id,
                    user_id=sender_agent.creator_id if sender_agent else agent.creator_id,
                    title=f"{agent.name} ↔ {sender_agent.name if sender_agent else 'Agent'}",
                    source_channel="agent",
                    peer_agent_id=agent.id,
                    created_at=datetime.now(timezone.utc),
                )
                reply_db.add(session)
            
            await reply_db.flush()
            
            # Find participant for sender agent
            participant_result = await reply_db.execute(
                select(Participant).where(
                    Participant.type == "agent",
                    Participant.ref_id == msg.sender_agent_id,
                )
            )
            sender_participant = participant_result.scalar_one_or_none()
            
            # Save assistant reply to conversation
            chat_msg = ChatMessage(
                agent_id=msg.sender_agent_id,
                conversation_id=str(session_uuid),
                role="assistant",
                content=body.result,
                user_id=agent.creator_id,
                participant_id=sender_participant.id if sender_participant else None,
            )
            reply_db.add(chat_msg)
            
            await reply_db.commit()
            
            # 3. Push WebSocket notification to sender agent's creator (if connected)
            try:
                from app.api.websocket import manager
                sender_agent_id_str = str(msg.sender_agent_id)
                await manager.send_message(sender_agent_id_str, {
                    "type": "agent_reply",
                    "role": "assistant",
                    "content": body.result,
                    "from_agent": agent.name,
                    "conversation_id": str(session_uuid),
                })
                logger.info(f"[Gateway] WebSocket push to agent {sender_agent_id_str}")  # ← Upstream logging
            except Exception as e:
                logger.warning(f"[Gateway] WebSocket push failed: {e}")  # ← Upstream logging
            
            logger.info(f"[Gateway] Reply routed back to sender agent {msg.sender_agent_id}")  # ← Upstream logging
    
    return {"status": "ok"}
```

**Validation:**
```bash
python -m py_compile backend/app/api/gateway.py
```

---

### 2.3 `docker-compose.yml` (1h)

**Commande:**
```bash
git checkout --ours docker-compose.yml  # Garder version fork
```

**Éditer le fichier:**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: clawith
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: clawith
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clawith"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - clawith_network

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - clawith_network

  backend:
    build:
      context: ./backend
      args:  # ← AJOUTER (upstream)
        CLAWITH_PIP_INDEX_URL: ${CLAWITH_PIP_INDEX_URL:-}
        CLAWITH_PIP_TRUSTED_HOST: ${CLAWITH_PIP_TRUSTED_HOST:-}
    restart: unless-stopped
    command: ["/bin/bash", "/app/entrypoint.sh"]
    environment:
      # Database (fork - Coolify env vars)
      DATABASE_URL: postgresql+asyncpg://clawith:${POSTGRES_PASSWORD}@postgres:5432/clawith
      REDIS_URL: redis://redis:6379/0
      # Secrets (fork)
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      # Upstream configs
      CORS_ORIGINS: '["*"]'
      DOCKER_NETWORK: clawith_network
      SS_CONFIG_FILE: /data/ss-nodes.json
      FEISHU_APP_ID: ${FEISHU_APP_ID:-}
      FEISHU_APP_SECRET: ${FEISHU_APP_SECRET:-}
      # Infisical MCP (fork custom)
      INFISICAL_HOST_URL: ${INFISICAL_HOST_URL:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_ID: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET:-}
      INFISICAL_PROJECT_ID: ${INFISICAL_PROJECT_ID:-}
      # AgentMail API (fork custom)
      AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
    volumes:
      - agent_data:/data/agents  # fork - named volume for Coolify
      - /var/run/docker.sock:/var/run/docker.sock
      - ./ss-nodes.json:/data/ss-nodes.json:ro  # ← AJOUTER (upstream)
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    logging:  # ← AJOUTER (upstream)
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - clawith_network

  frontend:
    image: ghcr.io/dataelement/clawith-frontend:latest  # ← ou build: context: ./frontend
    ports:
      - "${FRONTEND_PORT:-3008}:3000"
    environment:
      VITE_API_URL: http://backend:8000
    depends_on:
      - backend
    networks:
      - clawith_network

volumes:
  pgdata:
  redisdata:
  agent_data:

networks:
  clawith_network:
    driver: bridge
```

**Validation:**
```bash
docker compose config  # Valider syntaxe YAML
```

---

### 2.4 `backend/app/api/websocket.py` (1h)

**Commande:**
```bash
git checkout --ours backend/app/api/websocket.py
```

**Rechercher et remplacer:**
```bash
# Trouver tous les print()
grep -n "print(" backend/app/api/websocket.py

# Remplacer manuellement:
# print("...") → logger.info("...")
# print(f"...") → logger.info(f"...")
```

**Ajouter import en haut:**
```python
from loguru import logger  # ← AJOUTER
# Supprimer: import logging, logger = logging.getLogger(__name__)
```

**Validation:**
```bash
python -m py_compile backend/app/api/websocket.py
```

---

## 🟡 Étape 3: Résoudre Conflits Moyens (2-3h)

### 3.1 Services Logging (15 fichiers, 2h)

**Script de migration automatique:**

```bash
#!/bin/bash
# migrate_logging.sh

FILES=(
  "backend/app/services/agent_context.py"
  "backend/app/services/agent_tools.py"
  "backend/app/services/feishu_ws.py"
  "backend/app/services/llm_client.py"
  "backend/app/services/mcp_client.py"
  "backend/app/services/skill_seeder.py"
  "backend/app/services/tool_seeder.py"
  "backend/app/services/activity_logger.py"
  "backend/app/services/audit_logger.py"
  "backend/app/services/collaboration.py"
  "backend/app/services/dingtalk_stream.py"
  "backend/app/services/enterprise_sync.py"
  "backend/app/services/feishu_service.py"
  "backend/app/services/heartbeat.py"
  "backend/app/services/notification_service.py"
)

for file in "${FILES[@]}"; do
  echo "Processing $file..."
  
  # Backup
  cp "$file" "$file.bak"
  
  # Replace imports
  sed -i 's/^import logging$/from loguru import logger  # Migrated for v1.7.1/' "$file"
  sed -i 's/^logger = logging.getLogger(__name__)$/# Removed for loguru migration/' "$file"
  
  # Replace logging calls
  sed -i 's/logger\.info(/logger.info(/g' "$file"
  sed -i 's/logger\.warning(/logger.warning(/g' "$file"
  sed -i 's/logger\.error(/logger.error(/g' "$file"
  sed -i 's/logger\.debug(/logger.debug(/g' "$file"
  
  # Validate
  python -m py_compile "$file"
  if [ $? -ne 0 ]; then
    echo "ERROR: $file failed compilation, restoring backup"
    cp "$file.bak" "$file"
  else
    rm "$file.bak"
    echo "OK: $file migrated"
  fi
done
```

**Exécution:**
```bash
chmod +x migrate_logging.sh
./migrate_logging.sh
```

**Review manuel:**
```bash
# Vérifier chaque fichier
git diff backend/app/services/agent_context.py
# Confirmer logging changes correctes
```

---

### 3.2 `backend/entrypoint.sh` (30 min)

**Commande:**
```bash
git checkout --ours backend/entrypoint.sh
```

**Ajouter après migrations upstream:**
```bash
#!/bin/bash
set -e

# ... upstream migrations ...

# Alembic migrations
alembic upgrade head

# Data migrations (upstream)
python3 -m app.scripts.migrate_schedules_to_triggers

# ← AJOUTER: Custom MCP setup (fork)
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

---

### 3.3 `backend/pyproject.toml` (15 min)

**Commande:**
```bash
git checkout --ours backend/pyproject.toml
```

**Ajouter dependency:**
```toml
[project]
dependencies = [
    "loguru>=0.7.0",  # ← AJOUTER pour v1.7.1
    # ... autres deps existantes ...
]
```

**Validation:**
```bash
cd backend
pip install -e .
python -c "from loguru import logger; logger.info('Test')"
```

---

### 3.4 Frontend Pages (1h)

**Pour chaque fichier:**
```bash
git checkout --ours frontend/src/pages/AgentCreate.tsx
# Merge manuel: garder custom UI fork + upstream ClawHub buttons
```

**Fichiers à merger:**
- `AgentCreate.tsx` - Ajouter ClawHub import buttons
- `AgentDetail.tsx` - Upstream UI improvements
- `EnterpriseSettings.tsx` - GitHub Token config UI
- `Layout.tsx` - Sidebar improvements
- +4 autres fichiers

**Rebuild frontend:**
```bash
cd frontend
npm install
npm run build
```

---

### 3.5 i18n Files (30 min)

**Commande:**
```bash
git checkout --ours frontend/src/i18n/en.json
git checkout --ours frontend/src/i18n/zh.json
```

**Merge:**
- Garder traductions fork
- Ajouter nouvelles traductions upstream (ClawHub, Feishu user_id)
- Ajouter traductions françaises si nécessaire

---

## 🟢 Étape 4: Conflits Mineurs (1h)

### 4.1 VERSION Files (5 min)

```bash
echo "1.7.1" > backend/VERSION
echo "1.7.1" > frontend/VERSION
```

---

### 4.2 README Files (30 min)

```bash
git checkout --ours README.md README_es.md README_ja.md README_ko.md README_zh-CN.md
```

**Merge:**
- Garder banner upstream
- Ajouter sections custom fork si existe

---

### 4.3 Scripts & Configs (30 min)

```bash
# Review et merge manuel
git checkout --ours restart.sh setup.sh
git diff HEAD restart.sh  # Voir changements upstream
# Merge manuel si nécessaire
```

---

## ✅ Étape 5: Validation & Tests (2h)

### 5.1 Syntax Checks

```bash
# Backend
cd backend
python -m py_compile app/main.py
python -m py_compile app/api/gateway.py
python -m py_compile app/api/websocket.py

# Frontend
cd frontend
npm run lint
```

---

### 5.2 Docker Build

```bash
cd /data/workspace/clawith-fork

# Build backend
docker compose build backend

# Build frontend (si pas using pre-built image)
docker compose build frontend
```

---

### 5.3 Tests Fonctionnels

**Checklist:**
- [ ] `docker compose up -d`
- [ ] Tous services healthy: `docker compose ps`
- [ ] Logs propres: `docker compose logs backend | grep -i error`
- [ ] Frontend accessible: `curl https://clawith.your-domain.com`
- [ ] Login fonctionne
- [ ] Création agent fonctionne
- [ ] Chat avec agent → réponses OK
- [ ] **WebSocket temps réel** (test avec 2 onglets)
- [ ] **Gateway API agent-to-agent** (test custom fork)
- [ ] **Supergateway MCP** (test Infisical tools)
- [ ] **AgentMail tools** (test send/receive)
- [ ] **Infisical secrets** (test get_secret)
- [ ] Upload fichier < 100MB
- [ ] Feishu org sync (si utilisé)

---

### 5.4 Tests Performance

```bash
# API response time
curl -w "@curl-format.txt" -o /dev/null -s https://clawith.your-domain.com/api/health

# curl-format.txt:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_starttransfer: %{time_starttransfer}\n
# --------------------\n
# time_total:       %{time_total}\n
```

**Targets:**
- API response: < 500ms
- Page load: < 3 sec
- WebSocket latency: < 100ms

---

## 🚨 Étape 6: Rollback Plan (Si Problème)

### 6.1 Quick Rollback

```bash
# Stop services
docker compose down

# Restore code
git checkout main  # ou v1.7.0

# Restore DB
cat backup_20260324.sql | docker exec -i clawith-postgres-1 psql -U clawith clawith

# Restart
docker compose up -d
```

**Temps:** 10-15 minutes

---

### 6.2 Partial Rollback

Si seulement certains fichiers posent problème:

```bash
# Revert fichier spécifique
git checkout v1.7.0 -- backend/app/api/gateway.py

# Rebuild
docker compose build backend
docker compose up -d backend
```

---

## 📊 Étape 7: Commit & Merge

### 7.1 Commit Changes

```bash
git add .
git commit -m "feat: Upgrade Clawith v1.7.0 → v1.7.1

- Merge upstream dataelement/Clawith v1.7.1
- Preserve custom features: Supergateway, AgentMail, Infisical MCP
- Enhanced Gateway API with WebSocket + ChatMessage routing
- Migrate logging to loguru with trace ID support
- Update docker-compose for Coolify deployment

Features merged from upstream:
- ClawHub Skills Marketplace
- Feishu user_id architecture fix
- Logging system overhaul (loguru)
- UI improvements (avatars, sorting, notifications)

Custom features preserved:
- Supergateway POC for Infisical MCP
- AgentMail integration
- Infisical Secrets skill
- Gateway API agent-to-agent real-time routing

Migration notes:
- Run Feishu cleanup: docker exec backend python3 -m app.scripts.cleanup_duplicate_feishu_users
- Rebuild frontend: cd frontend && npm run build
- Update env vars: INFISICAL_*, AGENTMAIL_API_KEY

BREAKING CHANGES:
- Logging migrated from stdlib to loguru
- Feishu open_id → user_id (migration script provided)
"
```

---

### 7.2 Merge to Main

```bash
git checkout main
git merge upgrade/v1.7.1 --no-ff
git push origin main
```

---

### 7.3 Tag Version

```bash
git tag -a v1.7.1-lesmoires.1 -m "Clawith v1.7.1 + custom features (Supergateway, AgentMail, Infisical)"
git push origin v1.7.1-lesmoires.1
```

---

## 🎉 Étape 8: Post-Upgrade

### 8.1 Feishu Migration (Si Applicable)

```bash
docker exec clawith-backend-1 python3 -m app.scripts.cleanup_duplicate_feishu_users
```

---

### 8.2 Monitoring

**Setup alerts:**
- [ ] Error rate > 1% → alert
- [ ] API latency > 1s → alert
- [ ] WebSocket disconnections → alert
- [ ] DB connections > 80% → alert

---

### 8.3 Documentation Update

**Mettre à jour:**
- [ ] `README.md` - Version badge
- [ ] `RELEASE_NOTES.md` - Section v1.7.1-lesmoires.1
- [ ] Internal docs - Custom features list
- [ ] Team notification - Upgrade complete

---

## 📈 Checklist Finale

- [ ] Code mergé et testé
- [ ] DB backup avant upgrade
- [ ] Rollback plan testé
- [ ] Tous services healthy
- [ ] Features custom fonctionnelles
- [ ] Performance targets met
- [ ] Équipe notifiée
- [ ] Documentation updated
- [ ] Monitoring alerts configured
- [ ] Tag version pushed

---

**Guide créé par Claw - 24 mars 2026**
