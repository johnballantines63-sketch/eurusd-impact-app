#!/bin/bash
# SESSION 11 - COMMANDES D'EXÉCUTION
# Copier-coller ces commandes dans le terminal

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         SESSION 11 - INTÉGRATION v9-CLEAN                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Se placer dans le bon répertoire
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

echo "📂 Répertoire: $(pwd)"
echo ""

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1: TESTER LA FONCTION v9-CLEAN
# ═══════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════════"
echo "ÉTAPE 1: Test de la fonction v9-CLEAN"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "▶️  Lancer: python3 test_v9_clean_function.py"
echo ""
echo "✅ Résultats attendus:"
echo "   • Test 1 (11 sept): 28.50 pips prédit vs 44.2 réel"
echo "   • Test 2 (score 50): 13.87 pips"
echo "   • Test 3 (score NULL): None"
echo "   • Test 4 (tableau): scores 30-100"
echo "   • Test 5 (comparaison): +4.7% pour multi-événements"
echo ""
echo "Appuyer sur Entrée pour continuer..."
read

python3 test_v9_clean_function.py

echo ""
echo "════════════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2: INTÉGRER DANS LE PLANIFICATEUR
# ═══════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "ÉTAPE 2: Intégration automatique dans le planificateur"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  ATTENTION: Cette étape va modifier le fichier:"
echo "   fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
echo ""
echo "✅ Le script va:"
echo "   1. Créer backup automatique avec timestamp"
echo "   2. Modifier predict_impact_fast() pour utiliser v9-CLEAN"
echo "   3. Vérifier que les modifications sont correctes"
echo ""
echo "Appuyer sur Entrée pour continuer (ou Ctrl+C pour annuler)..."
read

python3 integrate_v9_clean.py

echo ""
echo "════════════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3: TESTER AVEC STREAMLIT
# ═══════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "ÉTAPE 3: Test avec Streamlit"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "▶️  Lancer Streamlit: streamlit run fx_impact_app/streamlit_app/Home.py"
echo ""
echo "📋 CHECKLIST TEST:"
echo "   1. Aller sur 'Planificateur Multi-Événements'"
echo "   2. Sélectionner date: 11 septembre 2025"
echo "   3. Charger événements"
echo "   4. Sélectionner événements 14:30 (CPI, Jobless, etc.)"
echo "   5. Entrer valeurs hypothétiques"
echo "   6. VÉRIFIER CONSOLE pour message:"
echo "      🎯 v9-CLEAN: CPI (score 82/100, 6 evt) → 28.5 pips"
echo ""
echo "❌ Si ancien message apparaît (à ne plus voir):"
echo "   📊 CPI: Score 82/100 → facteur 4.10x → MFE 41.0 pips"
echo "   → L'intégration a échoué"
echo ""
echo "Appuyer sur Entrée pour lancer Streamlit..."
read

streamlit run fx_impact_app/streamlit_app/Home.py

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4: RESTAURER SI PROBLÈME
# ═══════════════════════════════════════════════════════════════

# Note: Cette section est documentée mais pas exécutée automatiquement
cat << 'EOF'

════════════════════════════════════════════════════════════════
RESTAURATION EN CAS DE PROBLÈME
════════════════════════════════════════════════════════════════

Si Streamlit crash ou comportement anormal:

1. Trouver le backup créé:
   ls -lt fx_impact_app/streamlit_app/pages/*.backup_session11_*

2. Restaurer:
   cp fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py.backup_session11_YYYYMMDD_HHMMSS \
      fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py

3. Relancer Streamlit pour vérifier

════════════════════════════════════════════════════════════════

EOF

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SESSION 11 TERMINÉE                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Prochaines étapes:"
echo "   • Créer RAPPORT_SESSION11_FINAL.md"
echo "   • Mettre à jour START_HERE.md"
echo "   • Créer SESSION11_RECAP.md"
echo ""
echo "📚 Documentation créée:"
echo "   • SESSION11_INTEGRATION_REPORT.md"
echo "   • SESSION11_PROGRESS.txt"
echo "   • test_v9_clean_function.py"
echo "   • integrate_v9_clean.py"
echo ""
