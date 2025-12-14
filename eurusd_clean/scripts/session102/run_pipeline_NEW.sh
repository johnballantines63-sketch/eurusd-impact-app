#!/bin/bash
# PIPELINE COMPLET - MÉTHODOLOGIE ANDRÉ
# Exécute les 5 étapes dans l'ordre

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ PIPELINE COMPLET - ANALYSE AMPLIFICATION vs TENDANCE                        ║"
echo "║ Méthodologie André - Step by step                                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier que step0 existe
if [ ! -f "data/step0_selected_clusters.csv" ]; then
    echo "❌ Fichier manquant : data/step0_selected_clusters.csv"
    echo "   → Exécuter d'abord : python3 step0_extract_30_clusters.py"
    exit 1
fi

echo "✅ step0_selected_clusters.csv trouvé"
echo ""

# ÉTAPE 1
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ÉTAPE 1 : CALCUL IMPACTS PRÉDITS                                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
python3 step1_calculer_impacts_NEW.py
if [ $? -ne 0 ]; then
    echo "❌ ÉTAPE 1 ÉCHOUÉE"
    exit 1
fi
echo ""

# ÉTAPE 2
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ÉTAPE 2 : MESURER IMPACTS RÉELS                                             ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
python3 step2_mesurer_reels_NEW.py
if [ $? -ne 0 ]; then
    echo "❌ ÉTAPE 2 ÉCHOUÉE"
    exit 1
fi
echo ""

# ÉTAPE 3
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ÉTAPE 3 : CALCULER AMPLIFICATIONS PARFAITES                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
python3 step3_amplifications_parfaites_NEW.py
if [ $? -ne 0 ]; then
    echo "❌ ÉTAPE 3 ÉCHOUÉE"
    exit 1
fi
echo ""

# ÉTAPE 4
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ÉTAPE 4 : DÉTECTER TENDANCES                                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
python3 step4_detecter_tendances_NEW.py
if [ $? -ne 0 ]; then
    echo "❌ ÉTAPE 4 ÉCHOUÉE"
    exit 1
fi
echo ""

# ÉTAPE 5
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ÉTAPE 5 : TESTER STRATÉGIES                                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
python3 step5_tester_strategies_NEW.py
if [ $? -ne 0 ]; then
    echo "❌ ÉTAPE 5 ÉCHOUÉE"
    exit 1
fi
echo ""

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║ ✅ PIPELINE TERMINÉ AVEC SUCCÈS                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 FICHIERS GÉNÉRÉS :"
echo "   - data/step1_impacts_predits_NEW.csv"
echo "   - data/step2_impacts_reels_NEW.csv"
echo "   - data/step3_amplifications_parfaites_NEW.csv"
echo "   - data/step4_avec_tendances_NEW.csv"
echo "   - data/step5_resultats_finaux_NEW.csv"
echo ""
