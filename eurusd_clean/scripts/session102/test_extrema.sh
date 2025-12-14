#!/bin/bash

# Test fonction détection extrema
# Avant de relancer calibration complète

echo "=========================================="
echo "TEST DÉTECTION EXTREMA"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 detect_trend_extremum.py

echo ""
echo "=========================================="
echo "Test terminé"
echo "=========================================="
echo ""
echo "Si tests OK → relancer calibration :"
echo "  ./run_calibration.sh"
echo ""
