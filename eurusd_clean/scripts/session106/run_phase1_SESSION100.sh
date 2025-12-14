#!/bin/bash

echo "🚀 SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 (MÉTHODE SESSION 100)"
echo ""
echo "================================================================================"
echo "MÉTHODE CORRECTE (Session 100 validée) :"
echo "  - Prix départ = Dernier CLOSE AVANT événement"
echo "  - Peak = Maximum HIGH APRÈS événement"
echo "  - Validation : 11.09.2025 = 57.1 pips (écart 0.9 vs MT5 56.2 pips) ✅"
echo ""
echo "Teste la méthode Planificateur V2.4 sur 6 dates CPI"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 phase1_cluster3_validation_SESSION100.py

echo ""
echo "📊 Phase 1 terminée !"
echo ""
echo "Résultats sauvegardés dans : phase1_cluster3_results_SESSION100.csv"
