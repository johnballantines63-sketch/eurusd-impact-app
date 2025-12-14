#!/bin/bash
# ════════════════════════════════════════════════════════════════
# PIPELINE COMPLET SESSION 77
# ════════════════════════════════════════════════════════════════
# 
# Exécute les 3 étapes de calibration et validation :
# 1. Grid Search Calibration (29,700+ combinaisons)
# 2. Test 11 septembre (validation cas référence)
# 3. Validation Session 75 (7 mouvements qualité)
#
# Date : 25 octobre 2025
# Session : 77
# ════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════"
echo "PIPELINE SESSION 77 - CALIBRATION GRID SEARCH"
echo "════════════════════════════════════════════════════════════"
echo ""

# Répertoire de travail
cd "$(dirname "$0")/../.."
echo "📂 Répertoire : $(pwd)"
echo ""

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : GRID SEARCH CALIBRATION
# ════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 1/3 : Grid Search Calibration"
echo "────────────────────────────────────────────────────────────"
echo "⏱️  Durée estimée : 2-3 minutes"
echo "📊 Combinaisons : 33,264"
echo ""

python3 scripts/session77/1_grid_search_calibration.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR lors du Grid Search"
    exit 1
fi

echo ""
echo "✅ Grid Search terminé"
echo ""

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : TEST 11 SEPTEMBRE
# ════════════════════════════════════════════════════════════════

echo "🎯 ÉTAPE 2/3 : Test 11 Septembre"
echo "────────────────────────────────────────────────────────────"
echo "📅 Cas référence : 11 septembre 2025, 14h30 (CPI US)"
echo "🎯 Critère : MAE < 10 pips"
echo ""

python3 scripts/session77/2_test_11septembre.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR lors du test 11 septembre"
    exit 1
fi

echo ""
echo "✅ Test 11 septembre terminé"
echo ""

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : VALIDATION SESSION 75
# ════════════════════════════════════════════════════════════════

echo "📊 ÉTAPE 3/3 : Validation Session 75"
echo "────────────────────────────────────────────────────────────"
echo "📂 Dataset : 7 mouvements qualité"
echo "🎯 Critère : MAE < 32 pips (amélioration 50%)"
echo ""

python3 scripts/session77/3_validation_session75.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR lors de la validation Session 75"
    exit 1
fi

echo ""
echo "✅ Validation Session 75 terminée"
echo ""

# ════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════"
echo "✅ PIPELINE SESSION 77 TERMINÉ"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📁 Fichiers générés :"
echo "   • scripts/session77/calibration_results_session77.txt"
echo "   • scripts/session77/calibration_grid_analysis.csv"
echo "   • scripts/session77/test_11sept_results_session77.txt"
echo "   • scripts/session77/validation_session75_results_session77.txt"
echo "   • scripts/session77/validation_session75_details_session77.csv"
echo ""
echo "📊 Consulter les résultats pour valider les critères de succès"
echo ""
