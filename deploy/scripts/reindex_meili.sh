#!/usr/bin/env bash
#
# Script para reindexar Meilisearch
# Uso: ./reindex_meili.sh [API_URL]
#

set -euo pipefail

API_URL="${1:-http://localhost:8000}"

echo "[INFO] Iniciando reindex do Meilisearch..."
echo "[INFO] API URL: $API_URL"

# Chama endpoint de reindex
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/commands/reindex")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [[ "$http_code" -eq 202 ]]; then
    echo "[SUCCESS] Reindex concluído com sucesso!"
    echo "$body" | jq -r '.message // .'
    exit 0
else
    echo "[ERROR] Falha no reindex (HTTP $http_code)"
    echo "$body"
    exit 1
fi
