# MCP PDF Generator — Setup Guide

## Deployment on Coolify

### 1. Push files to moiria-claw

```bash
# Create directory
mkdir -p /opt/mcp-pdf-generator/src/tools /opt/mcp-pdf-generator/src/server

# Copy files
scp -r Dockerfile docker-compose.yaml package.json src/ root@46.225.220.208:/opt/mcp-pdf-generator/
```

### 2. Build and run

```bash
ssh root@46.225.220.208
cd /opt/mcp-pdf-generator
docker compose build
docker compose up -d
```

### 3. Verify

```bash
docker ps --filter name=mcp-pdf-generator
docker logs mcp-pdf-generator
docker exec mcp-pdf-generator node -e "console.log('ok')"
```

### 4. Register in LiteLLM

Add to `litellm-config.yaml`:

```yaml
mcp_servers:
  mcp_pdf_generator:
    transport: stdio
    command: docker
    args: ["exec", "-i", "mcp-pdf-generator", "node", "src/server/server.js"]
    env: {}
    description: "Generate PDFs from HTML via Puppeteer"
```

Then restart LiteLLM:
```bash
docker restart <litellm-container-name>
```

### 5. Seed in Clawith DB

```bash
# Seed tools via Coolify SSH
docker exec -i <clawith-backend> python3 -c "..."
```

Or use the clawith-skills-and-tools-seeder skill.
