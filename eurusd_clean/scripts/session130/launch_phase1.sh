#!/bin/bash
# LAUNCHER VALIDATION PHASE 1 - SESSION 130
# ==========================================
# Lance validation rapide puis propose scan complet

cd "$(dirname "$0")/../.."

echo "════════════════════════════════════════════════════════════════════════════════"
echo "LAUNCHER PHASE 1 - SESSION 130"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Étape 1 : VALIDATION RAPIDE (quelques secondes)"
echo "   Tests infrastructure sur 3 dates connues"
echo ""

# Lancer validation rapide
python scripts/session130/validate_phase1_quick.py

# Capturer code retour
EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ VALIDATION RÉUSSIE"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "🚀 Prêt à lancer SCAN COMPLET 2023-2025"
    echo ""
    echo "⏱️  Durée estimée : ~45 minutes"
    echo "📊 Output : ~100-150 mouvements détectés"
    echo ""
    read -p "Lancer SCAN COMPLET maintenant ? (o/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo ""
        echo "🚀 LANCEMENT SCAN COMPLET..."
        echo ""
        python scripts/session130/run_phase1.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "════════════════════════════════════════════════════════════════════════════════"
            echo "✅✅✅ PHASE 1 TERMINÉE AVEC SUCCÈS ✅✅✅"
            echo "════════════════════════════════════════════════════════════════════════════════"
            echo ""
            echo "📂 Fichiers créés :"
            echo "   ✅ scripts/session130/movements_2023_2025_complete.json"
            echo "   ✅ scripts/session130/patterns_classified.json"
            echo "   ✅ scripts/session130/reference_cases.json"
            echo ""
            echo "🎯 PROCHAINE ÉTAPE :"
            echo "   Revenir vers Claude avec résultats pour validation"
            echo ""
        else
            echo ""
            echo "❌ SCAN COMPLET ÉCHOUÉ"
            echo "   Vérifier logs ci-dessus"
            echo ""
        fi
    else
        echo ""
        echo "⏸️  SCAN COMPLET ANNULÉ"
        echo ""
        echo "Pour lancer plus tard :"
        echo "   python scripts/session130/run_phase1.py"
        echo ""
    fi
else
    echo "⚠️  VALIDATION PARTIELLE ou ÉCHOUÉE"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Vérifier logs ci-dessus avant de continuer"
    echo ""
    echo "Pour forcer scan complet quand même :"
    echo "   python scripts/session130/run_phase1.py"
    echo ""
fi
