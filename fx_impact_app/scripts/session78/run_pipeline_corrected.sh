#!/bin/bash

# PIPELINE SESSION 78 - VERSION CORRIGÉE SESSION 79
# ==================================================
# Exécute le pipeline complet avec scripts corrigés

echo ""
echo "======================================================================"
echo "PIPELINE SESSION 78 - VERSION CORRIGÉE SESSION 79"
echo "======================================================================"
echo ""

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 0 : TEST CORRECTIONS
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 0 : Test corrections"
echo "----------------------------------------------------------------------"
python3 0_test_corrections_session79.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR : Tests corrections échoués"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : OPTIMISATION FENÊTRE (VERSION CORRIGÉE)
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 1 : Optimisation fenêtre temporelle (corrigée)"
echo "----------------------------------------------------------------------"
python3 2_optimize_window_session78_CORRECTED.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR : Optimisation fenêtre échouée"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : VALIDATION FINALE (VERSION CORRIGÉE)
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 2 : Validation finale (corrigée)"
echo "----------------------------------------------------------------------"
python3 3_validation_finale_session78_CORRECTED.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR : Validation finale échouée"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════════

echo "======================================================================"
echo "✅ PIPELINE TERMINÉ"
echo "======================================================================"
echo ""
echo "📂 Fichiers générés :"
echo "   - optimize_window_results_session78_corrected.txt"
echo "   - validation_finale_session78_corrected.txt"
echo ""
echo "📊 Analyser les résultats :"
echo "   - Objectif : MAE Session 75 < 50 pips"
echo "   - Si succès : Créer formulas_validated_v2_1.py"
echo ""
