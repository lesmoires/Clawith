"""
Simple Infisical Secret Tool

Get secrets from Infisical with a single service token.
No complex permissions, no multi-tenant, no audit logging.
Just: "Get me STRIPE_API_KEY" → Returns the key.

Usage in agent:
    result = await get_secret("STRIPE_API_KEY")
"""

import httpx
import os


async def get_infisical_secret(secret_name: str, environment: str = "prod") -> str:
    """
    Get a secret from Infisical.
    
    Args:
        secret_name: Name of the secret (e.g., "STRIPE_API_KEY")
        environment: Environment (default: "prod")
    
    Returns:
        Secret value (string)
    
    Raises:
        ValueError: If secret not found
        httpx.HTTPError: If Infisical API fails
    """
    # Required env vars
    host_url = os.environ.get("INFISICAL_HOST_URL")
    project_id = os.environ.get("INFISICAL_PROJECT_ID")
    service_token = os.environ.get("INFISICAL_SERVICE_TOKEN")
    
    if not all([host_url, project_id, service_token]):
        raise ValueError(
            "Infisical not configured. Set INFISICAL_HOST_URL, "
            "INFISICAL_PROJECT_ID, and INFISICAL_SERVICE_TOKEN in environment."
        )
    
    # Fetch secrets from Infisical
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{host_url}/api/v1/secrets/overrides/list",
            headers={
                "Authorization": f"Bearer {service_token}",
                "Content-Type": "application/json"
            },
            json={
                "projectId": project_id,
                "environment": environment
            }
        )
        response.raise_for_status()
        data = response.json()
    
    # Find requested secret
    secrets = data.get("secrets", [])
    for secret in secrets:
        if secret.get("secretKey") == secret_name:
            return secret.get("secretValue", "")
    
    # Secret not found
    available = [s["secretKey"] for s in secrets]
    raise ValueError(
        f"Secret '{secret_name}' not found. Available: {', '.join(available) if available else 'none'}"
    )


# Tool definition for Clawith
INFISICAL_SECRET_TOOL = {
    "name": "get_infisical_secret",
    "description": "Get a secret from Infisical secret manager. Use this for API keys, database credentials, etc. Secrets are NEVER stored in agent files.",
    "parameters": {
        "type": "object",
        "properties": {
            "secret_name": {
                "type": "string",
                "description": "Name of the secret (e.g., 'STRIPE_API_KEY', 'DATABASE_PASSWORD')"
            },
            "environment": {
                "type": "string",
                "description": "Environment (default: 'prod')",
                "default": "prod"
            }
        },
        "required": ["secret_name"]
    }
}


# Tool registration is handled by Clawith's tool seeding system
# This tool will be auto-registered when agents use it
