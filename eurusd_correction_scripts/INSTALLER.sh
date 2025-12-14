#!/bin/bash
# Script d'installation et configuration rapide

echo "🔧 Installation Scripts de Correction - EUR/USD Trading App"
echo "=============================================================="
echo ""

# Rendre les scripts exécutables
echo "📝 Configuration des permissions..."
chmod +x ~/Desktop/eurusd_correction_scripts/01_diagnostic_complet.py
chmod +x ~/Desktop/eurusd_correction_scripts/02_correction_automatique.py
chmod +x ~/Desktop/eurusd_correction_scripts/03_validation_corrections.py
chmod +x ~/Desktop/eurusd_correction_scripts/04_rollback_backup.py

echo "✅ Scripts configurés et prêts à l'emploi"
echo ""
echo "📋 Scripts disponibles :"
echo "   1. 01_diagnostic_complet.py      - Diagnostic sans modification"
echo "   2. 02_correction_automatique.py  - Correction avec backup auto"
echo "   3. 03_validation_corrections.py  - Validation des corrections"
echo "   4. 04_rollback_backup.py        - Restauration depuis backup"
echo ""
echo "🚀 Pour commencer :"
echo "   cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC'"
echo "   python3 ~/Desktop/eurusd_correction_scripts/01_diagnostic_complet.py"
echo ""
echo "📖 Consultez README.md pour le guide complet"
echo ""

# Proposer de lancer le workflow
read -p "Voulez-vous lancer le workflow maintenant ? (o/n): " reponse

if [ "$reponse" = "o" ] || [ "$reponse" = "O" ]; then
    echo ""
    echo "🎬 Lancement du workflow complet..."
    cd "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC"
    
    echo ""
    echo "Étape 1/3 : Diagnostic..."
    python3 ~/Desktop/eurusd_correction_scripts/01_diagnostic_complet.py
    
    echo ""
    read -p "Continuer avec la correction ? (o/n): " continuer
    
    if [ "$continuer" = "o" ] || [ "$continuer" = "O" ]; then
        echo ""
        echo "Étape 2/3 : Correction automatique..."
        python3 ~/Desktop/eurusd_correction_scripts/02_correction_automatique.py
        
        echo ""
        echo "Étape 3/3 : Validation..."
        python3 ~/Desktop/eurusd_correction_scripts/03_validation_corrections.py
        
        echo ""
        echo "✨ Workflow terminé !"
        echo ""
        read -p "Lancer l'application Streamlit ? (o/n): " lancer_app
        
        if [ "$lancer_app" = "o" ] || [ "$lancer_app" = "O" ]; then
            echo ""
            echo "🚀 Lancement de l'application..."
            streamlit run fx_impact_app/streamlit_app/Home.py
        fi
    fi
else
    echo ""
    echo "👍 OK ! Lancez les scripts manuellement quand vous êtes prêt."
fi
