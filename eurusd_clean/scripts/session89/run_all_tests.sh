#!/bin/bash
# LANCEMENT COMPLET SESSION 89
# Test séquence complète : validation logique → diagnostic → tests réels

echo "================================================================================"
echo "🚀 SESSION 89 - TESTS COMPLETS FALLBACK ROBUSTE"
echo "================================================================================"
echo ""

cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session89

# Étape 1 : Validation logique
echo "📋 ÉTAPE 1/4 : Validation logique surprise_utils..."
echo "--------------------------------------------------------------------------------"
python validate_logic.py
if [ $? -ne 0 ]; then
    echo "❌ Validation logique échouée - ARRÊT"
    exit 1
fi
echo ""

# Étape 2 : Diagnostic colonnes DB
echo "📋 ÉTAPE 2/4 : Diagnostic colonnes base de données..."
echo "--------------------------------------------------------------------------------"
python check_columns.py
if [ $? -ne 0 ]; then
    echo "❌ Colonnes manquantes - ARRÊT"
    exit 1
fi
echo ""

# Étape 3 : Test cas 01.08.2025
echo "📋 ÉTAPE 3/4 : Test cas 01.08.2025 (Surprise 500%)..."
echo "--------------------------------------------------------------------------------"
python test_amplification_0108.py
echo ""

# Étape 4 : Test multi-dates (PRINCIPAL)
echo "📋 ÉTAPE 4/4 : Test multi-dates (3 dates critiques)..."
echo "--------------------------------------------------------------------------------"
python test_multi_dates.py
echo ""

echo "================================================================================"
echo "✅ TESTS SESSION 89 TERMINÉS"
echo "================================================================================"
echo ""
echo "📊 Vérifier les résultats ci-dessus pour décider :"
echo "   - Si MAE < 30 pips → Session 90 = Intégration production"
echo "   - Si MAE > 30 pips → Analyser et ajuster"
echo ""
echo "================================================================================"
