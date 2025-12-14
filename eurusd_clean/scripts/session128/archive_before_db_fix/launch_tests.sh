#!/bin/bash
# SESSION 128 - SCRIPT LANCEMENT RAPIDE TESTS
# ===========================================
# Usage : ./launch_tests.sh

echo "========================================"
echo "SESSION 128 - TESTS NON-RÉGRESSION"
echo "========================================"
echo ""
echo "Lancement tests validation système..."
echo ""

cd "$(dirname "$0")"

# Activer environnement virtuel si nécessaire
# source ../../../venv/bin/activate

python run_all_tests.py

echo ""
echo "========================================"
echo "FIN TESTS"
echo "========================================"
echo ""
echo "Consulter rapport : RAPPORT_TESTS_NON_REGRESSION.md"
