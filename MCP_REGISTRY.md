# MCP Registry

**Dernière mise à jour:** 2026-03-24  
**Maintenant:** Clawith Maintainer

---

## 🌐 LiteLLM MCP Gateway

**URL:** `https://litellm.moiria.com/mcp`  
**Auth:** `Authorization: Bearer <key>`  
**Config File:** `/data/coolify/services/wg0k80o88gcswco0ksgkkggc/litellm-config.yaml`  
**Status:** ✅ Production

---

### hetzner_cloud

**MCP Server:** `hetzner_cloud`  
**URL:** `https://litellm.moiria.com/mcp`  
**Status:** ✅ Production

#### Configuration
- **API Key:** `sk-drT2rTT5MKPeB8jNkTm41w` (dans Infisical: `/clawith/mcp/hetzner`)
- **Tools:** 19 outils Hetzner enregistrés
- **Assigned Agents:** DevOps Moiria, Clawith Maintainer

#### Tools Disponibles
1. `hetzner_list_servers` — Lister les serveurs
2. `hetzner_create_server` — Créer un serveur
3. `hetzner_delete_server` — Supprimer un serveur
4. `hetzner_list_networks` — Lister les réseaux
5. `hetzner_create_network` — Créer un réseau
6. `hetzner_list_firewalls` — Lister les firewalls
7. `hetzner_create_firewall` — Créer un firewall
8. `hetzner_list_ssh_keys` — Lister les clés SSH
9. `hetzner_create_ssh_key` — Créer une clé SSH
10. `hetzner_list_volumes` — Lister les volumes
11. `hetzner_create_volume` — Créer un volume
12. `hetzner_list_snapshots` — Lister les snapshots
13. `hetzner_create_snapshot` — Créer un snapshot
14. `hetzner_list_load_balancers` — Lister les load balancers
15. `hetzner_create_load_balancer` — Créer un load balancer
16. `hetzner_list_certificates` — Lister les certificats
17. `hetzner_create_certificate` — Créer un certificat
18. `hetzner_list_domains` — Lister les domaines
19. `hetzner_create_domain` — Créer un domaine

#### Usage Example
```bash
curl -X POST https://litellm.moiria.com/mcp \
  -H "Authorization: Bearer sk-drT2rTT5MKPeB8jNkTm41w" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "hetzner_list_servers",
    "params": {}
  }'
```

---

### infisical (via Supergateway)

**MCP Server:** `infisical`  
**URL:** `http://supergateway:8000/sse`  
**Status:** ✅ Production

#### Configuration
- **INFISICAL_HOST_URL:** `https://app.infisical.com` (dans Infisical: `/clawith/mcp/infisical`)
- **CLIENT_ID:** `<client_id>` (dans Infisical: `/clawith/mcp/infisical`)
- **CLIENT_SECRET:** `<client_secret>` (dans Infisical: `/clawith/mcp/infisical`)
- **PROJECT_ID:** `<project_id>` (dans Infisical: `/clawith/mcp/infisical`)
- **Tools:** 3 (get-secret, list-secrets, create-secret)
- **Assigned Agents:** Tous les agents

#### Tools Disponibles
1. `get-secret` — Récupérer un secret
2. `list-secrets` — Lister les secrets
3. `create-secret` — Créer un secret

#### Usage Example
```bash
# Via Supergateway SSE
# Configuré dans docker-compose.yml du projet Clawith
```

---

## 📊 MCP Access Matrix

| Agent | hetzner_cloud | infisical |
|-------|---------------|-----------|
| **Clawith Maintainer** | ✅ Admin | ✅ Admin |
| **DevOps Moiria** | ✅ Full | ✅ Full |
| **Clawith Repair** | ❌ None | ✅ Full |
| **Conver Thesis** | ❌ None | ❌ None |

---

## 🔐 Infisical Vault Access

| Vault | Access Level | Assigned Agents |
|-------|--------------|-----------------|
| `/clawith/mcp/hetzner` | Read | DevOps Moiria, Clawith Maintainer |
| `/clawith/mcp/infisical` | Read | All agents |
| `/clawith/admin` | Full | Clawith Maintainer only |
| `/clawith/mcp` | Full | Clawith Maintainer, Read: DevOps Moiria |
| `/clawith/gateway` | Read | Clawith Repair, Clawith Maintainer |

---

## 🔧 LiteLLM MCP Gateway Config

**File:** `/data/coolify/services/wg0k80o88gcswco0ksgkkggc/litellm-config.yaml`

### Configuration Template
```yaml
model_list:
  - model_name: hetzner_cloud
    litellm_params:
      model: mcp/hetzner_cloud
      api_base: https://litellm.moiria.com/mcp
      api_key: sk-drT2rTT5MKPeB8jNkTm41w

  - model_name: infisical
    litellm_params:
      model: mcp/infisical
      api_base: http://supergateway:8000/sse
```

### Health Check
```bash
curl -X GET https://litellm.moiria.com/health \
  -H "Authorization: Bearer <key>"
```

---

## 📝 MCP Request Workflow

1. **Recevoir demande** de nouveau MCP server
2. **Valider compatibilité** avec LiteLLM
3. **Ajouter credentials** dans Infisical (`/clawith/mcp/<name>`)
4. **Configurer LiteLLM** MCP Gateway
5. **Tester** la connection
6. **Assigner aux agents** selon leurs besoins
7. **Documenter** dans ce fichier
8. **Monitorer** la santé des connections

---

## 🚨 Troubleshooting

### MCP Connection Failed
1. Vérifier credentials dans Infisical
2. Tester URL MCP directement avec curl
3. Vérifier logs LiteLLM (`docker logs litellm-proxy`)
4. Vérifier firewall/network rules

### Tools Not Available
1. Vérifier que MCP server est enregistré dans LiteLLM
2. Vérifier que l'agent a accès au MCP server
3. Redémarrer LiteLLM proxy si nécessaire

---

## 📞 Contacts

- **Clawith Maintainer:** Admin MCP Gateway
- **DevOps Moiria:** Hetzner MCP operations
- **Guillaume:** guillaume.bleau@upentreprise.com

---

*Géré par: Clawith Maintainer*
