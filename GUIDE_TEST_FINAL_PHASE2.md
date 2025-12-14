# 🎯 GUIDE DE TEST FINAL - Phase 2 Pullback Graphique

**Date:** 14 octobre 2025
**Version:** 8.6.2
**Status:** Modification appliquée ✅ - Tests requis ⏳

---

## ✅ MODIFICATIONS APPLIQUÉES

### 1. Fichiers modifiés:
- ✅ `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`
  - Ligne ~2052: Bloc génération graphique remplacé
  - Nouveau système avec pullback visuel intégré

### 2. Fonctions disponibles:
- ✅ `generate_candlestick_curve_from_phases()` dans `price_curve_generator.py`
- ✅ `create_sequential_phases_chart()` dans `price_curve_generator.py`
- ✅ `display_sequential_timeline()` dans `streamlit_sequential_ui.py`

---

## 🧪 ÉTAPE 2 : TEST PYTHON (Optionnel - 2 min)

Si tu veux vérifier que les imports fonctionnent:

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 test_pullback_graph_fixed.py
```

**Résultat attendu:**
```
✅ TOUS LES TESTS PASSÉS !
```

**Note:** Ce test vérifie uniquement les imports et la génération de courbe. Le test visuel complet se fait dans Streamlit.

---

## 🎨 ÉTAPE 3 : TEST STREAMLIT (CRITIQUE - 10 min)

### A. Lancer l'application

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
streamlit run fx_impact_app/streamlit_app/Home.py
```

### B. Navigation dans l'interface

1. Aller sur la page **"📅 Planificateur Multi-Événements"**
2. Dans la sidebar:
   - **Mode:** Date précise
   - **Date:** 11 septembre 2025
   - **Pays:** US, EU
3. Cliquer **"🔍 Charger Événements"**

### C. Sélection des événements

**Événements attendus le 11/09/2025:**
- ✅ 14:30 - **CPI (US)** + **Jobless Claims (US)**
- ✅ 14:45 - **Current Account (DE)**

**Actions:**
1. Cocher tous les événements 14:30 et 14:45
2. Entrer des valeurs hypothétiques (ou garder les valeurs par défaut)
3. **IMPORTANT:** Cocher ☑️ **"Activer le Mode Timeline Séquentielle"**

### D. Génération du graphique

1. Scroll vers le bas jusqu'à la section **"📈 Évolution Prédite du Cours EUR/USD"**
2. Dans les paramètres:
   - Prix EUR/USD: 1.0950 (ou actuel)
   - Spread: 1.0 pips
   - Durée: 120 min
   - Volatilité: 0.3
3. Cliquer **"🎨 Générer Graphique de Prédiction"**

---

## ✅ VÉRIFICATIONS CRITIQUES

### Message de confirmation
Après avoir cliqué sur "Générer Graphique", tu dois voir:

```
✨ Utilisation du nouveau générateur avec pullback visuel
```

❌ **Si tu vois:** `⚠️ Phases non disponibles, utilisation ancien système vectoriel`
→ Cela signifie que le mode séquentiel n'est pas activé ou que `phases` n'a pas été calculé

### Éléments visuels attendus

**1. GRAPHIQUE avec zones colorées:**
- 🟢 **VERT** : Phase 1 (14:30-14:35) - Mouvement +207 pips
- 🟠 **ORANGE** : Pullback (14:35-14:45) - Descente -82.8 pips ← **NOUVEAU!**
- 🟢 **VERT** : Phase 2 (14:45+) - Mouvement +16.4 pips

**2. MARQUEURS verticaux:**
- 📍 **Ligne orange** à 14:35 avec annotation "🔄 Phase 2, Pullback: -82.8 pips"
- 📍 **Ligne verte** à 14:30 avec annotation "📍 Phase 1"

**3. STATS sous le graphique:**
```
🔄 Pullback détecté : 10 minutes de descente entre phases
```

**4. LÉGENDE du graphique:**
- □ Pré-événement (gris)
- □ Latence (jaune)
- □ Mouvement (vert/rouge)
- □ **🔄 Pullback (descente)** ← **NOUVEAU!**
- □ Retracement (rose)

---

## ❌ TROUBLESHOOTING

### Problème 1: Message "Phases non disponibles"

**Cause:** Mode séquentiel pas activé ou phases pas calculées

**Solution:**
1. Vérifier que ☑️ "Activer le Mode Timeline Séquentielle" est **COCHÉ**
2. Recharger la page (Ctrl+R)
3. Re-sélectionner les événements

### Problème 2: Pas de zone orange visible

**Cause:** Événements trop espacés (> 30 min)

**Solution:**
- Utiliser la date **11 septembre 2025** (événements espacés de 15 min)
- Si autre date, vérifier que deux événements sont < 30 min d'écart

### Problème 3: Import Error

**Cause:** Cache Python corrompu

**Solution:**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
streamlit cache clear
streamlit run fx_impact_app/streamlit_app/Home.py
```

### Problème 4: Graphique ne se génère pas

**Cause:** Erreur dans le code ou événements mal configurés

**Solution:**
1. Ouvrir la console du navigateur (F12) pour voir les erreurs
2. Vérifier le terminal où Streamlit tourne
3. Si erreur "phases not defined", vérifier que le mode séquentiel est activé

---

## 📊 CRITÈRES DE SUCCÈS

Pour que la Phase 2 soit considérée comme **✅ COMPLÉTÉE**, tu dois observer:

### ✅ Critères minimaux (OBLIGATOIRES):
1. [ ] Message "✨ Utilisation du nouveau générateur avec pullback visuel"
2. [ ] Zone **ORANGE** visible entre 14:35 et 14:45
3. [ ] Stats "🔄 Pullback détecté : X minutes"
4. [ ] Légende contient "🔄 Pullback (descente)"

### ✅ Critères de qualité (SOUHAITABLES):
5. [ ] Prix descend d'environ 82.8 pips dans zone orange
6. [ ] Marqueur vertical orange avec annotation pullback
7. [ ] Graphique responsive (zoom fonctionne)
8. [ ] Pas d'erreur dans console/terminal

---

## 🎉 SI TOUS LES TESTS PASSENT

**Tu peux confirmer que:**
- ✅ Phase 1 complétée (calcul pullback)
- ✅ Phase 2 complétée (affichage graphique)
- ✅ Version 8.6.2 opérationnelle !

**Prochaine étape:**
Créer un rapport final avec screenshots et observations

---

## 📸 CAPTURES D'ÉCRAN RECOMMANDÉES

Pour documentation:
1. Screenshot du graphique complet avec zone orange
2. Screenshot des stats "Pullback détecté"
3. Screenshot de la légende du graphique
4. Screenshot du message "Utilisation du nouveau générateur"

---

## 📞 EN CAS DE PROBLÈME

Si problème bloquant:
1. Vérifier le fichier de log Streamlit dans le terminal
2. Consulter `RAPPORT_EXHAUSTIF_PHASE2_GRAPHIQUE_PULLBACK.md` section 7 (Troubleshooting)
3. Vérifier que tous les fichiers sont bien présents:
   - `fx_impact_app/src/price_curve_generator.py`
   - `fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py`
   - `fx_impact_app/src/sequence_multi_event_timeline_v86.py`

---

**Bonne chance pour les tests ! 🚀**

**Temps estimé total:** 10-15 minutes
**Difficulté:** Faible (instructions détaillées)
