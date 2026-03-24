# Merge Resolution Action Plan

**Created:** 2026-03-24 12:04 UTC  
**Priority:** P0 — Critical  
**Estimated Time:** 2-4 hours manual work

---

## Critical Issues

### 1. Gateway API — 47 Merge Conflicts 🔴

**File:** `backend/app/api/gateway.py`  
**Impact:** Complete — File cannot be imported or run  
**Custom Code at Risk:**
- WebSocket push notifications (lines 290-430)
- ChatMessage routing and storage
- Agent-to-agent message forwarding
- Feishu integration enhancements

**Resolution Strategy:**

```bash
cd /data/workspace/clawith-fork

# Option A: Manual resolution (recommended for control)
# Open file and resolve each conflict, preserving our custom code
code backend/app/api/gateway.py  # or your preferred editor

# Option B: Use git mergetool
git mergetool backend/app/api/gateway.py

# Option C: Accept one side completely (NOT recommended — will lose custom code)
# git checkout --ours backend/app/api/gateway.py
# git checkout --theirs backend/app/api/gateway.py
```

**Priority Sections to Preserve:**
1. **Lines 290-330:** WebSocket + ChatMessage integration
2. **Lines 357-434:** Agent message forwarding with WebSocket push
3. **Lines 475-485:** LLM integration with ChatMessage
4. **Lines 540-600:** Message history and conversation management

**Conflict Pattern:**
```python
<<<<<<< HEAD
# Our custom code (Clawith Repair, WebSocket, ChatMessage)
=======
# Upstream changes (Feishu improvements, bug fixes)
>>>>>>> upstream/main
```

**Recommended Approach:**
- Keep BOTH sides where possible
- Our WebSocket/ChatMessage code is additive (doesn't conflict with upstream logic)
- Upstream Feishu improvements (user_id vs open_id) should be merged with our code

---

### 2. Infisical Secrets — Truncated File ⚠️

**File:** `backend/app/skills/infisical_secrets.py`  
**Expected:** 617 lines  
**Actual:** 147 lines  
**Impact:** Missing multi-tenant support, audit logging, advanced features

**Resolution Options:**

**Option A: Restore from Git History**
```bash
cd /data/workspace/clawith-fork
git log --oneline backend/app/skills/infisical_secrets.py | head -10
# Find commit before merge, then:
git checkout <commit-hash>^ -- backend/app/skills/infisical_secrets.py
```

**Option B: Check Backup Locations**
```bash
# Check if backup exists
ls -la /data/workspace/BACKUP_FILES/
ls -la ~/backups/clawith-fork/
```

**Option C: Re-implement from Documentation**
- Review original feature requirements
- Re-build multi-tenant support
- Add audit logging
- Test thoroughly

---

### 3. MCP Client — Merge Conflicts ⚠️

**File:** `backend/app/services/mcp_client.py`  
**Impact:** Partial — At least 1 conflict at line 17 (loguru import)

**Resolution:**
```bash
# Check all conflicts
grep -n "<<<<<<" backend/app/services/mcp_client.py

# Likely simple fix — keep loguru import from upstream
# It's an improvement over standard logging
```

---

## Step-by-Step Resolution Plan

### Phase 1: Backup (✅ Complete)
- [x] All files backed up to `BACKUP_FILES/`
- [x] Audit report created
- [x] Validation log created

### Phase 2: Gateway API Resolution (P0)
- [ ] Open `gateway.py` in editor
- [ ] Resolve conflicts systematically (top to bottom)
- [ ] **CRITICAL:** Preserve WebSocket code (lines 290-430)
- [ ] **CRITICAL:** Preserve ChatMessage routing
- [ ] Test syntax: `python3 -m py_compile backend/app/api/gateway.py`
- [ ] Test import: `python3 -c "from app.api.gateway import *"`

### Phase 3: Infisical Restoration (P0)
- [ ] Check git history for full version
- [ ] Restore 617-line version
- [ ] Verify multi-tenant features present
- [ ] Test import

### Phase 4: MCP Client Resolution (P1)
- [ ] Resolve loguru import conflict
- [ ] Check for other conflicts
- [ ] Test import

### Phase 5: Validation (P1)
- [ ] Install dependencies: `pip install httpx`
- [ ] Run all import tests
- [ ] Run functional tests
- [ ] Update VALIDATION_LOG.md

### Phase 6: Documentation (P2)
- [ ] Update FEATURES_INTEGRATION_REPORT.md with resolutions
- [ ] Document any changes made
- [ ] Commit with clear message

---

## Git Commands for Resolution

```bash
# Start resolution
cd /data/workspace/clawith-fork
git status

# See conflicted files
git diff --name-only --diff-filter=U

# For each conflicted file:
# 1. Open in editor
# 2. Resolve conflicts
# 3. Mark as resolved
git add backend/app/api/gateway.py

# After all resolved:
git commit -m "fix: Resolve merge conflicts, preserve custom features

- Resolved 47 conflicts in gateway.py (WebSocket + ChatMessage preserved)
- Restored infisical_secrets.py (617 lines)
- Fixed mcp_client.py loguru import

Custom features preserved:
✅ AgentMail Integration
✅ Infisical MCP + Secrets
✅ Gateway API Enhanced (WebSocket + ChatMessage)
✅ LiteLLM MCP Gateway"

# Verify
git status
python3 -m py_compile backend/app/api/gateway.py
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Lose WebSocket code | Medium | 🔴 Critical | Manual review of lines 290-430 |
| Lose ChatMessage routing | Medium | 🔴 Critical | Verify lines 357-434 after merge |
| Infisical features lost | High | 🟡 High | Restore from git history |
| Break Feishu integration | Low | 🟡 Medium | Test Feishu paths after merge |
| MCP client broken | Low | 🟠 Medium | Simple conflict, easy to fix |

---

## Success Criteria

- [ ] `gateway.py` imports without errors
- [ ] WebSocket push code present and functional
- [ ] ChatMessage routing works
- [ ] `infisical_secrets.py` has 617 lines
- [ ] `mcp_client.py` imports without errors
- [ ] All 4 features pass validation tests
- [ ] No merge conflict markers remain in codebase

---

**Next Action:** Begin Phase 2 — Manual merge resolution of gateway.py

**Estimated Completion:** 2026-03-24 16:00 UTC (4 hours)
