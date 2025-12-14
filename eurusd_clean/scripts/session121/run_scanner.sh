#!/bin/bash
# Script pour exécuter le scanner Single Wave V2

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════════"
echo " SCANNER SINGLE WAVE V2 - SESSION 121"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

python3 find_single_wave_cases_v2.py

echo ""
echo "✅ Scanner terminé!"
