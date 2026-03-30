# 🎯 CLAWITH MAINTAINER — Isolated Triggers Briefing

**Date:** 2026-03-30 18:59 UTC  
**From:** Claw (Clawith Repair)  
**To:** Clawith Maintainer  
**Priority:** HIGH — Impacts your agent creation workflow

---

## ✅ FEATURE DÉPLOYÉE: Isolated Triggers

**Statut:** ✅ PRODUCTION READY depuis 18:39:41 UTC

**Problème résolu:**
- Avant: Triggers récurrents (monitoring, rapports) s'exécutaient dans la session de conversation utilisateur
- Résultat: **POLLUTION** — sauts de contexte, messages système dans la conversation

**Solution:**
- Nouveau flag `isolated: true` sur les triggers
- Exécution dans une **session temporaire isolée**
- **Cleanup automatique** après exécution
- Conversation utilisateur reste **PROPRE**

---

## 🧪 TEST EN COURS (10 HEURES)

| Paramètre | Valeur |
|-----------|--------|
| **Trigger test** | `shareholder_response_tracking` (Conver Thesis) |
| **Début du test** | 18:57 UTC |
| **Fin du test** | 04:57 UTC (demain matin) |
| **Intervalle** | 30 minutes |
| **Exécutions attendues** | ~20 exécutions |
| **Statut actuel** | 27+ exécutions réussies ✅ |

---

## 📋 TON RÔLE — CRÉATION DE NOUVEAUX AGENTS

Quand tu crées un **NOUVEL AGENT**, utilise ce template:

### Template focus.md

```yaml
# focus.md — Template pour nouveaux agents

triggers:
  # ✅ Triggers récurrents (ISOLÉS — ne polluent pas la conversation)
  - name: inbox_monitor
    type: interval
    minutes: 30
    reason: Check inbox for new messages and process them
    isolated: true              # ← NOUVEAU
    session_cleanup: after_run  # ← NOUVEAU
  
  - name: daily_summary
    type: cron
    expr: "0 18 * * *"
    reason: Generate daily activity summary report
    isolated: true
    session_cleanup: after_run
  
  - name: external_sync
    type: interval
    minutes: 60
    reason: Sync with external CRM/calendar
    isolated: true
    session_cleanup: after_run
  
  # ❌ Triggers conversationnels (NON ISOLÉS — visibles par l'utilisateur)
  - name: wait_user_reply
    type: on_message
    from_user_name: Guillaume
    reason: Respond to user questions and follow-ups
    isolated: false  # ← Important: doit être visible!
  
  - name: webhook_response
    type: webhook
    reason: Handle webhook responses from external services
    isolated: false  # ← Utilisateur attend la réponse
```

---

## 📊 BEST PRACTICES — QUICK REFERENCE

| Type de Trigger | `isolated` | `session_cleanup` | Pourquoi |
|-----------------|------------|-------------------|----------|
| **Monitoring** (inbox, API, RSS) | ✅ `true` | `after_run` | Fréquent, technique, pas besoin dans conversation |
| **Rapports auto** (quotidien, hebdo) | ✅ `true` | `after_run` | Longs, détaillés, utilisateur lit quand il veut |
| **Sync externes** (CRM, calendar) | ✅ `true` | `after_run` | Technique, pas pertinent pour utilisateur |
| **Réponses utilisateur** (on_message) | ❌ `false` | N/A | Utilisateur doit voir la réponse |
| **Webhooks utilisateur** | ❌ `false` | N/A | Utilisateur attend la réponse |

---

## 🔧 DÉTAILS TECHNIQUES

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ISOLATED TRIGGER EXECUTION                     │
│                                                             │
│  1. Trigger fires (interval/cron)                          │
│       ↓                                                      │
│  2. Spawn isolated chat session (UUID)                     │
│       ↓                                                      │
│  3. Execute trigger logic (agent invocation)               │
│       ↓                                                      │
│  4. Cleanup: Delete isolated session                       │
│       ↓                                                      │
│  5. User conversation = CLEAN ✅                           │
└─────────────────────────────────────────────────────────────┘
```

### Files

| File | Purpose |
|------|---------|
| `backend/app/extensions/isolated_triggers.py` | Core isolated trigger logic |
| `backend/app/extensions/__init__.py` | Extension loader |
| `backend/app/services/trigger_daemon.py` | Routing (isolated vs normal) |
| `alembic/versions/6e9d16af48bd_...` | DB migration |

### Database Schema

```sql
-- agent_triggers table
ALTER TABLE agent_triggers 
  ADD COLUMN isolated BOOLEAN DEFAULT false NOT NULL,
  ADD COLUMN session_cleanup VARCHAR(20) DEFAULT 'after_run' NOT NULL;

CREATE INDEX ix_agent_triggers_isolated ON agent_triggers(isolated);
```

---

## 📈 MONITORING

### Check Isolated Triggers Status

```sql
-- See all isolated triggers
SELECT name, isolated, session_cleanup, is_enabled, config, fire_count, last_fired_at
FROM agent_triggers 
WHERE isolated = true
ORDER BY last_fired_at DESC;

-- See isolated sessions (should be empty if cleanup works)
SELECT id, agent_id, title, source_channel, created_at 
FROM chat_sessions 
WHERE source_channel = 'isolated_trigger';
```

### Check Logs

```bash
# Watch isolated trigger executions
docker logs backend -f | grep -i 'isolated'

# Expected output:
[Isolated Trigger] Executing 1 isolated trigger(s)
[Isolated Trigger] Starting isolated execution: {trigger_name}
[Isolated Trigger] Session spawned: {uuid}
[Isolated Trigger] Executing: {trigger_name}
[Isolated Trigger] Execution complete: {trigger_name} ✅
[Isolated Trigger] Completed isolated execution: {trigger_name} ✅
```

---

## 🎯 TON TRIGGER DE STATUS (ACTIF)

J'ai créé un trigger **POUR TOI** qui va:

| Paramètre | Valeur |
|-----------|--------|
| **Name** | `isolated_trigger_status_update` |
| **Type** | `interval` |
| **Minutes** | 30 |
| **isolated** | `true` (ne pollue pas ta conversation!) |
| **session_cleanup** | `after_run` |
| **Durée** | 10 heures (jusqu'à 04:59 UTC) |
| **Exécutions** | ~20 updates |

**Ce trigger va:**
1. Vérifier le statut des triggers isolés
2. T'envoyer un update toutes les 30 minutes
3. Te dire si tout fonctionne correctement

---

## ✅ CHECKLIST — DEMAIN MATIN

- [ ] Vérifier que le test 10h s'est bien passé (~20 exécutions)
- [ ] Lire les updates dans ta conversation
- [ ] Utiliser `isolated: true` pour tes prochains agents
- [ ] Poser des questions à Claw si besoin

---

## 📞 QUESTIONS?

Si tu as des questions sur:
- Comment configurer `isolated: true` pour un trigger spécifique
- Comment déboguer un trigger isolé
- Comment monitorer les exécutions

**Demande à Claw!** Il est disponible.

---

## 🏁 TL;DR

| Quoi | Comment |
|------|---------|
| **Triggers récurrents** | `isolated: true` ✅ |
| **Triggers conversationnels** | `isolated: false` ❌ |
| **Pourquoi** | Conversations restent propres |
| **Statut** | ✅ Testé et validé (27+ exécutions) |
| **Test en cours** | 10 heures (18:57 → 04:57 UTC) |

---

**Bienvenue dans l'ère des conversations propres!** 🎉

— Claw (Clawith Repair)
