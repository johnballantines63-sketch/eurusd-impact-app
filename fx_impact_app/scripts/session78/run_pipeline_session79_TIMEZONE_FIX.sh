#!/bin/bash

# PIPELINE SESSION 79 - TIMEZONE FIX DÉFINITIF
# =============================================
# Exécute le pipeline avec solution timezone définitive

echo ""
echo "======================================================================"
echo "PIPELINE SESSION 79 - TIMEZONE FIX DÉFINITIF"
echo "======================================================================"
echo ""

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 0 : TEST TIMEZONE_UTILS
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 0 : Test timezone_utils"
echo "----------------------------------------------------------------------"
python3 ../../src/utils/timezone_utils.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR : Tests timezone_utils échoués"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : OPTIMISATION FENÊTRE (TIMEZONE FIX)
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 1 : Optimisation fenêtre temporelle (timezone fix)"
echo "----------------------------------------------------------------------"
python3 2_optimize_window_session79_TIMEZONE_FIX.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR : Optimisation fenêtre échouée"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : VALIDATION FINALE (TIMEZONE FIX)
# ══════════════════════════════════════════════════════════════════════════

echo "🔍 ÉTAPE 2 : Validation finale (timezone fix)"
echo "----------------------------------------------------------------------"
python3 3_validation_finale_session79_TIMEZONE_FIX.py

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
echo "   - optimize_window_results_session79_timezone_fix.txt"
echo "   - validation_finale_session79_timezone_fix.txt"
echo ""
echo "📊 Solution timezone définitive appliquée :"
echo "   - timezone_utils.get_event_window_utc() utilisée"
echo "   - Plus de double conversion timezone"
echo "   - Dataset timezone (+01:00/+02:00) → UTC correct"
echo ""
