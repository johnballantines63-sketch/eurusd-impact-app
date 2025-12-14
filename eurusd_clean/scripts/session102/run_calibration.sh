#!/bin/bash

# Calibration formule amplification avec ancrage référence
# Session 102

echo "=========================================="
echo "CALIBRATION FORMULE AMPLIFICATION"
echo "=========================================="
echo ""
echo "Méthode :"
echo "1. Ancrage sur 11.09.2025 (référence)"
echo "2. Test 7 formules mathématiques"
echo "3. Calibration paramètres"
echo "4. Sélection meilleure formule"
echo ""
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 calibrate_amp_formula.py

echo ""
echo "=========================================="
echo "Calibration terminée"
echo "=========================================="
