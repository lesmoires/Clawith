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
    Get a secret from Infisical using Universal Auth.
    
    Args:
        secret_name: Name of the secret (e.g., "STRIPE_API_KEY")
        environment: Environment (default: "prod")
    
    Returns:
        Secret value (string)
    
    Raises:
        ValueError: If secret not found or not configured
        httpx.HTTPError: If Infisical API fails
    """
    # Required env vars (Universal Auth)
    host_url = os.environ.get("INFISICAL_HOST_URL")
    project_id = os.environ.get("INFISICAL_PROJECT_ID")
    client_id = os.environ.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_ID")
    client_secret = os.environ.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET")
    
    if not all([host_url, project_id, client_id, client_secret]):
        raise ValueError(
            "Infisical not configured. Set INFISICAL_HOST_URL, "
            "INFISICAL_PROJECT_ID, INFISICAL_UNIVERSAL_AUTH_CLIENT_ID, "
            "and INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET in environment."
        )
    
    # Step 1: Get access token
    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_response = await client.post(
            f"{host_url}/api/v1/auth/universal-auth/login",
            headers={"Content-Type": "application/json"},
            json={
                "clientId": client_id,
                "clientSecret": client_secret
            }
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get("accessToken")
        
        if not access_token:
            raise ValueError("Failed to get access token from Infisical")
        
        # Step 2: Fetch secrets
        response = await client.post(
            f"{host_url}/api/v1/secrets/overrides/list",
            headers={
                "Authorization": f"Bearer {access_token}",
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
