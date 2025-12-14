# REF-025 : Investigation - Dates GENERIC sans Clusters Identiques

**Date :** 2025-12-06  
**Problème :** Dates avec core_type GENERIC n'ont pas de clusters identiques

---

## 🔍 RÉSULTATS INVESTIGATION

### 2025-06-23 (GENERIC, US)

**Noyau dur :**
- 4 événements core : EU bonds (12:45)
  - `eu bond auction_EU_3`
  - `2029 eu bonds_EU_3`
  - `2035 eu bonds_EU_3`
  - `2051 eu bonds_EU_3`

**Dates historiques :**
- ✅ 20 dates trouvées avec événements à 12:45 (±10 min)
- ❌ **Aucun cluster identique** (Jaccard < 0.60)

**Analyse Jaccard (top 5 dates) :**

| Date Historique | N Events | Intersection | Union | Jaccard | Seuil 0.60 |
|-----------------|----------|--------------|-------|---------|-------------|
| 2025-06-16 | 1 | 0 | 5 | 0.000 | ❌ FAIL |
| 2025-06-09 | 1 | 0 | 5 | 0.000 | ❌ FAIL |
| 2025-06-02 | 4 | 1 | 7 | 0.143 | ❌ FAIL |
| 2025-05-30 | 1 | 0 | 5 | 0.000 | ❌ FAIL |
| 2025-05-21 | 2 | 0 | 6 | 0.000 | ❌ FAIL |

**Problème identifié :**
- Les événements historiques sont différents (différents types de bonds, ou format différent)
- Jaccard max : 0.143 (trop faible, seuil 0.60)
- **Cause :** Événements rares ou noms variables

---

### 2025-10-10 (GENERIC, EU)

**Noyau dur :**
- 2 événements core : ECOFIN (02:00)
  - `ecofin meeting_EU_3`
  - `ecofin meetin_EU_3` (typo ?)

**Dates historiques :**
- ✅ 20 dates trouvées avec événements à 02:00 (±10 min)
- ❌ **Aucun cluster identique** (Jaccard = 0.000)

**Analyse Jaccard (top 5 dates) :**

| Date Historique | N Events | Intersection | Union | Jaccard | Seuil 0.60 |
|-----------------|----------|--------------|-------|---------|-------------|
| 2025-10-09 | 4 | 0 | 6 | 0.000 | ❌ FAIL |
| 2025-10-08 | 5 | 0 | 7 | 0.000 | ❌ FAIL |
| 2025-10-07 | 7 | 0 | 9 | 0.000 | ❌ FAIL |
| 2025-10-06 | 8 | 0 | 10 | 0.000 | ❌ FAIL |
| 2025-10-05 | 2 | 0 | 4 | 0.000 | ❌ FAIL |

**Problème identifié :**
- Aucune intersection (Jaccard = 0.000)
- Les événements historiques à 02:00 sont différents (pas ECOFIN)
- **Cause :** Événements rares ou timing différent

---

## 🔍 CAUSES IDENTIFIÉES

### 1. Événements Rares

**Problème :** Les événements GENERIC sont souvent rares ou uniques
- EU bonds : Différents types (2029, 2035, 2051) selon la date
- ECOFIN : Événement rare, pas toujours présent

**Impact :** Pas assez de dates historiques avec les mêmes événements

### 2. Normalisation Event Key

**Problème :** La normalisation des `event_key` peut ne pas fonctionner correctement
- `ecofin meeting` vs `ecofin meetin` (typo ?)
- `2029 eu bonds` vs `eu bond auction` (formats différents)

**Impact :** Jaccard faible même si événements similaires

### 3. Seuil Jaccard Trop Strict

**Problème :** Seuil 0.60 peut être trop strict pour événements GENERIC
- 2025-06-02 : Jaccard = 0.143 (1 intersection sur 7 union)
- Si on baisse à 0.15, on trouverait des clusters

**Impact :** Clusters similaires rejetés

### 4. Heure d'Événement

**Problème :** Certains événements GENERIC sont à des heures rares
- 12:45 (EU bonds) : Heure peu commune
- 02:00 (ECOFIN) : Heure très rare

**Impact :** Moins de dates historiques à la même heure

---

## 💡 SOLUTIONS PROPOSÉES

### Solution 1 : Seuil Jaccard Adaptatif pour GENERIC

**Principe :** Utiliser un seuil plus bas pour core_type GENERIC

**Implémentation :**
```python
if core_type == 'GENERIC':
    jaccard_threshold = 0.30  # Au lieu de 0.60
else:
    jaccard_threshold = 0.60
```

**Avantages :**
- Trouve des clusters similaires même si pas identiques
- Permet d'utiliser RF même pour GENERIC

**Inconvénients :**
- Clusters moins similaires (qualité moindre)

### Solution 2 : Améliorer Normalisation Event Key

**Principe :** Normaliser mieux les event_key pour GENERIC

**Exemples :**
- `ecofin meeting` et `ecofin meetin` → `ecofin_meeting`
- `2029 eu bonds` et `eu bond auction` → `eu_bond_auction`

**Avantages :**
- Meilleure détection de similarité
- Jaccard plus élevé

**Inconvénients :**
- Nécessite règles de normalisation spécifiques

### Solution 3 : Recherche par Famille d'Événements

**Principe :** Pour GENERIC, rechercher par famille plutôt que par événements exacts

**Exemples :**
- EU bonds → Tous les événements "bond" EU
- ECOFIN → Tous les événements "ecofin" EU

**Avantages :**
- Trouve plus de clusters similaires
- Meilleure couverture

**Inconvénients :**
- Clusters moins précis

### Solution 4 : RF Global avec core_score

**Principe :** Utiliser RF global même sans clusters identiques, avec core_score

**Implémentation :**
- Actuellement : RF global avec `core_score = 0.0` pour GENERIC
- Amélioration : Calculer `core_score` même pour GENERIC (basé sur famille)

**Avantages :**
- Utilise core_score même pour GENERIC
- Meilleure prédiction

**Inconvénients :**
- Nécessite calcul core_score pour GENERIC

---

## 🎯 RECOMMANDATION

### Approche Hybride

1. **Court terme** : Seuil Jaccard adaptatif pour GENERIC (0.30 au lieu de 0.60)
2. **Moyen terme** : Améliorer normalisation event_key
3. **Long terme** : Recherche par famille pour GENERIC

### Priorité

**✅ Solution 1 (Seuil adaptatif)** : Plus simple, impact immédiat

**Implémentation :**
```python
# Dans etape4_rechercher_clusters_identiques
if core_type == 'GENERIC':
    jaccard_threshold_generic = 0.30  # Seuil plus bas
    # Utiliser jaccard_threshold_generic au lieu de jaccard_threshold
```

---

## 📊 IMPACT ATTENDU

### Avant (Seuil 0.60)

| Date | Core Type | Clusters Identiques | RF Utilisé |
|------|-----------|---------------------|------------|
| 2025-06-23 | GENERIC | 0 | ❌ Non (RF global fallback) |
| 2025-10-10 | GENERIC | 0 | ❌ Non (RF global fallback) |

### Après (Seuil 0.30 pour GENERIC)

| Date | Core Type | Clusters Identiques | RF Utilisé |
|------|-----------|---------------------|------------|
| 2025-06-23 | GENERIC | ? (≥ 1 attendu) | ✅ Oui (RF par date) |
| 2025-10-10 | GENERIC | ? (≥ 1 attendu) | ✅ Oui (RF par date) |

**Bénéfice :** Meilleure utilisation de RF avec core_score pour GENERIC

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




