# NOTES DÉTAILLÉES - FORMULAS_VALIDATED.PY

**Date analyse :** 27 octobre 2025  
**Fichier analysé :** `fx_impact_app/src/formulas_validated.py`  
**Version :** 1.1 (23 octobre 2025 - Session 55)

---

## 🎯 STRUCTURE MODULE

### 4 Formules Validées

1. **calculate_adjusted_empirical_score()** - Session 55 (99.9%)
2. **calculate_impact_d()** - Session 51 (98.6%)
3. **calculate_ttr_c()** - Session 52 (94.4%)
4. **calculate_pullback_v2()** - Session 53 (99.3%)

---

## 🔍 FORMULE 1 : calculate_adjusted_empirical_score()

### Localisation : Lignes 112-215

### Signature

```python
def calculate_adjusted_empirical_score(
    base_empirical_score: float,
    surprise_pct: float
) -> float
```

### Formule EXACTE

```python
abs_surprise = abs(surprise_pct)

# Zone 1 : < 5%
if abs_surprise < 5:
    factor = 1.0

# Zone 2 : 5-15%
elif abs_surprise < 15:
    factor = 1.0 + (abs_surprise - 5) / 10 * 0.5

# Zone 3 : 15-30%
elif abs_surprise < 30:
    factor = 1.5 + (abs_surprise - 15) / 15 * 0.4

# Zone 4 : ≥ 30%
else:
    factor = 1.9

# Résultat
adjusted_score = base_empirical_score * factor
```

### ✅ ZONES SURPRISE VALIDÉES

| Zone | Surprise | Factor Min | Factor Max | Interpolation |
|------|----------|------------|------------|---------------|
| 1 | < 5% | 1.0 | 1.0 | Fixe |
| 2 | 5-15% | 1.0 | 1.5 | Linéaire |
| 3 | 15-30% | 1.5 | 1.9 | Linéaire |
| 4 | ≥ 30% | 1.9 | 1.9 | Plafond |

### Calculs Interpolation Zone 2

**Formule :**
```
factor = 1.0 + (surprise - 5) / 10 × 0.5
```

**Exemples :**
- surprise = 5% → factor = 1.0 + 0/10 × 0.5 = 1.0
- surprise = 10% → factor = 1.0 + 5/10 × 0.5 = 1.25
- surprise = 15% → factor = 1.0 + 10/10 × 0.5 = 1.5 ✅

### Calculs Interpolation Zone 3

**Formule :**
```
factor = 1.5 + (surprise - 15) / 15 × 0.4
```

**Exemples :**
- surprise = 15% → factor = 1.5 + 0/15 × 0.4 = 1.5
- surprise = 22.5% → factor = 1.5 + 7.5/15 × 0.4 = 1.7
- surprise = 30% → factor = 1.5 + 15/15 × 0.4 = 1.9 ✅

### Validation Session 55

**Cas 11 septembre 2025 :**
- base_empirical_score = 44.8
- surprise_pct = 33.3%
- **Zone 4 (≥ 30%) → factor = 1.9**
- adjusted_score = 44.8 × 1.9 = **85.1** ✅
- Score attendu = ~85
- **MAE = 0.1 (99.9% précision)**

---

## 🔍 FORMULE 2 : calculate_impact_d()

### Localisation : Lignes 218-307

### Signature

```python
def calculate_impact_d(
    empirical_score: float,
    num_events: int = 1,
    amplification: float = 1.0,
    correction_factor: float = 0.758
) -> float
```

### Formule EXACTE

```python
# 1. Choix formule selon nombre d'événements
if num_events >= 2:
    # Multi-événements
    intercept = -10.47
    coefficient = 0.477
else:
    # Événement isolé
    intercept = -7.08
    coefficient = 0.419

# 2. Calcul impact brut
impact_brut = intercept + (coefficient * empirical_score)

# 3. Appliquer amplification
impact_amplifie = abs(impact_brut) * amplification

# 4. Appliquer correction vectorielle
impact_final = impact_amplifie * correction_factor

return impact_final
```

### ✅ FORMULES VALIDÉES

**Cas num_events >= 2 :**
```
impact_brut = -10.47 + 0.477 × score
```

**Cas num_events = 1 :**
```
impact_brut = -7.08 + 0.419 × score
```

**Impact final :**
```
impact_final = |impact_brut| × amplification × 0.758
```

### Validation Session 51

**Cas 11 septembre 2025 :**
- empirical_score = 85.1 (ajusté)
- num_events = 9
- amplification = 1.0 (pas d'amplification dans test original)
- correction_factor = 0.758

**Calcul :**
1. num_events = 9 ≥ 2 → formule multi-événements
2. impact_brut = -10.47 + 0.477 × 85.1 = -10.47 + 40.59 = 30.12
3. impact_amplifie = |30.12| × 1.0 = 30.12
4. impact_final = 30.12 × 0.758 = **22.8 pips**

**⚠️ PROBLÈME DÉTECTÉ :**

**Planificateur V2.4 obtient 57.0 pips avec score = 85**

**Calcul inverse :**
```
57.0 = impact_final
57.0 / 0.758 = 75.2 (impact amplifié)
75.2 = |impact_brut| × amplification
```

**Si amplification = 1.0 :**
```
75.2 = |-10.47 + 0.477 × score|
75.2 + 10.47 = 0.477 × score
85.67 = 0.477 × score
score = 179.6 ❌ (impossible, score ajusté = 85.1)
```

**Si amplification = 2.5 :**
```
75.2 = |impact_brut| × 2.5
impact_brut = 30.08
30.08 = -10.47 + 0.477 × score
40.55 = 0.477 × score
score = 85.0 ✅
```

**✅ CONCLUSION :**
**Planificateur V2.4 utilise amplification = 2.5, PAS 1.0 !**

---

## 🚨 CORRECTION COMPRÉHENSION AMPLIFICATION

### Message Session 96 vs Code Réel vs Formule D

**Message Session 96 dit :**
- Amplification dynamique selon surprise
- Zones 5%, 15%, etc.

**Planificateur V2.4 fait :**
```python
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=2.5  # FIXE
)
```

**Formule D accepte :**
```python
amplification: float = 1.0  # Paramètre par défaut
```

**✅ VÉRITÉ :**
- **Formule D = formule générique, paramètre amplification configurable**
- **Planificateur V2.4 = passe amplification FIXE 2.5**
- **Message S96 décrivait logique EXTERNE (pas dans Formule D)**

---

## 🔍 FORMULE 3 : calculate_ttr_c()

### Localisation : Lignes 310-379

### Signature

```python
def calculate_ttr_c(
    latency_minutes: float,
    surprise_pct: float
) -> float
```

### Formule EXACTE

```python
abs_surprise = abs(surprise_pct)

# Zone 1 : < 10%
if abs_surprise < 10:
    multiplier = 3.0

# Zone 2 : 10-30%
elif abs_surprise < 30:
    multiplier = 2.5

# Zone 3 : > 30%
else:
    multiplier = 2.0

# Calcul TTR
ttr = latency_minutes * multiplier

return ttr
```

### ✅ MULTIPLIERS VALIDÉS

| Surprise | Multiplier | Rationale |
|----------|------------|-----------|
| < 10% | 3.0 | Mouvement lent, marché hésite |
| 10-30% | 2.5 | Mouvement normal |
| > 30% | 2.0 | Mouvement rapide, forte réaction |

### Validation Session 52

**Cas 11 septembre 2025 :**
- latency_minutes = 2.0
- surprise_pct = 33.3%
- **Zone 3 (> 30%) → multiplier = 2.0**
- ttr = 2.0 × 2.0 = **4.0 minutes** ✅
- TTR réel = 5.0 minutes
- **MAE = 1.0 minute (80% précision)**

**Note documentation dit 94.4% mais MAE = 0.3 min :**
- Documentation cite : TTR prédit 4.7 min vs réel 5.0 min
- Code calcule : 2.0 × 2.0 = 4.0 min

**❓ QUESTION : Latency utilisée était 2.35 min au lieu de 2.0 ?**

---

## 🔍 FORMULE 4 : calculate_pullback_v2()

### Localisation : Lignes 382-489

### Signature

```python
def calculate_pullback_v2(
    phase1_impact: float,
    minutes_since_peak: float,
    minutes_to_next_phase: float
) -> float
```

### Formule EXACTE

```python
# 1. Vérifier intervalle phases
if minutes_to_next_phase > 30:
    return 0.0  # Phases indépendantes

# 2. Vérifier validité minutes_since_peak
if minutes_since_peak < 0:
    return 0.0

# 3. Paramètres
log_coefficient = 0.30
max_pullback_ratio = 0.75

# 4. Calcul ratio logarithmique
pullback_ratio = min(
    log_coefficient * math.log(minutes_since_peak + 1),
    max_pullback_ratio
)

# 5. Appliquer au mouvement
pullback_pips = abs(phase1_impact) * pullback_ratio

return pullback_pips
```

### ✅ COMPORTEMENT VALIDÉ

| Minutes | Ratio | Notes |
|---------|-------|-------|
| 1 | 21% | Faible |
| 3 | 42% | Modéré |
| 5 | 54% | Significatif |
| 10 | 72% | Fort (validé) |
| 15 | 75% | Plafond |
| > 15 | 75% | Saturé |

### Validation Session 53

**Cas 11 septembre 2025 :**
- phase1_impact = 37.4 pips
- minutes_since_peak = 10
- minutes_to_next_phase = 15

**Calcul :**
1. 15 ≤ 30 → continuer
2. 10 ≥ 0 → continuer
3. pullback_ratio = min(0.30 × ln(10 + 1), 0.75)
4. pullback_ratio = min(0.30 × ln(11), 0.75)
5. pullback_ratio = min(0.30 × 2.398, 0.75)
6. pullback_ratio = min(0.719, 0.75) = 0.719
7. pullback_pips = 37.4 × 0.719 = **26.9 pips** ✅
8. Pullback réel = 27.1 pips
9. **MAE = 0.2 pips (99.3% précision)**

---

## 🚨 RÉSOLUTION DISCORDANCES

### ✅ Discordance #1 : Calcul Surprise RÉSOLU

**Message Session 96 mentionnait fallback estimate → forecast → previous**

**Code Planificateur V2.4 utilise SEULEMENT estimate**

**Code formulas_validated.py :**
- **Ne contient AUCUNE logique surprise**
- **Reçoit surprise_pct déjà calculée**

**✅ VÉRITÉ :**
- **calculate_adjusted_empirical_score() reçoit surprise_pct EN PARAMÈTRE**
- **Calcul surprise fait AVANT appel, dans Planificateur**
- **Planificateur V2.4 calcule surprise avec SEULEMENT estimate**
- **PAS de fallback forecast/previous dans code actuel**

**⚠️ Message S96 décrivait peut-être version antérieure ou théorique**

---

### ✅ Discordance #2 : Colonnes Chargées RÉSOLU

**Message Session 96 : forecast, previous dans query**

**Planificateur V2.4 : SEULEMENT actual, estimate**

**Code formulas_validated.py :**
- **Ne charge RIEN de la DB**
- **Reçoit valeurs calculées**

**✅ VÉRITÉ :**
- **Query Planificateur V2.4 charge : actual, estimate (PAS forecast, previous)**
- **formulas_validated.py = pures fonctions mathématiques**

---

### ✅ Discordance #3 : Amplification RÉSOLU

**Message Session 96 : Amplification dynamique zones surprise**

**Planificateur V2.4 : amplification=2.5 FIXE**

**Code formulas_validated.py :**
```python
def calculate_impact_d(
    amplification: float = 1.0  # Paramètre par défaut
)
```

**✅ VÉRITÉ :**
- **Formule D = fonction générique avec paramètre amplification**
- **Planificateur V2.4 = utilise amplification FIXE 2.5**
- **Amplification dynamique = EXTERNE à Formule D**
- **Message S96 décrivait logique qui N'EXISTE PAS dans code actuel**

**❓ QUESTION : Amplification dynamique implémentée où ?**
- Pas dans formulas_validated.py
- Pas dans Planificateur V2.4
- Module séparé ?
- Sessions 51-55 disent quoi ?

---

### ✅ Discordance #4 : Ajustement Score RÉSOLU

**Message Session 96 : Zones 1.0, 1.5, 1.9**

**Code formulas_validated.py : Zones EXACTES validées**

```python
< 5%    : factor = 1.0
5-15%   : factor = 1.0 → 1.5 linéaire
15-30%  : factor = 1.5 → 1.9 linéaire
≥ 30%   : factor = 1.9 plafond
```

**✅ Message S96 CORRECT sur ce point** ✅

---

### ✅ Discordance #5 : Pullback RÉSOLU

**Planificateur V2.4 : pullback = calculate_pullback_v2(37.4, 10, 15)**

**Valeurs 37.4, 10, 15 hardcodées**

**Code formulas_validated.py :**
- **Reçoit paramètres en entrée**
- **Ne hardcode rien**

**✅ VÉRITÉ :**
- **Valeurs 37.4, 10, 15 = SPÉCIFIQUES au cas 11 septembre 2025**
- **Planificateur utilise ces valeurs FIXES (PAS dynamiques)**
- **37.4 = impact phase 1 du 11 sept**
- **10 = minutes depuis peak du 11 sept**
- **15 = durée jusqu'à prochaine phase du 11 sept**

**❌ PROBLÈME : Planificateur calcule pullback avec valeurs FIXES du 11 sept**
**❌ PAS dynamique selon date testée !**

---

## ✅ POINTS VALIDÉS

### ✅ Formules Mathématiques

1. **calculate_adjusted_empirical_score()** ✅
   - Zones surprise : < 5%, 5-15%, 15-30%, ≥ 30%
   - Factors : 1.0, 1.0→1.5, 1.5→1.9, 1.9
   - Interpolation linéaire zones 2-3

2. **calculate_impact_d()** ✅
   - Formule multi-events : -10.47 + 0.477 × score
   - Formule single-event : -7.08 + 0.419 × score
   - Correction vectorielle : × 0.758
   - Amplification : paramètre configurable

3. **calculate_ttr_c()** ✅
   - Multipliers : 3.0 (< 10%), 2.5 (10-30%), 2.0 (> 30%)
   - Formule : latency × multiplier

4. **calculate_pullback_v2()** ✅
   - Ratio logarithmique : 0.30 × ln(minutes + 1)
   - Plafond : 0.75 (75%)
   - Seuil indépendance : 30 minutes

---

## 🚨 FONCTIONNALITÉS BONUS DÉCOUVERTES

### calculate_amplification_extended() (Session 88)

**Localisation : Lignes 26-109**

**Objectif :** Amplification pour surprises EXTRÊMES (> 100%)

**Formule :**
```python
Zone 1 (0-15%)     : factor = 1.0
Zone 2 (15-30%)    : factor = 1.0 → 2.5 (linéaire) [S51 validé]
Zone 3 (30-100%)   : factor = 2.5 → 5.0 (linéaire)
Zone 4 (>100%)     : factor = 5.0 + log10(surprise - 99) [plafonné 10.0]
```

**⚠️ NON UTILISÉE dans Planificateur V2.4**

**Status : Expérimentale, validation Session 88**

---

## 📋 SYNTHÈSE COMPRÉHENSION

### ✅ CE QU'ON SAIT MAINTENANT

**Formules Mathématiques :**
- ✅ Ajustement score : zones surprise 5%, 15%, 30% avec factors 1.0, 1.5, 1.9
- ✅ Impact D : formules multi/single events + correction 0.758
- ✅ TTR C : multipliers 3.0, 2.5, 2.0 selon surprise
- ✅ Pullback V2 : ratio logarithmique 0.30 × ln(min + 1), plafond 0.75

**Architecture :**
- ✅ formulas_validated.py = fonctions pures mathématiques
- ✅ Planificateur V2.4 = orchestrateur qui appelle formulas_validated.py
- ✅ Calcul surprise fait dans Planificateur (pas formulas_validated.py)
- ✅ Amplification configurée par Planificateur (2.5 fixe)

**Validations Session 51-55 :**
- ✅ Cas référence : 11 septembre 2025
- ✅ Précisions : 99.9%, 98.6%, 94.4%, 99.3%
- ✅ MAE : 0.1, 0.8 pips, 0.3 min, 0.2 pips

---

### ❓ CE QU'ON NE SAIT PAS ENCORE

**Questions Calcul Surprise :**
- ❓ Fallback estimate → forecast → previous existe vraiment ?
- ❓ Où est-il documenté ?
- ❓ Sessions 51-55 utilisaient quoi ?

**Questions Amplification :**
- ❓ Pourquoi Planificateur V2.4 utilise 2.5 fixe ?
- ❓ Amplification dynamique existe où ?
- ❓ calculate_amplification_extended() (S88) utilisée quand ?
- ❓ Sessions 51-55 utilisaient quelle amplification ?

**Questions Pullback :**
- ❓ Pourquoi valeurs 37.4, 10, 15 hardcodées ?
- ❓ Planificateur calcule pullback dynamique où ?
- ❓ Valeurs fixes = bug ou intentionnel ?

**Questions Colonnes DB :**
- ❓ forecast et previous existent dans DB ?
- ❓ Sessions 51-55 les utilisaient ?
- ❓ Pourquoi Planificateur V2.4 ne les charge pas ?

---

## 📋 PROCHAINES ÉTAPES

### ✅ Étapes Complétées
1. ✅ Lecture Planificateur V2.4
2. ✅ Lecture formulas_validated.py

### 🔄 Étapes Suivantes

3. **Lire Sessions 51-55** (PRIORITÉ #1)
   - Comprendre méthode ORIGINALE validation
   - Vérifier calcul surprise (fallback ou pas)
   - Vérifier amplification (dynamique ou fixe)
   - Vérifier colonnes DB utilisées
   - Vérifier pullback (dynamique ou fixe)

4. **Résoudre contradictions finales**
   - Message S96 vs Code Réel vs Sessions 51-55
   - Identifier version CORRECTE à implémenter

5. **Documenter méthodologie exacte**
   - Pseudo-code conforme
   - Checklist conformité

---

**FIN NOTES FORMULAS_VALIDATED.PY**
