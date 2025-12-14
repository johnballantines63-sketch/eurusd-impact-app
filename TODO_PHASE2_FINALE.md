# TODO LIST - PHASE 2 FINALE
## Version 8.6.2 - Intégration Graphique Pullback

**Date :** 14 octobre 2025  
**Status :** ⏳ 1 modification + 1 test

---

## ✅ FAIT (ne pas refaire)

- [x] Créer `generate_candlestick_curve_from_phases()` dans price_curve_generator.py
- [x] Créer `create_sequential_phases_chart()` dans price_curve_generator.py
- [x] Créer `plt_to_rgb()` dans price_curve_generator.py
- [x] Modifier streamlit_sequential_ui.py (imports + display_price_chart_with_pullback)
- [x] Ajouter imports dans 4_Planificateur-Multi-Evenements.py
- [x] Créer scripts de test et patch
- [x] Créer documentation exhaustive

---

## 🎯 À FAIRE MAINTENANT

### ☐ ÉTAPE 1 : Appliquer modification planificateur (5 min)

**Fichier :** `4_Planificateur-Multi-Evenements.py`

**Option A - Automatique (recommandé) :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 apply_pullback_graph_patch.py
```

**Option B - Manuel :**
1. Ouvrir `4_Planificateur-Multi-Evenements.py`
2. Chercher : `if st.button("🎨 Générer Graphique de Prédiction"`
3. Dans ce bloc, chercher : `price_df = generate_candlestick_curve_multi_events(`
4. Remplacer par code dans `MODIFICATION_GRAPHIQUE_PULLBACK.py`
5. Sauvegarder

**Vérification :**
```bash
grep "NOUVEAU v8.6.2 : Générer courbe AVEC PULLBACK VISUEL" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
```
Si résultat → ✅ Modification appliquée

---

### ☐ ÉTAPE 2 : Test validation Python (2 min)

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 test_pullback_graph.py
```

**Résultat attendu :**
```
✅ TOUS LES TESTS PASSÉS !
```

**Si erreur :**
- Vérifier imports (voir section Troubleshooting)
- Nettoyer caches Python

---

### ☐ ÉTAPE 3 : Test Streamlit complet (10 min)

**Commandes :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
streamlit run fx_impact_app/streamlit_app/Home.py
```

**Dans l'interface :**
1. Aller page "📅 Planificateur Multi-Événements"
2. Date : 11 septembre 2025
3. Sélectionner événements 14:30 et 14:45
4. ☑️ Cocher "Mode séquentiel"
5. Cliquer "🎨 Générer Graphique de Prédiction"

**Vérifications visuelles :**
- [ ] Message "✨ Utilisation du nouveau générateur avec pullback visuel"
- [ ] Phase 1 en VERT (14:30-14:35, +207 pips)
- [ ] Zone ORANGE entre 14:35 et 14:45 (pullback)
- [ ] Phase 2 en VERT (14:45+, +16.4 pips)
- [ ] Légende contient "🔄 Pullback (descente)"
- [ ] Stats "🔄 Pullback détecté : 10 minutes"
- [ ] Marqueurs verticaux annotés

---

### ☐ ÉTAPE 4 : Validation finale (3 min)

**Critères de succès :**
- [ ] Pullback calculé : 82.8 pips (affiché en texte)
- [ ] Pullback visible : Zone orange de 10 minutes
- [ ] Prix cohérent : Descend ~82.8 pips dans zone orange
- [ ] Pas d'erreur console
- [ ] Graphique responsive (zoom, hover fonctionnent)

---

### ☐ ÉTAPE 5 : Documentation post-test (5 min)

Si tests OK :
1. Prendre screenshot du graphique
2. Noter observations dans rapport
3. Marquer Phase 2 comme ✅ COMPLÉTÉE

Si problème :
1. Noter erreur exacte
2. Consulter section Troubleshooting (rapport exhaustif)
3. Documenter solution trouvée

---

## 📁 FICHIERS DE RÉFÉRENCE

**Si besoin d'aide :**
- `RESUME_EXECUTIF_REPRISE_PHASE2.md` - Résumé rapide (5 min lecture)
- `RAPPORT_EXHAUSTIF_PHASE2_GRAPHIQUE_PULLBACK.md` - Détails complets (30 min)

**Scripts utiles :**
- `test_pullback_graph.py` - Validation code
- `apply_pullback_graph_patch.py` - Patch auto
- `MODIFICATION_GRAPHIQUE_PULLBACK.py` - Instructions patch manuel

---

## 🚨 EN CAS DE PROBLÈME

### Erreur import
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

### Mode séquentiel non disponible
Vérifier console terminal :
```
🚀 [4_Planificateur] Module v8.6.2 (avec pullback FIX v2) importé avec succès !
```
Si absent → Problème import `sequence_multi_event_timeline_v86`

### Pullback non visible
Debug dans code :
```python
pullback_rows = price_df[price_df['phase'] == 'pullback']
print(f"Pullback : {len(pullback_rows)} minutes")
```

**Plus de détails :** Section 7 du rapport exhaustif

---

## ⏱️ TEMPS ESTIMÉ TOTAL

- Étape 1 : 5 min (patch)
- Étape 2 : 2 min (test Python)
- Étape 3 : 10 min (test Streamlit)
- Étape 4 : 3 min (validation)
- Étape 5 : 5 min (doc)

**TOTAL : ~25 minutes**

---

## 🎯 OBJECTIF FINAL

Après ces 5 étapes :

**✅ Phase 2 COMPLÉTÉE**
- Pullback calculé ✅ (Phase 1)
- Pullback affiché texte ✅ (Phase 1)
- Pullback affiché graphique ✅ (Phase 2)
- Tests validés ✅
- Documentation complète ✅

**→ Projet v8.6.2 opérationnel !**

---

**Dernière mise à jour :** 14 octobre 2025  
**Prochaine action :** Appliquer ÉTAPE 1
