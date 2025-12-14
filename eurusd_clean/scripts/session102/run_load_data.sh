#!/bin/bash
# Script pour exécuter le chargement des données réelles
# Session 102

cd "$(dirname "$0")"

echo "🚀 Exécution load_real_event_data.py..."
python3 load_real_event_data.py

echo ""
echo "✅ Script terminé !"
echo ""
echo "📁 Résultats dans : real_event_data.csv"
