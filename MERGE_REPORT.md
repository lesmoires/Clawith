# 🔄 Merge Report: upstream/main → feature/upgrade-1.7.1

**Date:** 2026-03-24  
**Branch:** feature/upgrade-1.7.1  
**Source:** upstream/main (v1.7.1)  
**Status:** ✅ **COMPLETED**

---

## 📊 Summary

- **Total files merged:** 150+
- **Conflicts resolved:** 80+
- **Custom features preserved:** 5
- **Upstream improvements integrated:** 7

---

## 📁 Files Modified by Category

### Documentation (LOW Risk - Auto-resolved)
- ✅ README.md
- ✅ README_es.md, README_ja.md, README_ko.md, README_zh-CN.md
- ✅ .env.example (preserved Infisical + AgentMail config)
- ✅ .gitignore
- ✅ backend/VERSION, frontend/VERSION

### Backend API (MEDIUM Risk - Upstream accepted)
- ✅ backend/app/api/agents.py
- ✅ backend/app/api/atlassian.py
- ✅ backend/app/api/auth.py
- ✅ backend/app/api/chat_sessions.py
- ✅ backend/app/api/dingtalk.py
- ✅ backend/app/api/discord_bot.py
- ✅ backend/app/api/enterprise.py
- ✅ backend/app/api/feishu.py
- ✅ backend/app/api/files.py
- ✅ backend/app/api/notification.py
- ✅ backend/app/api/organization.py
- ✅ backend/app/api/pages.py (NEW from upstream)
- ✅ backend/app/api/plaza.py
- ✅ backend/app/api/skills.py
- ✅ backend/app/api/slack.py
- ✅ backend/app/api/teams.py
- ✅ backend/app/api/tenants.py
- ✅ backend/app/api/tools.py
- ✅ backend/app/api/upload.py
- ✅ backend/app/api/webhooks.py
- ✅ backend/app/api/wecom.py

### Backend Core (HIGH Risk - Manually merged)
- ✅ **backend/app/api/gateway.py** — Preserved WebSocket push + agent-to-agent routing
- ✅ **backend/app/api/websocket.py** — Upstream improvements (logger, participant tracking)
- ✅ **backend/app/main.py** — Preserved enterprise_info migration + logging config
- ✅ **backend/app/core/logging_config.py** (NEW from upstream)
- ✅ **backend/app/core/middleware.py** (NEW from upstream - TraceIdMiddleware)

### Backend Models (MEDIUM Risk - Upstream accepted)
- ✅ backend/app/models/agent.py
- ✅ backend/app/models/llm.py
- ✅ backend/app/models/notification.py
- ✅ backend/app/models/tenant.py
- ✅ backend/app/models/tenant_setting.py (NEW from upstream)
- ✅ backend/app/models/published_page.py (NEW from upstream)
- ✅ backend/app/schemas/schemas.py

### Backend Services (MEDIUM Risk - Upstream accepted)
- ✅ backend/app/services/activity_logger.py
- ✅ backend/app/services/agent_context.py
- ✅ backend/app/services/agent_manager.py
- ✅ backend/app/services/agent_seeder.py
- ✅ backend/app/services/agent_tools.py
- ✅ backend/app/services/audit_logger.py
- ✅ backend/app/services/autonomy_service.py
- ✅ backend/app/services/collaboration.py
- ✅ backend/app/services/dingtalk_stream.py
- ✅ backend/app/services/discord_gateway.py (NEW from upstream)
- ✅ backend/app/services/enterprise_sync.py
- ✅ backend/app/services/feishu_service.py
- ✅ backend/app/services/feishu_ws.py
- ✅ backend/app/services/heartbeat.py
- ✅ backend/app/services/llm_client.py
- ✅ backend/app/services/mcp_client.py
- ✅ backend/app/services/notification_service.py
- ✅ backend/app/services/org_sync_service.py
- ✅ backend/app/services/resource_discovery.py
- ✅ backend/app/services/scheduler.py
- ✅ backend/app/services/skill_seeder.py
- ✅ backend/app/services/supervision_reminder.py
- ✅ backend/app/services/task_executor.py
- ✅ backend/app/services/template_seeder.py
- ✅ backend/app/services/text_extractor.py
- ✅ backend/app/services/token_tracker.py
- ✅ backend/app/services/tool_seeder.py
- ✅ backend/app/services/trigger_daemon.py
- ✅ backend/app/services/wecom_stream.py

### Backend Alembic Migrations
- ✅ backend/alembic/versions/add_llm_max_output_tokens.py
- ✅ backend/alembic/versions/add_llm_temperature.py (NEW)
- ✅ backend/alembic/versions/add_notification_agent_id.py (NEW)
- ✅ backend/alembic/versions/add_published_pages.py (NEW)
- ✅ backend/alembic/versions/multi_tenant_registration.py

### Frontend (MEDIUM Risk - Upstream accepted)
- ✅ frontend/src/App.tsx
- ✅ frontend/src/components/ChannelConfig.tsx
- ✅ frontend/src/i18n/en.json, zh.json
- ✅ frontend/src/index.css
- ✅ frontend/src/pages/AdminCompanies.tsx
- ✅ frontend/src/pages/AgentCreate.tsx
- ✅ frontend/src/pages/AgentDetail.tsx
- ✅ frontend/src/pages/Chat.tsx
- ✅ frontend/src/pages/CompanySetup.tsx
- ✅ frontend/src/pages/Dashboard.tsx
- ✅ frontend/src/pages/EnterpriseSettings.tsx
- ✅ frontend/src/pages/InvitationCodes.tsx
- ✅ frontend/src/pages/Layout.tsx
- ✅ frontend/src/pages/Login.tsx
- ✅ frontend/src/pages/OpenClawSettings.tsx (NEW from upstream)
- ✅ frontend/src/pages/Plaza.tsx
- ✅ frontend/src/pages/UserManagement.tsx
- ✅ frontend/src/services/api.ts
- ✅ frontend/VERSION
- ✅ frontend/nginx.conf

### Infrastructure (HIGH Risk - Manually merged)
- ✅ **docker-compose.yml** — Preserved Coolify network + Supergateway + Infisical
- ✅ backend/Dockerfile
- ✅ backend/entrypoint.sh
- ✅ backend/pyproject.toml
- ✅ restart.sh

### Custom Features (PRESERVED)
- ✅ backend/app/tools/agentmail_tools.py
- ✅ backend/app/skills/infisical_secrets.py

---

## 🚀 Push Status

```bash
✅ Pushed to origin/feature/upgrade-1.7.1
   Commit: 1b68e5fd35
```

---

## 📝 Next Steps

1. **Test locally:** Run `docker-compose up` to verify all services start
2. **Run migrations:** Check alembic migrations apply cleanly
3. **Test custom features:** Verify Infisical, AgentMail, WebSocket work
4. **Create PR:** Open PR to merge feature/upgrade-1.7.1 → main

---

*Generated by Git Merge Specialist*
