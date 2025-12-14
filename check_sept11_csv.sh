#!/bin/bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

echo "==================================================================="
echo "RECHERCHE 11 SEPTEMBRE 2025 DANS LE CSV"
echo "==================================================================="

echo ""
echo "Nombre total de lignes dans le CSV:"
wc -l events_extreme_surprise_dukascopy_session25.csv

echo ""
echo "Lignes contenant '2025-09-11':"
grep "2025-09-11" events_extreme_surprise_dukascopy_session25.csv | wc -l

echo ""
echo "Contenu des lignes 11 septembre:"
grep "2025-09-11" events_extreme_surprise_dukascopy_session25.csv

echo ""
echo "==================================================================="
