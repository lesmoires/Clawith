# Clawith Documentation

Welcome to the Clawith documentation hub. This directory contains technical guides, best practices, and feature documentation.

---

## 📚 FEATURE DOCUMENTATION

### Core Features

| Document | Description | Status |
|----------|-------------|--------|
| **[ISOLATED_TRIGGERS.md](./ISOLATED_TRIGGERS.md)** | Clean conversations for AI agents with isolated trigger execution | ✅ Production |
| **AGENTMAIL_TOOLS_DOCUMENTATION.md** | AgentMail MCP integration guide | ✅ Production |
| **AGENTMAIL_MCP_SERVER_COMPARISON.md** | AgentMail MCP server analysis | ✅ Reference |

### Architecture

| Document | Description | Status |
|----------|-------------|--------|
| **ARCHITECTURE_SPEC.md** | System architecture specification | ✅ Reference |
| **AGENTS_REGISTRY.md** | Agent registration and configuration | ✅ Reference |
| **BRANCHING_STRATEGY.md** | Git branching and release strategy | ✅ Active |

---

## 🛠️ OPERATIONAL GUIDES

### Troubleshooting

| Document | Description | Use Case |
|----------|-------------|----------|
| **BACKEND_CRASH_LOOP_FIX.md** | Backend crash loop resolution | Incident response |
| **CLAWITH_FIX_REPORT.md** | Comprehensive fix report | Post-mortem |
| **CLAWITH_ROOT_CAUSE_ANALYSIS.md** | Root cause analysis methodology | Investigation |

### Best Practices

| Document | Description | Audience |
|----------|-------------|----------|
| **BACKUP_CHECKLIST.md** | Backup procedures and verification | Operations |
| **CLEANUP_PLAN.md** | System cleanup procedures | Operations |
| **CONFLICTS_RESOLVED.md** | Conflict resolution patterns | Developers |

---

## 📋 AGENT GUIDES

### For Agent Creators

| Document | Description | Priority |
|----------|-------------|----------|
| **CLAWITH_MAINTAINER_ISOLATED_TRIGGER_BRIEFING.md** | Using isolated triggers in new agents | 🔴 HIGH |
| **CLAWITH_MAINTAINER_STATUS.md** | Maintainer role and responsibilities | 🔴 HIGH |
| **CLAWITH_MAINTAINER_HANDOFF.md** | Handoff procedures | Medium |

### For Agent Operators

| Document | Description | Priority |
|----------|-------------|----------|
| **AGENT_COMMUNICATIONS_PLAN.md** | Inter-agent communication patterns | Medium |
| **CONVER_THESIS_AGENTMAIL_AUDIT.md** | Case study: Conver Thesis setup | Reference |
| **CONVER_THESIS_KNOWLEDGE_TRANSFER_AUDIT.md** | Knowledge transfer procedures | Reference |

---

## 🔧 TECHNICAL REFERENCES

### Configuration

| Document | Description | Link |
|----------|-------------|------|
| **CLAWITH_API_NOTES.md** | API reference and notes | [View](../CLAWITH_API_NOTES.md) |
| **CLAWITH_MANUAL.md** | User manual | [View](../CLAWITH_MANUAL.md) |

### Investigation Reports

| Document | Description | Date |
|----------|-------------|------|
| **CLAWITH_FEATURE_BRANCH_INVESTIGATION.md** | Feature branch analysis | 2026-03-26 |
| **CLAWITH_SSH_INVESTIGATION_GUIDE.md** | SSH access investigation | 2026-03-26 |
| **CLAWITH_STABILITY_ANALYSIS.md** | System stability analysis | 2026-03-28 |
| **CLAWITH_WRONG_BRANCH_CRITICAL.md** | Critical branch issue | 2026-03-26 |

---

## 🚨 INCIDENT REPORTS

| Document | Date | Severity | Status |
|----------|------|----------|--------|
| **SECURITY_INCIDENT_2026-03-30.md** | 2026-03-30 | HIGH | ✅ Contained |
| **CLAWITH_ALERT.md** | 2026-03-23 | MEDIUM | ✅ Resolved |
| **CLAWITH_STABILITY_CHECK_2026-03-26.md** | 2026-03-26 | LOW | ✅ Resolved |

---

## 📝 MEMORY & LOGS

Daily session logs and memory files are stored in:

```
/memory/
├── 2026-03-23.md
├── 2026-03-24.md
├── 2026-03-25.md
├── 2026-03-27.md
├── 2026-03-28.md
├── 2026-03-29.md
└── 2026-03-30.md  ← Isolated Triggers implementation
```

---

## 🎯 QUICK START

### For New Contributors

1. Read **[ARCHITECTURE_SPEC.md](./ARCHITECTURE_SPEC.md)** — System overview
2. Read **[BRANCHING_STRATEGY.md](./BRANCHING_STRATEGY.md)** — Git workflow
3. Read **[ISOLATED_TRIGGERS.md](./ISOLATED_TRIGGERS.md)** — Latest feature

### For Agent Creators

1. Read **[CLAWITH_MAINTAINER_ISOLATED_TRIGGER_BRIEFING.md](./CLAWITH_MAINTAINER_ISOLATED_TRIGGER_BRIEFING.md)** — Best practices
2. Review **[AGENTS_REGISTRY.md](./AGENTS_REGISTRY.md)** — Agent configuration
3. Check **[AGENTMAIL_TOOLS_DOCUMENTATION.md](./AGENTMAIL_TOOLS_DOCUMENTATION.md)** — MCP tools

### For Operations

1. Review **[BACKUP_CHECKLIST.md](./BACKUP_CHECKLIST.md)** — Backup procedures
2. Check **[CLEANUP_PLAN.md](./CLEANUP_PLAN.md)** — Maintenance tasks
3. Monitor incident reports above

---

## 📞 SUPPORT

- **Documentation Issues:** Open GitHub issue
- **Feature Questions:** Contact Clawith Maintainer
- **Incidents:** Check incident reports above

---

**Last Updated:** 2026-03-30 19:05 UTC  
**Maintained By:** Clawith Team
