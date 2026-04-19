# Moiria Deploy Customizations — Docker Compose

**Base:** Upstream v1.8.1 `docker-compose.yml`  
**Overlay:** This file (`docker-compose.yml`)  
**Reference:** `docker-compose.upstream-ref.yml` = upstream v1.8.1 vanilla

---

## Changements par rapport à upstream

### 1. Backend

| Upstream (dev) | Moiria (prod) | Raison |
|----------------|---------------|--------|
| `./backend:/app` (bind mount) | Code from built image | Prod: le container utilise le code buildé, pas le git clone |
| `./backend/agent_data:/data/agents` (bind) | `agent_data:` (named volume) | Les données agents survivent aux redeployments |
| Pas de ports exposés | `8000:8000` | Accès API pour Coolify health checks |
| `DOCKER_NETWORK: clawith_network` | `DOCKER_NETWORK: clawith_network` | Idem |
| Pas de réseaux custom | `clawith_network` + `coolify` (external) | Traefik proxy access |
| `POSTGRES_PASSWORD: clawith` (hardcoded) | `${POSTGRES_PASSWORD:-clawith}` | Sécurité: variable d'env |
| `DATABASE_URL: ...clawith@...` (hardcoded password) | `...${POSTGRES_PASSWORD:-clawith}@...` | Idem |

#### Env vars ajoutées (Moiria)

| Variable | Usage |
|----------|-------|
| `INFISICAL_HOST_URL` | Infisical MCP integration |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` | Infisical auth |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` | Infisical auth |
| `INFISICAL_PROJECT_ID` | Infisical project scope |
| `AGENTMAIL_API_KEY` | AgentMail API access |

### 2. Supergateway (NOUVEAU — n'existe pas en upstream)

Service MCP bridge pour Infisical:
- Image: `node:20-alpine`
- Command: `supergateway --stdio 'npx -y @infisical/mcp' --port 8000`
- Health check sur `/health`
- Network: `clawith_network`

### 3. Frontend

| Upstream (dev) | Moiria (prod) | Raison |
|----------------|---------------|--------|
| `VITE_API_URL: http://localhost:8000` | `VITE_API_URL: http://backend:8000` | Docker internal networking |
| Pas de dépendance supergateway | `depends_on: [backend, supergateway]` | Startup ordering |
| Pas de labels | Traefik labels (voir ci-dessous) | HTTPS routing |
| Pas de réseaux custom | `clawith_network` + `coolify` | Traefik access |

#### Traefik labels

```yaml
traefik.enable=true
traefik.http.routers.clawith-http.rule=Host(`agents.moiria.com`)
traefik.http.routers.clawith-http.entrypoints=http
traefik.http.routers.clawith-http.middlewares=clawith-redirect
traefik.http.middlewares.clawith-redirect.redirectscheme.scheme=https
traefik.http.middlewares.clawith-redirect.redirectscheme.permanent=true
traefik.http.routers.clawith-https.rule=Host(`agents.moiria.com`)
traefik.http.routers.clawith-https.entrypoints=https
traefik.http.routers.clawith-https.tls=true
traefik.http.routers.clawith-https.tls.certresolver=letsencrypt
traefik.http.routers.clawith-https.service=clawith
traefik.http.services.clawith.loadbalancer.server.port=3000
traefik.http.middlewares.clawith-gzip.compress=true
traefik.http.routers.clawith-https.middlewares=clawith-gzip
```

### 4. Networks

| Upstream | Moiria |
|----------|--------|
| `default: name: clawith_network` | `clawith_network` (bridge) + `coolify` (external) |

### 5. Volumes

| Upstream | Moiria |
|----------|--------|
| `pgdata`, `redisdata` | `pgdata`, `redisdata`, **`agent_data`** |

---

## Merge strategy pour futures releases

Quand une nouvelle version upstream sort (ex: v1.8.2):

```bash
# 1. Fetch upstream
git fetch upstream

# 2. Check what changed in docker-compose.yml
git diff v1.8.1..upstream/v1.8.2 -- docker-compose.yml

# 3. Si upstream a changé le docker-compose:
#    a. Sauvegarder la nouvelle référence
#    git show upstream/v1.8.2:docker-compose.yml > docker-compose.upstream-ref.yml
#    b. Appliquer nos customisations manuellement sur docker-compose.yml
#    c. Tester en staging
```

**Pourquoi pas un overlay `-f docker-compose.override.yml` ?**  
Parce que nos changements remplacent des sections entières (volumes backend, networks, labels Traefik, service supergateway) — pas juste des ajouts. Un overlay ne peut pas *supprimer* des sections du fichier de base.
