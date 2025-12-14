#!/bin/bash
# Script de test Session 68
# Teste le Planificateur V2.4 avec Single Wave Fort

echo "🎯 SESSION 68 - TEST PLANIFICATEUR V2.4"
echo "========================================"
echo ""
echo "📋 Plan de test :"
echo "  1. Test date 2025-02-12 (CPI 4 events)"
echo "  2. Test date 2024-12-06 (NFP 8 events)"
echo ""
echo "🚀 Lancement Streamlit..."
echo ""

cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app

# Lancer Streamlit
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py
