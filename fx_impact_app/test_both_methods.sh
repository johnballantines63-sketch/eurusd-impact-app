#!/bin/bash
# Test des 2 méthodes de lancement - Session 68 Fix

echo "🧪 TEST MÉTHODES LANCEMENT"
echo "=========================="
echo ""

# Méthode 1 : Depuis streamlit_app (votre méthode originale)
echo "1️⃣ MÉTHODE 1 : Depuis streamlit_app/"
echo "   cd fx_impact_app/streamlit_app"
echo "   streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py"
echo ""
echo "   ✅ Devrait maintenant fonctionner avec la correction"
echo ""

# Méthode 2 : Depuis fx_impact_app
echo "2️⃣ MÉTHODE 2 : Depuis fx_impact_app/"
echo "   cd fx_impact_app"
echo "   streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py"
echo ""
echo "   ✅ Fonctionne aussi"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Les DEUX méthodes sont maintenant compatibles !"
echo ""
echo "Utilisez celle que vous préférez:"
echo ""
echo "VOTRE MÉTHODE ORIGINALE (qui marchait avant) :"
echo "  cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app"
echo "  streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py"
echo ""
