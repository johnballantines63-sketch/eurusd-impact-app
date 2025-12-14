#!/bin/bash

# Script lancement analyse complète tendances 72h
# Session 101.5 - Méthodologie André

echo "=========================================="
echo "ANALYSE COMPLÈTE TENDANCES 72H"
echo "=========================================="
echo ""
echo "Méthodologie :"
echo "1. Baseline amp=2.5"
echo "2. Amplification parfaite par date"
echo "3. Métriques tendance : R², durée, amplitude, score"
echo "4. Corrélations multiples"
echo "5. Analyse qualitative patterns"
echo ""
echo "Durée estimée : 30-60 secondes"
echo ""
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 analyze_trends_complete.py

echo ""
echo "=========================================="
echo "Analyse terminée"
echo "=========================================="
echo ""
echo "Fichier résultats : trends_analysis_complete.csv"
echo ""
