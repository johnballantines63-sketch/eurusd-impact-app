# NOTES LECTURE formulas_validated.py
## Session 97 - Formules GOLD STANDARD

---

## 📌 INFORMATIONS GÉNÉRALES

**Fichier :** `fx_impact_app/src/formulas_validated.py`  
**Version :** 1.1 - Session 55  
**Lignes :** 650  
**Auteur :** André Valentin avec Claude

**Formules disponibles :**
1. `calculate_adjusted_empirical_score()` - 99.9% précision (S55)
2. `calculate_impact_d()` - 98.6% précision (S51)
3. `calculate_ttr_c()` - 94.4% précision (S52)
4. `calculate_pullback_v2()` - 99.3% précision (S53)

---

## 🔍 FORMULE 1 : calculate_adjusted_empirical_score() (Lignes 95-172)

### SIGNATURE

```python
def calculate_adjusted_empirical_score(
    base_empirical_score: float,
    surprise_pct: float
) -> float
```

### VALIDATION

**Session 55 - 11 septembre 2025 :**
- Score base DB : 44.8
- Surprise : 33.3%
- Score ajusté : 85.1
- Score attendu : ~85
- **MAE : 0.1 (99.9% précision) ✅**

### FORMULE EXACTE

```python
abs_surprise = abs(surprise_pct)

# Zone 1 : Surprise faible (< 5%)
if abs_surprise < 5:
    factor = 1.0

# Zone 2 : Surprise moyenne (5-15%)
elif abs_surprise < 15:
    factor = 1.0 + (abs_surprise - 5) / 10 * 0.5

# Zone 3 : Surprise forte (15-30%)
elif abs_surprise < 30:
    factor = 1.5 + (abs_surprise - 15) / 15 * 0.4

# Zone 4 : Surprise extrême (≥ 30%)
else:
    factor = 1.9

adjusted_score = base_empirical_score * factor
```

### ZONES AMPLIFICATION

| Surprise | Factor | Notes |
|----------|--------|-------|
| < 5% | 1.0 | Pas d'ajustement |
| 5% | 1.0 | Début Zone 2 |
| 10% | 1.25 | Milieu Zone 2 |
| 15% | 1.5 | Début Zone 3 |
| 22.5% | 1.7 | Milieu Zone 3 |
| 30% | 1.9 | Zone 4 plafond |
| ≥ 30% | 1.9 | Plafond fixe |

### RATIONALE

**Problème identifié :**
- Scores DB calculés sur historique moyen
- NE tiennent PAS compte surprise
- Corrélation surprise ↔ score : -0.122 (négligeable)

**Solution :**
- Ajuster score dynamiquement selon surprise
- Zones progressives (évite changements brusques)
- Plafond à 1.9x pour événements exceptionnels

**Exemple :**
- CPI surprise 0% : score 44.8 (inchangé)
- CPI surprise 33% : score 85.1 (×1.9)
- Impact réel diffère de +52% → ajustement nécessaire

---

## 🔍 FORMULE 2 : calculate_impact_d() (Lignes 175-267)

### SIGNATURE

```python
def calculate_impact_d(
    empirical_score: float,
    num_events: int = 1,
    amplification: float = 1.0,
    correction_factor: float = 0.758
) -> float
```

### VALIDATION

**Session 51 - 11 septembre 2025 :**
- Impact prédit : +57.0 pips
- Impact réel : +56.2 pips
- **MAE : 0.8 pips (98.6% précision) ✅ GOLD STANDARD**

### FORMULE EXACTE

```python
# Choix formule selon nombre événements
if num_events >= 2:
    # Formule multi-événements
    intercept = -10.47
    coefficient = 0.477
else:
    # Formule événement isolé
    intercept = -7.08
    coefficient = 0.419

# Calcul impact brut
impact_brut = intercept + (coefficient * empirical_score)

# Appliquer amplification (pour surprises extrêmes)
impact_amplifie = abs(impact_brut) * amplification

# Appliquer correction vectorielle
impact_final = impact_amplifie * correction_factor

return impact_final
```

### ÉQUATIONS COMPLÈTES

**Multi-événements (num_events ≥ 2) :**
```
Impact = |(-10.47 + 0.477 × score)| × amplification × 0.758
```

**Événement isolé (num_events = 1) :**
```
Impact = |(-7.08 + 0.419 × score)| × amplification × 0.758
```

### PARAMÈTRES PAR DÉFAUT

- `num_events = 1` → Défaut événement isolé
- `amplification = 1.0` → Défaut pas d'amplification
- `correction_factor = 0.758` → Correction vectorielle FIXE

### ⚠️ OBSERVATIONS CRITIQUES

1. **Amplification PARAMÈTRE :**
   - Reçue en argument (pas calculée dans fonction)
   - Planificateur passe `amplification=2.5` codé en dur
   - **La fonction N'applique PAS d'amplification dynamique**

2. **Correction vectorielle 0.758 :**
   - Toujours appliquée (pas conditionnelle)
   - Valeur FIXE pour somme vectorielle multi-événements
   - Session 51 : Validée empiriquement

3. **Score utilisé :**
   - Reçoit `empirical_score` déjà AJUSTÉ
   - Docstring dit : "⚠️ Utiliser calculate_adjusted_empirical_score() si surprise > 5%"
   - **Chaîne : base_score → ajustement → impact**

4. **Valeur absolue :**
   - `abs(impact_brut)` → Force direction positive
   - Impact toujours positif (mouvement haut)

### EXEMPLES NUMÉRIQUES

**Exemple 1 - 11 septembre 2025 (multi-événements) :**
```
score_ajusté = 85.1
num_events = 9
amplification = 2.5 (passée par Planificateur)

impact_brut = -10.47 + (0.477 × 85.1) = 30.1
impact_amplifié = 30.1 × 2.5 = 75.3
impact_final = 75.3 × 0.758 = 57.0 pips ✅
```

**Exemple 2 - Événement isolé faible surprise :**
```
score = 50 (pas ajusté, surprise < 5%)
num_events = 1
amplification = 1.0

impact_brut = -7.08 + (0.419 × 50) = 13.9
impact_amplifié = 13.9 × 1.0 = 13.9
impact_final = 13.9 × 0.758 = 10.5 pips
```

---

## 🔍 FORMULE 3 : calculate_ttr_c() (Lignes 270-335)

### SIGNATURE

```python
def calculate_ttr_c(
    latency_minutes: float,
    surprise_pct: float
) -> float
```

### VALIDATION

**Session 52 - 11 septembre 2025 :**
- TTR prédit : 4.7 minutes
- TTR réel : 5.0 minutes
- **MAE : 0.3 minutes (18 secondes) (94.4% précision) ✅**

### FORMULE EXACTE

```python
abs_surprise = abs(surprise_pct)

# Zone 1 : Surprise faible (< 10%)
if abs_surprise < 10:
    multiplier = 3.0

# Zone 2 : Surprise moyenne (10-30%)
elif abs_surprise < 30:
    multiplier = 2.5

# Zone 3 : Surprise forte (> 30%)
else:
    multiplier = 2.0

# Calcul TTR
ttr = latency_minutes * multiplier
```

### ÉQUATION

```
TTR = latency × multiplier(surprise)
```

### ZONES MULTIPLIER

| Surprise | Multiplier | Rationale |
|----------|-----------|-----------|
| < 10% | 3.0x | Mouvement lent, marché hésite |
| 10-30% | 2.5x | Mouvement normal, réaction standard |
| > 30% | 2.0x | Mouvement rapide, forte réaction |

### RATIONALE

**Observation :**
Plus la surprise est forte, plus le marché atteint son pic rapidement.

**Logique inverse surprise :**
- Surprise faible → Marché hésite → TTR allongé (×3.0)
- Surprise forte → Réaction violente → TTR raccourci (×2.0)

### EXEMPLES NUMÉRIQUES

**Exemple 1 - CPI forte surprise :**
```
latency = 2.0 min
surprise = 33.3%

multiplier = 2.0 (surprise > 30%)
TTR = 2.0 × 2.0 = 4.0 min ✅
```

**Exemple 2 - Jobless Claims surprise moyenne :**
```
latency = 1.0 min
surprise = 11.9%

multiplier = 2.5 (surprise 10-30%)
TTR = 1.0 × 2.5 = 2.5 min
```

**Exemple 3 - CPI faible surprise :**
```
latency = 2.0 min
surprise = 0.1%

multiplier = 3.0 (surprise < 10%)
TTR = 2.0 × 3.0 = 6.0 min
```

---

## 🔍 FORMULE 4 : calculate_pullback_v2() (Lignes 338-438)

### SIGNATURE

```python
def calculate_pullback_v2(
    phase1_impact: float,
    minutes_since_peak: float,
    minutes_to_next_phase: float
) -> float
```

### VALIDATION

**Session 53 - 11 septembre 2025 :**
- Pullback prédit : 26.9 pips
- Pullback réel : 27.1 pips
- **MAE : 0.2 pips (99.3% précision) ✅ EXCELLENT**

### FORMULE EXACTE

```python
# Pas de pullback pour phases éloignées (> 30 min)
if minutes_to_next_phase > 30:
    return 0.0

# Sécurité : vérifier validité
if minutes_since_peak < 0:
    return 0.0

# Coefficient logarithmique calibré
log_coefficient = 0.30

# Plafond Fibonacci niveau supérieur (75%)
max_pullback_ratio = 0.75

# Calcul ratio pullback logarithmique
pullback_ratio = min(
    log_coefficient * math.log(minutes_since_peak + 1),
    max_pullback_ratio
)

# Appliquer au mouvement Phase 1 (valeur absolue)
pullback_pips = abs(phase1_impact) * pullback_ratio

return pullback_pips
```

### ÉQUATIONS

**Condition préalable :**
```
Si minutes_to_next_phase > 30 → pullback = 0 (phases indépendantes)
```

**Ratio pullback :**
```
ratio = min(0.30 × ln(minutes_since_peak + 1), 0.75)
```

**Pullback final :**
```
pullback = |phase1_impact| × ratio
```

### COMPORTEMENT LOGARITHMIQUE

| Durée | Ratio | Notes |
|-------|-------|-------|
| 1 min | 21% | Faible |
| 3 min | 42% | Modéré |
| 5 min | 54% | Significatif |
| 10 min | 72% | Fort (validé 11 sept) |
| 15 min | 75% | Plafond (atteint) |
| > 15 min | 75% | Saturé |

### RATIONALE

**Pourquoi logarithmique ?**

1. **Forte correction initiale** (panic selling/buying)
2. **Ralentissement progressif** (absorption par le marché)
3. **Saturation naturelle** (nouvel équilibre trouvé)

**Pas linéaire car :**
- Premiers minutes : corrections violentes
- Minutes suivantes : stabilisation graduelle
- Après 15 min : mouvement stabilisé

### EXEMPLES NUMÉRIQUES

**Exemple 1 - 11 septembre 2025 (validé) :**
```
phase1_impact = 37.4 pips
minutes_since_peak = 10 min
minutes_to_next_phase = 15 min

ratio = min(0.30 × ln(10 + 1), 0.75)
     = min(0.30 × 2.398, 0.75)
     = min(0.719, 0.75)
     = 0.719 (72%)

pullback = 37.4 × 0.719 = 26.9 pips ✅
```

**Exemple 2 - Pullback après 5 min :**
```
phase1_impact = 50.0 pips
minutes_since_peak = 5 min
minutes_to_next_phase = 20 min

ratio = min(0.30 × ln(5 + 1), 0.75)
     = min(0.30 × 1.792, 0.75)
     = min(0.538, 0.75)
     = 0.538 (54%)

pullback = 50.0 × 0.538 = 27.0 pips
```

**Exemple 3 - Phases éloignées (pas de pullback) :**
```
phase1_impact = 37.4 pips
minutes_since_peak = 10 min
minutes_to_next_phase = 35 min

→ minutes_to_next_phase > 30
→ return 0.0 (phases indépendantes)
```

---

## 📊 FONCTION BONUS : calculate_amplification_extended() (Lignes 36-93)

**⚠️ NOTE IMPORTANTE :**
Cette fonction existe dans le module mais **N'est PAS utilisée par le Planificateur V2.4**.

### SIGNATURE

```python
def calculate_amplification_extended(surprise_pct: float) -> float
```

### SESSION

**Session 88 - Amplification étendue pour surprises extrêmes**

### VALIDATION CIBLE

**01.08.2025 :**
- Surprise : 500%
- Amplification : ~9.7x
- Impact attendu : 150-180 pips
- **MAE : < 30 pips ✅**

### FORMULE COMPLÈTE

```python
abs_surprise = abs(surprise_pct)

# Zone 1 : Surprise faible (< 15%)
if abs_surprise < 15:
    return 1.0

# Zone 2 : Surprise moyenne (15-30%)
# VALIDÉ Session 51 - NE PAS MODIFIER
elif abs_surprise < 30:
    return 1.0 + (abs_surprise - 15) / 15 * 1.5

# Zone 3 : Surprise forte (30-100%)
elif abs_surprise < 100:
    return 2.5 + (abs_surprise - 30) / 70 * 2.5

# Zone 4 : Surprise extrême (> 100%)
else:
    # Croissance logarithmique avec plafond à 10x
    return min(5.0 + 0.55 * math.log10(abs_surprise - 99), 10.0)
```

### ZONES AMPLIFICATION

| Surprise | Amplification | Notes |
|----------|--------------|-------|
| 10% | 1.0x | Pas d'ampli |
| 22.5% | 1.75x | S51 validé |
| 33% | 2.5x | S51 validé |
| 50% | 3.2x | Modéré |
| 100% | 5.0x | Fort |
| 200% | 7.0x | Extrême |
| 500% | 9.7x | Exceptionnel |
| 1000% | 10.0x | Plafond |

### ⚠️ UTILISATION

**IMPORTANT :**
- Cette fonction existe mais **N'est PAS appelée** par Planificateur V2.4
- Planificateur passe `amplification=2.5` codé en dur à `calculate_impact_d()`
- **Pas de calcul dynamique amplification dans production actuelle**

---

## 🎯 RÉSUMÉ FORMULES VALIDÉES

### Chaîne de Calcul Complète

```
1. AJUSTEMENT SCORE (Session 55)
   base_score → calculate_adjusted_empirical_score() → adjusted_score

2. CALCUL IMPACT (Session 51)
   adjusted_score → calculate_impact_d(amplification=2.5) → impact_pips

3. CALCUL TTR (Session 52)
   latency + surprise → calculate_ttr_c() → ttr_minutes

4. CALCUL PULLBACK (Session 53)
   impact + timing → calculate_pullback_v2() → pullback_pips
```

### Précisions par Formule

| Formule | Précision | MAE | Session | Status |
|---------|-----------|-----|---------|--------|
| Adjusted Score | 99.9% | 0.1 | 55 | VALIDÉ |
| Impact D | 98.6% | 0.8 pips | 51 | GOLD STANDARD |
| TTR C | 94.4% | 0.3 min | 52 | VALIDÉ |
| Pullback V2 | 99.3% | 0.2 pips | 53 | EXCELLENT |

### Dépendances Entre Formules

```
base_score ──→ surprise ──→ adjusted_score
                  │              │
                  │              ↓
                  │         calculate_impact_d()
                  │              │
                  ↓              ↓
           calculate_ttr_c()  impact_pips
                  │              │
                  ↓              ↓
              ttr_minutes   calculate_pullback_v2()
                                 │
                                 ↓
                            pullback_pips
```

---

## ⚠️ DÉCOUVERTES CRITIQUES

### 1. Fallback Surprise NON Implémenté

**Message Session 96 mentionne :**
> "fallback estimate → forecast → previous"

**Code réel :**
- Planificateur : Utilise SEULEMENT `estimate`
- Aucun fallback `forecast` ou `previous`
- **Discordance documentation vs code**

### 2. Amplification 2.5 Codée en Dur

**Planificateur ligne 213 :**
```python
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=2.5  # ← CODÉ EN DUR
)
```

**Conséquence :**
- Pas de calcul dynamique amplification
- `calculate_amplification_extended()` existe mais N'est PAS utilisée
- Amplification fixe 2.5x pour TOUS cas (sauf score < 40)

### 3. Pullback Codé en Dur dans Planificateur

**Planificateur ligne 231 :**
```python
pullback = calculate_pullback_v2(37.4, 10, 15)  # ← VALEURS FIXES
```

**Problème :**
- Valeurs fixes 11 septembre
- Pas dynamique selon impact calculé
- Probablement juste pour display ?

### 4. Query Charge TOUS HIGH Impacts

**Code query ligne 160 :**
```sql
WHERE ef.empirical_score > 40  -- Tous événements HIGH
```

**Commentaires disent :**
> "Charge uniquement événements CPI"

**Réalité :**
- Charge CPI, NFP, Retail Sales, etc.
- Filtre : score > 40 (pas label CPI)
- **Commentaires obsolètes**

---

## 📋 QUESTIONS RESTANTES

### À Clarifier par Lecture Sessions 51-55

1. **Amplification dynamique :**
   - Session 51 mentionne "amplification zones surprise"
   - Code actuel utilise 2.5 fixe
   - Y a-t-il eu changement méthodologie ?

2. **Fallback surprise :**
   - Documentation mentionne fallback
   - Code n'implémente pas
   - Quelle est la version correcte ?

3. **Correction 0.758 :**
   - Toujours appliquée (même événement isolé)
   - Session 51 valide-t-elle pour tous cas ?

4. **Coefficient 0.55 (Session 89-91) :**
   - Mentionné dans message S96
   - Pas présent dans code actuel
   - A-t-il été abandonné ?

---

**Token usage actuel : ~60k / 190k (32%)**
**Marge avant limite 105k : 45k tokens**

**Prochaine étape : Lecture Sessions 51-55 (rapports complets)**
