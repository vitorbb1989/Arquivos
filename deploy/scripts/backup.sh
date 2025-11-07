#!/usr/bin/env bash
#
# Script de backup do PostgreSQL
# Cria dump do banco cmdgen e salva em /backups
# Uso: ./backup.sh
#
# Para agendar (crontab):
#   0 2 * * * /root/stacks/cmdgen/deploy/scripts/backup.sh
#

set -euo pipefail

# Configurações
BACKUP_DIR="${BACKUP_DIR:-/var/backups/cmdgen}"
DB_CONTAINER="${DB_CONTAINER:-cmdgen_postgres}"
DB_NAME="${DB_NAME:-cmdgen}"
DB_USER="${DB_USER:-cmdgen}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cmdgen_$TIMESTAMP.sql"

echo "[INFO] Iniciando backup do banco $DB_NAME..."

# Cria diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# Executa pg_dump via docker exec
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -F p -c > "$BACKUP_FILE"

if [[ $? -eq 0 ]]; then
    echo "[SUCCESS] Backup criado: $BACKUP_FILE"

    # Comprime backup
    gzip "$BACKUP_FILE"
    echo "[INFO] Backup comprimido: ${BACKUP_FILE}.gz"

    # Remove backups antigos
    find "$BACKUP_DIR" -name "cmdgen_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "[INFO] Backups com mais de $RETENTION_DAYS dias removidos"

    # Lista backups
    echo "[INFO] Backups disponíveis:"
    ls -lh "$BACKUP_DIR"

    exit 0
else
    echo "[ERROR] Falha ao criar backup"
    exit 1
fi
