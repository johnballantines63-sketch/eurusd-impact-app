#!/bin/bash

# Script de lancement de l'analyse Pattern W
# Session 63 - Analyse quantitative CPI

echo "🚀 Lancement analyse Pattern W pour CPI..."
echo ""

cd "$(dirname "$0")/.."

python scripts/analysis/analyze_cpi_pattern_w.py

echo ""
echo "✅ Analyse terminée"
