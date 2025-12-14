#!/bin/bash
# Script master Session 102 : Exécute TOUTES les analyses
# 1. Charge données réelles depuis DB
# 2. Analyse avec vraies données

cd "$(dirname "$0")"

echo "=================================="
echo "🚀 SESSION 102 - ANALYSE COMPLÈTE"
echo "=================================="
echo ""

# ÉTAPE 1 : Charger données réelles
echo "📊 ÉTAPE 1/2 : Chargement données réelles..."
echo ""
chmod +x run_load_data.sh
./run_load_data.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors du chargement des données"
    exit 1
fi

echo ""
echo "=================================="
echo ""

# ÉTAPE 2 : Analyser avec vraies données
echo "📈 ÉTAPE 2/2 : Analyse avec vraies données..."
echo ""
chmod +x run_analyze.sh
./run_analyze.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de l'analyse"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ SESSION 102 - TERMINÉE AVEC SUCCÈS"
echo "=================================="
echo ""
echo "📁 Fichiers créés :"
echo "   - real_event_data.csv"
echo "   - analysis_real_data_complete.csv"
echo "   - correlations_analysis.csv"
echo ""
echo "🎯 Consultez les résultats pour la recommandation formule !"
