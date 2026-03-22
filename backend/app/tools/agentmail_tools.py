"""
AgentMail Tools for Clawith

Send and receive emails using AgentMail API.
Perfect for AI agents that need email capabilities.

Usage in agent:
    result = await agentmail_send_email(
        from_inbox="conver.thesis@agentmail.to",
        to=["recipient@example.com"],
        subject="Hello",
        text="Message"
    )
"""

import httpx
import os
from typing import Optional


def _get_api_key() -> str:
    """Get AgentMail API key from environment."""
    api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        raise ValueError(
            "AgentMail not configured. Set AGENTMAIL_API_KEY in environment."
        )
    return api_key


async def agentmail_list_inboxes() -> dict:
    """
    List all inboxes in your AgentMail account.
    
    Returns:
        dict: List of inboxes with their details
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.agentmail.to/v0/inboxes",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()


async def agentmail_create_inbox(display_name: str) -> dict:
    """
    Create a new inbox with a unique email address.
    
    Args:
        display_name: Human-readable name for the inbox
    
    Returns:
        dict: Inbox details including email address
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.agentmail.to/v0/inboxes",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"display_name": display_name}
        )
        response.raise_for_status()
        return response.json()


async def agentmail_send_email(
    from_inbox: str,
    to: list[str],
    subject: str,
    text: str,
    html: Optional[str] = None,
    cc: Optional[list[str]] = None,
    in_reply_to: Optional[str] = None
) -> dict:
    """
    Send an email from an inbox.
    
    Args:
        from_inbox: Inbox email address (e.g., "conver.thesis@agentmail.to")
        to: List of recipient email addresses
        subject: Email subject
        text: Plain text body
        html: HTML body (optional, recommended for better deliverability)
        cc: List of CC recipients (optional)
        in_reply_to: Message ID to reply to (optional, for threading)
    
    Returns:
        dict: Response with message_id and thread_id
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    payload = {
        "to": to,
        "subject": subject,
        "text": text
    }
    
    if html:
        payload["html"] = html
    if cc:
        payload["cc"] = cc
    if in_reply_to:
        payload["in_reply_to"] = in_reply_to
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://api.agentmail.to/v0/inboxes/{from_inbox}/messages/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        return response.json()


async def agentmail_list_messages(inbox_id: str, limit: int = 10) -> dict:
    """
    List messages in an inbox.
    
    Args:
        inbox_id: Inbox email address or ID
        limit: Maximum number of messages to return (default: 10)
    
    Returns:
        dict: List of messages with metadata
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"https://api.agentmail.to/v0/inboxes/{inbox_id}/messages",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()


async def agentmail_get_thread(inbox_id: str, thread_id: str) -> dict:
    """
    Get a complete email thread with all messages.
    
    Args:
        inbox_id: Inbox email address or ID
        thread_id: Thread ID
    
    Returns:
        dict: Thread details with all messages
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"https://api.agentmail.to/v0/inboxes/{inbox_id}/threads/{thread_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()


async def agentmail_reply_to_message(
    inbox_id: str,
    message_id: str,
    text: str,
    html: Optional[str] = None
) -> dict:
    """
    Reply to a specific message.
    
    Args:
        inbox_id: Inbox email address or ID
        message_id: Message ID to reply to
        text: Reply text body
        html: Reply HTML body (optional)
    
    Returns:
        dict: Response with message_id and thread_id
    
    Raises:
        ValueError: If API key not configured
        httpx.HTTPError: If API call fails
    """
    api_key = _get_api_key()
    
    payload = {"text": text}
    if html:
        payload["html"] = html
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/{message_id}/reply",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        return response.json()


# Tool definitions for Clawith registration

AGENTMAIL_LIST_INBOXES_TOOL = {
    "name": "agentmail_list_inboxes",
    "description": "List all email inboxes in your AgentMail account. Returns inbox IDs, email addresses, and display names.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

AGENTMAIL_CREATE_INBOX_TOOL = {
    "name": "agentmail_create_inbox",
    "description": "Create a new email inbox with a unique @agentmail.to address. Provide a display name for the inbox.",
    "parameters": {
        "type": "object",
        "properties": {
            "display_name": {
                "type": "string",
                "description": "Human-readable name for the inbox (e.g., 'Conver Thesis', 'Support Agent')"
            }
        },
        "required": ["display_name"]
    }
}

AGENTMAIL_SEND_EMAIL_TOOL = {
    "name": "agentmail_send_email",
    "description": "Send an email from an AgentMail inbox. Supports plain text and HTML for best deliverability.",
    "parameters": {
        "type": "object",
        "properties": {
            "from_inbox": {
                "type": "string",
                "description": "Inbox email address to send from (e.g., 'conver.thesis@agentmail.to')"
            },
            "to": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of recipient email addresses"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "text": {
                "type": "string",
                "description": "Plain text email body"
            },
            "html": {
                "type": "string",
                "description": "HTML email body (optional, recommended for better deliverability)"
            },
            "cc": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of CC recipients (optional)"
            },
            "in_reply_to": {
                "type": "string",
                "description": "Message ID to reply to for threading (optional)"
            }
        },
        "required": ["from_inbox", "to", "subject", "text"]
    }
}

AGENTMAIL_LIST_MESSAGES_TOOL = {
    "name": "agentmail_list_messages",
    "description": "List recent messages in an inbox. Returns message metadata including sender, subject, and timestamp.",
    "parameters": {
        "type": "object",
        "properties": {
            "inbox_id": {
                "type": "string",
                "description": "Inbox email address or ID"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of messages to return (default: 10, max: 50)",
                "default": 10
            }
        },
        "required": ["inbox_id"]
    }
}

AGENTMAIL_GET_THREAD_TOOL = {
    "name": "agentmail_get_thread",
    "description": "Get a complete email thread with all messages in chronological order.",
    "parameters": {
        "type": "object",
        "properties": {
            "inbox_id": {
                "type": "string",
                "description": "Inbox email address or ID"
            },
            "thread_id": {
                "type": "string",
                "description": "Thread ID (from list_messages or send_email response)"
            }
        },
        "required": ["inbox_id", "thread_id"]
    }
}

AGENTMAIL_REPLY_TO_MESSAGE_TOOL = {
    "name": "agentmail_reply_to_message",
    "description": "Reply to a specific email message. Automatically maintains thread with In-Reply-To headers.",
    "parameters": {
        "type": "object",
        "properties": {
            "inbox_id": {
                "type": "string",
                "description": "Inbox email address or ID"
            },
            "message_id": {
                "type": "string",
                "description": "Message ID to reply to (from list_messages or get_thread)"
            },
            "text": {
                "type": "string",
                "description": "Reply text body"
            },
            "html": {
                "type": "string",
                "description": "Reply HTML body (optional)"
            }
        },
        "required": ["inbox_id", "message_id", "text"]
    }
}
