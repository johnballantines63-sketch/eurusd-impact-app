#!/bin/bash
# SESSION 108 - VALIDATION CLUSTER #1
# =====================================
# Exécute les 3 phases d'analyse du Cluster #1 :
# 1. Mesure impacts réels (11 dates)
# 2. Test formule Session 101 (R² 72h)
# 3. Test méthode Inversion (André)

echo "========================================================================"
echo "SESSION 108 - VALIDATION FORMULES SUR CLUSTER #1"
echo "========================================================================"
echo ""
echo "Cluster #1 : 11 dates Manufacturing|Consumer|Employment (15:45)"
echo ""

# Répertoire de travail
cd "$(dirname "$0")"

echo "----------------------------------------------------------------------"
echo "PHASE 1 : MESURE IMPACTS RÉELS"
echo "----------------------------------------------------------------------"
echo ""

python3 phase1_cluster1_measure_impacts.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR Phase 1 - Arrêt du pipeline"
    exit 1
fi

echo ""
echo "✅ Phase 1 terminée"
echo ""
echo "----------------------------------------------------------------------"
echo "PHASE 2B : TEST FORMULE SESSION 101 (R² 72H)"
echo "----------------------------------------------------------------------"
echo ""

python3 phase2b_cluster1_R2_analysis.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR Phase 2B - Arrêt du pipeline"
    exit 1
fi

echo ""
echo "✅ Phase 2B terminée"
echo ""
echo "----------------------------------------------------------------------"
echo "PHASE 2E : TEST MÉTHODE INVERSION (ANDRÉ)"
echo "----------------------------------------------------------------------"
echo ""

python3 phase2e_cluster1_inversion_trend.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR Phase 2E"
    exit 1
fi

echo ""
echo "✅ Phase 2E terminée"
echo ""
echo "========================================================================"
echo "PIPELINE SESSION 108 TERMINÉ ✅"
echo "========================================================================"
echo ""
echo "📂 Résultats générés :"
echo "   - phase1_cluster1_results.csv"
echo "   - cluster1_complete_analysis.csv"
echo "   - cluster1_inversion_analysis.csv"
echo ""
echo "📝 Prochaine étape :"
echo "   Analyser résultats et comparer avec Cluster #3 (Session 107)"
echo ""
