# ✨ Features Préservées

**Merge:** upstream/main → feature/upgrade-1.7.1  
**Date:** 2026-03-24

---

## 🎯 Résumé

Pendant le merge avec upstream v1.7.1, nous avons **préservé 5 features custom Clawith** tout en intégrant les améliorations d'upstream.

---

## 1️⃣ Infisical MCP Integration

**Fichier:** `.env.example`, `docker-compose.yml`, `backend/app/main.py`

**Description:** Intégration avec Infisical pour la gestion des secrets via Supergateway MCP.

**Ce qui a été préservé:**
```bash
# .env.example
INFISICAL_HOST_URL=https://secrets.moiria.com
INFISICAL_UNIVERSAL_AUTH_CLIENT_ID=
INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET=
INFISICAL_PROJECT_ID=
```

```yaml
# docker-compose.yml
servicessupergateway:
  image: node:20-alpine
  command: supergateway --stdio 'npx -y @infisical/mcp' --port 8000
  environment:
    - INFISICAL_HOST_URL=${INFISICAL_HOST_URL}
    - INFISICAL_UNIVERSAL_AUTH_CLIENT_ID=${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID}
    - INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET=${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET}
    - INFISICAL_PROJECT_ID=${INFISICAL_PROJECT_ID}
```

**Usage:** Les agents peuvent accéder aux secrets sécurisés via le MCP Infisical.

**Fichier custom associé:** `backend/app/skills/infisical_secrets.py`

---

## 2️⃣ AgentMail API Integration

**Fichier:** `.env.example`, `docker-compose.yml`

**Description:** Intégration avec AgentMail pour l'envoi/réception d'emails via MCP.

**Ce qui a été préservé:**
```bash
# .env.example
# AgentMail API Key - MCP Email Server
# Get from: https://console.agentmail.to
AGENTMAIL_API_KEY=am_us_e4a0a432ee65d852f772fa558100f6293d29748aaf587d2912a98a9d1f29e819
```

```yaml
# docker-compose.yml
backend:
  environment:
    # AgentMail API
    AGENTMAIL_API_KEY: ${AGENTMAIL_API_KEY:-}
```

**Usage:** Les agents peuvent envoyer et recevoir des emails via le serveur MCP AgentMail.

**Fichier custom associé:** `backend/app/tools/agentmail_tools.py`

---

## 3️⃣ WebSocket Push pour Agent-to-Agent

**Fichier:** `backend/app/api/gateway.py`

**Description:** Système de notification WebSocket en temps réel pour les communications agent-to-agent.

**Ce qui a été préservé:**
```python
# backend/app/api/gateway.py - report_result()

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
    logger.info(f"[Gateway] WebSocket push to agent {sender_agent_id_str}")
except Exception as e:
    logger.warning(f"[Gateway] WebSocket push failed: {e}")
```

**Fonctionnement:**
1. Quand un agent répond à un autre agent
2. La réponse est écrite dans `gateway_messages` (pour polling)
3. **ET** sauvegardée comme `ChatMessage` (pour l'historique)
4. **ET** poussée via WebSocket (pour notification temps réel)

**Avantage:** UX temps réel - les utilisateurs voient les réponses agent-to-agent instantanément sans attendre le prochain poll.

---

## 4️⃣ Coolify Network Configuration

**Fichier:** `docker-compose.yml`

**Description:** Configuration réseau pour Coolify avec proxy Traefik.

**Ce qui a été préservé:**
```yaml
# docker-compose.yml
backend:
  networks:
    - clawith_network
    - coolify  # For Traefik proxy access (prevents gateway timeout)

frontend:
  labels:
    - traefik.enable=true
    - traefik.http.routers.clawith-http.rule=Host(`agents.moiria.com`)
    - traefik.http.routers.clawith-https.rule=Host(`agents.moiria.com`)
    - traefik.http.routers.clawith-https.tls=true
    - traefik.http.routers.clawith-https.tls.certresolver=letsencrypt
  networks:
    - clawith_network
    - coolify  # For Traefik proxy access (prevents gateway timeout)

networks:
  clawith_network:
    driver: bridge
  coolify:
    external: true  # Coolify's global network for Traefik proxy
```

**Usage:** Permet à Coolify de router le trafic HTTPS vers l'application avec TLS automatique via Let's Encrypt.

---

## 5️⃣ Enterprise Info Migration

**Fichier:** `backend/app/main.py`

**Description:** Migration des données enterprise_info partagées vers un stockage par tenant.

**Ce qui a été préservé:**
```python
# backend/app/main.py - lifespan()

# Migrate old shared enterprise_info/ → enterprise_info_{first_tenant_id}/
try:
    import shutil
    from pathlib import Path as _Path
    from app.config import get_settings as _gs
    from app.models.tenant import Tenant as _T
    from app.database import async_session as _ses
    from sqlalchemy import select as _sel
    
    _data_dir = _Path(_gs().AGENT_DATA_DIR)
    _old_dir = _data_dir / "enterprise_info"
    
    if _old_dir.exists() and any(_old_dir.iterdir()):
        async with _ses() as _db:
            _first = await _db.execute(_sel(_T).order_by(_T.created_at).limit(1))
            _tenant = _first.scalar_one_or_none()
            if _tenant:
                _new_dir = _data_dir / f"enterprise_info_{_tenant.id}"
                if not _new_dir.exists():
                    shutil.copytree(str(_old_dir), str(_new_dir))
                    logger.info(f"[startup] Migrated enterprise_info → enterprise_info_{_tenant.id}")
except Exception as e:
    logger.warning(f"[startup] enterprise_info migration failed: {e}")
```

**Usage:** Assure la compatibilité ascendante en migrant les anciennes données partagées vers un stockage multi-tenant.

---

## 📁 Fichiers Custom Préservés

Ces fichiers contiennent notre logique métier custom et n'ont **PAS** été écrasés:

| Fichier | Description | Lignes |
|---------|-------------|--------|
| `backend/app/tools/agentmail_tools.py` | Outils MCP pour AgentMail | ~250 |
| `backend/app/skills/infisical_secrets.py` | Skill pour Infisical secrets | ~120 |

**Commande de vérification:**
```bash
ls -la backend/app/tools/agentmail_tools.py backend/app/skills/infisical_secrets.py
# ✅ Les deux fichiers existent
```

---

## 🔄 Améliorations Upstream Intégrées

En plus de préserver nos features, nous avons intégré ces améliorations d'upstream:

| Feature | Fichier | Bénéfice |
|---------|---------|----------|
| Logger (loguru) | Tous les fichiers | Meilleur logging que print() |
| TraceIdMiddleware | backend/app/main.py | Traçage des requêtes |
| Participant tracking | backend/app/models/*.py | Suivi des participants |
| Pages API | backend/app/api/pages.py | Nouvelles endpoints |
| Version endpoint | backend/app/main.py | `/api/version` public |
| Discord gateway | backend/app/services/discord_gateway.py | Support Discord amélioré |
| Tenant settings | backend/app/models/tenant_setting.py | Config par tenant |

---

## ✅ Vérification Post-Merge

Pour vérifier que les features sont fonctionnelles:

```bash
# 1. Vérifier les fichiers custom
test -f backend/app/tools/agentmail_tools.py && echo "✅ AgentMail tools present"
test -f backend/app/skills/infisical_secrets.py && echo "✅ Infisical secrets present"

# 2. Vérifier la config docker-compose
grep -q "supergateway" docker-compose.yml && echo "✅ Supergateway configured"
grep -q "coolify" docker-compose.yml && echo "✅ Coolify network configured"
grep -q "AGENTMAIL_API_KEY" docker-compose.yml && echo "✅ AgentMail env var present"
grep -q "INFISICAL" docker-compose.yml && echo "✅ Infisical env vars present"

# 3. Vérifier gateway.py
grep -q "WebSocket" backend/app/api/gateway.py && echo "✅ WebSocket push present"
grep -q "agent_reply" backend/app/api/gateway.py && echo "✅ Agent-to-agent routing present"

# 4. Vérifier main.py
grep -q "enterprise_info" backend/app/main.py && echo "✅ Enterprise migration present"
grep -q "TraceIdMiddleware" backend/app/main.py && echo "✅ TraceIdMiddleware present"
```

---

## 🎉 Conclusion

**Toutes les features custom Clawith ont été préservées avec succès!**

Le merge combine:
- ✅ Nos 5 features custom (Infisical, AgentMail, WebSocket, Coolify, Enterprise migration)
- ✅ 7 améliorations upstream (logging, tracing, pages, version, discord, tenant settings)
- ✅ 80+ conflits résolus manuellement ou automatiquement

**Prochaine étape:** Tester localement avec `docker-compose up` et créer une PR.

---

*Généré par Git Merge Specialist*
