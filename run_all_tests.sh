#!/bin/bash
# 🧪 SUITE DE TESTS COMPLÈTE - Session 41
# Corrections appliquées : Pré-chargement + Current Account

echo "================================================================================"
echo "🧪 SUITE DE TESTS - SESSION 41"
echo "================================================================================"
echo ""
echo "Corrections appliquées :"
echo "  ✅ #1 - Pré-chargement stats au démarrage"
echo "  ✅ #2 - Suppression normalisation Current Account"
echo ""
echo "================================================================================"
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "test_correction_current_account.py" ]; then
    echo "❌ Erreur : Ce script doit être exécuté depuis le répertoire du projet"
    echo "   cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC"
    exit 1
fi

echo "📍 Répertoire de travail : $(pwd)"
echo ""

# ============================================================================
# TEST 1 : Vérification DB Current Account
# ============================================================================

echo "================================================================================"
echo "TEST 1 : Vérification DB - Current Account"
echo "================================================================================"
echo ""
echo "Ce test vérifie comment Current Account est stocké dans la base de données"
echo ""

read -p "Exécuter Test 1 ? (O/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]] || [[ -z $REPLY ]]; then
    python3 verify_current_account.py
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
fi

echo ""

# ============================================================================
# TEST 2 : Test Correction Current Account
# ============================================================================

echo "================================================================================"
echo "TEST 2 : Test Correction - Current Account dans precomputed_stats"
echo "================================================================================"
echo ""
echo "Ce test vérifie si Current Account est trouvé dans precomputed_stats"
echo "après le chargement depuis la DB"
echo ""

read -p "Exécuter Test 2 ? (O/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]] || [[ -z $REPLY ]]; then
    python3 test_correction_current_account.py
    TEST2_EXIT=$?
    echo ""
    if [ $TEST2_EXIT -eq 0 ]; then
        echo "✅ Test 2 RÉUSSI"
    else
        echo "❌ Test 2 ÉCHOUÉ"
        echo ""
        echo "⚠️ Current Account n'est pas pré-calculé dans la DB"
        echo ""
        read -p "Voulez-vous exécuter le pré-calcul maintenant ? (O/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]] || [[ -z $REPLY ]]; then
            echo ""
            echo "Exécution du pré-calcul..."
            python3 precompute_ULTIMATE_v2.py
            echo ""
            echo "Pré-calcul terminé. Relancer Test 2..."
            python3 test_correction_current_account.py
        fi
    fi
    read -p "Appuyez sur Entrée pour continuer..."
fi

echo ""

# ============================================================================
# TEST 3 : Test d'intégration predict_impact_fast()
# ============================================================================

echo "================================================================================"
echo "TEST 3 : Test d'intégration - predict_impact_fast()"
echo "================================================================================"
echo ""
echo "Ce test simule exactement l'appel à predict_impact_fast() pour Current Account"
echo "et compare l'ancien comportement vs le nouveau"
echo ""

read -p "Exécuter Test 3 ? (O/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]] || [[ -z $REPLY ]]; then
    python3 test_integration_predict_impact.py
    TEST3_EXIT=$?
    echo ""
    if [ $TEST3_EXIT -eq 0 ]; then
        echo "✅ Test 3 RÉUSSI"
    else
        echo "❌ Test 3 ÉCHOUÉ"
    fi
    read -p "Appuyez sur Entrée pour continuer..."
fi

echo ""

# ============================================================================
# TEST 4 : Vérification familles pré-calculées
# ============================================================================

echo "================================================================================"
echo "TEST 4 : État des familles pré-calculées"
echo "================================================================================"
echo ""
echo "Ce test affiche toutes les familles pré-calculées dans la DB"
echo ""

read -p "Exécuter Test 4 ? (O/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]] || [[ -z $REPLY ]]; then
    python3 check_precomputed_families_status.py
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
fi

echo ""

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

echo "================================================================================"
echo "🎯 RÉSUMÉ DES TESTS"
echo "================================================================================"
echo ""
echo "Tous les tests ont été exécutés."
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. 🚀 Redémarrer Streamlit :"
echo "   cd fx_impact_app"
echo "   streamlit run streamlit_app/Home.py"
echo ""
echo "2. 📅 Tester dans l'application :"
echo "   - Aller sur la page Planificateur"
echo "   - Charger les événements du 11 septembre 2025"
echo "   - Sélectionner 'Current Account'"
echo ""
echo "3. ✅ Vérifier que :"
echo "   - Message toast '32 familles chargées' au démarrage"
echo "   - Calcul instantané (< 100ms)"
echo "   - PAS de warning 'Aucun événement historique'"
echo "   - Stats affichées : lat ~10min, mfe ~20pips"
echo ""
echo "================================================================================"
echo ""
echo "📊 TOKENS SESSION 41 : ~140k / 190k utilisés (74%)"
echo "================================================================================"
