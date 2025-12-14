#!/bin/bash
# PIPELINE SESSION 78 - AMÉLIORATION FORMULES V2
# =============================================

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "PIPELINE SESSION 78 - CORRECTION TIMEZONE + OPTIMISATION"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Répertoire scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : DIAGNOSTIC TIMEZONE
# ════════════════════════════════════════════════════════════════════

echo "ÉTAPE 1/3 : Diagnostic timezone"
echo "────────────────────────────────────────────────────────────────────"
echo ""

python3 1_diagnostic_timezone_session78.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur à l'étape 1"
    exit 1
fi

echo ""
echo "✅ Étape 1 terminée"
echo ""
echo "Appuyez sur Entrée pour continuer vers l'étape 2..."
read

# ════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : OPTIMISATION FENÊTRE TEMPORELLE
# ════════════════════════════════════════════════════════════════════

echo ""
echo "ÉTAPE 2/3 : Optimisation fenêtre temporelle"
echo "────────────────────────────────────────────────────────────────────"
echo ""

python3 2_optimize_window_session78.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur à l'étape 2"
    exit 1
fi

echo ""
echo "✅ Étape 2 terminée"
echo ""
echo "Appuyez sur Entrée pour continuer vers l'étape 3..."
read

# ════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : VALIDATION FINALE
# ════════════════════════════════════════════════════════════════════

echo ""
echo "ÉTAPE 3/3 : Validation finale"
echo "────────────────────────────────────────────────────────────────────"
echo ""

python3 3_validation_finale_session78.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur à l'étape 3"
    exit 1
fi

echo ""
echo "✅ Étape 3 terminée"
echo ""

# ════════════════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ════════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "PIPELINE SESSION 78 TERMINÉ"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Fichiers générés :"
echo "  - optimize_window_results_session78.txt"
echo "  - optimize_window_details_session78.csv"
echo "  - validation_finale_session78.txt"
echo "  - validation_finale_details_session78.csv"
echo ""
echo "🎯 Prochaine étape :"
echo "  → Lire validation_finale_session78.txt pour statut final"
echo "  → Si succès : Créer formulas_validated_v2_1.py"
echo ""
