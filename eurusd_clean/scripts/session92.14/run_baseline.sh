#!/bin/bash

# Script lancement test baseline - Session 92.14
# Exécute le test baseline du Planificateur

echo "=========================================="
echo "TEST BASELINE PLANIFICATEUR - SESSION 92.14"
echo "=========================================="
echo ""

# Vérifier environnement Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé"
    exit 1
fi

echo "✅ Python 3 trouvé : $(python3 --version)"
echo ""

# Se placer dans le bon répertoire
cd "$(dirname "$0")"

echo "📂 Répertoire : $(pwd)"
echo ""

# Exécuter test baseline
echo "🚀 Lancement test baseline..."
echo ""

python3 test_baseline_planificateur.py

echo ""
echo "=========================================="
echo "✅ SCRIPT TERMINÉ"
echo "=========================================="
