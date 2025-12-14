#!/bin/bash
#
# VALIDATION IMPACT CORRIGÉ + RECALCUL amp_optimal
# =================================================
#
# Lance les deux scripts en séquence
#

echo "════════════════════════════════════════════════════════════════════════════════"
echo "VALIDATION MÉTHODOLOGIE - IMPACT CORRIGÉ"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

echo "ÉTAPE 1/2 : Mesure Impact Réel (Méthode MT5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 measure_impact_real_corrected.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ÉTAPE 1 ÉCHOUÉE"
    exit 1
fi

echo ""
echo ""
echo "ÉTAPE 2/2 : Recalcul amp_optimal avec Impact Corrigé"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 recalculate_amp_optimal_corrected.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ÉTAPE 2 ÉCHOUÉE"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅✅ VALIDATION COMPLÈTE TERMINÉE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📂 Fichiers générés :"
echo "   - impact_real_corrected.json"
echo "   - calibration_reference_11_09.json"
echo ""
echo "🎯 Facteur référence validé pour Option A !"
