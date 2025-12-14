#!/bin/bash

echo "🔬 SESSION 106 - DIAGNOSTIC TIMEZONE : CAS 11.09.2025"
echo ""
echo "================================================================================"
echo "Applique EXACTEMENT méthode Session 92.5 :"
echo "  - Event 14:30 Bern = 12:30:00+02:00 dans DB"
echo "  - Prix à chercher : 12:30:00 dans prices_1m.datetime"
echo "  - Compare 3 méthodes de calcul d'impact"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

python3 diagnostic_timezone_11sept.py

echo ""
echo "📊 Diagnostic terminé !"
