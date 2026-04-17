#!/bin/bash
# Backup Agent Data — Manuel ou Automatique
# Usage: ./backup-agent-data.sh [COMMENTAIRE_OPTIONNEL]

set -e

BACKUP_DIR="/data/backups"
SOURCE="/data/coolify/applications/twcgssk04ckw4kgw0gcwcw48/backend/agent_data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMMENT=${1:-""}

echo "=========================================="
echo "BACKUP AGENT DATA — $(date)"
echo "=========================================="

# Vérifier que la source existe
if [ ! -d "$SOURCE" ]; then
    echo "❌ ERREUR: Source inexistante: $SOURCE"
    exit 1
fi

# Créer le backup
FILENAME="agent_data_backup_${TIMESTAMP}${COMMENT:+_$COMMENT}.tar.gz"
echo "📦 Création: $FILENAME"
tar -czf ${BACKUP_DIR}/${FILENAME} -C $(dirname $SOURCE) $(basename $SOURCE)

# Vérifier le backup
if [ -f ${BACKUP_DIR}/${FILENAME} ]; then
    SIZE=$(ls -lh ${BACKUP_DIR}/${FILENAME} | awk '{print $5}')
    FILES=$(tar -tzf ${BACKUP_DIR}/${FILENAME} | wc -l)
    echo "✅ SUCCÈS: $SIZE, $FILES fichiers"
    echo "📁 Location: ${BACKUP_DIR}/${FILENAME}"
else
    echo "❌ ÉCHEC: Le fichier backup n'existe pas"
    exit 1
fi

# Nettoyer les vieux backups (garder 7 jours)
echo "🧹 Nettoyage des backups > 7 jours..."
find ${BACKUP_DIR} -name "agent_data_backup_*.tar.gz" -mtime +7 -delete
KEPT=$(ls ${BACKUP_DIR}/agent_data_backup_*.tar.gz 2>/dev/null | wc -l)
echo "📊 Backups conservés: $KEPT"

echo "=========================================="
echo "BACKUP TERMINÉ — $(date)"
echo "=========================================="
