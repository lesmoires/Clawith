# Hetzner MCP Tools — Full Reference (104 tools)

All tools use the MCP server `hetzner_cloud` on `https://litellm.moiria.com`.
MCP tool name prefix: `hetzner_cloud-hetzner_`
DB tool name: `hetzner_*`

## Servers (16)

| Tool | Description |
|------|-------------|
| `hetzner_list_servers` | List all servers |
| `hetzner_get_server` | Get server details by ID |
| `hetzner_create_server` | Create new server (requires: name, server_type, image, location) |
| `hetzner_delete_server` | ⚠️ Permanently delete server |
| `hetzner_update_server` | Update server name or labels |
| `hetzner_power_on` | Power on stopped server |
| `hetzner_power_off` | ⚠️ Force power off (pull the plug) |
| `hetzner_reboot` | ACPI soft reboot |
| `hetzner_shutdown` | ACPI graceful shutdown |
| `hetzner_reset` | Hard reset (reset button) |
| `hetzner_rebuild_server` | ⚠️ Rebuild from image (wipes data) |
| `hetzner_resize_server` | Change server type (stops, migrates, starts) |
| `hetzner_enable_rescue` | Enable rescue mode (requires reboot) |
| `hetzner_disable_rescue` | Disable rescue mode |
| `hetzner_list_server_actions` | List actions for a server |
| `hetzner_get_server_metrics` | Get CPU/disk/network metrics |

## Server Types & Discovery (12)

| Tool | Description |
|------|-------------|
| `hetzner_list_locations` | List all datacenters |
| `hetzner_get_location` | Get location details |
| `hetzner_list_server_types` | List server types with specs/pricing |
| `hetzner_get_server_type` | Get server type details |
| `hetzner_list_datacenters` | List datacenters with supported types |
| `hetzner_get_datacenter` | Get datacenter details |
| `hetzner_list_images` | List images (system, snapshot, backup, app) |
| `hetzner_get_image` | Get image details |
| `hetzner_list_isos` | List ISO images |
| `hetzner_get_iso` | Get ISO details |
| `hetzner_attach_iso` | Attach ISO to server |
| `hetzner_detach_iso` | Detach ISO from server |

## Networks (11)

| Tool | Description |
|------|-------------|
| `hetzner_list_networks` | List all networks |
| `hetzner_get_network` | Get network details |
| `hetzner_create_network` | Create network with IP range |
| `hetzner_update_network` | Update network name/labels |
| `hetzner_delete_network` | ⚠️ Delete network (also deletes subnets/routes) |
| `hetzner_add_subnet` | Add subnet to network |
| `hetzner_delete_subnet` | Remove subnet from network |
| `hetzner_add_route` | Add route to network |
| `hetzner_delete_route` | Remove route from network |

## IPs (12)

| Tool | Description |
|------|-------------|
| `hetzner_list_primary_ips` | List all primary IPs |
| `hetzner_get_primary_ip` | Get primary IP details |
| `hetzner_create_primary_ip` | Create new primary IP |
| `hetzner_update_primary_ip` | Update primary IP name/labels/auto_delete |
| `hetzner_delete_primary_ip` | ⚠️ Delete primary IP (must unassign first) |
| `hetzner_assign_primary_ip` | Assign primary IP to server |
| `hetzner_unassign_primary_ip` | Unassign primary IP |
| `hetzner_change_primary_ip_rdns` | Change reverse DNS for primary IP |
| `hetzner_list_floating_ips` | List all floating IPs |
| `hetzner_get_floating_ip` | Get floating IP details |
| `hetzner_create_floating_ip` | Create new floating IP |
| `hetzner_update_floating_ip` | Update floating IP name/description/labels |
| `hetzner_delete_floating_ip` | ⚠️ Delete floating IP (must unassign first) |
| `hetzner_assign_floating_ip` | Assign floating IP to server |
| `hetzner_unassign_floating_ip` | Unassign floating IP |
| `hetzner_change_floating_ip_rdns` | Change reverse DNS for floating IP |

## Firewalls (7)

| Tool | Description |
|------|-------------|
| `hetzner_list_firewalls` | List all firewalls |
| `hetzner_get_firewall` | Get firewall details |
| `hetzner_create_firewall` | Create firewall with rules |
| `hetzner_update_firewall` | Update firewall name/labels |
| `hetzner_delete_firewall` | ⚠️ Delete firewall (remove from resources first) |
| `hetzner_apply_firewall` | Apply firewall to servers/label selectors |
| `hetzner_remove_firewall` | Remove firewall from servers/label selectors |
| `hetzner_set_firewall_rules` | Replace all firewall rules |

## Volumes (8)

| Tool | Description |
|------|-------------|
| `hetzner_list_volumes` | List all volumes |
| `hetzner_get_volume` | Get volume details |
| `hetzner_create_volume` | Create new volume |
| `hetzner_update_volume` | Update volume name/labels |
| `hetzner_delete_volume` | ⚠️ Delete volume (must detach first) |
| `hetzner_attach_volume` | Attach volume to server |
| `hetzner_detach_volume` | Detach volume from server |
| `hetzner_resize_volume` | Increase volume size (only larger) |

## Load Balancers (14)

| Tool | Description |
|------|-------------|
| `hetzner_list_load_balancers` | List all load balancers |
| `hetzner_get_load_balancer` | Get load balancer details |
| `hetzner_create_load_balancer` | Create new load balancer |
| `hetzner_update_load_balancer` | Update load balancer name/labels |
| `hetzner_delete_load_balancer` | ⚠️ Delete load balancer |
| `hetzner_change_lb_type` | Change load balancer type/plan |
| `hetzner_change_lb_algorithm` | Change balancing algorithm |
| `hetzner_get_lb_metrics` | Get load balancer metrics |
| `hetzner_attach_lb_to_network` | Attach load balancer to network |
| `hetzner_detach_lb_from_network` | Detach load balancer from network |
| `hetzner_add_lb_service` | Add service (port listener) to load balancer |
| `hetzner_update_lb_service` | Update load balancer service |
| `hetzner_delete_lb_service` | Remove service from load balancer |
| `hetzner_add_lb_target` | Add target to load balancer |
| `hetzner_remove_lb_target` | Remove target from load balancer |
| `hetzner_list_lb_types` | List load balancer types |

## SSH Keys (5)

| Tool | Description |
|------|-------------|
| `hetzner_list_ssh_keys` | List all SSH keys |
| `hetzner_get_ssh_key` | Get SSH key details |
| `hetzner_create_ssh_key` | Add new SSH public key |
| `hetzner_update_ssh_key` | Update SSH key name/labels |
| `hetzner_delete_ssh_key` | ⚠️ Delete SSH key permanently |

## Certificates (6)

| Tool | Description |
|------|-------------|
| `hetzner_list_certificates` | List all certificates |
| `hetzner_get_certificate` | Get certificate details |
| `hetzner_create_certificate` | Create uploaded or managed certificate |
| `hetzner_update_certificate` | Update certificate name/labels |
| `hetzner_delete_certificate` | Delete certificate (must not be in use) |
| `hetzner_retry_certificate` | Retry failed certificate issuance/renewal |

## Images (4)

| Tool | Description |
|------|-------------|
| `hetzner_create_image` | Create snapshot from server |
| `hetzner_update_image` | Update image description/type/labels |
| `hetzner_delete_image` | ⚠️ Delete snapshot/backup image |

## Placement Groups (4)

| Tool | Description |
|------|-------------|
| `hetzner_list_placement_groups` | List all placement groups |
| `hetzner_get_placement_group` | Get placement group details |
| `hetzner_create_placement_group` | Create new placement group |
| `hetzner_update_placement_group` | Update placement group name/labels |
| `hetzner_delete_placement_group` | Delete placement group (remove servers first) |

## Common Parameters

### Create Server
```json
{
  "name": "my-server",
  "server_type": "cx22",
  "image": "ubuntu-24.04",
  "location": "fsn1",
  "ssh_keys": [12345],
  "labels": {"env": "prod"},
  "start_after_create": true
}
```

### Create Firewall
```json
{
  "name": "web-firewall",
  "rules": [
    {
      "direction": "in",
      "protocol": "tcp",
      "port": "80",
      "source_ips": ["0.0.0.0/0", "::/0"]
    }
  ],
  "apply_to": [{"type": "server", "server": 123456}]
}
```

### Create Volume
```json
{
  "name": "data-volume",
  "size": 100,
  "location": "fsn1",
  "format": "ext4"
}
```
