#!/bin/bash

# 🔧 Script d'application de la correction Pullback V6
# Corrige le bug "double négatif" qui causait une dérive d'amplitude

echo "🔧 CORRECTION PULLBACK V6"
echo "=========================="
echo ""
echo "📋 Ce script va :"
echo "   1. Créer un backup de la version actuelle"
echo "   2. Appliquer la correction V6 (modèle de substitution)"
echo "   3. Vérifier que la correction est appliquée"
echo ""

# Demander confirmation
read -p "Voulez-vous continuer ? (o/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "❌ Opération annulée"
    exit 1
fi

echo ""
echo "🚀 Application de la correction..."
echo ""

# Exécuter le script Python
python3 apply_pullback_v6_correction.py

# Vérifier le code de retour
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ CORRECTION APPLIQUÉE AVEC SUCCÈS !"
    echo ""
    echo "⚠️  N'OUBLIEZ PAS :"
    echo "   1. Vider le cache Python :"
    echo "      find . -name '__pycache__' -exec rm -rf {} +"
    echo ""
    echo "   2. Vider le cache navigateur :"
    echo "      Cmd+Shift+Del ou mode privé"
    echo ""
    echo "   3. Tester avec :"
    echo "      • Date : 11/09/2025"
    echo "      • Prix : 1.16810"
    echo "      • Amplitude attendue : ~120-159 pips"
    echo ""
else
    echo ""
    echo "❌ ERREUR lors de l'application de la correction"
    echo "   Consultez les messages ci-dessus pour plus d'infos"
    exit 1
fi
