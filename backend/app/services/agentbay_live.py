"""AgentBay live preview helpers.

Provides utility functions for fetching live preview data
(VNC URL, browser snapshots) from active AgentBay sessions.
These are used by the WebSocket handler to push real-time
preview updates to the frontend.
"""

import uuid
from typing import Optional

from loguru import logger


async def get_desktop_live_url(agent_id: uuid.UUID) -> Optional[str]:
    """Get the VNC viewer URL for an agent's active computer session.

    Returns None if no computer session is active or the URL
    cannot be retrieved.
    """
    from app.services.agentbay_client import _agentbay_sessions

    cache_key = (agent_id, "computer")
    if cache_key not in _agentbay_sessions:
        return None

    client, _last_used = _agentbay_sessions[cache_key]
    return await client.get_live_url()


async def get_browser_snapshot(agent_id: uuid.UUID) -> Optional[str]:
    """Get a base64-encoded screenshot of an agent's active browser session.

    Returns data:image/jpeg;base64,... string or None if no browser
    session is active or the screenshot fails.
    """
    from app.services.agentbay_client import _agentbay_sessions

    cache_key = (agent_id, "browser")
    if cache_key not in _agentbay_sessions:
        return None

    client, _last_used = _agentbay_sessions[cache_key]
    return await client.get_browser_snapshot_base64()


def detect_agentbay_env(tool_name: str) -> Optional[str]:
    """Detect which AgentBay environment a tool belongs to.

    Returns 'desktop', 'browser', 'code', or None if not an AgentBay tool.
    """
    if tool_name.startswith("agentbay_computer_"):
        return "desktop"
    if tool_name.startswith("agentbay_browser_"):
        return "browser"
    if tool_name in ("agentbay_code_execute", "agentbay_command_exec"):
        return "code"
    return None
