#!/bin/bash

echo "🚀 SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 (RÈGLE SESSION 92.10 FINALE)"
echo ""
echo "================================================================================"
echo "RÈGLE TIMEZONE CORRECTE (Session 92.10) :"
echo "  - Event à 14:30 Bern → Query à 12:30:00+02:00 dans DB"
echo "  - Soustraire 2h à l'heure Bern pour query"
echo "  - Prix référence = LOW première bougie event"
echo ""
echo "Validation Session 99 :"
echo "  - 11.09.2025 : ~57 pips (LOW = 1.16680)"
echo ""
echo "Teste la méthode Planificateur V2.4 sur 6 dates CPI"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 phase1_cluster3_validation_SESSION9210_FINAL.py

echo ""
echo "📊 Phase 1 terminée !"
echo ""
echo "Résultats sauvegardés dans : phase1_cluster3_results_SESSION9210_FINAL.csv"
