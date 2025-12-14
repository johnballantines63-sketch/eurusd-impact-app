#!/bin/bash

# Script d'exécution test cluster calculator
# Session 113 - Étape 2/4

cd "$(dirname "$0")/../.."

echo "======================================================================"
echo "TEST MODULE CLUSTER_IMPACT_CALCULATOR - SESSION 113"
echo "======================================================================"
echo ""

# Activer environnement virtuel
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "❌ Erreur: .venv/bin/activate introuvable"
    exit 1
fi

# Exporter API key si nécessaire
export EODHD_API_KEY="68ac152b303f79.26633922"

# Exécuter le test
python scripts/session113/test_cluster_calculator_11sept.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ SUCCÈS - MODULE VALIDÉ"
    echo "======================================================================"
else
    echo ""
    echo "======================================================================"
    echo "❌ ÉCHEC - AJUSTEMENTS NÉCESSAIRES"
    echo "======================================================================"
fi

exit $exit_code
