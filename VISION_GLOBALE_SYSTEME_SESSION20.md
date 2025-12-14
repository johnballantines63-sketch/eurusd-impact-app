# 🎯 VISION GLOBALE DU SYSTÈME - SESSION 20

**Date :** 19 octobre 2025  
**Session :** 20  
**Objectif :** Comprendre l'ENSEMBLE du système avant de valider les formules

---

## 🏗️ ARCHITECTURE COMPLÈTE DU SYSTÈME

### Vue d'ensemble : Qu'est-ce qu'on construit ?

**PLANIFICATEUR DE TRADING EUR/USD MULTI-ÉVÉNEMENTS**

Le système prédit **COMPLÈTEMENT** le mouvement EUR/USD suite à des événements économiques :

```
ÉVÉNEMENT(S) → PRÉDICTION COMPLÈTE → GRAPHIQUE COMPLET
    ↓                    ↓                      ↓
  14:30              [Timeline]            Courbe EUR/USD
  CPI US           Avec phases            avec zones colorées
                   et pullbacks
```

---

## 📊 LES 3 COMPOSANTES PRINCIPALES

### 1. PRÉDICTION DE L'IMPACT INITIAL (Phase 1)

**Objectif :** Prédire l'amplitude du premier mouvement

**Formule actuelle (V2 - Session 15) :**
```python
# Calcul de base (v9-CLEAN)
impact_base = -7.08 + 0.419 × empirical_score

# Amplification selon surprise
if score < 40:
    amplification = 1.0  # Filtrage
elif surprise < 5%:
    amplification = 1.0
elif surprise < 15%:
    amplification = 1.0 + (surprise - 5%) × 0.15
else:
    amplification = 2.5  # Plafond

# Impact final
impact_pips = abs(impact_base) × amplification × 0.758
```

**Inputs :**
- `empirical_score` : Score 0-100 de l'événement (dans event_families)
- `surprise` : |(actual - estimate) / estimate|

**Output :**
- Impact prédit en pips (ex: +207 pips)

---

### 2. PRÉDICTION DE LA TIMELINE COMPLÈTE (Phases + Pullbacks)

**Objectif :** Prédire TOUTE la séquence temporelle

**Module : `sequence_multi_event_timeline_v87.py`**

#### 2A. Calcul des phases

**Phase = Période d'impact d'un événement ou groupe d'événements**

```python
Phase {
    'start_time': '2025-09-11 14:30:00',    # Début
    'end_time': '2025-09-11 14:35:00',       # Fin
    'duration_min': 5,                        # Durée
    'impact_combined': +207,                  # Impact en pips
    'direction': +1,                          # Direction (+1/-1)
    'latency': 0.5,                           # Latence avant impact
    'ttr': 5.0,                               # Time To Return
    'event_keys': ['cpi', 'core_cpi'],       # Événements
    'max_score': 65,                          # Score max
    'max_surprise': 0.33                      # Surprise max (33%)
}
```

**Calculs inclus :**
- **Latency (latence)** : Délai entre annonce et début mouvement (0.5-2 min)
- **TTR (Time To Return)** : Durée du mouvement avant stabilisation (3-8 min)
- **Direction** : +1 (hausse) ou -1 (baisse) selon surprise positive/négative

#### 2B. Calcul des pullbacks

**Pullback = Correction entre deux phases**

```python
Pullback {
    'start_time': '2025-09-11 14:35:00',     # Fin phase 1
    'end_time': '2025-09-11 14:45:00',        # Début phase 2
    'pullback_pips': -82.8,                   # Amplitude correction
    'duration_min': 10,                       # Durée
    'from_phase': 0,                          # Phase d'origine
    'to_phase': 1                             # Phase suivante
}
```

**Formule pullback :**
```python
minutes_between = (phase2_start - phase1_end).total_seconds() / 60
pullback_pips = phase1_impact × 0.06 × minutes_between
pullback_pips = min(pullback_pips, phase1_impact × 0.60)  # Max 60%
```

---

### 3. GÉNÉRATION GRAPHIQUE COMPLÈTE

**Objectif :** Transformer la timeline en courbe EUR/USD visuelle

**Module : `price_curve_generator.py`**

#### 3A. Génération de la courbe prix

**Fonction :** `generate_candlestick_curve_from_phases()`

**Processus :**
1. Prix de départ (ex: 1.1000)
2. Pour chaque phase :
   - Ajouter latence (prix plat)
   - Générer mouvement (courbe lissée)
   - Atteindre prix cible
3. Pour chaque pullback :
   - Générer correction (inverse)
   - Durée proportionnelle

**Output :** DataFrame avec colonnes [datetime, open, high, low, close]

#### 3B. Création du graphique Plotly

**Fonction :** `create_sequential_phases_chart()`

**Éléments visuels :**
- 🟢 **Zones vertes** : Phases d'impact (hausse/baisse)
- 🟠 **Zones orange** : Pullbacks (corrections)
- 📍 **Marqueurs** : Début de chaque phase
- 📊 **Annotations** : Impact en pips, durée, TTR
- 📈 **Courbe prix** : Évolution EUR/USD minute par minute

**Légende :**
```
Phase 1 (hausse)
Phase 2 (correction) ← PULLBACK
Phase 3 (nouvelle hausse)
```

---

## 🎯 CE QUE NOUS DEVONS VALIDER EN SESSION 20

### PROBLÈME IDENTIFIÉ

Les **données ont changé** (Session 19) :
- Avant : 33,277 événements (MoM/YoY mélangés)
- Après : 58,449 événements (MoM/YoY distingués)
- Impact : **La formule V2 a été calibrée sur des données biaisées**

### CE QUI DOIT ÊTRE RE-VALIDÉ

#### 1. ✅ Formule impact initial (V2)

**Questions :**
- V2 est-elle toujours optimale avec les vraies données ?
- Les seuils (5%, 15%, plafond 2.5x) sont-ils toujours pertinents ?
- Les nouveaux champs (comparison, change_percentage) peuvent-ils améliorer V2 ?

**Test :**
- Re-mesurer MAE V2 sur TOUS les groupes avec données propres
- Comparer avec Session 17 (MAE 174.9%)
- Analyser cas 11 septembre (erreur 29% → attendu ~13%)

#### 2. ❓ Formule pullback (à re-valider aussi)

**Formule actuelle :**
```python
pullback = phase1_impact × 0.06 × minutes_between
pullback = min(pullback, phase1_impact × 0.60)
```

**Questions :**
- Les facteurs 0.06 et 0.60 sont-ils toujours corrects ?
- Avec les données propres, les pullbacks historiques sont-ils différents ?

**Note :** Pas prioritaire car pas de données pullback historiques calculées

#### 3. ❓ Formule latence/TTR (à investiguer)

**Formules actuelles (empiriques) :**
```python
latency = 0.5 + (empirical_score / 100) × 1.5  # 0.5-2 min
ttr = 3 + (empirical_score / 100) × 5          # 3-8 min
```

**Questions :**
- Ces formules sont-elles validées sur données réelles ?
- Peut-on calculer latency/TTR réels depuis prices_1m ?

---

## 📋 PLAN D'ANALYSE SESSION 20 (RÉVISÉ)

### PHASE 1 : Re-validation formule impact (PRIORITÉ 1) ✅

**Script 1 :** `remeasure_v2_with_clean_data_session20.py`
- Re-mesurer V2 sur tous les groupes
- Comparer avec V1
- Analyser 11 septembre
- Verdict : V2 toujours valide ?

**Script 2 :** `explore_new_fields_predictive_power_session20.py`
- Analyser pouvoir prédictif des 5 nouveaux champs
- Tester change_percentage vs notre surprise
- Analyser impact MoM vs YoY
- Recommandations pour V3

### PHASE 2 : Tests formules alternatives (PRIORITÉ 2)

**Script 3 :** `test_alternative_formulas_session20.py`
- Tester 5-10 variantes de formule
- Utiliser les insights des nouveaux champs
- Mesurer MAE de chaque variante
- Identifier formule optimale

### PHASE 3 : Validation latence/TTR (OPTIONNEL)

**Script 4 :** `analyze_latency_ttr_from_prices_session20.py`
- Calculer latency/TTR réels depuis prices_1m
- Comparer avec formules actuelles
- Proposer amélirations

### PHASE 4 : Validation pullback (OPTIONNEL)

**Note :** Nécessite calcul pullbacks historiques (complexe)
- Reporter à session ultérieure si temps

---

## 🎯 CRITÈRES DE SUCCÈS SESSION 20

### Minimum vital (80K tokens)

1. ✅ V2 re-validée avec données propres (MAE ~140-170%)
2. ✅ Nouveaux champs analysés (pouvoir prédictif mesuré)
3. ✅ Recommandations claires pour V3

### Optimal (150K tokens)

4. ✅ 3-5 formules alternatives testées
5. ✅ Formule optimale identifiée (MAE < 140%)
6. ✅ Plan d'implémentation V3 documenté

### Bonus (si temps)

7. ✅ Latency/TTR analysés depuis données réelles
8. ✅ Pullback historiques calculés

---

## 📊 MÉTRIQUES ATTENDUES

### Formule impact (V2)

| Métrique | Session 17 | Session 20 (attendu) | Verdict |
|----------|------------|----------------------|---------|
| MAE V2 | 174.9% | ~140-170% | ✅ Amélioration |
| Gain vs V1 | -418 pts | ~-350 pts | ✅ Toujours meilleur |
| Cas 11 sept | 29% erreur | ~13% erreur | ✅ Amélioration |

### Nouveaux champs

| Champ | Corrélation impact | Utilité | Action |
|-------|-------------------|---------|--------|
| change_percentage | À mesurer | Remplacer surprise ? | À décider |
| comparison (MoM/YoY) | À mesurer | Différencier ? | À décider |
| period | À mesurer | Ajustement saisonnier ? | À décider |

---

## 🔄 WORKFLOW SESSION 20

```
1. Lire documents continuité
   ↓
2. Lancer script 1 : Re-mesure V2
   ↓
3. Analyser résultats → V2 toujours valide ?
   ↓
4. Lancer script 2 : Exploration nouveaux champs
   ↓
5. Analyser résultats → Quels champs utiles ?
   ↓
6. Décision : Garder V2 ou créer V3 ?
   ↓
   SI V3 NÉCESSAIRE :
   ↓
7. Lancer script 3 : Tester formules alternatives
   ↓
8. Identifier formule optimale (MAE minimum)
   ↓
9. Documenter formule V3
   ↓
10. Mettre à jour event_families si nécessaire
```

---

## 📝 RAPPEL : OBJECTIF FINAL DU SYSTÈME

**Le système doit prédire COMPLÈTEMENT :**

1. ✅ **Impact initial** : +207 pips dans 5 minutes
2. ✅ **Latence** : 0.5 min avant début mouvement
3. ✅ **TTR** : 5 min pour atteindre le maximum
4. ✅ **Pullback** : -82.8 pips pendant 10 minutes
5. ✅ **Phase 2** : +16.4 pips dans 5 minutes
6. ✅ **Graphique** : Courbe complète EUR/USD

**CE N'EST PAS JUSTE une prédiction d'impact, c'est une TIMELINE COMPLÈTE !**

---

## 🎓 CONCLUSION

Session 20 = **RE-VALIDATION COMPLÈTE** avant toute modification.

**Pourquoi c'est critique :**
- Données ont changé (+75% événements, MoM/YoY distingués)
- V2 calibrée sur données biaisées
- 5 nouveaux champs exploitables
- Ne pas figer une mauvaise approche

**Plan :**
1. Re-valider V2 avec données propres
2. Explorer nouveaux champs
3. Tester alternatives si nécessaire
4. Documenter choix

**Tokens disponibles : 190K → Suffisant pour analyse complète !**

---

**FIN DU DOCUMENT DE VISION GLOBALE**

**Date :** 19 octobre 2025  
**Session :** 20  
**Auteur :** Claude & André  
**Importance :** ⭐⭐⭐ CRITIQUE - LIRE AVANT SESSION 20
