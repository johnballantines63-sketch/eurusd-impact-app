# NOTES DÉTAILLÉES - PLANIFICATEUR V2.4

**Date analyse :** 27 octobre 2025  
**Fichier analysé :** `5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 4.py`  
**Version :** 2.4 (Session 68 - Single Wave Fort)

---

## 🎯 ARCHITECTURE GÉNÉRALE

### Imports Formules Validées (Lignes 44-49)

```python
from formulas_validated import (
    calculate_impact_d,           # Session 51 - 98.6% précision
    calculate_ttr_c,              # Session 52 - 94.4% précision
    calculate_pullback_v2,        # Session 53 - 99.3% précision
    calculate_adjusted_empirical_score,  # Session 55 - 99.9% précision
    get_all_formulas_info
)
```

**✅ Point clé : Utilise EXACTEMENT les 4 formules validées**

### Imports Modules Détection (Lignes 52-58)

```python
# Double Wave (Session 64-65)
from double_wave import (
    detect_double_wave_conditions,
    predict_double_wave_timeline
)

# Single Wave Strong (Session 67-68)
from single_wave_strong import (
    detect_single_wave_strong,
    predict_single_wave_timeline
)
```

**✅ Point clé : 2 types de mouvements gérés automatiquement**

---

## 🔍 FONCTION 1 : get_high_impact_events_for_date()

### Localisation : Lignes 132-171

### Query SQL EXACTE (Lignes 148-159)

```python
query = """
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,
    ef.family,
    ef.empirical_score,
    ef.latency_median
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""
```

### ⚠️ DIFFÉRENCES CRITIQUES vs Message Session 96

**Message Session 96 mentionnait (ligne 208-224) :**
- forecast (estimate ET forecast)
- previous

**Planificateur V2.4 RÉEL charge seulement :**
- actual
- estimate
- **PAS forecast**
- **PAS previous**

### ✅ Critères Filtrage

| Critère | Valeur | Obligatoire |
|---------|--------|-------------|
| country | 'US' | ✅ |
| empirical_score | > 40 | ✅ |
| empirical_score | NOT NULL | ✅ |

### ✅ Colonnes Retournées

1. event_key
2. label (event_title)
3. ts_utc (timestamp événement)
4. actual
5. estimate
6. family
7. empirical_score
8. latency_median

**⚠️ IMPORTANT : PAS de forecast, PAS de previous dans query**

### Session 71 : Correction Importante (Ligne 118-120)

```python
# SESSION 71 : Corrigé pour traiter TOUS événements score > 40 (pas uniquement CPI)
# SESSION 68 : Traite CPI, NFP, Retail Sales, etc. (tous HIGH impacts)
```

**✅ Point clé : TOUS événements HIGH (score > 40), pas seulement CPI**

---

## 🔍 FONCTION 2 : calculate_predictions()

### Localisation : Lignes 174-332

### Phase 1 : Calcul Score et Surprise (Lignes 188-203)

```python
# Calculer score moyen et surprise max (lignes 65-76 de test_planificateur_v2_final.py)
base_score_avg = cpi_events['empirical_score'].mean()

surprises = []
max_surprise = 0
for _, event in cpi_events.iterrows():
    if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
        surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
        surprises.append(surprise_pct)
        if surprise_pct > max_surprise:
            max_surprise = surprise_pct

avg_surprise = sum(surprises) / len(surprises) if surprises else 0
```

### ⚠️ CALCUL SURPRISE : EXACTEMENT

**Formule :**
```
surprise = |actual - estimate| / |estimate| × 100
```

**Validation :**
- ✅ actual NOT NULL
- ✅ estimate NOT NULL
- ✅ estimate ≠ 0

**⚠️ CRITIQUE : Utilise SEULEMENT estimate, PAS forecast, PAS previous**

**Message Session 96 parlait de fallback (estimate → forecast → previous → 0)**
**Planificateur V2.4 RÉEL utilise SEULEMENT estimate** ❌

---

### Phase 2 : Ajustement Score (Lignes 205-206)

```python
# NOUVEAU : Ajuster le score (lignes 84-88)
adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
```

**✅ Appel fonction Session 55 (99.9% précision)**

**Question : Quelle est l'implémentation EXACTE de cette fonction ?**
→ Besoin lire `formulas_validated.py`

---

### Phase 3 : Calcul Impact (Lignes 208-214)

```python
# Test avec amplification optimale 2.5 (lignes 90-96)
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=2.5
)
```

**✅ Appel Formule D - Session 51 (98.6% précision)**

**⚠️ AMPLIFICATION FIXE : 2.5** (pas dynamique selon surprise)

**Question : Comment Formule D gère num_events ?**
→ Besoin lire `formulas_validated.py`

---

### Phase 4 : Calcul TTR (Lignes 216-226)

```python
# Test TTR (lignes 104-116)
cpi_main = cpi_events.iloc[0]
if pd.notna(cpi_main['actual']) and pd.notna(cpi_main['estimate']) and cpi_main['estimate'] != 0:
    surprise_pct = abs((cpi_main['actual'] - cpi_main['estimate']) / cpi_main['estimate']) * 100
else:
    surprise_pct = 0

latency_min = cpi_main['latency_median'] / 60 if pd.notna(cpi_main['latency_median']) else 2.0
ttr_predicted = calculate_ttr_c(latency_min, surprise_pct)
```

**⚠️ UTILISE SEULEMENT PREMIER ÉVÉNEMENT (iloc[0])**

**Conversion latency :** secondes → minutes (`/ 60`)

**✅ Appel Formule C - Session 52 (94.4% précision)**

---

### Phase 5 : Calcul Pullback (Lignes 228-229)

```python
# Test Pullback (lignes 122-130)
pullback = calculate_pullback_v2(37.4, 10, 15)
```

**❌ VALEURS HARDCODÉES : 37.4, 10, 15**

**Question : Pourquoi valeurs fixes ? Quelle logique ?**
→ Besoin comprendre Formule V2 Pullback

---

### Phase 6 : Détection Type Mouvement (Lignes 231-285)

#### 6.1 Préparation Événements (Lignes 236-246)

```python
# Préparer événements pour détection
events_for_detection = []
for _, event in cpi_events.iterrows():
    events_for_detection.append({
        'actual': event.get('actual'),
        'estimate': event.get('estimate'),
        'forecast': event.get('estimate'),  # ⚠️ UTILISE estimate comme forecast
        'previous': event.get('estimate'),  # ⚠️ UTILISE estimate comme previous
        'importance_n': 3  # CPI = HIGH importance
    })

start_time = pd.to_datetime(cpi_events.iloc[0]['ts_utc'])
```

**⚠️ DUPLICATION : forecast = previous = estimate**

**⚠️ importance_n FIXE = 3** (HIGH pour CPI)

---

#### 6.2 Détection Single Wave Strong (Lignes 248-252)

```python
# 1. Tester Single Wave Strong d'abord (95% des cas)
is_single_wave_strong = detect_single_wave_strong(
    events_for_detection,
    surprise_threshold=15.0,
    min_cluster_size=3
)
```

**Conditions Single Wave Strong :**
- surprise > 15%
- cluster_size ≥ 3

---

#### 6.3 Détection Double Wave (Lignes 254-259)

```python
# 2. Tester Double Wave (rare, conditions strictes)
is_double_wave = detect_double_wave_conditions(
    events_for_detection,
    surprise_threshold=20.0,
    min_cluster_size=5
)
```

**Conditions Double Wave :**
- surprise > 20%
- cluster_size ≥ 5

---

#### 6.4 Logique Décision (Lignes 261-285)

```python
movement_type = None
single_wave_timeline = None
double_wave_timeline = None

if is_double_wave:
    # Double Wave (rare)
    movement_type = "Double Wave Momentum"
    double_wave_timeline = predict_double_wave_timeline(
        base_impact=impact,
        surprise_pct=max_surprise,
        cluster_size=len(cpi_events),
        start_time=start_time
    )
elif is_single_wave_strong:
    # Single Wave Fort (standard CPI/NFP)
    movement_type = "Single Wave Fort"
    single_wave_timeline = predict_single_wave_timeline(
        base_impact=impact,
        surprise_pct=max_surprise,
        cluster_size=len(cpi_events),
        start_time=start_time
    )
else:
    # Single Wave Standard (cas simple)
    movement_type = "Single Wave Standard"
```

**Priorité :**
1. Double Wave (conditions strictes)
2. Single Wave Strong (standard)
3. Single Wave Standard (fallback)

---

### Phase 7 : Retour Résultats (Lignes 287-302)

```python
return {
    'num_events': len(cpi_events),
    'base_score_avg': base_score_avg,
    'adjusted_score': adjusted_score,
    'max_surprise': max_surprise,
    'avg_surprise': avg_surprise,
    'impact_pips': impact,
    'ttr_minutes': ttr_predicted,
    'pullback_pips': pullback,
    'events': cpi_events,
    'movement_type': movement_type,
    'is_single_wave_strong': is_single_wave_strong,
    'is_double_wave': is_double_wave,
    'single_wave_timeline': single_wave_timeline,
    'double_wave_timeline': double_wave_timeline
}
```

**✅ Retourne 14 valeurs dans dict**

---

## 🚨 DÉCOUVERTES CRITIQUES

### 🔴 DISCORDANCE #1 : Calcul Surprise

**Message Session 96 dit :**
```
Fallback surprise : estimate → forecast → previous → 0
```

**Planificateur V2.4 RÉEL fait :**
```python
# SEULEMENT estimate, AUCUN fallback
if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
    surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
else:
    surprise_pct = 0
```

**⚠️ Si estimate NULL ou 0 → surprise = 0 (pas de fallback forecast/previous)**

---

### 🔴 DISCORDANCE #2 : Colonnes Chargées

**Message Session 96 dit :**
```
Query charge : actual, estimate, forecast, previous
```

**Planificateur V2.4 RÉEL charge :**
```sql
SELECT e.actual, e.estimate  -- PAS forecast, PAS previous
```

**⚠️ forecast et previous absents de la query SQL**

---

### 🔴 DISCORDANCE #3 : Amplification

**Message Session 96 dit :**
```
Amplification zones surprise :
- < 5% : 1.0
- 5-15% : 1.0 → 1.5 linéaire
- ≥ 15% : 2.5 plafond
```

**Planificateur V2.4 RÉEL fait :**
```python
amplification=2.5  # FIXE, pas dynamique
```

**⚠️ Amplification TOUJOURS 2.5, pas conditionnelle**

---

### 🔴 DISCORDANCE #4 : Ajustement Score

**Message Session 96 dit zones précises (1.0, 1.0→1.5, 1.5→1.9, 1.9 plafond)**

**Planificateur V2.4 RÉEL :**
```python
adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
```

**⚠️ Implémentation EXACTE inconnue → besoin lire formulas_validated.py**

---

### 🔴 DISCORDANCE #5 : Pullback

**Planificateur V2.4 :**
```python
pullback = calculate_pullback_v2(37.4, 10, 15)  # Valeurs hardcodées
```

**❓ Pourquoi 37.4, 10, 15 ?**
**❓ Valeurs spécifiques au 11 septembre ?**

---

## ✅ POINTS VALIDÉS

### ✅ Formules Utilisées

1. `calculate_adjusted_empirical_score()` - Session 55 (99.9%)
2. `calculate_impact_d()` - Session 51 (98.6%)
3. `calculate_ttr_c()` - Session 52 (94.4%)
4. `calculate_pullback_v2()` - Session 53 (99.3%)

**Appels directs aux fonctions validées** ✅

---

### ✅ Filtre HIGH Impact

```python
WHERE ef.empirical_score IS NOT NULL
  AND ef.empirical_score > 40
```

**Correct : score > 40** ✅

---

### ✅ Détection Type Mouvement

- Double Wave : surprise > 20%, cluster ≥ 5
- Single Wave Strong : surprise > 15%, cluster ≥ 3
- Single Wave Standard : fallback

**Logique claire** ✅

---

## ❓ QUESTIONS À RÉSOUDRE

### ❓ Q1 : Implémentation calculate_adjusted_empirical_score()

**Besoin lire :** `fx_impact_app/src/formulas_validated.py`

**Questions :**
- Quelle formule EXACTE ?
- Zones surprise appliquées comment ?
- Factors 1.0, 1.5, 1.9 où ?

---

### ❓ Q2 : Implémentation calculate_impact_d()

**Besoin lire :** `fx_impact_app/src/formulas_validated.py`

**Questions :**
- Formule single event vs multi-events ?
- Comment gère amplification (fixe 2.5 ou dynamique) ?
- Correction vectorielle 0.758 appliquée où ?

---

### ❓ Q3 : Implémentation calculate_ttr_c()

**Besoin lire :** `fx_impact_app/src/formulas_validated.py`

**Questions :**
- Multipliers zones surprise ?
- Formule EXACTE ?

---

### ❓ Q4 : Implémentation calculate_pullback_v2()

**Besoin lire :** `fx_impact_app/src/formulas_validated.py`

**Questions :**
- Que signifient paramètres 37.4, 10, 15 ?
- Formule EXACTE ?

---

### ❓ Q5 : Fallback Surprise

**Question :**
- Message S96 mentionne fallback estimate → forecast → previous
- Code réel utilise SEULEMENT estimate
- **Quelle est la VRAIE méthode ?**
- Sessions 51-55 disent quoi ?

---

### ❓ Q6 : Colonnes forecast/previous

**Question :**
- Pourquoi absentes de la query ?
- Sessions 51-55 les utilisaient ou pas ?

---

## 📋 PROCHAINES ÉTAPES

### ✅ Étape Complétée
1. ✅ Lecture Planificateur V2.4 ligne par ligne

### 🔄 Étapes Suivantes

2. **Lire formulas_validated.py** (PRIORITÉ #1)
   - Comprendre EXACTEMENT chaque formule
   - Vérifier amplification dynamique ou fixe
   - Vérifier correction 0.758
   - Comprendre pullback_v2

3. **Lire Sessions 51-55** (PRIORITÉ #2)
   - Valider formule D EXACTE
   - Valider ajustement score EXACT
   - Valider fallback surprise
   - Valider colonnes utilisées

4. **Résoudre contradictions**
   - Message S96 vs Code Réel
   - Documenter différences
   - Identifier version correcte

---

## 🎯 SYNTHÈSE PROVISOIRE

**Ce qu'on SAIT :**
- ✅ 4 formules validées utilisées
- ✅ Query charge score > 40
- ✅ Surprise calculée avec estimate uniquement
- ✅ Amplification = 2.5 fixe dans code
- ✅ 3 types mouvements détectés

**Ce qu'on NE SAIT PAS ENCORE :**
- ❓ Implémentation EXACTE 4 formules
- ❓ Amplification vraiment fixe ou dynamique ?
- ❓ Fallback surprise existe ou non ?
- ❓ Correction 0.758 où appliquée ?
- ❓ Zones ajustement score exactes ?

**Action requise :**
**LIRE formulas_validated.py MAINTENANT** 🚀

---

**FIN NOTES PLANIFICATEUR V2.4**
