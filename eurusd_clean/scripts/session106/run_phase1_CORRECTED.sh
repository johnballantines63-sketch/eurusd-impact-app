#!/bin/bash

echo "🚀 SESSION 106 - PHASE 1 : VALIDATION CLUSTER #3 (CPI) - CORRIGÉ"
echo ""
echo "================================================================================"
echo "CORRECTION : Timezone handling (méthode Session 92.5)"
echo "  - Timestamps DB sont DÉJÀ en Bern time (+02:00)"
echo "  - Événement 14:30 Bern = 12:30:00+02:00 dans DB"
echo "  - Pas de conversion nécessaire"
echo ""
echo "Teste la méthode Planificateur V2.4 sur 6 dates CPI"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 phase1_cluster3_validation_CORRECTED.py

echo ""
echo "📊 Phase 1 terminée !"
echo ""
echo "Résultats sauvegardés dans : phase1_cluster3_results_CORRECTED.csv"
