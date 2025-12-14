#!/bin/bash

# =============================================================================
# ANALYSE COMPLÈTE SESSION 138
# Exécute les 3 scripts d'analyse en séquence
# =============================================================================

echo "================================================================================"
echo "ANALYSE COMPLÈTE SESSION 138 - v1 vs v2"
echo "================================================================================"
echo ""

# Script 1: Comparaison v1 vs v2
echo "▶ SCRIPT 1/3 : Comparaison v1 vs v2"
echo "--------------------------------------------------------------------------------"
python analyze_v1_vs_v2.py
echo ""
echo "✅ Script 1 terminé"
echo ""
echo "Appuyez sur ENTER pour continuer..."
read

# Script 2: Analyse DOUBLE_WAVE v2
echo ""
echo "================================================================================"
echo "▶ SCRIPT 2/3 : Analyse DOUBLE_WAVE v2"
echo "--------------------------------------------------------------------------------"
python analyze_doublewave_v2.py
echo ""
echo "✅ Script 2 terminé"
echo ""
echo "Appuyez sur ENTER pour continuer..."
read

# Script 3: Vérification cas #310
echo ""
echo "================================================================================"
echo "▶ SCRIPT 3/3 : Vérification cas #310"
echo "--------------------------------------------------------------------------------"
python verify_case_310.py
echo ""
echo "✅ Script 3 terminé"
echo ""

# Synthèse finale
echo "================================================================================"
echo "✅ ANALYSE COMPLÈTE TERMINÉE"
echo "================================================================================"
echo ""
echo "📁 FICHIERS CRÉÉS:"
echo "   - comparison_v1_v2.csv              (396 mouvements comparés)"
echo "   - sample_doublewave_verification.csv (10 cas pour vérification manuelle)"
echo "   - case_310_verification.csv          (Détails cas #310)"
echo ""
echo "🎯 PROCHAINES ÉTAPES:"
echo "   1. Examiner les résultats des 3 analyses"
echo "   2. Vérifier manuellement 10 cas DOUBLE_WAVE échantillon"
echo "   3. Si taux précision ≥80% → Algorithme validé"
echo "   4. Continuer workflow LOO-CV avec v2"
echo ""
echo "================================================================================"
