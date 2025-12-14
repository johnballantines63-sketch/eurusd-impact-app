#!/bin/bash

# Test hypothèse tendance sur clusters similaires
# Session 102

echo "=========================================="
echo "TEST IMPACT TENDANCE SUR CLUSTERS"
echo "=========================================="
echo ""
echo "Hypothèse : Tendance 72h forte → amp faible"
echo "            (prix déjà ajusté)"
echo ""
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 test_trend_impact_on_clusters.py

echo ""
echo "=========================================="
echo "Test terminé"
echo "=========================================="
