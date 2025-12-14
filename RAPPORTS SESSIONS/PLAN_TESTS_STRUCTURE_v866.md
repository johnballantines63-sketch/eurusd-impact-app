# 🧪 PLAN DE TESTS STRUCTURÉ - v8.6.5 → v8.6.6

**Date :** 16 octobre 2025  
**Objectif :** Valider corrections et multiplicateurs

---

## PHASE 1 : DEBUG GRAPHIQUE (URGENT)

### Test 1.1 : Vérification logs calcul

**Pré-requis :** Prints DEBUG ajoutés (voir DEMARRAGE_RAPIDE_DEBUG_v865.md)

**Procédure :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
streamlit run fx_impact_app/streamlit_app/Home.py
```

1. Page "Planificateur Multi-Événements"
2. Date : 11 septembre 2025
3. Événements : 14:30 + 14:45
4. Mode séquentiel : ✅ Activé
5. Générer graphique

**Validation logs Phase 1 :**
```
🔍 DEBUG PHASE 1
Impact brut calculé     : 207.0 pips          ← ✅ Attendu ~207
Facteur atténuation     : 1.00                ← ✅ Attendu 1.00
Pullback depuis Phase-1 : 0.0 pips            ← ✅ Attendu 0
Multiplicateur appliqué : 1.26×               ← ✅ Attendu 1.26
➡️ IMPACT FINAL          : 260.8 pips         ← ✅ Attendu ~260
Direction               : UP                  ← ✅ Attendu UP
```

**Critères succès :**
- ☑️ Impact final entre 255-265 pips
- ☑️ Multiplicateur = 1.26

**Si échec :**
- Impact trop élevé → Vérifier ligne ~490 sequence_multi_event_timeline_v86.py
- Multiplicateur incorrect → Vérifier condition `if phase_idx == 0:`

---

**Validation logs Phase 2 :**
```
🔍 DEBUG PHASE 2
Impact brut calculé     : 25.0 pips           ← ✅ Attendu ~25
Facteur atténuation     : 1.00                ← ✅ Attendu 1.00
Pullback depuis Phase-1 : 180.0 pips          ← ✅ Attendu ~180
Multiplicateur appliqué : 16.00×              ← ⚠️ Variable (compensation + ×8.8)
➡️ IMPACT FINAL          : 400.0 pips         ← ✅ Attendu ~400
Direction               : UP                  ← ✅ Attendu UP
```

**Message complémentaire attendu :**
```
🚀 Phase 2 REBOND: compensation 180.0 + momentum 220.0 = 400.0
```

**Critères succès :**
- ☑️ Impact final entre 395-405 pips
- ☑️ Compensation = pullback (~180)
- ☑️ Momentum = brut × 8.8 (~220)

**Si échec :**
- Impact trop faible → Vérifier condition `elif phase_idx > 0 and pullback_pips > 0:`
- Momentum incorrect → Vérifier `momentum = impact_combined * 8.8`

---

**Validation logs Graphique :**
```
📊 Minute   0 | Phase: pre_event     | Impact:    +0.0 pips | Target: 1.16810 | Current: 1.16810
📊 Minute   5 | Phase: mouvement     | Impact:  +140.0 pips | Target: 1.16950 | Current: 1.16950
📊 Minute  10 | Phase: mouvement     | Impact:  +210.0 pips | Target: 1.17020 | Current: 1.17020
📊 Minute  15 | Phase: mouvement     | Impact:  +260.0 pips | Target: 1.17070 | Current: 1.17070
📊 Minute  20 | Phase: pullback      | Impact:  -100.0 pips | Target: 1.16970 | Current: 1.16970
📊 Minute  25 | Phase: pullback      | Impact:  -180.0 pips | Target: 1.16890 | Current: 1.16890
📊 Minute  30 | Phase: mouvement     | Impact:  +200.0 pips | Target: 1.17090 | Current: 1.17090
📊 Minute  35 | Phase: mouvement     | Impact:  +300.0 pips | Target: 1.17190 | Current: 1.17190
📊 Minute  40 | Phase: mouvement     | Impact:  +400.0 pips | Target: 1.17290 | Current: 1.17290
```

**Critères succès :**
- ☑️ Minute 15 : Target ~1.1707 (260 pips depuis départ)
- ☑️ Minute 25 : Target ~1.1689 (180 pips descente pullback)
- ☑️ Minute 40 : Target ~1.1729 (400 pips depuis creux pullback)

**Si échec :**
- Valeurs ×10 trop élevées → Bug conversion pips/prix (ligne ~362 price_curve_generator.py)
- Cumul phases → Bug séquence phases (ligne ~320-400 price_curve_generator.py)

---

### Test 1.2 : Validation graphique Plotly

**Après correction selon logs Test 1.1**

**Vérifications visuelles :**

1. **Axe Y (prix) :**
   - Départ : 1.16810 ✅
   - Pic Phase 1 : ~1.17070 (pas 1.19220 ❌)
   - Creux pullback : ~1.16890 (pas 1.14525 ❌)
   - Pic Phase 2 : ~1.17290 (pas 1.18941 ❌)

2. **Couleurs :**
   - Phase 1 mouvement : VERT ✅
   - Zone pullback : ORANGE ✅
   - Phase 2 mouvement : VERT ✅

3. **Annotations :**
   - Phase 1 : "📍 Phase 1 - Impact: +260.8 pips"
   - Phase 2 : "🔄 Phase 2 - Pullback: -180.0 pips - Impact: +400.0 pips"

4. **Légende :**
   - 🟢 Mouvement (vert)
   - 🟠 Pullback (orange)
   - 🟡 Latence (jaune pâle)

**Critères succès :**
- ☑️ Tous les prix dans plage réaliste (1.168-1.174)
- ☑️ Zone orange visible entre 14:35 et 14:45
- ☑️ Annotations avec bonnes valeurs

**Si échec :**
- Axes décalés → Vérifier fig.update_yaxes() dans create_sequential_phases_chart()
- Couleurs incorrectes → Vérifier phase_colors dict
- Annotations absentes → Vérifier boucle add_vline()

---

### Test 1.3 : Comparaison avec MT5 réel

**Superposer graphique prédit et prix MT5 :**

| Temps | Prédit v8.6.6 | Réel MT5 | Écart | Écart % |
|-------|---------------|----------|-------|---------|
| 14:30 | 1.16810 | 1.16810 | 0 | 0% |
| 14:35 | ~1.17070 | 1.17170 | -100 pips | -28% |
| 14:45 | ~1.16890 | 1.16970 | -80 pips | -40% |
| 15:10 | ~1.17290 | 1.17380 | -90 pips | -22% |

**Critères succès :**
- ☑️ Tous les écarts < 100 pips (amélioration vs ×9.3)
- ☑️ Erreur Phase 1 : -20% à -30%
- ☑️ Erreur Phase 2 : -20% à -30%

**Si échec (erreur > 50%) :**
- Multiplicateurs doivent être ajustés
- Retour au calibrage manuel

---

## PHASE 2 : VALIDATION MULTI-DATES

### Test 2.1 : 12 septembre 2025 (jour suivant)

**Hypothèse :** Si multiplicateurs v8.6.5 corrects, doivent fonctionner le lendemain

**Procédure :**
1. Streamlit : Date 12 septembre 2025
2. Identifier événements majeurs (NFP ?)
3. Générer prédiction
4. Comparer avec prix MT5 réels

**Données à collecter :**
```
Date : 12/09/2025
Événements : [liste]
Prix départ : [X.XXXXX]
Prix pic Phase 1 : Prédit [XX] pips vs Réel [XX] pips
Pullback : Prédit [XX] pips vs Réel [XX] pips
Prix pic Phase 2 : Prédit [XX] pips vs Réel [XX] pips

Erreurs :
- Phase 1 : [X]%
- Pullback : [X]%
- Phase 2 : [X]%
```

**Critères succès :**
- ☑️ Erreur Phase 1 < 40%
- ☑️ Erreur Pullback < 50%
- ☑️ Erreur Phase 2 < 40%

**Si échec :**
- Erreur > 50% → Multiplicateurs spécifiques au 11 sept
- Ajuster ou créer multiplicateurs adaptatifs

---

### Test 2.2 : 18 septembre 2025 (FOMC)

**Événement majeur différent**

**Procédure identique Test 2.1**

**Particularités FOMC :**
- Volatilité généralement plus élevée
- Peut nécessiter multiplicateurs différents
- Pullback peut être plus agressif

**Critères succès :**
- ☑️ Direction prédite correcte (UP/DOWN)
- ☑️ Erreur < 50% sur amplitude

---

### Test 2.3 : 2 octobre 2025 (Jobless Claims)

**Famille événement différente (inversée)**

**Procédure identique Test 2.1**

**Particularités Jobless Claims :**
- Événement "inversé" (comme Current Account)
- Formule direction peut différer
- Impact généralement moyen (50-100 pips)

**Critères succès :**
- ☑️ Direction correcte malgré inversion
- ☑️ Erreur < 40%

---

### Test 2.4 : Calcul statistiques globales

**Après tests 2.1, 2.2, 2.3 :**

```python
# Calculer MAE et RMSE
import numpy as np

erreurs_phase1 = [test1_err, test2_err, test3_err]
erreurs_phase2 = [test1_err, test2_err, test3_err]

mae_phase1 = np.mean(np.abs(erreurs_phase1))
rmse_phase1 = np.sqrt(np.mean(np.array(erreurs_phase1)**2))

print(f"Phase 1 - MAE: {mae_phase1:.1f}%, RMSE: {rmse_phase1:.1f}%")
print(f"Phase 2 - MAE: {mae_phase2:.1f}%, RMSE: {rmse_phase2:.1f}%")
```

**Critères succès :**
- ☑️ MAE Phase 1 < 35%
- ☑️ MAE Phase 2 < 35%
- ☑️ RMSE < 40%

**Si échec (MAE > 40%) :**
- Multiplicateurs ne se généralisent pas
- Options :
  1. Calibrer par famille événement
  2. Calibrer par niveau volatilité
  3. Machine Learning adaptatif

---

## PHASE 3 : VALIDATION GRAPHIQUE PULLBACK

### Test 3.1 : Vérification zone orange

**Pré-requis :** Tests Phase 1 passés

**Procédure :**
1. Test 11 septembre 2025
2. Graphique généré
3. Vérifier visuellement

**Critères visuels :**
- ☑️ Zone ORANGE entre 14:35 et 14:45
- ☑️ Descente progressive dans zone orange
- ☑️ ~10 chandeliers orange (1 par minute)
- ☑️ Prix descend de ~180 pips

**Validation DataFrame :**
```python
pullback_rows = price_df[price_df['phase'] == 'pullback']
print(f"Nombre minutes pullback : {len(pullback_rows)}")  # Attendu : 8-12
print(f"Prix début : {pullback_rows.iloc[0]['close']:.5f}")
print(f"Prix fin : {pullback_rows.iloc[-1]['close']:.5f}")
amplitude = (pullback_rows.iloc[0]['close'] - pullback_rows.iloc[-1]['close']) * 10000
print(f"Amplitude : {amplitude:.1f} pips")  # Attendu : ~180
```

**Critères succès :**
- ☑️ 8-12 minutes pullback
- ☑️ Amplitude 170-190 pips

---

### Test 3.2 : Stats pullback affichées

**UI doit afficher :**

```
📊 STATISTIQUES PULLBACK

Col1 : 🔄 Durée Pullback
       10 minutes

Col2 : 📉 Amplitude Pullback
       -180.0 pips ↓

Col3 : 📈 Impact Total
       +260.0 pips (pic max)
```

**Critères succès :**
- ☑️ Durée affichée
- ☑️ Amplitude affichée avec flèche ↓
- ☑️ Impact total affiché

---

## PHASE 4 : TESTS DE RÉGRESSION

### Test 4.1 : Événement unique (pas de pullback)

**Objectif :** Vérifier que système fonctionne sans pullback

**Procédure :**
1. Date avec UN SEUL événement majeur
2. Exemple : 4 octobre 2025 (NFP seul)
3. Générer prédiction

**Validation :**
- ☑️ Pas de zone orange (pullback_pips = 0)
- ☑️ Phase 1 avec multiplicateur ×1.26
- ☑️ Pas de Phase 2
- ☑️ Graphique affiche montée puis retracement

**Critères succès :**
- ☑️ Pas de crash
- ☑️ Prédiction cohérente

---

### Test 4.2 : Phases éloignées (> 30 min)

**Objectif :** Vérifier seuil 30 minutes

**Procédure :**
1. Date avec 2 événements espacés > 30 min
2. Exemple : 14:30 et 15:15
3. Générer prédiction

**Validation :**
- ☑️ pullback_pips = 0 pour Phase 2
- ☑️ Phase 2 utilise multiplicateur standard ×1.5
- ☑️ Pas de zone orange entre phases

**Critères succès :**
- ☑️ Comportement conforme documentation

---

### Test 4.3 : 3+ événements rapprochés

**Objectif :** Système gère-t-il 3 phases ?

**Procédure :**
1. Date avec 3 événements < 30 min chacun
2. Générer prédiction

**Validation :**
- ☑️ 3 phases créées
- ☑️ Pullback calculé entre Phase 1→2
- ☑️ Pullback calculé entre Phase 2→3
- ☑️ 2 zones orange

**Critères succès :**
- ☑️ Pas de crash
- ☑️ Logique pullback appliquée correctement

---

## PHASE 5 : TESTS LIMITES

### Test 5.1 : Volatilité extrême

**Scenario :** Événement avec surprise > 15

**Attendu :**
- Facteur atténuation = 1.20 (amplification)
- Impact peut dépasser 500 pips

**Validation :**
- ☑️ Système gère grandes amplitudes
- ☑️ Graphique reste lisible

---

### Test 5.2 : Direction incohérente

**Scenario :** Surprise positive mais direction DOWN

**Attendu :**
- Facteur atténuation = 1.00
- Direction prédite correcte

**Validation :**
- ☑️ Système ne confond pas surprise et direction

---

### Test 5.3 : Données manquantes

**Scenario :** Événement sans historical MFE

**Attendu :**
- Fallback sur valeur par défaut (10 pips ?)
- Message warning dans logs

**Validation :**
- ☑️ Pas de crash
- ☑️ Warning clair

---

## RÉCAPITULATIF DES TESTS

### Matrice de validation

| Phase | Test | Status | Critique | Temps |
|-------|------|--------|----------|-------|
| 1 | Debug graphique ×9.3 | ⏳ | 🔴 OUI | 1-2h |
| 2 | Multi-dates (3 tests) | ⏳ | ⚠️ OUI | 1h |
| 3 | Graphique pullback | ⏳ | ⚠️ MOYEN | 30min |
| 4 | Régression (3 tests) | ⏳ | ⚠️ FAIBLE | 1h |
| 5 | Limites (3 tests) | ⏳ | 💡 OPTIONNEL | 30min |

**Temps total estimé :** 4-5 heures

---

## CRITÈRES DE RÉUSSITE GLOBAUX

### ✅ Succès minimal (MVP)
- ☑️ Test 1.1 : Logs corrects (260 pips, 400 pips)
- ☑️ Test 1.2 : Graphique affiche bonnes valeurs
- ☑️ Test 1.3 : Erreur < 30% vs MT5

### ✅ Succès standard
- ☑️ Succès minimal +
- ☑️ Test 2.1, 2.2, 2.3 : MAE < 35%
- ☑️ Test 3.1 : Zone orange visible

### ✅ Succès complet
- ☑️ Succès standard +
- ☑️ Tests Phase 4 : Pas de régression
- ☑️ Tests Phase 5 : Gestion cas limites

---

## DOCUMENTATION DES RÉSULTATS

### Template rapport test

```markdown
# RAPPORT TEST [DATE] - v8.6.6

## Configuration
- Date testée : [XX/XX/2025]
- Événements : [liste]
- Version : v8.6.6

## Résultats

### Phase 1
- Prédit : [XX] pips
- Réel : [XX] pips
- Erreur : [X]%

### Pullback
- Prédit : [XX] pips
- Réel : [XX] pips
- Erreur : [X]%

### Phase 2
- Prédit : [XX] pips
- Réel : [XX] pips
- Erreur : [X]%

## Graphique
[Screenshot ou description]

## Conclusion
- Status : ✅ PASSÉ / ❌ ÉCHOUÉ
- Actions requises : [liste]
```

---

## COMMANDES UTILES

```bash
# Lancer test complet
cd ~/Desktop/eurusd_news_impact_calculator_MPC
./run_tests.sh  # Si script créé

# Test unitaire Python
python3 test_pullback_graph.py

# Validation manuelle
streamlit run fx_impact_app/streamlit_app/Home.py

# Nettoyer avant chaque test
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
rm -rf ~/.streamlit/cache 2>/dev/null
```

---

**FIN DU PLAN DE TESTS**

**Créé le :** 16 octobre 2025  
**Pour :** EUR/USD News Impact Calculator v8.6.6  
**Durée tests complète :** 4-5 heures
