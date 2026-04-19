# Moiria Deploy Customizations — Docker Compose

**Base:** Upstream v1.8.1 `docker-compose.yml`  
**Overlay:** This file (`docker-compose.yml`)  
**Reference:** `docker-compose.upstream-ref.yml` = upstream v1.8.1 vanilla

---

## Changes vs upstream

### 1. Backend

| Upstream (dev) | Moiria (prod) | Reason |
|----------------|---------------|--------|
| `./backend:/app` (bind mount) | Code from built image | Prod: container uses built image code, not git clone |
| `./backend/agent_data:/data/agents` (bind) | `agent_data:` (named volume) | Agent data survives redeployments |
| No exposed ports | `8000:8000` | API access for Coolify health checks |
| `DOCKER_NETWORK: clawith_network` | `DOCKER_NETWORK: clawith_network` | Same |
| No custom networks | `clawith_network` + `coolify` (external) | Traefik proxy access |
| `POSTGRES_PASSWORD: clawith` (hardcoded) | `${POSTGRES_PASSWORD:-clawith}` | Security: env variable |
| `DATABASE_URL: ...clawith@...` (hardcoded password) | `...${POSTGRES_PASSWORD:-clawith}@...` | Same |

#### Added env vars (Moiria-specific)

| Variable | Usage |
|----------|-------|
| `INFISICAL_HOST_URL` | Infisical MCP integration |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` | Infisical auth |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` | Infisical auth |
| `INFISICAL_PROJECT_ID` | Infisical project scope |
| `AGENTMAIL_API_KEY` | AgentMail API access |

### 2. Supergateway (NEW — not in upstream)

MCP bridge service for Infisical:
- Image: `node:20-alpine`
- Command: `supergateway --stdio 'npx -y @infisical/mcp' --port 8000`
- Health check on `/health`
- Network: `clawith_network`

### 3. Frontend

| Upstream (dev) | Moiria (prod) | Reason |
|----------------|---------------|--------|
| `VITE_API_URL: http://localhost:8000` | `VITE_API_URL: http://backend:8000` | Docker internal networking |
| No supergateway dependency | `depends_on: [backend, supergateway]` | Startup ordering |
| No labels | Traefik labels (see below) | HTTPS routing |
| No custom networks | `clawith_network` + `coolify` | Traefik access |

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

## Merge strategy for future releases

When a new upstream version is released (e.g. v1.8.2):

```bash
# 1. Fetch upstream
git fetch upstream

# 2. Check what changed in docker-compose.yml
git diff v1.8.1..upstream/v1.8.2 -- docker-compose.yml

# 3. If upstream changed docker-compose:
#    a. Save the new reference
#    git show upstream/v1.8.2:docker-compose.yml > docker-compose.upstream-ref.yml
#    b. Manually apply our customizations to docker-compose.yml
#    c. Test in staging
```

**Why not a `-f docker-compose.override.yml` overlay?**  
Because our changes replace entire sections (backend volumes, networks, Traefik labels, supergateway service) — not just additions. An overlay cannot *remove* sections from the base file.
