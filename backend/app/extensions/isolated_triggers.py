"""
Isolated Trigger Executor — Clawith Custom Extension (v2 with Trigger Logs)

This module provides isolated execution for triggers, spawning temporary
sessions that are automatically cleaned up after execution. Results are
copied to a dedicated "Trigger Logs" session for visibility.

This is a Clawith-specific extension. When OpenClaw upstream provides
native isolated trigger support, this module should be deprecated and
replaced with the upstream implementation.

Tracking: Issue #CLAWITH-2026-001
Target Upstream Version: OpenClaw v2.x (TBD)

Usage:
    In focus.md or trigger config:
    
    triggers:
      - name: shareholderresponsetracking
        type: interval
        minutes: 10
        reason: Check shareholder responses
        isolated: true              # ← Enable isolated execution
        session_cleanup: after_run  # ← Auto-cleanup after execution
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger

from app.database import async_session
from sqlalchemy import text


async def get_or_create_trigger_logs_session(agent_id: uuid.UUID) -> Tuple[str, str]:
    """
    Get or create a dedicated "Trigger Logs" session for an agent.
    
    This session is PERSISTENT and visible in the UI, unlike isolated sessions
    which are temporary and cleaned up.
    
    Args:
        agent_id: The agent UUID
    
    Returns:
        Tuple of (session_id, user_id)
    """
    try:
        async with async_session() as session:
            # Try to find existing trigger_logs session
            result = await session.execute(
                text("""
                    SELECT id, user_id FROM chat_sessions 
                    WHERE agent_id = :agent_id 
                    AND source_channel = 'trigger_logs'
                    ORDER BY created_at DESC 
                    LIMIT 1
                """),
                {"agent_id": str(agent_id)}
            )
            row = result.fetchone()
            
            if row:
                session_id = str(row[0])
                user_id = str(row[1])
                logger.info(
                    f"[Trigger Logs] Found existing session: {session_id}",
                    extra={"agent_id": str(agent_id)}
                )
                return (session_id, user_id)
            
            # Create new trigger_logs session
            # First get the user_id from the agent
            result = await session.execute(
                text("SELECT creator_id FROM agents WHERE id = :agent_id"),
                {"agent_id": str(agent_id)}
            )
            row = result.fetchone()
            if not row:
                raise ValueError(f"Agent {agent_id} not found")
            user_id = str(row[0])
            
            session_id = str(uuid.uuid4())
            
            await session.execute(
                text("""
                    INSERT INTO chat_sessions (
                        id,
                        agent_id,
                        user_id,
                        title,
                        source_channel,
                        created_at,
                        last_message_at
                    ) VALUES (
                        :id,
                        :agent_id,
                        :user_id,
                        :title,
                        'trigger_logs',
                        :created_at,
                        :created_at
                    )
                """),
                {
                    "id": session_id,
                    "agent_id": str(agent_id),
                    "user_id": user_id,
                    "title": "📊 Trigger Logs",
                    "created_at": datetime.now(timezone.utc),
                }
            )
            await session.commit()
            
            logger.info(
                f"[Trigger Logs] Created new session: {session_id}",
                extra={"agent_id": str(agent_id), "user_id": user_id}
            )
            return (session_id, user_id)
            
    except Exception as e:
        logger.error(
            f"[Trigger Logs] Failed to get/create session: {e}",
            extra={"agent_id": str(agent_id)},
            exc_info=True
        )
        raise


async def append_message_to_session(
    session_id: str,
    agent_id: uuid.UUID,
    user_id: str,
    content: str,
    role: str = "assistant"
) -> bool:
    """
    Append a message to a chat session.
    
    Args:
        session_id: The session to append to
        agent_id: The agent UUID
        user_id: The user UUID
        content: Message content
        role: "assistant" or "user" (default: "assistant")
    
    Returns:
        bool: True if successful
    """
    try:
        async with async_session() as session:
            message_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # Insert message
            await session.execute(
                text("""
                    INSERT INTO chat_messages (
                        id,
                        conversation_id,
                        agent_id,
                        user_id,
                        role,
                        content,
                        created_at
                    ) VALUES (
                        :id,
                        :conversation_id,
                        :agent_id,
                        :user_id,
                        :role,
                        :content,
                        :created_at
                    )
                """),
                {
                    "id": message_id,
                    "conversation_id": session_id,
                    "agent_id": str(agent_id),
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "created_at": now,
                }
            )
            
            # Update session's last_message_at
            await session.execute(
                text("""
                    UPDATE chat_sessions 
                    SET last_message_at = :last_message_at 
                    WHERE id = :session_id
                """),
                {
                    "last_message_at": now,
                    "session_id": session_id,
                }
            )
            
            await session.commit()
            
            logger.debug(
                f"[Trigger Logs] Message appended: {message_id}",
                extra={"session_id": session_id}
            )
            return True
            
    except Exception as e:
        logger.error(
            f"[Trigger Logs] Failed to append message: {e}",
            extra={"session_id": session_id},
            exc_info=True
        )
        return False


async def spawn_isolated_session(agent_id: uuid.UUID, trigger_name: str) -> str:
    """
    Spawn a temporary session for isolated trigger execution.
    
    Args:
        agent_id: The agent UUID this trigger belongs to
        trigger_name: Name of the trigger (for logging/tracking)
    
    Returns:
        session_id: UUID of the isolated chat session
    
    Note:
        Creates a chat_sessions record with source_channel='isolated_trigger'
        for easy identification and cleanup.
    """
    session_id = uuid.uuid4()
    
    try:
        async with async_session() as session:
            # Get agent to find user_id
            from app.models.agent import Agent
            result = await session.execute(
                text("SELECT creator_id FROM agents WHERE id = :agent_id"),
                {"agent_id": str(agent_id)}
            )
            row = result.fetchone()
            if not row:
                raise ValueError(f"Agent {agent_id} not found")
            user_id = row[0]
            
            # Insert chat session record
            await session.execute(
                text("""
                    INSERT INTO chat_sessions (
                        id,
                        agent_id,
                        user_id,
                        title,
                        source_channel,
                        created_at,
                        last_message_at
                    ) VALUES (
                        :id,
                        :agent_id,
                        :user_id,
                        :title,
                        'isolated_trigger',
                        :created_at,
                        :created_at
                    )
                """),
                {
                    "id": str(session_id),
                    "agent_id": str(agent_id),
                    "user_id": str(user_id),
                    "title": f"Isolated Trigger: {trigger_name}",
                    "created_at": datetime.now(timezone.utc),
                }
            )
            await session.commit()
            
        logger.info(
            f"[Isolated Trigger] Session spawned: {session_id}",
            extra={
                "trigger_name": trigger_name,
                "agent_id": str(agent_id),
                "session_type": "isolated_trigger",
            }
        )
        return str(session_id)
        
    except Exception as e:
        logger.error(
            f"[Isolated Trigger] Failed to spawn session: {e}",
            extra={
                "trigger_name": trigger_name,
                "agent_id": str(agent_id),
            },
            exc_info=True
        )
        raise


async def cleanup_isolated_session(session_key: str, trigger_name: str) -> bool:
    """
    Clean up an isolated session after trigger execution.
    
    Deletes the session record and all associated messages from the database.
    
    Args:
        session_key: The session identifier to clean up
        trigger_name: Name of the trigger (for logging)
    
    Returns:
        bool: True if cleanup succeeded, False otherwise
    """
    try:
        async with async_session() as session:
            # Delete associated messages first (foreign key constraint)
            await session.execute(
                text("DELETE FROM chat_messages WHERE conversation_id = :session_id"),
                {"session_id": session_key}
            )
            
            # Delete session record
            result = await session.execute(
                text("DELETE FROM chat_sessions WHERE id = :session_id"),
                {"session_id": session_key}
            )
            
            await session.commit()
            
            deleted_count = result.rowcount
            
        if deleted_count > 0:
            logger.info(
                f"[Isolated Trigger] Session cleaned up: {session_key}",
                extra={
                    "trigger_name": trigger_name,
                    "session_id": session_key,
                }
            )
            return True
        else:
            logger.warning(
                f"[Isolated Trigger] Session not found for cleanup: {session_key}",
                extra={"trigger_name": trigger_name}
            )
            return False
            
    except Exception as e:
        logger.error(
            f"[Isolated Trigger] Cleanup failed: {e}",
            extra={
                "trigger_name": trigger_name,
                "session_id": session_key,
            },
            exc_info=True
        )
        return False


async def execute_isolated_trigger(
    trigger_name: str,
    agent_id: uuid.UUID,
    reason: str,
    session_cleanup: str = "after_run",
    log_to_trigger_logs: bool = True
) -> bool:
    """
    Execute a trigger in an isolated session with automatic cleanup.
    Results are copied to the "Trigger Logs" session for visibility.
    
    This is the main entry point for isolated trigger execution. It:
    1. Spawns a temporary session
    2. Executes the trigger logic in that session
    3. Copies the result to the Trigger Logs session
    4. Cleans up the isolated session (if session_cleanup == "after_run")
    
    Args:
        trigger_name: Name of the trigger (e.g., "shareholderresponsetracking")
        agent_id: The agent UUID this trigger belongs to
        reason: The trigger reason/action to execute
        session_cleanup: When to cleanup ("after_run", "never", "on_error")
        log_to_trigger_logs: Whether to log results to trigger_logs session
    
    Returns:
        bool: True if execution succeeded, False otherwise
    
    Raises:
        Exception: Re-raises any execution errors after cleanup
    """
    session_key = None
    execution_result = None
    execution_success = False
    
    try:
        # Step 1: Spawn isolated session
        session_key = await spawn_isolated_session(agent_id, trigger_name)
        
        # Step 2: Execute trigger logic
        # Note: This imports here to avoid circular imports
        from app.services.trigger_daemon import _invoke_agent_for_triggers
        from app.api.websocket import manager as ws_manager
        
        logger.info(
            f"[Isolated Trigger] Executing: {trigger_name}",
            extra={
                "trigger_name": trigger_name,
                "agent_id": str(agent_id),
                "session_id": session_key,
            }
        )
        
        # FIX: Save current active connections, replace with ONLY isolated session
        # This ensures _invoke_agent_for_triggers writes ONLY to the isolated session
        agent_id_str = str(agent_id)
        
        # Save current connections (user's WebSocket sessions)
        saved_connections = ws_manager.active_connections.get(agent_id_str, []).copy()
        
        # Replace with ONLY the isolated session
        ws_manager.active_connections[agent_id_str] = [(None, session_key)]
        
        logger.info(
            f"[Isolated Trigger] Isolated session {session_key} set as only active connection",
            extra={"trigger_name": trigger_name, "saved_count": len(saved_connections)}
        )
        
        try:
            # Create a mock trigger object for invocation
            from app.models.trigger import AgentTrigger
            mock_trigger = AgentTrigger(
                id=uuid.uuid4(),
                agent_id=agent_id,
                name=trigger_name,
                type='interval',
                config={},
                reason=reason,
            )
            
            # Execute and capture result
            execution_result = await _invoke_agent_for_triggers(agent_id, [mock_trigger])
            execution_success = True
        finally:
            # Restore original connections (user's WebSocket sessions)
            ws_manager.active_connections[agent_id_str] = saved_connections
            
            logger.info(
                f"[Isolated Trigger] Restored {len(saved_connections)} original connection(s)",
                extra={"trigger_name": trigger_name}
            )
        
        # Step 3: Log to Trigger Logs session (if enabled)
        if log_to_trigger_logs:
            try:
                trigger_logs_session_id, user_id = await get_or_create_trigger_logs_session(agent_id)
                
                # Build log message
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                status_icon = "✅" if execution_success else "❌"
                
                log_content = f"""### {status_icon} {trigger_name} — {now}

**Status:** {'Success' if execution_success else 'Failed'}
**Trigger:** `{trigger_name}`
**Reason:** {reason[:200]}{'...' if len(reason) > 200 else ''}

---
"""
                
                await append_message_to_session(
                    session_id=trigger_logs_session_id,
                    agent_id=agent_id,
                    user_id=user_id,
                    content=log_content,
                    role="assistant"
                )
                
                logger.info(
                    f"[Trigger Logs] Logged execution: {trigger_name}",
                    extra={"session_id": trigger_logs_session_id}
                )
                
            except Exception as log_error:
                logger.error(
                    f"[Trigger Logs] Failed to log execution: {log_error}",
                    extra={"trigger_name": trigger_name},
                    exc_info=True
                )
                # Don't fail the trigger if logging fails
        
        # Step 4: Cleanup isolated session if configured
        if session_cleanup == "after_run":
            await cleanup_isolated_session(session_key, trigger_name)
        
        logger.info(
            f"[Isolated Trigger] Execution complete: {trigger_name}",
            extra={"trigger_name": trigger_name, "agent_id": str(agent_id)}
        )
        return True
        
    except Exception as e:
        logger.error(
            f"[Isolated Trigger] Execution failed: {e}",
            extra={
                "trigger_name": trigger_name,
                "agent_id": str(agent_id),
                "session_id": session_key,
            },
            exc_info=True
        )
        
        # Log failure to Trigger Logs
        if log_to_trigger_logs:
            try:
                trigger_logs_session_id, user_id = await get_or_create_trigger_logs_session(agent_id)
                
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                
                log_content = f"""### ❌ {trigger_name} — {now}

**Status:** Failed
**Trigger:** `{trigger_name}`
**Error:** `{str(e)[:500]}`

---
"""
                
                await append_message_to_session(
                    session_id=trigger_logs_session_id,
                    agent_id=agent_id,
                    user_id=user_id,
                    content=log_content,
                    role="assistant"
                )
                
            except Exception as log_error:
                logger.error(
                    f"[Trigger Logs] Failed to log error: {log_error}",
                    extra={"trigger_name": trigger_name}
                )
        
        # Cleanup on error if configured
        if session_cleanup in ("after_run", "on_error") and session_key:
            logger.info(
                f"[Isolated Trigger] Cleaning up after error: {session_key}",
                extra={"trigger_name": trigger_name}
            )
            await cleanup_isolated_session(session_key, trigger_name)
        
        # Re-raise for upstream error handling
        raise


# ============================================================================
# Extension Registration
# ============================================================================

def register_extension():
    """
    Register this extension with the Clawith extension system.
    
    This is called automatically when extensions are loaded.
    """
    logger.info("[Extension] isolated_triggers loaded")


# ============================================================================
# Orphan Session Cleanup (Maintenance)
# ============================================================================

async def cleanup_orphan_isolated_sessions(max_age_hours: int = 1) -> int:
    """
    Clean up orphaned isolated sessions (safety net).
    
    This should be run periodically (e.g., hourly cron) to catch any
    sessions that weren't cleaned up properly.
    
    Args:
        max_age_hours: Delete sessions older than this
    
    Returns:
        int: Number of sessions cleaned up
    """
    try:
        async with async_session() as session:
            result = await session.execute(
                text("""
                    DELETE FROM chat_sessions 
                    WHERE source_channel = 'isolated_trigger'
                    AND created_at < NOW() - INTERVAL :age
                """),
                {"age": f"{max_age_hours} hours"}
            )
            await session.commit()
            
            deleted_count = result.rowcount
            
        if deleted_count > 0:
            logger.warning(
                f"[Isolated Trigger] Cleaned up {deleted_count} orphan sessions",
                extra={"max_age_hours": max_age_hours}
            )
        
        return deleted_count
        
    except Exception as e:
        logger.error(
            f"[Isolated Trigger] Orphan cleanup failed: {e}",
            exc_info=True
        )
        return 0
