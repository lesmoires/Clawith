# Conflict Matrix: Clawith v1.7.0 → v1.7.1

**Date:** 24 mars 2026  
**Fork:** lesmoires/Clawith  
**Upstream:** dataelement/Clawith

---

## 🔴 High Risk Conflicts (Merge Manual Requis)

### 1. `backend/app/main.py`

**Risque:** 🔴 ÉLEVÉ  
**Cause:** Upstream a fait un logging overhaul complet (loguru), fork a des custom comments Supergateway

**Changements Upstream:**
- Import `loguru.logger`
- `configure_logging()` et `intercept_standard_logging()` au startup
- Remplacement de tous les `print()` par `logger.info/warning/error`
- Ajout `TraceIdMiddleware`
- Import `app.models.tenant_setting`

**Changements Fork:**
- Comment sur Supergateway MCP handling
- Pas de changements logging

**Résolution:**
```python
# Garder les deux: logging overhaul + Supergateway comment
from loguru import logger  # Upstream
from app.core.logging_config import configure_logging, intercept_standard_logging  # Upstream
from app.core.middleware import TraceIdMiddleware  # Upstream

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging first (Upstream)
    configure_logging()
    intercept_standard_logging()
    logger.info("[startup] Logging configured")
    
    # Note: MCP stdio servers are now handled by Supergateway (docker-compose service)
    # No need for embedded MCP HTTP wrapper anymore (Fork)
    
    # ... reste du code upstream
```

**Effort:** 1-2h  
**Test:** Vérifier logs avec trace IDs + Supergateway fonctionne

---

### 2. `backend/app/api/gateway.py`

**Risque:** 🔴 ÉLEVÉ  
**Cause:** Fork a ajouté WebSocket + ChatMessage routing, upstream a logging changes

**Changements Upstream:**
- Import `loguru.logger` au lieu de `logging`
- `print()` → `logger.info/warning`
- Feishu `open_id` → `user_id` fix

**Changements Fork:**
- +80 lignes de code pour WebSocket push + ChatMessage persistence
- Logic de création ChatSession pour agent-to-agent
- Participant lookup et ChatMessage save
- WebSocket notification via `manager.send_message()`

**Résolution:**
```python
from loguru import logger  # Upstream logging

# ... dans report_result() ...

if body.result and msg.sender_agent_id:
    async with async_session() as reply_db:
        conv_id = msg.conversation_id or f"gw_agent_{msg.sender_agent_id}_{agent.id}"
        
        # 1. Write reply to gateway_messages (Fork)
        gw_reply = GatewayMessage(...)
        reply_db.add(gw_reply)
        
        # 2. Save as ChatMessage (Fork)
        # ... tout le code Fork de ChatSession/ChatMessage/Participant ...
        
        await reply_db.commit()
        
        # 3. Push WebSocket notification (Fork)
        try:
            from app.api.websocket import manager
            # ... WebSocket push logic ...
            logger.info(f"[Gateway] WebSocket push to agent {sender_agent_id_str}")  # Upstream logging
        except Exception as e:
            logger.warning(f"[Gateway] WebSocket push failed: {e}")  # Upstream logging
        
        logger.info(f"[Gateway] Reply routed back to sender agent {msg.sender_agent_id}")  # Upstream
```

**Effort:** 2-3h  
**Test:** Agent-to-agent messaging + WebSocket notifications + logs trace ID

---

### 3. `docker-compose.yml`

**Risque:** 🔴 ÉLEVÉ  
**Cause:** Structures divergentes (Coolify env vars vs hardcoded)

**Fork (Coolify-friendly):**
```yaml
services:
  backend:
    build:
      context: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://clawith:${POSTGRES_PASSWORD}@postgres:5432/clawith
      REDIS_URL: redis://redis:6379/0
      # Infisical MCP (via Supergateway)
      INFISICAL_HOST_URL: ${INFISICAL_HOST_URL:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_ID: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}
      # AgentMail API
      AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
    volumes:
      - agent_data:/data/agents
      - /var/run/docker.sock:/var/run/docker.sock
```

**Upstream v1.7.1:**
```yaml
services:
  backend:
    build:
      context: ./backend
      args:
        CLAWITH_PIP_INDEX_URL: ${CLAWITH_PIP_INDEX_URL:-}
        CLAWITH_PIP_TRUSTED_HOST: ${CLAWITH_PIP_TRUSTED_HOST:-}
    environment:
      DATABASE_URL: postgresql+asyncpg://clawith:clawith@postgres:5432/clawith
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      FEISHU_APP_ID: ${FEISHU_APP_ID:-}
      DOCKER_NETWORK: clawith_network
      SS_CONFIG_FILE: /data/ss-nodes.json
    volumes:
      - ./backend:/app
      - ./backend/agent_data:/data/agents
      - /var/run/docker.sock:/var/run/docker.sock
      - ./ss-nodes.json:/data/ss-nodes.json:ro
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

**Résolution (Fusion):**
```yaml
services:
  backend:
    build:
      context: ./backend
      args:
        CLAWITH_PIP_INDEX_URL: ${CLAWITH_PIP_INDEX_URL:-}  # Upstream
        CLAWITH_PIP_TRUSTED_HOST: ${CLAWITH_PIP_TRUSTED_HOST:-}  # Upstream
    restart: unless-stopped
    command: ["/bin/bash", "/app/entrypoint.sh"]
    environment:
      # Database (Fork - Coolify env vars)
      DATABASE_URL: postgresql+asyncpg://clawith:${POSTGRES_PASSWORD}@postgres:5432/clawith
      REDIS_URL: redis://redis:6379/0
      # Secrets (Fork)
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      # Upstream configs
      CORS_ORIGINS: '["*"]'
      DOCKER_NETWORK: clawith_network
      SS_CONFIG_FILE: /data/ss-nodes.json
      FEISHU_APP_ID: ${FEISHU_APP_ID:-}
      FEISHU_APP_SECRET: ${FEISHU_APP_SECRET:-}
      # Infisical MCP (Fork custom)
      INFISICAL_HOST_URL: ${INFISICAL_HOST_URL:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_ID: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}
      INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET: ${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET:-}
      INFISICAL_PROJECT_ID: ${INFISICAL_PROJECT_ID:-}
      # AgentMail API (Fork custom)
      AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
    volumes:
      - agent_data:/data/agents  # Fork - named volume for Coolify
      - /var/run/docker.sock:/var/run/docker.sock
      - ./ss-nodes.json:/data/ss-nodes.json:ro  # Upstream
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    logging:
      driver: json-file  # Upstream
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - clawith_network  # Fork
```

**Effort:** 1h  
**Test:** Docker compose up + tous les services healthy

---

### 4. `backend/app/api/websocket.py`

**Risque:** 🟡 MOYEN-ÉLEVÉ  
**Cause:** Upstream logging changes + Fork custom logic potentielle

**Changements Upstream:**
- `print()` → `logger.info/warning/error`
- `logging` → `loguru.logger`
- Trace ID injection dans les logs

**Changements Fork:**
- Custom WebSocket manager logic
- Agent-to-agent notification handling

**Résolution:**
- Remplacer tous les `print()` par `logger.*`
- Garder custom logic Fork
- Ajouter trace ID context si manquant

**Effort:** 1h  
**Test:** WebSocket connections + notifications temps réel

---

## 🟡 Medium Risk Conflicts (Review Requis)

### 5. `backend/app/config.py`

**Risque:** 🟢 FAIBLE (identique des deux côtés)  
**Statut:** ✅ **Pas de conflit** - Mêmes changements

**Note:** Les deux côtés ont modifié `_read_version()` de la même manière. Merge automatique safe.

---

### 6. `backend/app/services/*.py` (15+ fichiers)

**Risque:** 🟡 MOYEN  
**Cause:** Upstream logging overhaul

**Fichiers Impactés:**
- `backend/app/services/agent_context.py`
- `backend/app/services/agent_tools.py`
- `backend/app/services/feishu_ws.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/mcp_client.py`
- `backend/app/services/skill_seeder.py`
- `backend/app/services/tool_seeder.py`
- +8 autres fichiers de services

**Changements Upstream:**
- `import logging` → `from loguru import logger`
- `logging.getLogger(__name__)` → supprimé
- `logger.info/warning/error/debug()` au lieu de `logging.*`

**Résolution:**
```python
# Avant (Fork)
import logging
logger = logging.getLogger(__name__)

# Après (Merge)
from loguru import logger
```

**Effort:** 2h (15 fichiers × 8min/fichier)  
**Test:** Logs de tous les services avec trace IDs

---

### 7. `backend/entrypoint.sh`

**Risque:** 🟡 MOYEN  
**Cause:** Upstream a ajouté auto-migrations

**Changements Upstream:**
- Auto-run `alembic upgrade head`
- Auto-run data migration scripts
- Better error handling

**Changements Fork:**
- Custom MCP/Supergateway setup
- Infisical/AgentMail config

**Résolution:**
- Garder auto-migrations upstream
- Ajouter custom MCP setup après migrations
- Tester que migrations + MCP setup coexistent

**Effort:** 30min  
**Test:** Fresh deploy + migrations run + MCP configured

---

### 8. `backend/pyproject.toml`

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream ajoute `loguru` dependency

**Changements Upstream:**
```toml
[project]
dependencies = [
    "loguru>=0.7.0",  # NOUVEAU
    # ... autres deps
]
```

**Résolution:**
- Ajouter `loguru` aux dependencies
- Vérifier pas de conflits avec deps Fork (Infisical, AgentMail)

**Effort:** 15min  
**Test:** `pip install -r requirements.txt` + import loguru

---

### 9. `backend/app/api/enterprise.py`

**Risque:** 🟡 MOYEN  
**Cause:** Upstream logging + Fork custom tenant logic

**Résolution:**
- Merge logging changes
- Préserver custom tenant isolation logic Fork

**Effort:** 30min

---

### 10. `backend/app/api/chat_sessions.py`

**Risque:** 🟡 MOYEN  
**Cause:** Logging changes + Fork custom session logic

**Effort:** 30min

---

### 11. `backend/app/schemas/schemas.py`

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream ajoute nouveaux schemas (ClawHub, Feishu user_id)

**Résolution:**
- Merge automatique probablement safe
- Vérifier schemas GatewayMessage inchangés

**Effort:** 30min

---

### 12. `backend/app/scripts/migrate_schedules_to_triggers.py`

**Risque:** 🟢 FAIBLE  
**Cause:** Script de migration, Fork a peut-être custom logic

**Effort:** 15min

---

### 13. `frontend/src/pages/*.tsx` (8 fichiers)

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream UI changes (ClawHub buttons, avatars, etc.)

**Fichiers:**
- `AdminCompanies.tsx`
- `AgentCreate.tsx`
- `AgentDetail.tsx`
- `EnterpriseSettings.tsx`
- `InvitationCodes.tsx`
- `Layout.tsx`
- +2 autres

**Résolution:**
- Merge upstream changes (ClawHub UI, new features)
- Préserver custom UI Fork si existe
- Rebuild frontend

**Effort:** 1h (8 fichiers + rebuild)

---

### 14. `frontend/src/i18n/*.json`

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream ajoute nouvelles traductions (ClawHub, Feishu user_id)

**Résolution:**
- Merge upstream translations
- Garder traductions custom Fork
- Ajouter traductions françaises si nécessaire

**Effort:** 30min

---

### 15. `frontend/nginx.conf`

**Risque:** 🟢 FAIBLE  
**Cause:** Fork a custom config pour Coolify/proxy

**Résolution:**
- Garder config Fork (probablement custom pour deployment)
- Vérifier compatibilité avec upstream changes

**Effort:** 15min

---

### 16. `frontend/vite.config.ts`

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream build config changes

**Effort:** 15min

---

### 17. `restart.sh` / `setup.sh`

**Risque:** 🟢 FAIBLE  
**Cause:** Scripts de deployment, Fork a custom logic

**Résolution:**
- Review changes upstream
- Garder custom Fork logic (Coolify, MCP setup)
- Merge upstream improvements

**Effort:** 30min

---

## 🟢 Low Risk / No Conflict

### 18. `backend/VERSION` / `frontend/VERSION`

**Risque:** 🟢 FAIBLE  
**Résolution:** Bump à `1.7.1`  
**Effort:** 5min

---

### 19. `frontend/dist.zip`

**Risque:** 🟢 FAIBLE  
**Résolution:** Rebuild frontend (`npm run build`)  
**Effort:** 5min (build time inclus)

---

### 20. `RELEASE_NOTES.md`

**Risque:** 🟢 FAIBLE  
**Résolution:** Merge documentation, ajouter section features custom Fork  
**Effort:** 15min

---

### 21. `README*.md` (5 fichiers)

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream ajoute Clawith slogan banner

**Résolution:**
- Merge upstream banner
- Garder custom sections Fork si existe

**Effort:** 30min

---

### 22. `backend/alembic/versions/df3da9cf3b27_add_entrypoint_missing_columns.py`

**Risque:** 🟢 FAIBLE  
**Cause:** Migration DB, déjà présente dans Fork

**Résolution:**
- Vérifier migration déjà appliquée
- Skip si déjà existante

**Effort:** 15min

---

### 23. `backend/app/models/tenant_setting.py`

**Risque:** 🟢 FAIBLE  
**Cause:** Upstream ajoute nouveau model (ClawHub config)

**Résolution:**
- Merge nouveau model
- Vérifier pas de conflit avec models custom Fork

**Effort:** 30min

---

### 24. `backend/app/core/logging_config.py`

**Risque:** 🟢 FAIBLE (NOUVEAU fichier upstream)  
**Cause:** Upstream ajoute logging configuration

**Résolution:**
- Ajouter fichier upstream
- Adapter si Fork a custom logging config

**Effort:** 30min

---

### 25. `backend/app/core/middleware.py`

**Risque:** 🟢 FAIBLE (NOUVEAU fichier upstream)  
**Cause:** Upstream ajoute TraceIdMiddleware

**Résolution:**
- Ajouter fichier upstream
- Intégrer dans `main.py`

**Effort:** 30min

---

## 📊 Résumé des Conflits

| Risque | Count | Effort Total |
|--------|-------|--------------|
| 🔴 ÉLEVÉ | 4 | 5-7h |
| 🟡 MOYEN | 10 | 4-5h |
| 🟢 FAIBLE | 11 | 2-3h |
| **TOTAL** | **25** | **11-15h** |

**Note:** L'estimation haute (15h) inclut buffer pour imprévus. En pratique, avec bonne concentration, 8-10h devrait suffire.

---

## 🎯 Priorité de Résolution

1. **🔴 `backend/app/main.py`** - Logging foundation (à faire en premier)
2. **🔴 `backend/app/api/gateway.py`** - Feature custom critique
3. **🔴 `docker-compose.yml`** - Deployment config
4. **🔴 `backend/app/api/websocket.py`** - Real-time features
5. **🟡 `backend/app/services/*.py`** - Logging propagation
6. **🟡 `backend/entrypoint.sh`** - Migrations + MCP setup
7. **🟢 Restes** - Par ordre alphabétique

---

## ✅ Validation Post-Merge

Pour chaque fichier mergé:
- [ ] `git diff` pour review
- [ ] Syntax check (`python -m py_compile` ou `npm run lint`)
- [ ] Test fonctionnel associé
- [ ] Logs vérifiés (trace IDs présents)

---

**Matrice générée par Claw - 24 mars 2026**
