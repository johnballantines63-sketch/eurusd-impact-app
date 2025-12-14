#!/bin/bash

echo "🚀 SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 (RÈGLE FINALE CORRIGÉE)"
echo ""
echo "================================================================================"
echo "RÈGLE FINALE CORRIGÉE (MT5 validée) :"
echo "  - Event à 14:30 Bern → Query à 12:30:00+02:00 dans DB"
echo "  - Soustraire 2h à l'heure Bern pour query"
echo "  - Prix référence = OPEN première bougie event (= CLOSE 14:29)"
echo ""
echo "Validation MT5 :"
echo "  - 11.09.2025 : ~57 pips (OPEN 14:30 = 1.16817)"
echo ""
echo "Teste la méthode Planificateur V2.4 sur 6 dates CPI"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 phase1_cluster3_validation_FINAL_CORRECTED.py

echo ""
echo "📊 Phase 1 terminée !"
echo ""
echo "Résultats sauvegardés dans : phase1_cluster3_results_FINAL_CORRECTED.csv"
