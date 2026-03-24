# Infisical Vaults

**Dernière mise à jour:** 2026-03-24  
**Maintenant:** Clawith Maintainer  
**Project:** Les Moires / Clawith

---

## 🏗️ Vault Structure

```
/clawith/
├── admin/              # Admin credentials (GitHub, Coolify, etc.)
├── mcp/                # MCP server credentials
│   ├── hetzner/        # Hetzner Cloud API
│   ├── infisical/      # Infisical MCP config
│   └── agentmail/      # AgentMail credentials
├── agents/             # Agent-specific secrets
│   ├── clawith-maintainer/
│   ├── devops-moiria/
│   └── clawith-repair/
└── gateway/            # Gateway API keys
```

---

## 🔐 /clawith/admin

**Access:** Clawith Maintainer only (Full)

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `GITHUB_TOKEN` | Token GitHub (lesmoires org) | Upstream sync, PR creation |
| `COOLIFY_TOKEN` | Token Coolify API | Déploiements, config services |
| `HETZNER_API_KEY` | API key Hetzner Cloud | Infrastructure management |
| `RAILWAY_TOKEN` | Token Railway API | Déploiements Railway (legacy) |
| `CLICKUP_API_KEY` | Token ClickUp API | Task management |
| `CLICKUP_TEAM_ID` | Team ID ClickUp | Task management |

### Access Control
- **Full Access:** Clawith Maintainer
- **Read Access:** Aucun (admin only)
- **Rotation:** Trimestrielle

---

## 🔐 /clawith/mcp

**Access:** Clawith Maintainer (Full), DevOps Moiria (Read)

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `LITELLM_MCP_KEY` | Clé API LiteLLM MCP Gateway | Auth MCP servers |
| `SUPERGATEWAY_URL` | URL Supergateway | Infisical MCP connection |

### Access Control
- **Full Access:** Clawith Maintainer
- **Read Access:** DevOps Moiria
- **Rotation:** Semestrielle

---

## 🔐 /clawith/mcp/hetzner

**Access:** DevOps Moiria, Clawith Maintainer

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `HETZNER_API_KEY` | API key Hetzner Cloud | `sk-drT2rTT5MKPeB8jNkTm41w` |

### MCP Server Config
- **Server Name:** `hetzner_cloud`
- **MCP URL:** `https://litellm.moiria.com/mcp`
- **Tools:** 19 outils Hetzner
- **Assigned Agents:** DevOps Moiria, Clawith Maintainer

### Access Control
- **Full Access:** DevOps Moiria, Clawith Maintainer
- **Rotation:** Semestrielle ou en cas de compromission

---

## 🔐 /clawith/mcp/infisical

**Access:** All agents (Read)

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `INFISICAL_HOST_URL` | URL Infisical API | `https://app.infisical.com` |
| `CLIENT_ID` | Client ID Infisical MCP | Auth MCP |
| `CLIENT_SECRET` | Client Secret Infisical MCP | Auth MCP |
| `PROJECT_ID` | Project ID Infisical | Scope des secrets |

### MCP Server Config
- **Server Name:** `infisical`
- **MCP URL:** `http://supergateway:8000/sse`
- **Tools:** 3 (get-secret, list-secrets, create-secret)
- **Assigned Agents:** Tous les agents

### Access Control
- **Read Access:** All agents
- **Rotation:** Annuelle

---

## 🔐 /clawith/mcp/agentmail

**Access:** Clawith Maintainer, DevOps Moiria

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `AGENTMAIL_API_KEY` | API key AgentMail | Email operations |
| `AGENTMAIL_API_URL` | URL AgentMail API | Email operations |

### Tools
- `agentmail_list_inboxes`
- `agentmail_send_email`
- `agentmail_list_messages`
- `agentmail_read_message`

### Access Control
- **Full Access:** Clawith Maintainer, DevOps Moiria
- **Rotation:** Trimestrielle

---

## 🔐 /clawith/gateway

**Access:** Clawith Repair, Clawith Maintainer

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `GATEWAY_API_KEY` | API key Gateway Clawith | `oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs` |
| `GATEWAY_BASE_URL` | URL de base Gateway | `https://agents.moiria.com/api/gateway/` |

### Endpoints
- `GET /poll` — Poller l'inbox
- `POST /send-message` — Envoyer un message
- `POST /report` — Reporter un message traité

### Access Control
- **Full Access:** Clawith Repair, Clawith Maintainer
- **Rotation:** En cas de compromission

---

## 🔐 /clawith/agents/clawith-maintainer

**Access:** Clawith Maintainer only

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `AGENT_API_KEY` | API key de l'agent | Auth Gateway |
| `AGENT_ID` | UUID de l'agent | Identification |

### Access Control
- **Full Access:** Clawith Maintainer
- **Rotation:** À la création de l'agent

---

## 🔐 /clawith/agents/devops-moiria

**Access:** DevOps Moiria, Clawith Maintainer

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `AGENT_API_KEY` | API key de l'agent | Auth Gateway |
| `AGENT_ID` | UUID de l'agent | Identification |

### Access Control
- **Full Access:** DevOps Moiria
- **Read Access:** Clawith Maintainer
- **Rotation:** À la création de l'agent

---

## 🔐 /clawith/agents/clawith-repair

**Access:** Clawith Repair, Clawith Maintainer

### Secrets
| Secret Key | Description | Usage |
|------------|-------------|-------|
| `AGENT_API_KEY` | API key de l'agent | Auth Gateway |
| `AGENT_ID` | UUID de l'agent | Identification |

### Access Control
- **Full Access:** Clawith Repair
- **Read Access:** Clawith Maintainer
- **Rotation:** À la création de l'agent

---

## 📊 Vault Access Matrix

| Vault | Clawith Maintainer | DevOps Moiria | Clawith Repair | Conver Thesis |
|-------|-------------------|---------------|----------------|---------------|
| `/clawith/admin` | ✅ Full | ❌ None | ❌ None | ❌ None |
| `/clawith/mcp` | ✅ Full | 👁️ Read | ❌ None | ❌ None |
| `/clawith/mcp/hetzner` | ✅ Full | ✅ Full | ❌ None | ❌ None |
| `/clawith/mcp/infisical` | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| `/clawith/mcp/agentmail` | ✅ Full | ✅ Full | ❌ None | ❌ None |
| `/clawith/gateway` | ✅ Full | ❌ None | ✅ Full | ❌ None |
| `/clawith/agents/*` | 👁️ Read | 👁️ Read (own) | 👁️ Read (own) | 👁️ Read (own) |

---

## 🔄 Secret Rotation Policy

| Vault | Rotation Frequency | Trigger Events |
|-------|-------------------|----------------|
| `/clawith/admin` | Trimestrielle | Départ collaborateur, compromission |
| `/clawith/mcp` | Semestrielle | Changement provider MCP |
| `/clawith/mcp/hetzner` | Semestrielle | Compromission, expiry |
| `/clawith/mcp/infisical` | Annuelle | Expiry tokens |
| `/clawith/gateway` | Event-driven | Compromission only |
| `/clawith/agents/*` | On creation | Agent recreation |

---

## 🚨 Security Best Practices

1. **JAMAIS** de tokens dans les URLs ou logs
2. **TOUJOURS** utiliser Infisical pour les secrets
3. **TOUJOURS** utiliser SSH ou credential helper pour Git
4. **JAMAIS** committer de `.env` avec des secrets
5. **TOUJOURS** rotation après un départ d'équipe
6. **TOUJOURS** auditer les accès trimestriellement

---

## 📝 Audit Log

| Date | Action | Performed By | Notes |
|------|--------|--------------|-------|
| 2026-03-24 | Création structure vaults | Claw (subagent) | Initial setup |
| 2026-03-24 | Documentation accès | Claw (subagent) | Registry complet |

---

## 📞 Contacts

- **Admin Vault Owner:** Clawith Maintainer
- **Security Contact:** Guillaume (guillaume.bleau@upentreprise.com)

---

*Géré par: Clawith Maintainer*
