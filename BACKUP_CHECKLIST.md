# BACKUP CHECKLIST — Clawith Fork Cleanup

**Date:** 24 mars 2026  
**Préparé par:** Claw (Code Audit Lead)  
**Objectif:** Zero data loss pendant cleanup

---

## 📋 Pre-Cleanup Checklist

### 1. Backup Database PostgreSQL ⭐ CRITIQUE

**Commande:**
```bash
# Créer backup timestampé
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_$(date +%Y%m%d_%H%M%S).sql

# Vérifier backup
ls -lh backup_*.sql
wc -l backup_*.sql
head -20 backup_*.sql
```

**Validation:**
- [ ] Fichier créé (taille > 0)
- [ ] Contient CREATE TABLE
- [ ] Contient INSERT INTO
- [ ] Taille attendue: ~10-100 MB (selon données)

**Stockage:**
- **Location:** `/data/workspace/clawith-fork/backups/`
- **Retention:** 30 jours minimum
- **Rotation:** Supprimer backups > 30 jours

**Optionnel - Backup cloud:**
```bash
# AWS S3
aws s3 cp backup_*.sql s3://moiria-backups/clawith/$(date +%Y%m%d)/

# Ou rsync vers serveur distant
rsync -avz backup_*.sql user@backup-server:/backups/clawith/
```

---

### 2. Backup Git (Tags + Branches) ⭐ CRITIQUE

**Commande:**
```bash
cd /data/workspace/clawith-fork

# Créer tag de backup
git tag backup/pre-cleanup-$(date +%Y%m%d)

# Push tag vers remote
git push origin backup/pre-cleanup-$(date +%Y%m%d)

# Vérifier tag
git tag -l "backup/*"
git show backup/pre-cleanup-$(date +%Y%m%d) --stat
```

**Validation:**
- [ ] Tag créé localement
- [ ] Tag pushé vers remote (GitHub/GitLab)
- [ ] Tag visible sur GitHub UI

**Alternative - Branche de backup:**
```bash
# Créer branche de backup
git checkout -b backup/pre-cleanup-$(date +%Y%m%d)
git push origin backup/pre-cleanup-$(date +%Y%m%d)
```

---

### 3. Backup Docker Compose ⭐ IMPORTANT

**Commande:**
```bash
cd /data/workspace/clawith-fork

# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d)

# Backup .env (si existe)
if [ -f .env ]; then
  cp .env .env.backup.$(date +%Y%m%d)
fi

# Vérifier backups
ls -lh docker-compose.yml.* .env.*
```

**Validation:**
- [ ] docker-compose.yml.backup.* créé
- [ ] .env.backup.* créé (si .env existe)
- [ ] Contient mêmes lignes que original

**Optionnel - Export env vars depuis Coolify:**
1. Aller sur Coolify Dashboard
2. Project → Clawith → Variables
3. Export → Download .env
4. Stocker avec backup

---

### 4. Backup Custom Files ⭐ IMPORTANT

**Fichiers custom à backup:**
```bash
cd /data/workspace/clawith-fork

# Créer dossier backup custom
mkdir -p backups/custom-files

# Backup AgentMail
cp backend/app/tools/agentmail_tools.py backups/custom-files/

# Backup Infisical
cp backend/app/skills/infisical_secrets.py backups/custom-files/
cp backend/app/tools/infisical_secret.py backups/custom-files/

# Backup Gateway API (modifié)
cp backend/app/api/gateway.py backups/custom-files/

# Backup main.py (modifié)
cp backend/app/main.py backups/custom-files/

# Vérifier
ls -lh backups/custom-files/
```

**Validation:**
- [ ] 5 fichiers backupés
- [ ] Tailles correspondent aux originaux

---

### 5. Snapshot VM/Serveur ⭐ RECOMMANDÉ

**Si Hetzner Cloud:**

1. **Via Console:**
   - Aller sur Hetzner Cloud Console
   - Servers → claw-family.in-mum-01
   - Actions → Create Snapshot
   - Nom: `clawith-pre-cleanup-$(date +%Y%m%d)`
   - Attendre complétion (~5-10 min)

2. **Via CLI (hcloud):**
```bash
hcloud server create-image claw-family.in-mum-01 \
  --type snapshot \
  --description "clawith-pre-cleanup-$(date +%Y%m%d)"
```

**Validation:**
- [ ] Snapshot créé
- [ ] Visible dans Hetzner Console
- [ ] Taille raisonnable (~10-50 GB)

---

### 6. Backup Configs Custom

**Infisical Config:**
```bash
# Si fichier config Infisical existe
if [ -f /data/ss-nodes.json ]; then
  cp /data/ss-nodes.json backups/ss-nodes.json.backup
fi
```

**Coolify Config:**
- Exporter depuis Coolify Dashboard
- Project → Settings → Export Configuration

**Traefik Config (si applicable):**
```bash
# Si Traefik config mounté
docker exec traefik cat /etc/traefik/traefik.yml > backups/traefik.yml.backup
```

---

## 📊 Backup Verification

### Checklist de Validation

| Backup | Fichier | Taille | Validé |
|--------|---------|--------|--------|
| **DB PostgreSQL** | `backup_YYYYMMDD_HHMMSS.sql` | ~XX MB | [ ] |
| **Git Tag** | `backup/pre-cleanup-YYYYMMDD` | N/A | [ ] |
| **Docker Compose** | `docker-compose.yml.backup` | ~4 KB | [ ] |
| **Env Vars** | `.env.backup` (si existe) | ~1 KB | [ ] |
| **Custom Files** | `backups/custom-files/` (5 fichiers) | ~20 KB | [ ] |
| **VM Snapshot** | `clawith-pre-cleanup-YYYYMMDD` | ~XX GB | [ ] |

---

## 🧪 Test Restore (Recommandé)

### Test 1: Restore DB (sur environnement de test)

```bash
# Créer DB de test
docker exec clawith-backend-postgres-1 psql -U clawith -c \
  "CREATE DATABASE clawith_test;"

# Restore dans test
cat backup_*.sql | docker exec -i clawith-backend-postgres-1 psql -U clawith clawith_test

# Vérifier
docker exec clawith-backend-postgres-1 psql -U clawith clawith_test -c \
  "SELECT COUNT(*) FROM users;"

# Cleanup test
docker exec clawith-backend-postgres-1 psql -U clawith -c \
  "DROP DATABASE clawith_test;"
```

**Validation:**
- [ ] Restore sans erreurs
- [ ] Tables créées
- [ ] Données présentes

---

### Test 2: Git Restore

```bash
# Créer branche test depuis tag
git checkout -b test/restore backup/pre-cleanup-YYYYMMDD

# Vérifier fichiers custom
ls backend/app/tools/agentmail_tools.py
ls backend/app/skills/infisical_secrets.py

# Retourner à branche principale
git checkout merge/v1.7.1

# Supprimer branche test
git branch -D test/restore
```

**Validation:**
- [ ] Checkout tag réussi
- [ ] Fichiers custom présents
- [ ] Retour à branche principale OK

---

## 📝 Backup Log

```
Date: YYYY-MM-DD HH:MM
Opérateur: [Nom]

Backups créés:
[ ] DB PostgreSQL: backup_YYYYMMDD_HHMMSS.sql (XX MB)
[ ] Git Tag: backup/pre-cleanup-YYYYMMDD
[ ] Docker Compose: docker-compose.yml.backup
[ ] Env Vars: .env.backup (si applicable)
[ ] Custom Files: 5 fichiers dans backups/custom-files/
[ ] VM Snapshot: clawith-pre-cleanup-YYYYMMDD (XX GB)

Stockage:
- Local: /data/workspace/clawith-fork/backups/
- Cloud: s3://moiria-backups/clawith/YYYYMMDD/
- Snapshot: Hetzner Cloud Console

Validation:
- [ ] Tous les backups vérifiés
- [ ] Test restore DB réussi (optionnel)
- [ ] Test restore Git réussi (optionnel)
- [ ] Prêt pour cleanup

Notes:
_______________________________________________
_______________________________________________
```

---

## 🔄 Restore Procedures

### Emergency Restore (si cleanup échoue)

**Scenario: Merge cassé, backend ne démarre plus**

```bash
# 1. Stop services
docker-compose down

# 2. Git rollback
cd /data/workspace/clawith-fork
git checkout main
git reset --hard backup/pre-cleanup-YYYYMMDD
git push origin main --force

# 3. Restore DB (si corruption)
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i clawith-backend-postgres-1 psql -U clawith clawith

# 4. Restart
docker-compose up -d

# 5. Vérifier
docker logs clawith-backend | tail -50
curl http://localhost:8000/health
```

**Temps estimé:** 10-15 minutes

---

### Partial Restore (si feature cassée)

**Scenario: AgentMail ne marche plus après merge**

```bash
# 1. Restore fichier custom depuis backup
cd /data/workspace/clawith-fork
cp backups/custom-files/agentmail_tools.py backend/app/tools/

# 2. Rebuild backend
docker-compose build backend
docker-compose restart backend

# 3. Tester
curl http://localhost:8000/api/tools | jq '.[] | select(.name | contains("agentmail"))'
```

**Temps estimé:** 5 minutes

---

## 🗓️ Backup Retention Policy

| Type | Retention | Rotation |
|------|-----------|----------|
| **DB Backups** | 30 jours | Supprimer > 30 jours |
| **Git Tags** | 90 jours | Supprimer tags > 90 jours |
| **VM Snapshots** | 90 jours | Supprimer snapshots > 90 jours |
| **Config Backups** | 30 jours | Supprimer > 30 jours |

**Cleanup automatique (cron):**
```bash
# /etc/cron.d/clawith-backup-cleanup
0 3 * * * root find /data/workspace/clawith-fork/backups/ -type f -mtime +30 -delete
0 3 * * * root git tag -l "backup/*" | xargs -I {} git tag -d {}
```

---

## 📞 Emergency Contacts

| Rôle | Nom | Contact |
|------|-----|---------|
| **Validateur** | Guillaume | [Contact] |
| **Ops Lead** | [À assigner] | [Contact] |
| **DB Admin** | [À assigner] | [Contact] |

---

## ✅ Pre-Cleanup Sign-off

**Avant de commencer le cleanup:**

- [ ] **Backup DB créé et vérifié**
- [ ] **Git tag pushé vers remote**
- [ ] **Docker Compose backupé**
- [ ] **Custom files backupés**
- [ ] **VM snapshot créé (si applicable)**
- [ ] **Test restore réussi (recommandé)**
- [ ] **Guillaume a validé**

**Signature:**
```
Nom: _______________________
Date: _______________________
Heure: _______________________
Statut: PRÊT POUR CLEANUP ✅
```

---

**Prochaine étape:** Exécuter CLEANUP_PLAN.md (P0 actions)
