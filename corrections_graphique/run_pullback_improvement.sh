#!/bin/bash

echo ""
echo "========================================================================"
echo " 🎨 AMÉLIORATION PULLBACK TECHNIQUE"
echo "========================================================================"
echo ""

PROJECT_DIR="$HOME/Desktop/eurusd_news_impact_calculator_MPC"
cd "$PROJECT_DIR" || exit 1

# Étape 1 : Amélioration
echo "🎨 Application de l'amélioration pullback..."
python3 corrections_graphique/add_pullback_model.py

if [ $? -ne 0 ]; then
    echo "❌ Échec"
    exit 1
fi

echo ""
echo "🧹 Nettoyage cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo ""
echo "🧹 Nettoyage cache Streamlit..."
rm -rf ~/.streamlit/cache/* 2>/dev/null

echo ""
echo "⚠️  IMPORTANT : Videz cache navigateur !"
echo "   Cmd+Shift+Del OU mode privé (Cmd+Shift+N)"
echo ""
echo "Appuyez sur Entrée pour lancer Streamlit..."
read -r

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

streamlit run fx_impact_app/streamlit_app/Home.py --server.headless true
