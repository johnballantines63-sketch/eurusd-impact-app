#!/bin/bash

# Script de lancement test overlapping complet
# Session 114

echo "════════════════════════════════════════════════════════════════"
echo "TEST OVERLAPPING COMPLET - 11 SEPTEMBRE 2025"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "streamlit_app/pages/2_Planificateur_V2.py" ]; then
    echo "❌ Erreur: Lancer depuis eurusd_clean/"
    echo "   cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean"
    exit 1
fi

# Activer venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Venv activé"
else
    echo "⚠️ Pas de .venv trouvé, on continue..."
fi

echo ""

# Lancer test
python scripts/session114/test_overlapping_complete_11sept.py

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Test terminé"
echo "════════════════════════════════════════════════════════════════"
