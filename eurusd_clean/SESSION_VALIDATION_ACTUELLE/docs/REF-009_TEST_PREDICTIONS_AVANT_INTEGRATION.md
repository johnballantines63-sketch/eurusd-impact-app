# REF-009 : Test Prédictions Avant Intégration Nouveaux Scores

**Date :** 2025-12-06  
**Objectif :** Tester les prédictions actuelles du pipeline avant d'intégrer les nouveaux scores de `core_scores`

---

## 📊 RÉSULTATS ACTUELS (Sans Nouveaux Scores)

### Dates Testées

| Date | Core Type | Impact Base | Amplification | Impact Prédit |
|------|-----------|-------------|----------------|---------------|
| 2025-05-29 | UNKNOWN | 22.76 pips | 1.610x | **74.40 pips** |
| 2025-09-11 | UNKNOWN | 34.16 pips | 1.600x | **60.70 pips** |
| 2025-08-01 | UNKNOWN | 46.94 pips | 6.179x | **188.40 pips** |
| 2025-11-20 | UNKNOWN | 39.10 pips | 1.380x | **36.60 pips** |

### Observations

1. **Core Type non identifié** : Le pipeline retourne "UNKNOWN" au lieu de "JOBLESS_PCE", "CPI", etc.
   - Cause probable : Le `core_type` n'est pas correctement extrait de `etape3_noyau_dur`
   - Impact : Les scores de `core_scores` ne peuvent pas être utilisés

2. **Prédictions fonctionnent** : Les impacts prédits sont calculés correctement
   - Utilisation actuelle : Scores depuis `event_families` (moyenne des scores individuels)

3. **Scores core_scores disponibles** :
   - JOBLESS_PCE (US) : 53.51
   - CPI (US) : 75.06
   - NFP (US) : 80.13
   - etc.

---

## 🎯 PROCHAINES ÉTAPES

### 1. Corriger Extraction Core Type

Le `core_type` doit être correctement extrait de `etape3_noyau_dur` pour pouvoir utiliser les scores de `core_scores`.

### 2. Intégrer Scores core_scores dans Pipeline

**Modification à faire :**

Dans `etape3_definir_noyau_dur` ou `etape6_calculer_impacts_base_amplifications` :

```python
# Si core_type identifié et score disponible dans core_scores
core_score = get_core_score_from_db(conn, core_type, country)
if core_score:
    # Utiliser score core_scores au lieu de moyenne event_families
    base_score_mean = core_score
else:
    # Fallback : moyenne des scores individuels (comportement actuel)
    base_score_mean = sum(base_scores) / len(base_scores)
```

### 3. Tester Prédictions avec Nouveaux Scores

Comparer :
- **Avant** : Prédictions avec scores `event_families` (moyenne)
- **Après** : Prédictions avec scores `core_scores` (spécifiques par type)

---

## 📋 ATTENDU

Avec les nouveaux scores intégrés :

- **2025-05-29 (JOBLESS_PCE)** : Score 53.51 au lieu de moyenne event_families
- **2025-09-11 (CPI)** : Score 75.06 au lieu de moyenne event_families
- **Impact Base** : Devrait être plus précis (score spécifique vs moyenne)
- **Impact Prédit** : Devrait être amélioré

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




