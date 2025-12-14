#!/bin/bash

################################################################################
# INSTALLATION DU SCRIPT DE LANCEMENT PROPRE
################################################################################

echo "════════════════════════════════════════════════════════════════════════"
echo " 📦 INSTALLATION DU SCRIPT DE LANCEMENT"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Rendre le script exécutable
chmod +x ~/Desktop/eurusd_news_impact_calculator_MPC/start_streamlit_clean.sh

echo "✅ Script rendu exécutable"
echo ""

# Créer un alias dans .zshrc ou .bash_profile
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if [ -n "$SHELL_RC" ]; then
    # Vérifier si l'alias existe déjà
    if ! grep -q "alias streamlit-clean" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Streamlit avec nettoyage cache" >> "$SHELL_RC"
        echo "alias streamlit-clean='~/Desktop/eurusd_news_impact_calculator_MPC/start_streamlit_clean.sh'" >> "$SHELL_RC"
        echo "✅ Alias 'streamlit-clean' ajouté à $SHELL_RC"
        echo ""
        echo "⚠️  Rechargez votre terminal avec : source $SHELL_RC"
    else
        echo "ℹ️  Alias 'streamlit-clean' déjà présent"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo " ✅ INSTALLATION TERMINÉE"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 UTILISATION :"
echo ""
echo "Méthode 1 (Recommandée) :"
echo "  streamlit-clean"
echo ""
echo "Méthode 2 (Chemin complet) :"
echo "  ~/Desktop/eurusd_news_impact_calculator_MPC/start_streamlit_clean.sh"
echo ""
echo "Méthode 3 (Depuis le dossier) :"
echo "  cd ~/Desktop/eurusd_news_impact_calculator_MPC"
echo "  ./start_streamlit_clean.sh"
echo ""
echo "💡 Le cache sera automatiquement vidé à chaque lancement !"
echo ""
