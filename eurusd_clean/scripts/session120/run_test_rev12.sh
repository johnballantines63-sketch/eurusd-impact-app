#!/bin/bash
# Script de lancement test rev12 - Session 120
# Usage: ./run_test_rev12.sh

echo "=========================================="
echo "🧪 TEST REV12 - SESSION 120"
echo "=========================================="
echo ""

# Chemin projet
PROJECT_ROOT="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean"
TEST_SCRIPT="$PROJECT_ROOT/scripts/session120/test_rev12_validation.py"

# Vérifier existence script
if [ ! -f "$TEST_SCRIPT" ]; then
    echo "❌ Erreur: Script test introuvable"
    echo "   Chemin: $TEST_SCRIPT"
    exit 1
fi

# Vérifier existence database
DB_PATH="$PROJECT_ROOT/data/warehouse.duckdb"
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Erreur: Base de données introuvable"
    echo "   Chemin: $DB_PATH"
    exit 1
fi

echo "✓ Script test trouvé"
echo "✓ Base de données trouvée"
echo ""
echo "Lancement test..."
echo ""

# Lancer test
cd "$PROJECT_ROOT/scripts/session120"
python test_rev12_validation.py

# Capturer code retour
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test terminé avec succès"
else
    echo "⚠️ Test terminé avec erreur (code $EXIT_CODE)"
fi
echo "=========================================="

exit $EXIT_CODE
