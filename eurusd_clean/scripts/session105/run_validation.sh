#!/bin/bash
#
# SESSION 105 - VALIDATION MESURE 11.09
# ======================================
#
# Valide que la méthode mesure donne 56.8 ±2 pips
#

echo "🚀 SESSION 105 - VALIDATION MESURE 11.09.2025"
echo ""

cd "$(dirname "$0")"

python3 validate_mesure_11_09.py

echo ""
echo "📊 Validation terminée !"
echo ""
echo "Si ✅✅✅ → Continuer Phase 3.2 (mesures 6 dates)"
echo "Si ❌❌❌ → Débugger avant de continuer"
