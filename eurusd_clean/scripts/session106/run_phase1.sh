#!/bin/bash

echo "🚀 SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 (CPI)"
echo ""
echo "================================================================================"
echo "Teste la méthode Planificateur V2.4 sur 6 dates CPI"
echo ""
echo "Pour chaque date :"
echo "  1. Charger événements (méthode Planificateur)"
echo "  2. Calculer impact prédit (amp=2.5 baseline)"
echo "  3. Mesurer impact réel (méthode Session 92.5)"
echo "  4. Calculer amp_optimal (scipy)"
echo "  5. Analyser variabilité"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 phase1_cluster3_validation.py

echo ""
echo "📊 Phase 1 terminée !"
echo ""
echo "Résultats sauvegardés dans : phase1_cluster3_results.csv"
