# Tools Registry

**Dernière mise à jour:** 2026-03-24  
**Maintenant:** Clawith Maintainer

---

## 🔧 Core Tools (Tous les agents)

Ces tools sont disponibles pour tous les agents Clawith:

| Tool | Description | Usage |
|------|-------------|-------|
| `list_files` | Lister les fichiers d'un dossier | Exploration, navigation |
| `read_file` | Lire le contenu d'un fichier | Lecture de code, config, docs |
| `write_file` | Écrire dans un fichier | Création, modification |
| `delete_file` | Supprimer un fichier | Cleanup, removal |
| `edit` | Modifier un fichier (search/replace) | Corrections précises |
| `exec` | Exécuter des commandes shell | Scripts, déploiements |
| `web_search` | Recherche web (Brave API) | Recherche d'infos |
| `web_fetch` | Fetch contenu URL | Documentation, articles |
| `browser` | Contrôle navigateur | UI automation, tests |
| `message` | Envoyer messages (Discord, etc.) | Communication |
| `tts` | Text-to-speech | Réponses vocales |

---

## 🎯 Custom Tools

### AgentMail Tools

**Fichier:** `backend/app/tools/agentmail_tools.py` (373 lignes)  
**Status:** ✅ Production

| Tool | Description | Assigned Agents |
|------|-------------|-----------------|
| `agentmail_list_inboxes` | Lister les boîtes mail | Clawith Maintainer, DevOps Moiria |
| `agentmail_send_email` | Envoyer un email | Clawith Maintainer, DevOps Moiria |
| `agentmail_list_messages` | Lister les messages | Clawith Maintainer, DevOps Moiria |
| `agentmail_read_message` | Lire un message | Clawith Maintainer, DevOps Moiria |

**Infisical Vault:** `/clawith/mcp/agentmail`

---

### Infisical Tools

**Fichiers:** 
- `backend/app/skills/infisical_secrets.py` (764 lignes)
- `backend/app/tools/infisical_secret.py`

**Status:** ✅ Production

| Tool | Description | Assigned Agents |
|------|-------------|-----------------|
| `get_infisical_secret` | Récupérer un secret | All agents |
| `list_infisical_secrets` | Lister les secrets | All agents |
| `create_infisical_secret` | Créer un secret | Clawith Maintainer |
| `agentmail_list_inboxes` (Infisical MCP) | Via MCP | All agents |

**Infisical Vault:** `/clawith/mcp/infisical`  
**MCP URL:** `http://supergateway:8000/sse`

---

### Gateway Tools

**Fichier:** `backend/app/api/gateway.py` (767 lignes)  
**Status:** ✅ Production (Clawith Repair sync)

| Tool | Description | Assigned Agents |
|------|-------------|-----------------|
| `send_message_to_agent` | Envoyer message à un agent | Clawith Repair, Clawith Maintainer |
| `poll_gateway_messages` | Poller l'inbox | All OpenClaw agents |
| `report_message_result` | Reporter un message traité | All OpenClaw agents |

**API Key:** `oc-YTNU2nbBSBWXdROK-U_hOBjgcq-8xPWpSI82iY9MEQs`  
**Base URL:** `https://agents.moiria.com/api/gateway/`

---

### MCP Tools (via LiteLLM)

**Config File:** `/data/coolify/services/wg0k80o88gcswco0ksgkkggc/litellm-config.yaml`  
**Status:** ✅ Production

#### Hetzner Cloud MCP

**MCP Server:** `hetzner_cloud`  
**URL:** `https://litellm.moiria.com/mcp`  
**Tools:** 19 outils enregistrés

| Tool | Description | Assigned Agents |
|------|-------------|-----------------|
| `hetzner_list_servers` | Lister les serveurs | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_server` | Créer un serveur | DevOps Moiria, Clawith Maintainer |
| `hetzner_delete_server` | Supprimer un serveur | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_networks` | Lister les réseaux | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_network` | Créer un réseau | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_firewalls` | Lister les firewalls | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_firewall` | Créer un firewall | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_ssh_keys` | Lister les clés SSH | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_ssh_key` | Créer une clé SSH | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_volumes` | Lister les volumes | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_volume` | Créer un volume | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_snapshots` | Lister les snapshots | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_snapshot` | Créer un snapshot | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_load_balancers` | Lister les load balancers | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_load_balancer` | Créer un load balancer | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_certificates` | Lister les certificats | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_certificate` | Créer un certificat | DevOps Moiria, Clawith Maintainer |
| `hetzner_list_domains` | Lister les domaines | DevOps Moiria, Clawith Maintainer |
| `hetzner_create_domain` | Créer un domaine | DevOps Moiria, Clawith Maintainer |

**Infisical Vault:** `/clawith/mcp/hetzner`  
**API Key:** `sk-drT2rTT5MKPeB8jNkTm41w` (dans Infisical)

---

## 📊 Tools Distribution Matrix

| Agent | Core Tools | Custom Tools | MCP Tools |
|-------|------------|--------------|-----------|
| **Clawith Maintainer** | ✅ All | ✅ All | ✅ All |
| **DevOps Moiria** | ✅ Core | ✅ Hetzner, Infisical | ✅ Hetzner, Infisical |
| **Clawith Repair** | ✅ Core | ✅ Gateway | ✅ Infisical |
| **Conver Thesis** | ✅ Core | ❌ None | ❌ None |

---

## 🔄 Tool Request Workflow

1. **Recevoir demande** de nouveau tool
2. **Valider compatibilité** avec l'architecture
3. **Ajouter au catalogue central** (ce fichier)
4. **Assigner aux agents** qui en ont besoin
5. **Documenter** dans AGENTS_REGISTRY.md
6. **Tester** le tool avec l'agent
7. **Mettre à jour** ce fichier

---

## 📝 Notes

- Les tools custom doivent être validés par Clawith Maintainer avant distribution
- Les tools MCP nécessitent une configuration dans LiteLLM MCP Gateway
- Les secrets pour les tools doivent être stockés dans Infisical
- Ce fichier doit être mis à jour à chaque nouveau tool ajouté

---

*Géré par: Clawith Maintainer*
