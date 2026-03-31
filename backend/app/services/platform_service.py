"""Platform-wide service for URL resolution and host type detection."""

import os
import re
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_settings import SystemSetting

class PlatformService:
    """Service to handle platform-wide settings and URL resolution."""

    def is_ip_address(self, host: str) -> bool:
        """Check if a host is an IP address (IPv4)."""
        # Strip protocol and port if present
        h = host.split("://")[-1].split(":")[0].split("/")[0]
        # Basic IPv4 regex
        ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        return bool(ip_pattern.match(h))

    async def get_public_base_url(self, db: AsyncSession, request: Request | None = None) -> str:
        """Resolve the platform's public base URL with priority lookup.
        
        Priority:
        1. SystemSetting (key: 'platform', value: {'public_base_url': '...'})
        2. Environment variable (PUBLIC_BASE_URL)
        3. Incoming request's base URL (fallback)
        """
        # 1. Try SystemSetting
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == "platform"))
        setting = result.scalar_one_or_none()
        if setting and setting.value and setting.value.get("public_base_url"):
            return setting.value.get("public_base_url").rstrip("/")

        # 2. Try environment variable
        env_url = os.environ.get("PUBLIC_BASE_URL")
        if env_url:
            return env_url.rstrip("/")

        # 3. Fallback to request
        if request:
            # Note: request.base_url might include trailing slash
            return str(request.base_url).rstrip("/")

        # Absolute fallback for background tasks without request context
        return "http://localhost:8000"

    async def get_tenant_sso_base_url(self, db: AsyncSession, tenant, request: Request | None = None) -> str:
        """Generate the SSO base URL for a tenant based on IP/Domain logic.
        
        - If base is IP: return base
        - If base is Domain: return {tenant_slug}.{domain}
        """
        base_url = await self.get_public_base_url(db, request)
        
        # Parse protocol and host
        # Example: http://1.2.3.4:8000 or http://clawith.ai
        parts = base_url.split("://")
        if len(parts) < 2:
            return base_url
            
        protocol = parts[0]
        host_port = parts[1]
        
        # Split host and port
        host_parts = host_port.split(":")
        host = host_parts[0]
        port = f":{host_parts[1]}" if len(host_parts) > 1 else ""
        
        if self.is_ip_address(host):
            # IP: No subdomain, just base URL
            return base_url
        else:
            # Domain: {tenant_slug}.{domain}
            # Special case for localhost: keep it as is or handle it
            if host == "localhost":
                return f"{protocol}://{host}{port}"
                
            return f"{protocol}://{tenant.slug}.{host}{port}"

# Global instance
platform_service = PlatformService()
