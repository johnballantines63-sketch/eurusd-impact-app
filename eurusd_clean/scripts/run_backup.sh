#!/bin/bash
# Script de lancement du backup validé
# Usage : ./scripts/run_backup.sh

echo "================================"
echo "🔄 CRÉATION BACKUP ORGANISÉ"
echo "================================"
echo ""

cd "$(dirname "$0")/.."

python3 scripts/create_validated_backup.py

echo ""
echo "✅ Backup terminé !"
echo ""
