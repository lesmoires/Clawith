# CLEANUP PLAN — Clawith Fork

**Date:** 24 mars 2026  
**Préparé par:** Claw (Code Audit Lead)  
**Validé par:** Guillaume (à valider avant suppressions)

---

## 📊 Summary

| Catégorie | Count | Effort |
|-----------|-------|--------|
| **Files to keep** | 3 core features | 2h (merge) |
| **Files to refactor** | 4 features | 11-13h |
| **Files to delete** | 2 items | 0.5h |

**Effort total:** 15.5-17.5 heures (~2-3 jours)

---

## 🗂️ Inventory

### ✅ Files to Keep (Core Features)

| File/Feature | Reason | Priority |
|--------------|--------|----------|
| `backend/app/tools/agentmail_tools.py` | Email capabilities, unique | P0 |
| `backend/app/skills/infisical_secrets.py` | Secret management | P0 |
| `backend/app/tools/infisical_secret.py` | Infisical MCP tool | P0 |
| `backend/app/api/gateway.py` | Clawith Repair sync | P0 |
| `docker-compose.yml` (partiel) | Infisical + AgentMail env vars | P0 |

**Action:** Préserver pendant merge, intégrer proprement

---

### ⚠️ Files to Refactor

| File/Feature | Action | Priority | Effort |
|--------------|--------|----------|--------|
| `docker-compose.yml` | Nettoyer, aligner upstream | P1 | 1h |
| `backend/app/main.py` | Merge upstream + garder custom | P1 | 2h |
| `backend/app/api/tools.py` | Intégrer AgentMail proprement | P1 | 2h |
| Supergateway service | Remplacer par LiteLLM | P1 | 4h |
| `backend/app/api/feishu.py` | Auditer usage | P2 | 2h |

**Action:** Merge manuel, tests, validation

---

### ❌ Files to Delete

| File | Reason | Priority | Effort |
|------|--------|----------|--------|
| `dev_deploy_temp.tar.gz` | 1.1 GB, temporaire, inutile | P0 | 0.01h |
| `UPGRADE_ANALYSIS.md` | Post-merge, obsolète | P2 | 0.1h |
| `MERGE_STRATEGY.md` | Post-merge, obsolète | P2 | 0.1h |
| `CONFLICT_MATRIX.md` | Post-merge, obsolète | P2 | 0.1h |
| `ROLLBACK_PLAN.md` | Post-merge, obsolète | P2 | 0.1h |
| `UPGRADE_README.md` | Post-merge, obsolète | P2 | 0.1h |

**Action:** Supprimer après merge réussi

---

## 🚀 Immediate Actions (P0)

### 1. Supprimer fichier temporaire (5 min)

```bash
cd /data/workspace/clawith-fork
rm dev_deploy_temp.tar.gz
git status  # Vérifier
git commit -m "chore: Remove temporary deploy archive (1.1 GB)"
```

**Risque:** 🟢 Nul (fichier temporaire)  
**Backup:** Non nécessaire

---

### 2. Backup DB (15 min)

**AVANT toute opération de merge:**

```bash
# Backup DB PostgreSQL
docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_$(date +%Y%m%d_%H%M%S).sql

# Vérifier backup
ls -lh backup_*.sql
wc -l backup_*.sql

# Optionnel: Backup vers cloud/s3
# aws s3 cp backup_*.sql s3://moiria-backups/clawith/
```

**Risque:** 🟢 Faible (précaution)  
**Backup:** Oui (fichier backup_*.sql)

---

### 3. Snapshot Git (5 min)

```bash
cd /data/workspace/clawith-fork

# Créer tag de backup
git tag backup/pre-merge-$(date +%Y%m%d)
git push origin backup/pre-merge-$(date +%Y%m%d)

# Créer branche de travail
git checkout -b merge/v1.7.1
```

**Risque:** 🟢 Nul (git tag)  
**Backup:** Oui (tag + push)

---

## 📦 Short-term Actions (P1)

### 4. Merge Upstream v1.7.1 (4-6h)

```bash
cd /data/workspace/clawith-fork

# Ajouter remote upstream (si pas déjà fait)
git remote add dataelement https://github.com/dataelement/Clawith.git
git fetch dataelement --tags

# Vérifier version upstream
git log dataelement/main --oneline | head -10

# Merge
git merge v1.7.1 --no-commit --no-ff

# Voir conflits
git status --short | grep "^UU"
```

**Fichiers critiques à résoudre:**
- `backend/app/main.py` — Logging + MCP wrapper
- `backend/app/api/gateway.py` — Garder custom WebSocket
- `backend/app/api/tools.py` — Intégrer AgentMail
- `docker-compose.yml` — Garder env vars custom

**Risque:** 🟡 Moyen (conflits de merge)  
**Backup:** Oui (tag pre-merge)  
**Test requis:** ✅ Tests backend + frontend

---

### 5. Intégrer AgentMail proprement (2h)

**Après merge, vérifier:**

```bash
# Vérifier que AgentMail est toujours dans docker-compose
grep -A2 "AGENTMAIL_API_KEY" docker-compose.yml

# Vérifier que tools.py inclut AgentMail
grep -n "agentmail" backend/app/api/tools.py

# Tester API
curl http://localhost:8000/api/tools | jq '.[] | select(.name | contains("agentmail"))'
```

**Si manquant:**
```python
# backend/app/api/tools.py
from app.tools.agentmail_tools import (
    agentmail_list_inboxes,
    agentmail_create_inbox,
    agentmail_send_email,
    agentmail_read_email
)

# Register tools...
```

**Risque:** 🟡 Moyen (régression)  
**Test requis:** ✅ Test send/receive email

---

### 6. Remplacer Supergateway par LiteLLM (4h)

**Pourquoi:** LiteLLM MCP Gateway est plus standard et mieux maintenu

**Étapes:**

1. **Installer LiteLLM MCP:**
```bash
# Dans docker-compose.yml
services:
  litellm-mcp:
    image: ghcr.io/berriai/litellm:main
    command: ["--mcp"]
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - KIMI_KEY=${KIMI_KEY}
    ports:
      - "4000:4000"
    networks:
      - clawith_network
```

2. **Supprimer Supergateway:**
```bash
# docker-compose.yml
# Supprimer service 'supergateway'

# backend/app/main.py
# Supprimer commentaires MCP wrapper
```

3. **Mettre à jour backend:**
```python
# backend/app/config.py
LITELLM_MCP_URL = os.getenv("LITELLM_MCP_URL", "http://litellm-mcp:4000")
```

4. **Tester:**
```bash
docker-compose up -d litellm-mcp
curl http://localhost:4000/health
```

**Risque:** 🟡 Moyen (changement d'infra)  
**Test requis:** ✅ Test MCP calls  
**Rollback:** Revert docker-compose + restart supergateway

---

### 7. Nettoyer docker-compose.yml (1h)

**Après merge:**

```bash
# Comparer avec upstream
curl -s https://raw.githubusercontent.com/dataelement/Clawith/v1.7.1/docker-compose.yml > upstream-docker-compose.yml
diff -u upstream-docker-compose.yml docker-compose.yml

# Nettoyer:
# - Garder env vars custom (Infisical, AgentMail)
# - Supprimer supergateway (si remplacé)
# - Aligner versions images
# - Garder coolify network (requis pour Traefik)
```

**Risque:** 🟢 Faible  
**Test requis:** ✅ `docker-compose config` + restart

---

### 8. Auditer Feishu (2h)

**Vérifier si activement utilisé:**

```bash
# Chercher références Feishu
grep -r "feishu" backend/app/ --include="*.py" | wc -l

# Vérifier logs
docker logs clawith-backend | grep -i feishu | tail -20

# Vérifier DB
docker exec clawith-backend-postgres-1 psql -U clawith -d clawith -c \
  "SELECT COUNT(*) FROM channel_configs WHERE channel_type = 'feishu';"
```

**Si unused:**
```bash
# Archive (optionnel)
git mv backend/app/api/feishu.py backend/app/api/feishu.py.archived
```

**Risque:** 🟢 Faible (audit seulement)  
**Décision:** Guillaume (confirm usage)

---

## 🗃️ Long-term Actions (P2)

### 9. Archiver documentation upgrade (30 min)

**Après merge réussi:**

```bash
cd /data/workspace/clawith-fork

# Créer dossier archive
mkdir -p docs/archive/upgrade-v1.7.1

# Déplacer docs
mv UPGRADE_ANALYSIS.md MERGE_STRATEGY.md CONFLICT_MATRIX.md ROLLBACK_PLAN.md UPGRADE_README.md docs/archive/upgrade-v1.7.1/

# Commit
git add docs/archive/
git commit -m "docs: Archive upgrade docs (post-merge v1.7.1)"
```

**Risque:** 🟢 Nul  
**Backup:** Oui (git)

---

### 10. Tests de régression (2h)

**Après merge:**

```bash
# Backend tests
cd backend
pytest -xvs

# Frontend tests
cd frontend
npm test

# Integration tests
# - Send email (AgentMail)
# - Get secret (Infisical)
# - Gateway sync (Clawith Repair)
# - Feishu (si utilisé)
```

**Checklist:**
- [ ] Email send/receive
- [ ] Infisical secret fetch
- [ ] Gateway WebSocket
- [ ] Feishu (si applicable)
- [ ] Docker Compose startup
- [ ] Frontend backend communication

**Risque:** 🟡 Moyen (régression)  
**Backup:** Oui (tag pre-merge)

---

## 💾 BACKUP CHECKLIST

### Avant Cleanup

- [ ] **Backup DB PostgreSQL**
  ```bash
  docker exec clawith-backend-postgres-1 pg_dump -U clawith clawith > backup_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Backup Git (tag + push)**
  ```bash
  git tag backup/pre-cleanup-$(date +%Y%m%d)
  git push origin backup/pre-cleanup-$(date +%Y%m%d)
  ```

- [ ] **Backup docker-compose.yml**
  ```bash
  cp docker-compose.yml docker-compose.yml.backup
  ```

- [ ] **Backup env vars**
  ```bash
  # Si .env existe
  cp .env .env.backup
  
  # Ou exporter depuis Coolify
  # (Coolify → Project → Variables → Export)
  ```

- [ ] **Snapshot VM/serveur** (si applicable)
  - Via Hetzner Cloud Console
  - Ou outil de backup (rsync, etc.)

---

### Après Cleanup

- [ ] **Vérifier backup DB**
  ```bash
  ls -lh backup_*.sql
  wc -l backup_*.sql
  ```

- [ ] **Tester restore DB** (optionnel mais recommandé)
  ```bash
  # Sur environnement de test
  cat backup_*.sql | docker exec -i test-postgres psql -U clawith clawith
  ```

- [ ] **Documenter backup location**
  - Fichier: `backup_YYYYMMDD_HHMMSS.sql`
  - Location: `/path/to/backups/`
  - Taille: ~XX MB

---

## 🔄 How to Restore

### Scenario 1: Rollback Git

```bash
cd /data/workspace/clawith-fork

# Voir tags
git tag -l "backup/*"

# Revert to backup tag
git checkout backup/pre-cleanup-20260324
git branch -f merge/v1.7.1 backup/pre-cleanup-20260324
git checkout merge/v1.7.1

# Force push (si nécessaire)
git push origin merge/v1.7.1 --force
```

---

### Scenario 2: Restore DB

```bash
# Stop backend
docker-compose stop backend

# Restore DB
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i clawith-backend-postgres-1 psql -U clawith clawith

# Restart backend
docker-compose start backend
```

---

### Scenario 3: Restore docker-compose.yml

```bash
# Stop services
docker-compose down

# Restore file
cp docker-compose.yml.backup docker-compose.yml

# Restart
docker-compose up -d
```

---

## 📅 Timeline

| Phase | Actions | Durée | Deadline |
|-------|---------|-------|----------|
| **P0 (Immediate)** | Delete temp file, Backup DB, Git snapshot | 30 min | Jour 1 |
| **P1 (Short-term)** | Merge upstream, Integrate AgentMail, Replace Supergateway | 11-13h | Jour 2-3 |
| **P2 (Long-term)** | Archive docs, Audit Feishu, Regression tests | 4.5h | Jour 4 |

**Total:** 2-4 jours (selon conflits de merge)

---

## ✅ Validation Criteria

### Merge réussi si:

- [ ] Backend démarre sans erreurs
- [ ] Frontend se connecte au backend
- [ ] AgentMail send/receive fonctionne
- [ ] Infisical MCP fetch fonctionne
- [ ] Gateway WebSocket sync fonctionne
- [ ] Pas de régression sur features existantes

---

## 📞 Contacts

- **Validateur:** Guillaume (avant suppressions P0/P1)
- **Code Audit Lead:** Claw (subagent)
- **Upgrade Lead:** À assigner
- **MCP Lead:** À assigner

---

**Prochain livrable:** BACKUP_CHECKLIST.md (détaillé) ou exécution directe

**Statut:** ⏳ En attente de validation Guillaume avant P0
