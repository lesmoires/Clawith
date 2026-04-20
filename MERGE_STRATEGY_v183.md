# Merge Strategy: v1.8.2 → v1.8.3-beta.2 (+ upstream/main)

**Date:** 2026-04-20  
**Target:** Moiria fork (lesmoires/Clawith) `main`  
**Base:** v1.8.2 (`8ac1f61`)  
**Source:** upstream `v1.8.3-beta.2` (`1718388`)  
**Also consider:** upstream `main` (13 commits beyond v1.8.3-beta.2)

---

## 0. Scope Decision

### Option A: Merge v1.8.3-beta.2 only
- **Pros:** Cleaner boundary, beta tag is a known point
- **Cons:** Misses 13 important fixes on upstream/main including:
  - **#246** — Patch 4 critical security vulnerabilities ⚠️
  - **#410** — Fix N+1 queries in session list API (perf)
  - **#416** — Fix tool call message pairs broken down
  - **#437** — Alembic migrations idempotent (important for partial states)
  - **#404** — Org member identity mapping fix
  - **#173** — Increase api_key length + unify LLM failover

### Option B: Merge upstream/main directly
- **Pros:** Get all fixes including security #246
- **Cons:** Slightly more files to review (~60 vs ~32)

### Recommendation: **Option B** — Merge `upstream/main`

The security fix #246 alone justifies going to main. The file count increase is manageable (extra changes are mostly in files that are NONE conflict anyway).

**Rest of this doc assumes Option B (upstream/main).**

---

## 1. Pre-Merge Checklist

```bash
cd /data/workspace/Clawith

# 1. Ensure origin/main is pushed (already done ✅)
git status

# 2. Fetch latest upstream
git fetch upstream --tags --force

# 3. Create merge branch
git checkout -b merge/v1.8.3-upstream-main

# 4. Dry-run merge to see conflicts upfront
git merge --no-commit --no-ff upstream/main
# If conflicts appear → resolve them → commit
# If clean → still commit with --no-ff
```

---

## 2. Conflict Resolution Matrix

### ✅ Category A: Zero Conflict (5 files)

These files merge cleanly. No action needed.

| File | Why Clean |
|------|-----------|
| `backend/app/api/chat_sessions.py` | Fork: `list_sessions` (~L152-240). Upstream: `get_session_messages` (~L311-330). Different functions. |
| `backend/app/api/gateway.py` | Fork: `poll_messages` (~L134-165) tuple guards. Upstream: `_send_to_agent_background` (~L416) string rename. |
| `backend/app/api/tenants.py` | Fork: `resolve_tenant_by_domain` SSO relaxation (~L386-405). Upstream: `a2a_async_enabled` Pydantic fields (~L37-54). |
| `backend/app/config.py` | Fork: docstring only (L1-7). Upstream: `EXA_API_KEY` in Settings (L103-108). |
| `backend/app/services/tool_seeder.py` | Fork: Hetzner tools at end of file (L1877+). Upstream: search tools in middle (L429-615) + `parameters_schema` in seed function (L2082). Different regions. |

---

### ⚠️ Category B: Post-Merge Verification (1 file)

#### `backend/app/api/websocket.py`

**Conflict type:** Semantic (git should merge cleanly, but we must verify)

**The issue:** We removed `session_id=session_id` from `execute_tool()` call (~L370) to fix a `NameError`. Upstream still has it.

**After merge, verify this block:**
```python
# In call_llm(), ~line 370 area
result = await execute_tool(
    tool_name, args,
    agent_id=agent_id,
    user_id=user_id or agent_id,
    # ✅ MUST STAY REMOVED:
    # session_id=session_id,
)
```

**Upstream changes we WANT to keep:**
- `max_tool_rounds_override` parameter in `call_llm` (L121-152) — useful for A2A wake
- Message saving rewrite with `[image_data:]` marker detection (L678-726) — part of multimodal support

**Resolution:** Git will likely keep our removal (since upstream didn't change that line). But if it reverts, delete `session_id=session_id` again.

---

### 🔴 Category C: Manual Merge Required (2 files)

#### C1. `backend/app/api/agentbay_control.py`

**Conflict type:** Both sides rewrote `_get_client` function (~L147-260)

| Side | What they did |
|------|---------------|
| **Fork** | Simplified `search_order` to inline tuple, trimmed logs, added `browser_latest` support (`env_type in ("browser", "browser_latest")` + `_browser_initialized.add((..., env_type))`) |
| **Upstream** | Added 3-phase search: Phase 1 (exact match), Phase 2 (scan all sessions by agent_id, pick MRU), Phase 3 (create new). Also added `browser_latest` support |

**Both sides independently fixed `browser_latest` — different implementations.**

**Resolution strategy:**

1. **Accept upstream's full 3-phase `_get_client`** as base (Phase 2 fallback is valuable — handles mismatched session_ids)
2. **Verify Phase 3 already has `browser_latest` fix in upstream** — check if upstream already handles it. If not, apply our fix:
   ```python
   # In Phase 3 (create new):
   if env_type in ("browser", "browser_latest"):  # NOT just "browser"
       ...
       _browser_initialized.add((agent_id, session_id, env_type))  # NOT hardcoded "browser"
   ```
3. **Keep ALL our fork changes outside `_get_client`** — these are fork-only and won't conflict:
   - `_tc_browser_cleanup` simplified
   - `_perform_click/type/press_keys` — `browser` in outer scope + `finally: browser.close()`
   - Removed `_get_interaction_lock` serialization from click/type/press/drag
   - `env_type` → `env_t` cosmetic renames

**Step-by-step:**
```bash
# After git merge shows conflict:
# Open the file in editor
# Resolve the _get_client section manually:
#   1. Keep upstream's 3-phase structure
#   2. Verify browser_latest handling in all 3 phases
#   3. Mark conflict resolved
# Keep our changes in all other functions (git should handle these)
```

---

#### C2. `backend/app/services/agent_tools.py` — THE BIG ONE

**Conflict type:** Our fork deleted ~5000 lines and added ~1500 lines (massive rewrite), while upstream added ~700 lines on top of the old code.

**Sub-conflicts (5):**

##### C2a. `send_message_to_agent` tool definition (~L532-560)
- **Fork:** Unchanged from v1.8.2
- **Upstream:** Expanded description with decision guide, made `msg_type` required
- **Resolution:** ✅ **Take upstream.** We didn't modify this area.

##### C2b. `get_agent_tools_for_llm` function
- **Fork:** Stripped `_agent_has_any_channel`, `_get_computer_os_type`, `_channel_tools`, `_patch_computer_tool_descriptions`. Simplified to `has_feishu` check + DB loading.
- **Upstream:** Kept all that logic AND added `_strip_a2a_msg_type()` + `a2a_async_enabled` tenant flag.
- **Resolution:** Take **our fork's simplified function** as base, then add:
  1. Import `_strip_a2a_msg_type` (or copy it from upstream)
  2. Add tenant-level `a2a_async_enabled` check
  3. Apply `_strip_a2a_msg_type()` when flag is False
  
  Since we removed the channel logic, we also don't need the channel-related tool patching. The A2A strip logic is additive and should fit at the end of our simplified function.

##### C2c. `_send_message_to_agent` function
- **Fork:** Complete rewrite with our own `_resolve_a2a_target`, `_ensure_a2a_session`, `_wake_agent_async`. Uses `Agent` instead of `AgentModel`.
- **Upstream:** Added async A2A helpers + msg_type branching to the OLD version.
- **Resolution:** Take **our fork's version**. It's more comprehensive. Then verify:
  - Upstream's `_resolve_a2a_target` → check if our version has the same logic
  - Upstream's `_ensure_a2a_session` → check if ours matches
  - Upstream's `_create_on_message_trigger` → check if ours matches
  - Upstream's `_wake_agent_async` → check if ours matches
  
  If upstream has any bugfixes in these helpers that we don't have, cherry-pick those specific changes.

##### C2d. `execute_tool` dispatch block
- **Fork:** Removed `session_id` param, removed 30+ tool branches (channel, AgentBay, Bitable, Approval, ClawHub). Added Infisical, AgentMail, Hetzner routing.
- **Upstream:** Added 5 new search tool branches (`exa_search`, `duckduckgo_search`, `tavily_search`, `google_search`, `bing_search`).
- **Resolution:** Take **our fork's dispatch block**, then add the 5 search tool routes:
  ```python
  if tool_name == "exa_search":
      return await _exa_search(args, agent_id=agent_id)
  if tool_name == "duckduckgo_search":
      return await _duckduckgo_search_tool(args)
  # ... etc for tavily, google, bing
  ```

##### C2e. File management tools (`search_files`, `find_files`, `edit_file`)
- **Fork:** We added v1.8.1-style versions (different signatures)
- **Upstream:** Added these as NEW tools in v1.8.3-beta.2 (different signatures from ours)
- **Resolution:** Take **our fork's versions**. They're already wired into our `execute_tool` dispatch and tested. The upstream versions are newer but have different signatures — switching would require updating our dispatch + any code that calls them.

##### C2f. `_web_search` function
- **Fork:** Removed `agent_id` parameter
- **Upstream:** Made `agent_id` optional (`UUID | None`) + added Exa engine branch
- **Resolution:** Take **upstream's version** (it already has optional agent_id + Exa), but verify our custom config loading is preserved.

##### C2g. AgentBay tools
- **Fork:** All AgentBay browser/computer tool handlers **deleted** (~20 functions)
- **Upstream:** Modified `_agentbay_file_transfer` descriptions for OS paths
- **Resolution:** ✅ **No conflict.** We deleted them, so upstream's description changes are irrelevant. If we ever re-add AgentBay, we'll pick up the upstream changes.

##### C2h. New search tools to add from upstream
Upstream added these entirely new functions that we need to port:
- `_resolve_a2a_target()`, `_ensure_a2a_session()`, `_create_on_message_trigger()`, `_wake_agent_async()` — check if we already have them
- `_strip_a2a_msg_type()` — need to add or adapt
- `_search_exa()`, `_exa_search()` — need to add
- `_duckduckgo_search_tool()`, `_tavily_search_tool()`, `_google_search_tool()`, `_bing_search_tool()` — need to add
- `_search_files()`, `_find_files()`, `_edit_file()` — we already have our own versions, skip upstream's

---

## 3. Additional upstream/main changes (beyond v1.8.3-beta.2)

These 13 commits affect files that are mostly Category A (no conflict):

| Commit | File(s) | Relevance |
|--------|---------|-----------|
| #246 security fix | `auth.py`, `registration_service.py`, `auth_provider.py`, `permissions.py` | ⚠️ **CRITICAL** — 4 vulns patched |
| #410 N+1 fix | `chat_sessions.py` (agents list endpoint) | 🟢 Low conflict risk |
| #416 tool call pairs | `websocket.py` | ⚠️ Already in our post-merge verify scope |
| #437 alembic idempotent | `20260330_refactor_user_system_phase2.py` (we have this file, fork-modified) | ⚠️ Check if upstream changes overlap with ours |
| #404 org sync identity | `org_sync_adapter.py` (fork-modified) | ⚠️ Check overlap |
| #173 api_key length | `llm.py` (model), `increase_api_key_length` migration | 🟢 New model file, no conflict |
| #213 profile update | `auth.py` | 🟢 No conflict |
| #212 write_file JSON | `agent_tools.py` | 🔴 Already in our agent_tools scope |
| #184 WeCom stability | `wecom_stream.py`, `channel_user_service.py` | 🟢 New/modified files, no conflict |

**Action:** Review the #246 security fix specifically. If it patches something we care about (auth, registration), we need it.

---

## 4. Database Migrations

### v1.8.3-beta.2 adds:
- `add_a2a_async_enabled.py` — adds `a2a_async_enabled BOOLEAN DEFAULT FALSE` to `tenants`, drops from `agents`
  - Uses `ADD COLUMN IF NOT EXISTS` — idempotent ✅
  - Chains on `d9cbd43b62e5` which we already have ✅

### upstream/main adds (additional):
- `increase_api_key_length.py` — alters `api_keys.key` column length
- Potential changes to our existing migration files

### Pre-deploy steps:
```bash
# After merge, test migration on staging first
docker exec clawith-backend-1 alembic upgrade heads

# Verify a2a_async_enabled column exists
docker exec clawith-postgres-1 psql -U clawith -d clawith -c "\d tenants"
```

---

## 5. Execution Order

```
Step 1: git fetch upstream --tags --force
Step 2: git checkout -b merge/v1.8.3-upstream-main
Step 3: git merge --no-commit --no-ff upstream/main
Step 4: Resolve conflicts in order:
  4a. agentbay_control.py (_get_client 3-phase + browser_latest fix)
  4b. agent_tools.py (5 sub-conflicts + port new search tools)
  4c. websocket.py (verify session_id removal)
Step 5: Review #246 security fix changes
Step 6: git commit -m "merge: integrate upstream/main (includes v1.8.3-beta.2)"
Step 7: Test locally (docker compose up -d --build)
Step 8: Run alembic upgrade heads
Step 9: Smoke test on staging
Step 10: Deploy to production
```

---

## 6. Rollback Plan

If something goes wrong post-deploy:
```bash
# Revert the merge commit
git revert -m 1 <merge-commit-hash>
docker compose down && docker compose up -d --build
docker exec clawith-backend-1 alembic downgrade -1
```

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| agent_tools.py merge error | Medium | High | Careful line-by-line review, test all tool dispatch routes |
| agentbay_control.py browser_latest regression | Low | Medium | Test Take Control with both browser and computer env types |
| Migration conflict with our custom migration | Low | High | Test migration on staging first |
| A2A async feature enabled by mistake | Low | Medium | Default is FALSE, verify in DB after deploy |
| upstream/main security #246 breaks our auth | Low | High | Test login flow after merge |
