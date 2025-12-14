#!/bin/bash
#
# TEST MÉTHODOLOGIE CAS 11.09 - LANCEUR
# ======================================
#
# Valide toute la méthodologie sur cas référence avant calibration
#

echo "🚀 LANCEMENT TEST MÉTHODOLOGIE - CAS 11.09.2025"
echo ""

cd "$(dirname "$0")"

python3 test_methodologie_complete_11_09.py

echo ""
echo "📊 Test terminé !"
echo ""
echo "Si validation OK (✅✅) → Lancer calibration 44 dates"
echo "Si problèmes (⚠️) → Corriger avant de continuer"
