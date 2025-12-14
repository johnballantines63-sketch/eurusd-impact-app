#!/bin/bash

echo ""
echo "========================================================================"
echo " 🚨 CORRECTION CRITIQUE - BOUCLE ÉCRASANTE"
echo "========================================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Répertoire du projet
PROJECT_DIR="$HOME/Desktop/eurusd_news_impact_calculator_MPC"
cd "$PROJECT_DIR" || exit 1

echo "📍 Répertoire : $PROJECT_DIR"
echo ""

# Étape 1 : Correction CRITIQUE
echo "========================================================================"
echo " ÉTAPE 1/5 : Correction du Planificateur"
echo "========================================================================"
echo ""
echo -e "${RED}🚨 PROBLÈME IDENTIFIÉ :${NC}"
echo "  Le Planificateur crée correctement events_for_generator,"
echo "  puis une boucle l'ÉCRASE en ajoutant tous les événements individuels !"
echo ""
echo -e "${GREEN}✅ SOLUTION :${NC}"
echo "  Commenter la boucle qui écrase tout"
echo ""

python3 corrections_graphique/fix_remove_loop_CRITICAL.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Échec de la correction${NC}"
    exit 1
fi

echo ""

# Étape 2 : Nettoyage cache Python
echo "========================================================================"
echo " ÉTAPE 2/5 : Nettoyage cache Python"
echo "========================================================================"
echo ""

echo "🧹 Suppression __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo -e "${GREEN}✅ Cache Python nettoyé${NC}"
echo ""

# Étape 3 : Nettoyage cache Streamlit
echo "========================================================================"
echo " ÉTAPE 3/5 : Nettoyage cache Streamlit"
echo "========================================================================"
echo ""

rm -rf ~/.streamlit/cache/* 2>/dev/null
rm -rf .streamlit/cache/* 2>/dev/null
rm -rf ~/.cache/streamlit/* 2>/dev/null

echo -e "${GREEN}✅ Cache Streamlit nettoyé${NC}"
echo ""

# Étape 4 : Cache navigateur
echo "========================================================================"
echo " ÉTAPE 4/5 : ⚠️  CACHE NAVIGATEUR (ACTION MANUELLE)"
echo "========================================================================"
echo ""
echo -e "${RED}🔔 CRITIQUE : Vous DEVEZ vider le cache navigateur !${NC}"
echo ""
echo -e "${YELLOW}Recommandé : Fermer ET rouvrir le navigateur${NC}"
echo ""
echo "Option A : Vider cache"
echo "  1. Cmd+Shift+Del"
echo "  2. Cocher 'Cache'"
echo "  3. Cliquer 'Effacer'"
echo ""
echo "Option B : Mode privé (RECOMMANDÉ)"
echo "  1. FERMER complètement le navigateur"
echo "  2. Cmd+Shift+N → Mode privé"
echo "  3. Aller sur URL Streamlit"
echo ""
echo "Appuyez sur Entrée quand c'est fait..."
read -r

echo ""

# Étape 5 : Lancement Streamlit
echo "========================================================================"
echo " ÉTAPE 5/5 : Lancement Streamlit"
echo "========================================================================"
echo ""

# Activer environnement virtuel
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Démarrage Streamlit..."
echo ""
streamlit run fx_impact_app/streamlit_app/Home.py --server.headless true

echo ""
echo "========================================================================"
echo " 🎯 TEST À EFFECTUER"
echo "========================================================================"
echo ""
echo "Dans Planificateur Multi-Événements :"
echo ""
echo "1. Date : 11/09/2025 14:30"
echo "2. Charger événements US"
echo "3. Prix départ : 1.09500"
echo "4. Générer graphique"
echo ""
echo -e "${GREEN}✅ RÉSULTAT ATTENDU :${NC}"
echo "   Prix final : ~1.15000-1.15500"
echo "   Amplitude : ~56 pips ✅"
echo ""
echo -e "${RED}❌ SI TOUJOURS INCORRECT :${NC}"
echo "   Prix final : 1.12666"
echo "   Amplitude : 316 pips ❌"
echo ""
echo "   → Cache navigateur pas vidé !"
echo "   → FERMER complètement navigateur"
echo "   → Rouvrir en mode privé"
echo ""
echo "========================================================================"
echo ""
