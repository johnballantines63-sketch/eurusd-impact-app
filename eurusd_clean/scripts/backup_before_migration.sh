#!/bin/bash
# Script de backup avant migration timezone
# Usage: bash scripts/backup_before_migration.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_DIR="$DATA_DIR/backups/backup_$(date +%Y%m%d_%H%M%S)"

echo "=" | head -c 80
echo ""
echo "📦 BACKUP AVANT MIGRATION TIMEZONE"
echo "=" | head -c 80
echo ""
echo ""

# Créer le répertoire de backup
mkdir -p "$BACKUP_DIR"
echo "📁 Répertoire de backup : $BACKUP_DIR"
echo ""

# 1. Backup de la base de données (CRITIQUE)
echo "1️⃣ Backup de la base de données..."
if [ -f "$DATA_DIR/warehouse.duckdb" ]; then
    cp "$DATA_DIR/warehouse.duckdb" "$BACKUP_DIR/"
    SIZE=$(du -h "$BACKUP_DIR/warehouse.duckdb" | cut -f1)
    echo "   ✅ warehouse.duckdb copié ($SIZE)"
else
    echo "   ❌ warehouse.duckdb introuvable !"
    exit 1
fi
echo ""

# 2. Backup des fichiers de cache
echo "2️⃣ Backup des fichiers de cache..."
mkdir -p "$BACKUP_DIR/cache"

CACHE_FILES=(
    "cache_clusters.csv"
    "cache_clusters_catalogued_simple.csv"
    "cache_cluster_patterns.csv"
)

for cache_file in "${CACHE_FILES[@]}"; do
    if [ -f "$DATA_DIR/$cache_file" ]; then
        cp "$DATA_DIR/$cache_file" "$BACKUP_DIR/cache/"
        echo "   ✅ $cache_file copié"
    else
        echo "   ⚠️  $cache_file : n'existe pas (ignoré)"
    fi
done
echo ""

# 3. Backup des scripts modifiés (optionnel)
echo "3️⃣ Backup des scripts modifiés..."
mkdir -p "$BACKUP_DIR/scripts"

SCRIPT_FILES=(
    "scripts/finnhub_import.py"
    "scripts/session113/update_dukascopy_prices.py"
)

for script_file in "${SCRIPT_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$script_file" ]; then
        SCRIPT_DIR="$BACKUP_DIR/scripts/$(dirname "$script_file" | sed 's|^scripts/||')"
        mkdir -p "$SCRIPT_DIR"
        cp "$PROJECT_ROOT/$script_file" "$BACKUP_DIR/$script_file"
        echo "   ✅ $script_file copié"
    else
        echo "   ⚠️  $script_file : n'existe pas (ignoré)"
    fi
done
echo ""

# Résumé
echo "=" | head -c 80
echo ""
echo "✅ BACKUP TERMINÉ"
echo "=" | head -c 80
echo ""
echo "📁 Emplacement : $BACKUP_DIR"
echo ""
echo "📋 Contenu du backup :"
ls -lh "$BACKUP_DIR"
if [ -d "$BACKUP_DIR/cache" ]; then
    echo ""
    echo "📋 Cache :"
    ls -lh "$BACKUP_DIR/cache"
fi
if [ -d "$BACKUP_DIR/scripts" ]; then
    echo ""
    echo "📋 Scripts :"
    find "$BACKUP_DIR/scripts" -type f
fi
echo ""
echo "💡 Pour restaurer :"
echo "   cp $BACKUP_DIR/warehouse.duckdb $DATA_DIR/warehouse.duckdb"
echo ""


