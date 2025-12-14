#!/bin/bash
# Script de correction ultra-rapide - 1 commande

echo ""
echo "🔧 Correction Bug Impact = 0.0 pips"
echo "===================================="
echo ""

# Aller au dossier du script
cd "$(dirname "$0")"

# Lancer la correction Python
python3 FIX_SIMPLE.py

echo ""
echo "💡 Si succès, lancez l'app avec:"
echo "   cd .."
echo "   streamlit run fx_impact_app/streamlit_app/Home.py"
echo ""
