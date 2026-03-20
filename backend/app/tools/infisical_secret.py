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
from app.core.database import async_session
from app.models.tool import Tool
from sqlalchemy import select


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


async def register_tool():
    """Register the Infisical secret tool in Clawith."""
    async with async_session() as session:
        # Check if tool already exists
        result = await session.execute(
            select(Tool).where(Tool.name == "get_infisical_secret")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Infisical secret tool already registered")
            return existing
        
        # Create new tool
        tool = Tool(
            name="get_infisical_secret",
            description=INFISICAL_SECRET_TOOL["description"],
            parameters=INFISICAL_SECRET_TOOL["parameters"],
            code="from app.tools.infisical_secret import get_infisical_secret; result = await get_infisical_secret(**params)",
            is_builtin=True
        )
        
        session.add(tool)
        await session.commit()
        print("✅ Infisical secret tool registered successfully")
        return tool
