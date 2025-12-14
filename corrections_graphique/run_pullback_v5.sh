#!/bin/bash
echo "🎨 Application amélioration pullback V5..."
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 corrections_graphique/add_pullback_v5_adapted.py
echo ""
echo "🧹 Nettoyage cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo ""
echo "⚠️  IMPORTANT :"
echo "  1. FERMEZ COMPLÈTEMENT le navigateur"
echo "  2. Rouvrez en mode privé (Cmd+Shift+N)"
echo "  3. Relancez Streamlit"
echo ""
echo "Appuyez sur Entrée pour continuer..."
read
if [ -d ".venv" ]; then source .venv/bin/activate; elif [ -d "venv" ]; then source venv/bin/activate; fi
streamlit run fx_impact_app/streamlit_app/Home.py --server.headless true
