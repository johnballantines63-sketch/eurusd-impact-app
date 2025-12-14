#!/bin/bash
# Script pour nettoyer le cache Python - Session 46

echo "🧹 Nettoyage cache Python..."

# Supprimer tous les __pycache__
find /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Supprimer tous les .pyc
find /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app -type f -name "*.pyc" -delete 2>/dev/null

echo "✅ Cache Python nettoyé !"
echo ""
echo "⚠️ Maintenant, relancez Streamlit :"
echo "   cd fx_impact_app"
echo "   streamlit run streamlit_app/Home.py"
