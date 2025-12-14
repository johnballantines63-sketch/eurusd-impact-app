#!/bin/bash

echo ""
echo "========================================================================"
echo " 🚀 CORRECTION FINALE - AMPLITUDE 463 → 52 PIPS"
echo "========================================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire du projet
PROJECT_DIR="$HOME/Desktop/eurusd_news_impact_calculator_MPC"
cd "$PROJECT_DIR" || exit 1

echo -e "${BLUE}📍 Répertoire : $PROJECT_DIR${NC}"
echo ""

# Étape 1 : Correction FINALE
echo "========================================================================"
echo " ÉTAPE 1/4 : Application de la correction FINALE"
echo "========================================================================"
echo ""
echo -e "${YELLOW}🔧 Cette correction va SIMPLIFIER le code :${NC}"
echo "  - Créer UN événement vectoriel synthétique"
echo "  - Supprimer la boucle complexe sur les événements"
echo "  - Corriger l'amplitude : 463 pips → 52 pips"
echo ""

python3 corrections_graphique/fix_vectorial_FINAL.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Échec de la correction${NC}"
    echo ""
    echo "Voulez-vous continuer quand même ? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Correction FINALE appliquée${NC}"
fi

echo ""

# Étape 2 : Nettoyage cache Streamlit
echo "========================================================================"
echo " ÉTAPE 2/4 : Nettoyage cache Streamlit"
echo "========================================================================"
echo ""

echo "🧹 Suppression du cache Streamlit..."
rm -rf ~/.streamlit/cache/* 2>/dev/null
rm -rf .streamlit/cache/* 2>/dev/null
rm -rf ~/.cache/streamlit/* 2>/dev/null
rm -rf __pycache__ 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo -e "${GREEN}✅ Cache Streamlit nettoyé${NC}"
echo ""

# Étape 3 : Instructions cache navigateur
echo "========================================================================"
echo " ÉTAPE 3/4 : ⚠️  CACHE NAVIGATEUR (ACTION MANUELLE REQUISE)"
echo "========================================================================"
echo ""
echo -e "${RED}🔔 CRITIQUE : Vous DEVEZ vider le cache navigateur !${NC}"
echo ""
echo -e "${YELLOW}Option A : Vider le cache (recommandé)${NC}"
echo "  1. Cmd+Shift+Del (ou Ctrl+Shift+Del sur Windows)"
echo "  2. Cocher 'Images et fichiers en cache'"
echo "  3. Sélectionner 'Tout'"
echo "  4. Cliquer 'Effacer les données'"
echo ""
echo -e "${YELLOW}Option B : Mode privé (plus rapide)${NC}"
echo "  1. Cmd+Shift+N (Chrome) ou Cmd+Shift+P (Firefox/Safari)"
echo "  2. Aller sur l'URL Streamlit qui s'affichera"
echo ""
echo -e "${RED}Sans cette étape, vous verrez encore 463 pips !${NC}"
echo ""
echo "Appuyez sur Entrée quand c'est fait (ou pour continuer)..."
read -r

echo ""

# Étape 4 : Lancement Streamlit
echo "========================================================================"
echo " ÉTAPE 4/4 : Lancement de Streamlit"
echo "========================================================================"
echo ""

echo "🚀 Démarrage de Streamlit..."
echo ""

# Activer l'environnement virtuel s'il existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancer Streamlit avec cache désactivé
STREAMLIT_SERVER_ENABLE_STATIC_SERVING=false streamlit run fx_impact_app/streamlit_app/Home.py --server.headless true

echo ""
echo "========================================================================"
echo " 🎯 VÉRIFICATION À EFFECTUER"
echo "========================================================================"
echo ""
echo "Dans le Planificateur Multi-Événements :"
echo ""
echo "1. Date : 11/09/2025 ou 2025-09-11 14:30"
echo "2. Pays : États-Unis (US)"
echo "3. Charger événements → Sélectionner"
echo "4. Prix départ : 1.16810"
echo "5. Générer Graphique"
echo ""
echo -e "${GREEN}✅ RÉSULTAT ATTENDU :${NC}"
echo "   Prix départ : 1.16810"
echo "   Prix final  : ~1.17370 (56 pips) ✅"
echo ""
echo -e "${RED}❌ RÉSULTAT INCORRECT (SI CACHE NON VIDÉ) :${NC}"
echo "   Prix final  : 1.21441 (463 pips) ❌"
echo ""
echo "Si vous voyez encore 463 pips :"
echo "  → Fermez COMPLÈTEMENT le navigateur"
echo "  → Rouvrez en mode privé (Cmd+Shift+N)"
echo "  → Testez à nouveau"
echo ""
echo "========================================================================"
echo ""
