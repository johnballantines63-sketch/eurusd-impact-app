# 🔬 CARTOGRAPHIE FORMULES - SESSION 50

**Date** : 23 octobre 2025  
**Découverte** : 4 formules différentes dans le code

---

## 📊 VUE D'ENSEMBLE

| # | Nom | Fichier | Lignes | Complexité | Vitesse |
|---|-----|---------|--------|------------|---------|
| **A** | predict_impact_fast | Planificateur | 398-461 | Faible | ⚡⚡⚡ |
| **B** | predict_impact | Planificateur | 750-867 | Élevée | 🐌 |
| **C** | predict_impact_v9_clean | forecaster_mvp | ~195-215 | Faible | ⚡⚡ |
| **D** | calculate_vectorial_sum | timeline v87 | ~320-450 | Moyenne | ⚡ |

---

## 🔴 FORMULE A : predict_impact_fast()

### Emplacement
```
fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py
Lignes : 398-461
```

### Formule Impact
```python
mfe = stats['mfe_p80']
impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
impact = mfe * impact_factor
```

### Formule Direction
```python
direction = get_event_direction(family, surprise)
# Utilise dictionnaire FAMILY_SENTIMENT
# Jobless_Claims: -1 (inversé)
# CPI: 1 (normal)
```

### Formule TTR
```python
# Si TTR > 20 min, appliquer correction
correction_factor = 0.23
ttr_corrected = stats['ttr_median'] * correction_factor
```

### Exemple
```python
# Jobless Claims: surprise = +28K = +11.9%
mfe_p80 = 45 pips
impact_factor = min(2.0, 1.0 + 11.9/100) = 1.119
impact = 45 × 1.119 = 50.4 pips
direction = get_event_direction('Jobless_Claims', 28) = +1 (UP)
predicted_pips = 50.4 pips UP
```

### Avantages
- ⚡ Très rapide (stats pré-calculées)
- ✅ Direction avec sentiment famille
- ✅ TTR corrigé pour longues latences
- ✅ Utilisée par interface Streamlit (testée)

### Inconvénients
- ⚠️ Nécessite stats pré-calculées en DB (32/36 familles)
- ⚠️ Formule simple (linéaire)

---

## 🔴 FORMULE B : predict_impact()

### Emplacement
```
fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py
Lignes : 750-867
```

### Formule Impact
```python
base_impact = stats['mfe_p80']
surprise_factor = min(abs(surprise) / 50.0, 2.0)
adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
```

### Formule Direction
```python
direction = 1 if surprise > 0 else -1  # ❌ SANS SENTIMENT !
```

### Formule TTR
```python
ttr = latency * 1.5  # ❌ PAS DE CORRECTION
```

### Exemple
```python
# Jobless Claims: surprise = +28K
mfe_p80 = 45 pips (calculé dynamiquement)
surprise_factor = min(28 / 50.0, 2.0) = 0.56
adjusted_impact = 45 × (0.5 + 0.5 × 0.56) = 45 × 0.78 = 35.1 pips
direction = 1 (surprise > 0) ❌ DEVRAIT ÊTRE +1 pour Jobless inversé
predicted_pips = 35.1 pips UP (FAUX, devrait considérer famille)
```

### Avantages
- ✅ Calcul dynamique (pas besoin cache)
- ✅ Utilise LatencyAnalyzer + ForecastEngine

### Inconvénients
- ❌ Direction simplifiée (IGNORE sentiment famille)
- ❌ TTR non corrigé
- 🐌 Très lent (2 requêtes DB + calculs)
- ❌ Formule différente de A (incohérence)

---

## 🔴 FORMULE C : predict_impact_v9_clean()

### Emplacement
```
fx_impact_app/src/forecaster_mvp.py
Lignes : ~195-215
```

### Formule Impact
```python
# 1 événement seul
impact = -7.08 + 0.419 × empirical_score

# ≥2 événements (multi-events)
impact = -10.47 + 0.477 × empirical_score
```

### Métriques
- **R² = 0.264** (corrélation faible)
- **MAE = 6.68 pips**
- **Dataset** : 2,087 groupes (2024-2025)

### Exemple
```python
# Multi-events (9 événements simultanés)
empirical_score = 85.0 (HIGH importance)
impact = -10.47 + 0.477 × 85 = 28.5 pips
# Tous les événements HIGH → même impact !
```

### Avantages
- ⚡ Très rapide (formule simple)
- ✅ Calibrée sur dataset historique
- ✅ Pas de dépendance stats pré-calculées

### Inconvénients
- ❌ Ne tient PAS COMPTE de la surprise !
- ❌ Tous événements HIGH = même impact
- ⚠️ R² faible (26% variance expliquée)
- ❌ Basée uniquement sur empirical_score

---

## 🔴 FORMULE D : Somme Vectorielle (Timeline v87)

### Emplacement
```
fx_impact_app/src/sequence_multi_event_timeline_v87.py
Lignes : ~320-450 (calculate_vectorial_sum)
```

### Algorithme Complet
```python
# 1. Pour chaque événement individuel
for event in group:
    impact_abs = predict_impact_v9_clean(score, num_events)  # Formule C
    direction = get_event_direction(family, surprise)
    contribution = impact_abs * direction
    contributions.append(contribution)

# 2. Somme algébrique
impact_brut = sum(contributions)

# 3. Amplification selon surprise max
max_surprise_pct = max([calculate_surprise_percentage(e) for e in group])
amplification_factor = calculate_amplification_factor(max_surprise_pct)
# Zone 1 (0-5%): 1.0
# Zone 2 (5-15%): 1.0 à 2.5 (linéaire)
# Zone 3 (>15%): 2.5 (plafond)

impact_amplifie = abs(impact_brut) * amplification_factor

# 4. Facteur correction vectoriel
impact_final = impact_amplifie * 0.758
direction_finale = +1 if impact_brut >= 0 else -1
```

### Exemple (11 septembre)
```python
# 9 événements 12:30 UTC
Event 1 (Continuing Jobless): 28.5 × -1 = -28.5 pips
Event 2 (Initial Jobless):    28.5 × +1 = +28.5 pips
Event 3 (4-Week Jobless):     28.5 × +1 = +28.5 pips
Event 4 (Core CPI MoM):       28.5 × +1 = +28.5 pips
Event 5 (CPI Index):          28.5 × -1 = -28.5 pips
Event 6 (CPI Final):          28.5 × -1 = -28.5 pips
Event 7 (CPI MoM):            28.5 × -1 = -28.5 pips
Event 8 (CPI YoY):            28.5 × +1 = +28.5 pips
Event 9 (Core CPI YoY):       28.5 × +1 = +28.5 pips

impact_brut = +28.5 pips
max_surprise = 33.3% (CPI MoM) → plafonnée à 30%
amplification = 2.5 (Zone 3)
impact_amplifie = 28.5 × 2.5 = 71.25 pips ❌ MAIS PAS APPLIQUÉ !
# (estimate NULL → amplification = 1.0)

impact_final = 28.5 × 1.0 × 0.758 = 21.6 pips
# MAIS dans test S50: 10.1 pips (pourquoi différence?)
```

### Avantages
- ✅ Somme vectorielle (mathématiquement correct)
- ✅ Direction avec sentiment
- ✅ Amplification surprises extrêmes
- ✅ Facteur correction calibré

### Inconvénients
- ⚠️ Basée sur Formule C (ignore surprise individuelle)
- ⚠️ Amplification pas toujours appliquée (estimate NULL)
- ⚠️ Complexe (4 étapes de calcul)
- ⚠️ Facteur 0.758 empirique (d'où vient-il?)

---

## 📊 COMPARAISON FORMULES

### Impact individuel (surprise = +10%)

| Formule | Base | Facteur surprise | Impact | Note |
|---------|------|------------------|--------|------|
| **A** | mfe_p80 = 45 | 1.0 + 10/100 = 1.10 | 49.5 pips | ✅ Tient compte surprise |
| **B** | mfe_p80 = 45 | 0.5 + 0.5×(10/50) = 0.6 | 27 pips | ⚠️ Formule différente |
| **C** | - | - | 28.5 pips | ❌ Ignore surprise |
| **D** | Formule C | × amplif × 0.758 | 21.6 pips | ⚠️ Basée sur C |

### Direction

| Formule | Méthode | Jobless (+28K) | CPI (+0.1%) | GDP (+2%) |
|---------|---------|----------------|-------------|-----------|
| **A** | Sentiment | +1 (UP) ✅ | -1 (DOWN) ✅ | -1 (DOWN) ✅ |
| **B** | Simple | +1 (UP) ✅ | +1 (UP) ❌ | +1 (UP) ❌ |
| **C** | N/A | N/A | N/A | N/A |
| **D** | Sentiment | +1 (UP) ✅ | -1 (DOWN) ✅ | -1 (DOWN) ✅ |

### Performance (estimée)

| Formule | Vitesse | Précision | Cohérence | Utilisée |
|---------|---------|-----------|-----------|----------|
| **A** | ⚡⚡⚡ | ? (à tester) | ✅ | Streamlit |
| **B** | 🐌 | ? (à tester) | ❌ | Fallback |
| **C** | ⚡⚡ | MAE 6.68 pips | ⚠️ | Timeline |
| **D** | ⚡ | MAE 18.0 pips | ✅ | Timeline multi |

---

## 🎯 TESTS À RÉALISER SESSION 51

### Test 1 : Formule A seule
```python
For each event in 11_sept_events:
    impact = predict_impact_fast(family, surprise, precomputed_stats)
    contribution = impact × direction
Total = sum(contributions)
```

**Hypothèse** : Meilleure que D car tient compte surprise

### Test 2 : Formule B seule
```python
For each event in 11_sept_events:
    impact = predict_impact(family, surprise)
    contribution = impact × direction_CORRECTED  # Ajouter sentiment
Total = sum(contributions)
```

**Hypothèse** : Moins bonne (formule différente)

### Test 3 : Formule C seule
```python
For each event in 11_sept_events:
    impact = predict_impact_v9_clean(score, num_events=9)
    contribution = impact × get_event_direction(family, surprise)
Total = sum(contributions)
```

**Hypothèse** : Comme D mais sans amplification/correction

### Test 4 : Formule D complète (déjà fait S50)
```
Total vectoriel = +28.5 pips
Réel MT5 = +56.2 pips
Écart = -27.7 pips (sous-estimation 2x)
```

---

## 💡 RECOMMANDATIONS

### Pour Session 51

1. **Tester les 4 formules** sur même dataset (11 sept)
2. **Comparer MAE/RMSE** objectivement
3. **Ne PAS privilégier** une formule a priori
4. **Choisir basé sur métriques**, pas intuition

### Hypothèse Probable

**Formule A** devrait être meilleure car :
- ✅ Tient compte surprise
- ✅ Direction avec sentiment
- ✅ Utilisée interface Streamlit (testée)

**MAIS** : Seuls les tests diront la vérité !

---

*Cartographie Formules Session 50*  
*Date : 23 octobre 2025*  
*4 formules identifiées et documentées*
