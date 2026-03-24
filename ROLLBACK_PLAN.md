# Rollback Plan: Clawith v1.7.1 → v1.7.0

**Date:** 24 mars 2026  
**Urgence:** Procédure d'urgence  
**Temps estimé:** 10-15 minutes (rollback complet)

---

## 🚨 Quand Rollback?

**Déclencheurs:**
- ❌ Backend ne démarre pas après upgrade
- ❌ DB corrompue ou migrations échouées
- ❌ Features custom critiques broken (Gateway API, MCP, AgentMail)
- ❌ Performance degradation > 50%
- ❌ Errors critiques en production (> 10% error rate)
- ❌ WebSocket ne fonctionne plus
- ❌ Perte de données détectée

**Ne PAS rollback pour:**
- ✅ Bugs UI mineurs
- ✅ Traductions manquantes
- ✅ Performance < 10% degradation
- ✅ Features upstream non-critiques

---

## 📋 Prérequis (À Préparer AVANT Upgrade)

### 1. Backup DB

**Avant upgrade, exécuter:**
```bash
cd /data/workspace/clawith-fork

# Backup complet DB
docker exec clawith-postgres-1 pg_dump -U clawith clawith > backup_pre_upgrade_$(date +%Y%m%d_%H%M%S).sql

# Vérifier backup
ls -lh backup_pre_upgrade_*.sql
wc -l backup_pre_upgrade_*.sql  # Doit être > 0 lignes
```

**Stockage:**
- Local: `/data/workspace/clawith-fork/backups/`
- Remote: SCP vers serveur backup
- Cloud: Upload S3/Infisical vault

---

### 2. Snapshot Git

```bash
# Tag version actuelle
git tag -a v1.7.0-pre-upgrade -m "Pre-upgrade snapshot $(date)"
git push origin v1.7.0-pre-upgrade

# Noter commit hash
git rev-parse HEAD > .rollback_commit.txt
```

---

### 3. Snapshot VM/Serveur

**Si Coolify/Hetzner:**
- Créer snapshot manuel avant upgrade
- Noter snapshot ID pour restore rapide

**Commande Hetzner:**
```bash
hcloud server create-image --name clawith-backup-$(date +%Y%m%d) <server-id>
```

---

### 4. Export Configs Custom

```bash
# Backup docker-compose.yml custom
cp docker-compose.yml docker-compose.yml.backup

# Backup env vars
docker compose config > .docker-env-backup.txt

# Backup MCP configs
cp mcp_hetzner_config.json mcp_hetzner_config.json.backup 2>/dev/null
cp -r backend/app/tools/ backend_app_tools.backup/ 2>/dev/null
cp -r backend/app/skills/ backend_app_skills.backup/ 2>/dev/null
```

---

## 🔄 Procédure de Rollback

### Option A: Rollback Complet (Recommandé)

**Temps:** 10-15 minutes  
**Risque:** Faible (retour à état connu)

#### Étape 1: Stop Services (1 min)

```bash
cd /data/workspace/clawith-fork
docker compose down
```

**Vérifier:**
```bash
docker compose ps  # Doit être vide
```

---

#### Étape 2: Restore Code (2 min)

```bash
# Option 1: Git checkout (si branche encore disponible)
git checkout v1.7.0

# Option 2: Git reset (si merge déjà fait)
git reset --hard v1.7.0-pre-upgrade

# Option 3: Restore from backup files
rm -rf backend frontend
tar -xzf clawith-backup-v1.7.0.tar.gz
```

**Vérifier:**
```bash
cat backend/VERSION  # Doit afficher: 1.7.0
git status  # Doit être clean
```

---

#### Étape 3: Restore DB (5 min)

```bash
# Lister backups disponibles
ls -lth backup_pre_upgrade_*.sql | head -5

# Restore dernier backup
docker exec -i clawith-postgres-1 psql -U clawith clawith < backup_pre_upgrade_20260324_*.sql

# Vérifier restore
docker exec clawith-postgres-1 psql -U clawith -c "SELECT COUNT(*) FROM agents;"
docker exec clawith-postgres-1 psql -U clawith -c "SELECT COUNT(*) FROM chat_sessions;"
```

**Si erreurs:**
```bash
# Drop et recréer DB
docker exec clawith-postgres-1 psql -U clawith -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i clawith-postgres-1 psql -U clawith clawith < backup_pre_upgrade_*.sql
```

---

#### Étape 4: Restore Configs Custom (2 min)

```bash
# Restore docker-compose custom
cp docker-compose.yml.backup docker-compose.yml

# Restore MCP tools
cp -r backend_app_tools.backup/* backend/app/tools/ 2>/dev/null
cp -r backend_app_skills.backup/* backend/app/skills/ 2>/dev/null

# Restore env vars
# (Via Coolify UI ou docker-compose.yml)
```

---

#### Étape 5: Redémarrer Services (3 min)

```bash
# Rebuild backend (au cas où)
docker compose build backend

# Start services
docker compose up -d

# Wait for health
sleep 30

# Check status
docker compose ps
```

**Attendre:**
- ✅ postgres: healthy
- ✅ redis: healthy
- ✅ backend: healthy
- ✅ frontend: running

---

#### Étape 6: Validation (5 min)

```bash
# Check logs
docker compose logs backend --tail 50 | grep -i error

# Test API
curl https://clawith.your-domain.com/api/health

# Test frontend
curl -I https://clawith.your-domain.com

# Test WebSocket (manuel via browser)
```

**Checklist:**
- [ ] Backend logs propres (pas d'erreurs critiques)
- [ ] Frontend charge correctement
- [ ] Login fonctionne
- [ ] Version affiche 1.7.0
- [ ] Features custom fonctionnent (Gateway, MCP, AgentMail)

---

### Option B: Partial Rollback (Fichiers Spécifiques)

**Temps:** 5-10 minutes  
**Usage:** Si seulement certains fichiers posent problème

#### Exemple: Rollback Gateway API

```bash
# Restore fichier spécifique
git checkout v1.7.0 -- backend/app/api/gateway.py

# Rebuild backend
docker compose build backend

# Restart backend seulement
docker compose up -d backend

# Test
docker compose logs backend --tail 50
```

#### Exemple: Rollback Logging

```bash
# Revert logging changes dans tous les services
cd backend/app/services
for file in *.py; do
  git checkout v1.7.0 -- $file
done

# Rebuild
docker compose build backend
docker compose up -d backend
```

---

### Option C: Database-Only Rollback

**Temps:** 5 minutes  
**Usage:** Si code OK mais DB corrompue

```bash
# Stop backend seulement
docker compose stop backend

# Restore DB
docker exec -i clawith-postgres-1 psql -U clawith clawith < backup_pre_upgrade_*.sql

# Restart backend
docker compose start backend

# Verify
docker compose logs backend --tail 50
```

---

## 🧪 Validation Post-Rollback

### Tests Critiques

```bash
# 1. Health check
curl https://clawith.your-domain.com/api/health
# Expected: {"status":"ok","version":"1.7.0"}

# 2. Login test (manuel)
# - Ouvrir frontend
# - Login avec compte admin
# - Vérifier dashboard accessible

# 3. Agent creation (manuel)
# - Créer agent test
# - Vérifier agent listé

# 4. Chat test (manuel)
# - Chat avec agent
# - Vérifier réponse reçue

# 5. Gateway API test (custom feature)
curl -X POST https://clawith.your-domain.com/api/gateway/messages \
  -H "X-Api-Key: <test-key>" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "content": "Test"}'

# 6. WebSocket test (manuel)
# - Ouvrir 2 onglets
# - Envoyer message
# - Vérifier temps réel

# 7. MCP tools test (custom feature)
# - Tester Infisical secret retrieval
# - Tester AgentMail send/receive
```

---

### Performance Checks

```bash
# API response time
curl -w "@curl-format.txt" -o /dev/null -s https://clawith.your-domain.com/api/health

# Expected:
# time_total: < 0.5s

# DB connections
docker exec clawith-postgres-1 psql -U clawith -c "SELECT count(*) FROM pg_stat_activity;"

# Expected: < 50 connections

# Memory usage
docker stats clawith-backend-1 --no-stream

# Expected: < 1GB RAM
```

---

## 🚨 Troubleshooting Rollback

### Problème: DB Restore Échoue

**Symptôme:**
```
ERROR:  relation "agents" does not exist
```

**Solution:**
```bash
# Drop complet DB
docker exec clawith-postgres-1 psql -U clawith -c "DROP DATABASE clawith WITH (FORCE);"
docker exec clawith-postgres-1 psql -U clawith -c "CREATE DATABASE clawith;"

# Restore
docker exec -i clawith-postgres-1 psql -U clawith clawith < backup.sql

# Re-run migrations
docker exec clawith-backend-1 alembic upgrade head
```

---

### Problème: Backend Ne Démarre Pas

**Symptôme:**
```
backend exited with code 1
```

**Diagnostic:**
```bash
docker compose logs backend --tail 100
```

**Solutions:**

**1. Dependency missing:**
```bash
docker compose build --no-cache backend
docker compose up -d backend
```

**2. DB connection failed:**
```bash
# Check DB healthy
docker compose ps postgres

# Test connection
docker exec backend python -c "from app.database import engine; import asyncio; asyncio.run(engine.connect())"
```

**3. Config error:**
```bash
# Check env vars
docker compose config

# Compare with backup
diff docker-compose.yml docker-compose.yml.backup
```

---

### Problème: Features Custom Broken

**Symptôme:**
```
ModuleNotFoundError: No module named 'app.tools.agentmail_tools'
```

**Solution:**
```bash
# Restore custom tools
cp -r backend_app_tools.backup/* backend/app/tools/

# Rebuild
docker compose build backend
docker compose up -d backend
```

---

### Problème: WebSocket Ne Fonctionne Plus

**Symptôme:**
```
WebSocket connection failed
```

**Diagnostic:**
```bash
# Check backend logs
docker compose logs backend | grep -i websocket

# Check nginx config
docker exec frontend nginx -t
```

**Solution:**
```bash
# Restore websocket.py
git checkout v1.7.0 -- backend/app/api/websocket.py

# Rebuild
docker compose build backend
docker compose up -d backend
```

---

## 📞 Escalation

**Si rollback échoue:**

### Niveau 1: Auto-Restore (10 min)

```bash
# Full reset
docker compose down -v  # Attention: supprime volumes!
git reset --hard v1.7.0
docker compose up -d
```

---

### Niveau 2: Manual Restore (30 min)

```bash
# Restore from VM snapshot (Hetzner/Coolify)
hcloud server attach-image <server-id> <backup-image-id>
hcloud server reboot <server-id>

# Wait for boot (~5 min)
# Verify services
```

---

### Niveau 3: Emergency Support

**Contacts:**
- Guillaume (Président UPentreprise)
- Ranga (CTO)
- VirtualGX Team (DevOps)

**Informations à fournir:**
- Timestamp upgrade started
- Error messages exactes
- Logs backend (last 100 lines)
- Backup file utilisé
- Rollback steps déjà tentés

---

## ✅ Post-Rollback Actions

### 1. Incident Report

**Documenter:**
- [ ] Heure rollback
- [ ] Raison rollback
- [ ] Steps exécutés
- [ ] Temps total downtime
- [ ] Impact utilisateurs
- [ ] Lessons learned

**Template:**
```markdown
# Incident Report: Rollback v1.7.1 → v1.7.0

**Date:** 2026-03-24
**Duration:** 15 minutes
**Impact:** Service indisponible pendant rollback

## Root Cause
[Description du problème]

## Actions Taken
1. Stop services
2. Restore code v1.7.0
3. Restore DB from backup
4. Restart services
5. Validation tests

## Prevention
[Comment éviter à l'avenir]
```

---

### 2. Team Notification

**Message template:**
```
🚨 ROLLBACK COMPLETE

Clawith a été rollbacké vers v1.7.0 suite à [raison].

✅ Status: Tous services opérationnels
⏰ Downtime: 15 minutes
📋 Next steps: Investigation en cours

Contact: @Guillaume pour questions
```

---

### 3. Backup Cleanup

```bash
# Garder derniers 5 backups
ls -t backup_pre_upgrade_*.sql | tail -n +6 | xargs rm

# Compress old backups
for file in backup_pre_upgrade_*.sql; do
  gzip $file
done

# Upload to remote storage
scp backup_pre_upgrade_*.sql.gz backup-server:/backups/clawith/
```

---

### 4. Plan Next Upgrade

**Review:**
- [ ] Pourquoi upgrade a échoué?
- [ ] Quels tests manquaient?
- [ ] Comment améliorer procédure?
- [ ] Quand retry upgrade?

**Actions:**
- [ ] Update MERGE_STRATEGY.md avec lessons learned
- [ ] Ajouter tests automatisés pour features custom
- [ ] Setup staging environment obligatoire
- [ ] Planifier next upgrade window

---

## 📊 Rollback Decision Tree

```
Upgrade échoue?
    │
    ├─→ Backend crash?
    │       ├─→ Logs montrent DB error? → Rollback DB (Option C)
    │       └─→ Logs montrent code error? → Rollback fichier (Option B)
    │
    ├─→ Features custom broken?
    │       ├─→ Gateway API? → Rollback gateway.py (Option B)
    │       ├─→ MCP tools? → Restore tools/ (Option B)
    │       └─→ AgentMail? → Restore agentmail_tools.py (Option B)
    │
    ├─→ Performance degradation?
    │       ├─→ > 50%? → Rollback complet (Option A)
    │       └─→ < 50%? → Monitor + fix hotfix
    │
    └─→ DB corrompue?
            └─→ Rollback DB + Code (Option A)
```

---

## 🎯 Checklist Rollback

**Préparation (AVANT upgrade):**
- [ ] Backup DB complété
- [ ] Backup DB vérifié (taille > 0)
- [ ] Git tag pre-upgrade créé
- [ ] Snapshot VM créé
- [ ] Configs custom exportées
- [ ] Équipe notifiée (upgrade en cours)

**Exécution (PENDANT rollback):**
- [ ] Services stoppés
- [ ] Code restauré v1.7.0
- [ ] DB restaurée from backup
- [ ] Configs custom restaurées
- [ ] Services redémarrés
- [ ] Health checks pass

**Validation (APRÈS rollback):**
- [ ] Backend logs propres
- [ ] Frontend accessible
- [ ] Login fonctionne
- [ ] Version = 1.7.0
- [ ] Features custom OK
- [ ] Performance normale
- [ ] Équipe notifiée (rollback complete)

**Post-Mortem:**
- [ ] Incident report écrit
- [ ] Team notification envoyée
- [ ] Backups cleanup
- [ ] Lessons learned documentés
- [ ] Next upgrade planifié

---

**Plan créé par Claw - 24 mars 2026**
