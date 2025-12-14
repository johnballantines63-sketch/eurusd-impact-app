#!/bin/bash
#
# LANCEUR TESTS MODULAIRES - CAS 11.09.2025
# ==========================================
#
# Exécute tous les steps en séquence avec possibilité de debug individuel
#

echo "════════════════════════════════════════════════════════════════════════════════"
echo "TESTS MODULAIRES - MÉTHODOLOGIE COMPLÈTE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Nettoyage fichiers précédents
rm -f step*.json 2>/dev/null

echo "🚀 LANCEMENT TESTS MODULAIRES"
echo ""

# STEP 1
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1/5 : Détection Tendance"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_step1_detection_tendance.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ STEP 1 ÉCHOUÉ - Arrêt"
    exit 1
fi
echo ""

# STEP 2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2/5 : Chargement Événements"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_step2_chargement_events.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ STEP 2 ÉCHOUÉ - Arrêt"
    exit 1
fi
echo ""

# STEP 3
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3/5 : Calcul Impact Baseline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_step3_calcul_baseline.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ STEP 3 ÉCHOUÉ - Arrêt"
    exit 1
fi
echo ""

# STEP 4
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4/5 : Mesure Impact Réel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_step4_mesure_impact_reel.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ STEP 4 ÉCHOUÉ - Arrêt"
    exit 1
fi
echo ""

# STEP 5
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5/5 : Amplification Optimale"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_step5_amp_optimal.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ STEP 5 ÉCHOUÉ - Arrêt"
    exit 1
fi
echo ""

# Succès
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅✅ TOUS LES TESTS MODULAIRES RÉUSSIS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📂 Fichiers générés :"
echo "   - step1_output.json (tendance)"
echo "   - step2_output.json (événements)"
echo "   - step3_output.json (baseline)"
echo "   - step4_output.json (impact réel)"
echo "   - step5_output.json (amp optimal)"
echo ""
echo "🚀 Prêt pour calibration 44 dates !"
