# Agents Registry

**Dernière mise à jour:** 2026-03-24  
**Maintenant:** Clawith Maintainer

---

## 🤖 Clawith Maintainer

- **Created:** 2026-03-24
- **Role:** Infrastructure & Maintenance Guardian
- **Status:** ⏳ En création
- **Agent Type:** openclaw
- **Creator:** Guillaume (via subagent)

### Tools
- **Core Tools:** All (admin)
- **Custom Tools:** All (admin)
- **MCP Tools:** All (admin)

### Infisical Vaults
- `/clawith/admin` — Full access
- `/clawith/mcp` — Full access
- `/clawith/agents/*` — Read access

### MCP Servers
- **All MCP Servers** — Admin access
- hetzner_cloud (via LiteLLM)
- infisical (via Supergateway)

### Responsibilities
1. **Upstream Monitoring** — Surveiller `dataelement/Clawith` pour nouvelles versions
2. **Fork Maintenance** — Gérer les branches, coordonner les merges upstream
3. **Tools & Skills Distribution** — Maintenir le catalogue central de tools
4. **Secret Management** — Gérer les accès Infisical et rotation des secrets
5. **MCP Gateway Management** — Configurer les MCP servers dans LiteLLM

---

## 🛠️ DevOps Moiria

- **Created:** 2026-03-XX
- **Role:** DevOps & Infrastructure
- **Status:** ✅ Actif

### Tools
- **Core Tools:** Core
- **Custom Tools:** Hetzner, Infisical
- **MCP Tools:** Hetzner, Infisical

### Infisical Vaults
- `/clawith/mcp/hetzner` — Read access
- `/clawith/mcp/infisical` — Read access

### MCP Servers
- `hetzner_cloud` (via LiteLLM)
- `infisical` (via Supergateway)

---

## 🔧 Clawith Repair

- **Created:** 2026-03-XX
- **Role:** Repair & Sync (OpenClaw bridge)
- **Status:** ✅ Actif

### Tools
- **Core Tools:** Core
- **Custom Tools:** Gateway
- **MCP Tools:** Infisical

### Infisical Vaults
- `/clawith/gateway` — Read access

### MCP Servers
- `infisical` (via Supergateway)

---

## 📋 Access Matrix Summary

| Agent | Core Tools | Custom Tools | MCP Tools | Infisical Vaults | MCP Servers |
|-------|------------|--------------|-----------|------------------|-------------|
| **Clawith Maintainer** | All | All | All | /clawith/admin, /clawith/mcp | All (admin) |
| **DevOps Moiria** | Core | Hetzner, Infisical | Hetzner, Infisical | /clawith/mcp/hetzner, /clawith/mcp/infisical | hetzner_cloud, infisical |
| **Clawith Repair** | Core | Gateway | Infisical | /clawith/gateway | infisical |

---

## 📝 Notes

- Tous les agents doivent être créés via l'UI Clawith ou l'API Admin
- Les accès Infisical doivent être configurés manuellement dans Infisical
- Les accès MCP doivent être configurés dans LiteLLM MCP Gateway
- Ce fichier doit être mis à jour à chaque nouvel agent créé

---

*Géré par: Clawith Maintainer*
