#!/bin/bash

# SESSION 18 - AUDIT COMPLET - SCRIPT MASTER
# Exécute les 3 volets de l'audit en séquence
# Date : 19 octobre 2025

echo "================================================================================"
echo "🚀 SESSION 18 - AUDIT COMPLET DES DONNÉES"
echo "================================================================================"
echo ""

# Activer environnement virtuel
source .venv/bin/activate

# VOLET 1 : Qualité des données brutes
echo "================================================================================"
echo "📊 VOLET 1 : AUDIT QUALITÉ DES DONNÉES BRUTES"
echo "================================================================================"
echo ""

python audit_data_quality_session18.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur dans Volet 1"
    exit 1
fi

echo ""
echo "✅ Volet 1 terminé avec succès !"
echo ""
sleep 2

# VOLET 2 : Analyse multi-événements empirique
echo "================================================================================"
echo "🔬 VOLET 2 : ANALYSE MULTI-ÉVÉNEMENTS EMPIRIQUE"
echo "================================================================================"
echo ""

python analyze_multi_events_empirical_session18.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur dans Volet 2"
    exit 1
fi

echo ""
echo "✅ Volet 2 terminé avec succès !"
echo ""
sleep 2

# VOLET 3 : Préparation Machine Learning
echo "================================================================================"
echo "🤖 VOLET 3 : PRÉPARATION MACHINE LEARNING"
echo "================================================================================"
echo ""

python prepare_ml_dataset_session18.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur dans Volet 3"
    exit 1
fi

echo ""
echo "✅ Volet 3 terminé avec succès !"
echo ""

# Résumé final
echo "================================================================================"
echo "🎉 AUDIT SESSION 18 TERMINÉ AVEC SUCCÈS !"
echo "================================================================================"
echo ""
echo "📁 Fichiers générés :"
echo "   - analysis_multi_events_methods_session18.csv"
echo "   - analysis_multi_events_validated_session18.csv"
echo "   - ml_dataset_multi_events_session18.csv"
echo "   - ml_dataset_simple_session18.csv"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Examiner les résultats de chaque volet"
echo "   2. Identifier les données prioritaires à corriger"
echo "   3. Décider si on crée l'interface de correction (Phase 2)"
echo "   4. Ou si on lance directement le Machine Learning"
echo ""
echo "================================================================================"
