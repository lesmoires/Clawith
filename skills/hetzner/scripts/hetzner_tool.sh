#!/bin/bash
# Call a Hetzner Cloud MCP tool via LiteLLM
# Usage: ./hetzner_tool.sh <tool_name> [json_args_file_or_string]
# Examples:
#   ./hetzner_tool.sh hetzner_list_servers
#   ./hetzner_tool.sh hetzner_create_server '{"name":"test","server_type":"cx22","image":"ubuntu-24.04","location":"fsn1"}'

LITELLM_URL="https://litellm.moiria.com"
API_KEY="${LITELLM_API_KEY:?Set env LITELLM_API_KEY}"
TOOL_NAME="${1:?Usage: $0 <tool_name> '[json_args]'}"
ARGS="${2:-"{}"}"

MCP_TOOL="hetzner_cloud-${TOOL_NAME}"

RAW=$(curl -s -X POST "${LITELLM_URL}/hetzner_cloud/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"${MCP_TOOL}\",\"arguments\":${ARGS}}}")

# Parse SSE response
echo "$RAW" | while IFS= read -r line; do
  if [[ "$line" == data:* ]]; then
    DATA="${line#data: }"
    echo "$DATA" | python3 -c "
import json, sys
text = sys.stdin.read()
try:
    d = json.loads(text)
except:
    print(text)
    sys.exit(0)
if d.get('error'):
    print(f'ERROR: {json.dumps(d[\"error\"], indent=2)}')
    sys.exit(1)
content = d.get('result', {}).get('content', [])
for c in content:
    t = c.get('text', '')
    try:
        parsed = json.loads(t)
        print(json.dumps(parsed, indent=2))
    except:
        print(t)
"
  fi
done
