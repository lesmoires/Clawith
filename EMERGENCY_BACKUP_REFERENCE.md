# 🚨 EMERGENCY BACKUP & RESTORE — QUICK REFERENCE

**IMPRIMER OU GARDER SOUS LA MAIN**

---

## 📦 BACKUP RAPIDE (AVANT TOUTE INTERVENTION)

```bash
# 1. Backup immédiat
/data/workspace/scripts/backup-agent-data.sh AVANT_INTERVENTION

# 2. Vérifier que le backup existe
ls -lht /data/backups/agent_data_backup_*.tar.gz | head -3
```

---

## 🔄 RESTAURATION URGENTE

```bash
# 1. Trouver le backup le plus récent
ls -lht /data/backups/agent_data_backup_*.tar.gz | head -1

# 2. Extraire
cd /data/backups
tar -xzf agent_data_backup_YYYYMMDD_HHMMSS*.tar.gz -C /tmp/restore

# 3. Stopper container
docker stop twcgssk04ckw4kgw0gcwcw48-backend-1

# 4. Sauvegarder l'état actuel (sécurité)
mv /data/coolify/applications/twcgssk04ckw4kgw0gcwcw48/backend/agent_data \
   /data/coolify/applications/twcgssk04ckw4kgw0gcwcw48/backend/agent_data.BROKEN_$(date +%Y%m%d_%H%M%S)

# 5. Restaurer
cp -a /tmp/restore/agent_data /data/coolify/applications/twcgssk04ckw4kgw0gcwcw48/backend/

# 6. Permissions
chown -R 1000:1000 /data/coolify/applications/twcgssk04ckw4kgw0gcwcw48/backend/agent_data

# 7. Redémarrer
docker start twcgssk04ckw4kgw0gcwcw48-backend-1

# 8. Vérifier
docker exec twcgssk04ckw4kgw0gcwcw48-backend-1 ls /data/agents/ | wc -l
```

---

## ❌ JAMAIS

```bash
# JAMAIS FAIRE ÇA:
rm -rf /data/coolify/applications/*/backend/agent_data
rm -rf /data/agents/

# TOUJOURS FAIRE ÇA À LA PLACE:
/data/workspace/scripts/backup-agent-data.sh AVANT_RM
mv /path/to/delete /path/to/delete.BACKUP_$(date +%Y%m%d_%H%M%S)
```

---

## 🔍 VÉRIFIER AVANT DE SUPPRIMER

```bash
# Toujours vérifier:
ls -la /path/to/delete/
du -sh /path/to/delete/
ls /path/to/delete/ | wc -l

# Si > 0 fichiers → BACKUP D'ABORD!
```

---

## 📊 BACKUPS AUTOMATIQUES

| Type | Fréquence | Location |
|------|-----------|----------|
| Agent Data | 02:00 UTC quotidien | `/data/backups/agent_data_backup_*.tar.gz` |
| Database | 02:00 UTC quotidien | `/data/backups/db_backup_*.sql.gz` |
| Coolify Config | 02:00 UTC quotidien | `/data/backups/coolify_config_*.tar.gz` |

**Recommandation:** Ajouter backup toutes les 4 heures (voir cron)

---

## 📞 CONTACTS EN CAS D'URGENCE

- **Guillaume:** @guillaume (Telegram/Signal)
- **Backup Location:** `/data/backups/`
- **Dernier backup:** `ls -lht /data/backups/agent_data_backup_*.tar.gz | head -1`

---

**Dernière mise à jour:** 2026-04-17  
**Incident référence:** `memory/INCIDENT_2026-04-17_CRITICAL_DATA_LOSS.md`
