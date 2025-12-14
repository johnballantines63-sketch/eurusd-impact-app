#!/bin/bash

echo "🔬 SESSION 106 - TEST DOUBLE HEURE : 13:30 vs 14:30"
echo ""
echo "================================================================================"
echo "Teste les prix à partir de :"
echo "  1. 13:30 (au cas où conversion automatique)"
echo "  2. 14:30 (ce qu'on a déjà testé)"
echo ""
echo "Pour trouver laquelle donne les 56.8 pips !"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 test_double_heure.py

echo ""
echo "📊 Test terminé !"
