# Coolify Deployment Instructions - Force Clean Rebuild

## Problem
Python bytecode cache (`.pyc` files) is preventing the fix from being applied.

## Solution: Force Clean Build in Coolify

### Option 1: Clear Build Cache + Redeploy (Recommended)

1. Go to https://coolify.moiria.com
2. Find **Clawith backend** service
3. Click on **"Build"** or **"Settings"** tab
4. Find **"Build Cache"** section
5. Click **"Clear Cache"** or **"Purge Build Cache"**
6. Go back to **Deployments** tab
7. Click **"Deploy"** or **"Redeploy"**
8. **IMPORTANT:** Enable **"Force rebuild"** or **"No cache"** option if available
9. Wait for deployment to complete (~5 minutes)

### Option 2: Manual SSH Container Restart

If you have SSH access to the server:

```bash
# SSH to server
ssh root@46.225.220.208

# Find the backend container
docker ps | grep clawith

# Stop and remove container (keeps volume)
docker rm -f clawith-backend-1

# Start fresh (Coolify will recreate)
docker compose -f /path/to/compose.yml up -d

# OR force recreate
docker compose -f /path/to/compose.yml up -d --force-recreate --no-deps
```

### Option 3: Change Dockerfile to Force Rebuild

Add a comment change to the Dockerfile to force Docker to rebuild all layers:

```dockerfile
# Force rebuild 2026-04-16
FROM python:3.12-slim
```

Then commit and push, which will force a complete rebuild.

---

## Verification

After deployment, test:

```python
send_message_to_agent(
    agent_name="DevOps Moiria",
    message="Test",
    msg_type="chat"
)
```

Should work without `TypeError`!

---

## Why This Happens

Python compiles `.py` files to `.pyc` bytecode for faster loading. When code changes but the container isn't fully rebuilt, Python may use stale `.pyc` files instead of the new code.

**Solution:** Clear cache + force rebuild ensures fresh compilation.
