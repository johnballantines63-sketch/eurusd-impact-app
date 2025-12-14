#!/bin/bash

# Script lancement Session 102 - Analyse complète avec vraies données DB
# 
# Étape 1 : Charger vraies données événements depuis DB
# Étape 2 : Analyser avec vraies données + corrélations

echo "=========================================="
echo "SESSION 102 - ANALYSE VRAIES DONNÉES DB"
echo "=========================================="
echo ""
echo "Étape 1/2 : Chargement données réelles..."
echo ""

cd "$(dirname "$0")"

python3 load_real_event_data.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR Étape 1 - Arrêt"
    exit 1
fi

echo ""
echo "=========================================="
echo ""
echo "Étape 2/2 : Analyse avec vraies données..."
echo ""

python3 analyze_with_real_data.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERREUR Étape 2 - Arrêt"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ SESSION 102 TERMINÉE"
echo "=========================================="
echo ""
echo "Fichiers générés :"
echo "  - real_event_data.csv"
echo "  - analysis_real_data_complete.csv"
echo ""
