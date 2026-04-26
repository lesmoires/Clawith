#!/bin/bash
sleep 5
cd /data/coolify/applications/twcgssk04ckw4kgw0gcwcw48
if ! grep -A 5 '^  postgres:' docker-compose.yaml | grep -q 'networks:'; then
    sed -i '/^  postgres:/,/^  redis:/{/retries: 5$/a\    networks:\n      - clawith_network
}' docker-compose.yaml
    sed -i '/^  redis:/,/^  backend:/{/retries: 5$/a\    networks:\n      - clawith_network
}' docker-compose.yaml
    docker compose down && docker compose up -d
fi
