#!/bin/bash
# Script pour exécuter l'analyse avec données réelles
# Session 102

cd "$(dirname "$0")"

echo "🚀 Exécution analyze_with_real_data.py..."
python3 analyze_with_real_data.py

echo ""
echo "✅ Script terminé !"
echo ""
echo "📁 Résultats dans :"
echo "   - analysis_real_data_complete.csv"
echo "   - correlations_analysis.csv"
