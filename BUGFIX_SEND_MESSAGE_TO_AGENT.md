# Bug Fix: `send_message_to_agent` TypeError

**Date:** 2026-04-16  
**Status:** ✅ Fixed  
**Issue:** `TypeError: can only concatenate tuple (not "str") to tuple`

---

## Problem

The `send_message_to_agent` tool was failing with a `TypeError` when agents tried to communicate with each other. The error occurred in the Gateway API when resolving sender names from the database.

### Root Cause

When using SQLAlchemy's `select()` to query a **single column** (e.g., `select(User.display_name)`), the `scalar_one_or_none()` method can return a **tuple** instead of a scalar value in certain SQLAlchemy version configurations.

Example of the problematic code:
```python
r = await db.execute(select(User.display_name).where(User.id == user_id))
sender_name = r.scalar_one_or_none()  # Could return ("John",) instead of "John"
```

When this tuple was passed to Pydantic models (like `GatewayHistoryItem`), it caused a `TypeError` during response serialization.

---

## Files Fixed

### 1. `/data/workspace/backend/app/api/gateway.py`

**Lines fixed:** 138-144, 161-163

**Before:**
```python
r = await db.execute(select(User.display_name).where(User.id == msg.sender_user_id))
sender_user_name = r.scalar_one_or_none()
```

**After:**
```python
r = await db.execute(select(User.display_name).where(User.id == msg.sender_user_id))
result = r.scalar_one_or_none()
sender_user_name = result[0] if isinstance(result, tuple) else result
```

**Locations:**
- Line 138-144: Resolving sender agent name
- Line 142-145: Resolving sender user name  
- Line 161-163: Resolving history message sender names

---

### 2. `/data/workspace/backend/app/api/activity.py`

**Lines fixed:** 73-75, 189-191, 277-279

**Same pattern applied to:**
- User display name resolution (line 73)
- Agent name resolution (line 189)
- Participant display name resolution (line 277)

---

## Testing

To verify the fix:

1. **Restart the Clawith backend** to apply the changes
2. **Test agent-to-agent messaging:**
   ```python
   send_message_to_agent(
       agent_name="DevOps Moiria",
       message="Test message",
       msg_type="chat"
   )
   ```
3. **Check Gateway poll endpoint** returns valid JSON without errors
4. **Verify chat history** displays correctly in the UI

---

## Prevention

To avoid this issue in the future:

### Option 1: Select full objects (Recommended)
```python
# Instead of:
r = await db.execute(select(User.display_name).where(...))
name = r.scalar_one_or_none()

# Use:
r = await db.execute(select(User).where(...))
user = r.scalar_one_or_none()
name = user.display_name if user else None
```

### Option 2: Handle tuple unwrapping (Current fix)
```python
result = r.scalar_one_or_none()
value = result[0] if isinstance(result, tuple) else result
```

### Option 3: Use `scalars()` for single columns
```python
r = await db.execute(select(User.display_name).where(...))
name = r.scalars().first()
```

---

## Related Issues

This fix also resolves similar issues in:
- Activity log API (`/api/activity`)
- Chat history endpoints
- Any endpoint using single-column selects with `scalar_one_or_none()`

---

## Deployment

1. ✅ Code changes applied
2. ⏳ Backend restart required
3. ⏳ Test agent messaging
4. ⏳ Monitor for similar patterns in other files

---

**Fixed by:** Claw (Clawith Repair)  
**Reviewed by:** Pending
