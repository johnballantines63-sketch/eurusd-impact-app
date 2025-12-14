#!/bin/bash

echo ""
echo "========================================================================"
echo " 🚀 SOLUTION COMPLÈTE - CORRECTION + TEST"
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

# Étape 1 : Correction
echo "========================================================================"
echo " ÉTAPE 1/4 : Application de la correction"
echo "========================================================================"
echo ""

python3 corrections_graphique/fix_vectorial_impact_complete.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Échec de la correction${NC}"
    echo ""
    echo "Voulez-vous continuer quand même ? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Correction appliquée${NC}"
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

echo -e "${GREEN}✅ Cache Streamlit nettoyé${NC}"
echo ""

# Étape 3 : Instructions cache navigateur
echo "========================================================================"
echo " ÉTAPE 3/4 : ⚠️  CACHE NAVIGATEUR (ACTION MANUELLE REQUISE)"
echo "========================================================================"
echo ""
echo -e "${YELLOW}🔔 IMPORTANT : Vous DEVEZ vider le cache navigateur${NC}"
echo ""
echo "Option A : Vider le cache (recommandé)"
echo "  1. Cmd+Shift+Del (ou Ctrl+Shift+Del sur Windows)"
echo "  2. Cocher 'Images et fichiers en cache'"
echo "  3. Sélectionner 'Tout'"
echo "  4. Cliquer 'Effacer les données'"
echo ""
echo "Option B : Mode privé (plus rapide)"
echo "  1. Cmd+Shift+N (Chrome) ou Cmd+Shift+P (Firefox/Safari)"
echo "  2. Aller sur l'URL Streamlit qui s'affichera"
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

# Lancer Streamlit
streamlit run fx_impact_app/streamlit_app/Home.py --server.headless true

echo ""
echo "========================================================================"
echo " 🎯 TEST À EFFECTUER"
echo "========================================================================"
echo ""
echo "Dans l'interface Streamlit qui vient de s'ouvrir :"
echo ""
echo "1. Aller dans 'Planificateur Multi-Événements'"
echo "2. Sidebar → Charger date : 11/09/2025 ou 2025-09-11 09:30"
echo "3. Pays : États-Unis (US)"
echo "4. Cliquer 'Charger Événements'"
echo "5. Sélectionner les événements disponibles"
echo "6. Renseigner valeurs hypothétiques"
echo "7. Descendre jusqu'à 'Graphique Minute par Minute'"
echo "8. Entrer prix actuel (ex: 1.0950)"
echo "9. Cliquer 'Générer Graphique'"
echo ""
echo -e "${GREEN}✅ RÉSULTAT ATTENDU :${NC}"
echo "   📊 Impact Total      : ~52 pips"
echo "   📈 Amplitude Graphique : ~52-67 pips (PAS 377 !)"
echo "   🎯 Précision         : ~98%"
echo ""
echo "========================================================================"
echo ""
