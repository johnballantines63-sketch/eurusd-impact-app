#!/bin/bash
# ORCHESTRATEUR VALIDATION ÉTENDUE - Session 90
# Exécute validation complète sur 10-15 dates

echo "================================================================================"
echo "🚀 VALIDATION ÉTENDUE COEFFICIENT 0.55 - Session 90"
echo "================================================================================"
echo ""

# Répertoire de travail
SCRIPT_DIR="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90"
cd "$SCRIPT_DIR"

echo "📍 Répertoire : $SCRIPT_DIR"
echo ""

# Étape 1 : Diagnostic 05.09.2025
echo "================================================================================"
echo "ÉTAPE 1/3 : Diagnostic approfondi 05.09.2025 (outlier)"
echo "================================================================================"
echo ""

python3 diagnose_0509_detailed.py

if [ $? -ne 0 ]; then
    echo "❌ ERREUR : Diagnostic 05.09 échoué"
    exit 1
fi

echo ""
echo "✅ Diagnostic 05.09 terminé"
echo ""
read -p "Appuyer sur Entrée pour continuer..."
echo ""

# Étape 2 : Liste dates disponibles
echo "================================================================================"
echo "ÉTAPE 2/3 : Recherche dates disponibles HIGH IMPACT"
echo "================================================================================"
echo ""

python3 list_available_dates.py

if [ $? -ne 0 ]; then
    echo "❌ ERREUR : Liste dates échouée"
    exit 1
fi

echo ""
echo "✅ Liste dates disponibles générée"
echo ""
echo "📋 Fichier CSV créé : dates_disponibles_session90.csv"
echo ""
echo "👉 INSTRUCTION IMPORTANTE :"
echo "   1. Ouvrir dates_disponibles_session90.csv"
echo "   2. Sélectionner 10-15 dates diversifiées :"
echo "      - 3-4 NFP"
echo "      - 3-4 CPI"
echo "      - 2-3 Jobless Claims"
echo "      - 1-2 Retail Sales"
echo "      - 1-2 Autres"
echo "   3. Ajouter ces dates dans validate_extended.py (variable TEST_DATES)"
echo ""
read -p "Dates sélectionnées et ajoutées dans validate_extended.py ? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️ Validation étendue interrompue"
    echo "   → Ajouter dates dans validate_extended.py puis relancer"
    exit 0
fi

# Étape 3 : Validation étendue
echo ""
echo "================================================================================"
echo "ÉTAPE 3/3 : Validation étendue (prédictions)"
echo "================================================================================"
echo ""

python3 validate_extended.py

if [ $? -ne 0 ]; then
    echo "❌ ERREUR : Validation étendue échouée"
    exit 1
fi

echo ""
echo "✅ Validation étendue terminée"
echo ""

# Note finale
echo "================================================================================"
echo "📝 NOTE FINALE"
echo "================================================================================"
echo ""
echo "Ce script a calculé les PRÉDICTIONS pour 10-15 dates."
echo ""
echo "⚠️ PROCHAINE ÉTAPE OBLIGATOIRE :"
echo "   Pour calculer MAE réel, il faut :"
echo "   1. Extraire impacts réels depuis prices_1m (voir Session 86)"
echo "   2. Comparer prédictions vs réalité"
echo "   3. Calculer MAE global"
echo ""
echo "💡 ALTERNATIVE :"
echo "   Utiliser script test_multi_dates.py (Session 89) qui fait déjà cela"
echo "   → Ajouter nouvelles dates dans TEST_DATES de test_multi_dates.py"
echo "   → Relancer test_multi_dates.py"
echo ""
echo "================================================================================"
