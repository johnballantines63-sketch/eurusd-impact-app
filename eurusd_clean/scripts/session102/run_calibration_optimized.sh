#!/bin/bash

# LANCEMENT COMPLET CALIBRATION OPTIMISÉE - SESSION 103
# ======================================================
#
# Lance les 3 étapes dans l'ordre :
# 1. Recalcul métriques 44 dates (méthode optimisée)
# 2. Calibration formule amplification
# 3. Affichage résultats

echo "================================================================================"
echo "CALIBRATION FORMULE AMPLIFICATION - MÉTHODE OPTIMISÉE SESSION 103"
echo "================================================================================"
echo ""
echo "Méthode : TOP-N extrema + détection dynamique (14 jours)"
echo "Correction : Fenêtre 72h arbitraire → Détection adaptative"
echo ""
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

# ÉTAPE 1 : Recalcul métriques
echo "ÉTAPE 1/2 : Recalcul métriques 44 dates avec méthode optimisée"
echo "--------------------------------------------------------------------------------"
python3 recalculate_metrics_optimized.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors du recalcul des métriques"
    exit 1
fi

echo ""
echo "================================================================================"
echo ""

# ÉTAPE 2 : Calibration
echo "ÉTAPE 2/2 : Calibration formule amplification"
echo "--------------------------------------------------------------------------------"
python3 calibrate_amp_formula_optimized.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de la calibration"
    exit 1
fi

echo ""
echo "================================================================================"
echo "CALIBRATION TERMINÉE !"
echo "================================================================================"
echo ""
echo "Fichiers générés :"
echo "  - analysis_real_data_optimized.csv (métriques recalculées)"
echo ""
echo "Prochaine étape :"
echo "  - Si formule validée : Intégrer dans Planificateur V2.7"
echo "  - Si partiel/rejeté : Utiliser amp constant 1.2"
echo ""
