---
name: hetzner
description: Manage Hetzner Cloud infrastructure — servers, networks, firewalls, volumes, load balancers, floating IPs, SSH keys, and certificates via the Hetzner MCP server. Use when: creating/deleting servers, resizing, rebooting, power cycling, managing firewalls/rules, creating/managing networks/subnets/routes, managing floating IPs and primary IPs, creating/attaching/detaching volumes, managing load balancers (create/update/delete/services/targets), managing SSH keys, managing certificates, listing locations/datacenters/server types/images, or any Hetzner Cloud API operation. Triggers on: "hetzner", "hcloud", "cloud server", "create server", "firewall", "floating IP", "load balancer", "Hetzner Cloud".
---

# Hetzner Cloud

Manage Hetzner Cloud infrastructure via the MCP server `hetzner_cloud` on `https://litellm.moiria.com`.

## Quick Access

**Direct MCP endpoint** (works immediately):
```bash
# List servers
curl -s -X POST "https://litellm.moiria.com/hetzner_cloud/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hetzner_cloud-hetzner_list_servers","arguments":{}}}'
```

**Tool name prefix**: All Hetzner MCP tools are prefixed with `hetzner_cloud-hetzner_`.
- DB tool name: `hetzner_list_servers`
- MCP tool name: `hetzner_cloud-hetzner_list_servers`

## Available Tools (104 total)

See [references/tools.md](references/tools.md) for the full list grouped by domain.

### Core Operations

| Operation | Tool | Notes |
|-----------|------|-------|
| List servers | `hetzner_list_servers` | All servers, filterable |
| Get server | `hetzner_get_server` | By ID |
| Create server | `hetzner_create_server` | Requires name, server_type, image, location |
| Delete server | `hetzner_delete_server` | ⚠️ Destructive |
| Power on/off | `hetzner_power_on` / `hetzner_power_off` | ⚠️ Destructive |
| Reboot | `hetzner_reboot` | ⚠️ Destructive |
| Shutdown | `hetzner_shutdown` | ⚠️ Destructive |
| Resize | `hetzner_resize_server` | Stop → migrate → start |
| Rebuild | `hetzner_rebuild_server` | ⚠️ Wipes data |

### Discovery

| Operation | Tool |
|-----------|------|
| Locations | `hetzner_list_locations` |
| Server types | `hetzner_list_server_types` |
| Datacenters | `hetzner_list_datacenters` |
| Images | `hetzner_list_images` |

## Security Boundary

**Destructive operations requiring confirmation** (power off, shutdown, reboot, delete server, delete firewall, delete network):
- Ask the user before executing
- Do not auto-approve destructive actions on production servers

## Server Context

Known servers (Hetzner project):

| Server | ID | IP | Purpose |
|--------|----|----|---------|
| moiria-claw | 122167220 | 46.225.220.208 | DevOps host, Clawith |
| moiria-coolify | 122167221 | 116.203.234.253 | Coolify PaaS |

## SSH Access

For CLI operations:
```bash
# Via hcloud CLI (if installed)
hcloud server list
hcloud firewall create --name test --label type=test
```

SSH key for Hetzner: env `HETZNER_SSH_KEY_BASE64` → decode to file for SSH access.
