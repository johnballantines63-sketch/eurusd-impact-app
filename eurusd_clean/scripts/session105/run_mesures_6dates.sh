#!/bin/bash
#
# SESSION 105 - MESURES CLUSTER #3 (6 DATES)
# ===========================================
#
# Mesure impact réel + métriques pour les 6 dates du Cluster #3
#

echo "🚀 SESSION 105 - MESURES CLUSTER #3 (6 DATES)"
echo ""

cd "$(dirname "$0")"

python3 measure_cluster3_6dates.py

echo ""
echo "📊 Mesures terminées !"
echo ""
echo "Vérifier :"
echo "  - cluster3_impacts_all_6dates.csv"
echo "  - cluster3_impacts_all_6dates.json"
