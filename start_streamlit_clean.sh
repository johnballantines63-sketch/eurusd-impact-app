#!/bin/bash

################################################################################
# Script de Lancement Streamlit avec Nettoyage Cache Navigateur
# Utilisation : ./start_streamlit_clean.sh
################################################################################

echo "════════════════════════════════════════════════════════════════════════"
echo " 🧹 NETTOYAGE CACHE NAVIGATEURS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Détecter quel navigateur est en cours d'exécution
BROWSER_RUNNING=""

if pgrep -x "Google Chrome" > /dev/null; then
    BROWSER_RUNNING="Chrome"
    echo "✅ Chrome détecté"
elif pgrep -x "Safari" > /dev/null; then
    BROWSER_RUNNING="Safari"
    echo "✅ Safari détecté"
elif pgrep -x "firefox" > /dev/null; then
    BROWSER_RUNNING="Firefox"
    echo "✅ Firefox détecté"
else
    echo "ℹ️  Aucun navigateur détecté en cours d'exécution"
fi

echo ""
echo "🧹 Nettoyage des caches..."
echo ""

# Chrome
if [ -d "$HOME/Library/Caches/Google/Chrome" ]; then
    echo "   → Chrome cache..."
    rm -rf "$HOME/Library/Caches/Google/Chrome/Default/Cache"/* 2>/dev/null
    rm -rf "$HOME/Library/Caches/Google/Chrome/Default/Code Cache"/* 2>/dev/null
    rm -rf "$HOME/Library/Caches/Google/Chrome/Default/GPUCache"/* 2>/dev/null
    echo "   ✅ Chrome cache vidé"
fi

# Safari
if [ -d "$HOME/Library/Caches/com.apple.Safari" ]; then
    echo "   → Safari cache..."
    rm -rf "$HOME/Library/Caches/com.apple.Safari"/* 2>/dev/null
    echo "   ✅ Safari cache vidé"
fi

# Firefox
if [ -d "$HOME/Library/Caches/Firefox" ]; then
    echo "   → Firefox cache..."
    rm -rf "$HOME/Library/Caches/Firefox/Profiles/*/cache2"/* 2>/dev/null
    echo "   ✅ Firefox cache vidé"
fi

# Streamlit cache
if [ -d "$HOME/.streamlit/cache" ]; then
    echo "   → Streamlit cache..."
    rm -rf "$HOME/.streamlit/cache"/* 2>/dev/null
    echo "   ✅ Streamlit cache vidé"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo " 🚀 LANCEMENT STREAMLIT"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Aller dans le répertoire du projet
cd ~/Desktop/eurusd_news_impact_calculator_MPC

# Lancer Streamlit
echo "📊 Démarrage de l'application..."
echo ""
echo "💡 Astuce : Le cache navigateur sera vidé à chaque lancement"
echo "💡 Pour arrêter : Ctrl+C dans ce terminal"
echo ""

streamlit run fx_impact_app/streamlit_app/Home.py
