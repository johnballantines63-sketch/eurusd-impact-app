# REF-016 : Détail Complet du Noyau Dur - 2025-09-11

**Date :** 2025-12-06  
**Exemple :** 2025-09-11 - CPI (US)

---

## 📊 RÉSUMÉ

- **Mouvement fort détecté :** 62.40 pips (UP)
- **Cluster principal :** 12 événements à 14:30
- **Core Type :** CPI
- **Événements composant le noyau dur :** 6 événements CPI
- **Événements exclus (sans estimate) :** 0

---

## 🔍 TOUS LES ÉVÉNEMENTS DU CLUSTER (12 événements)

| Heure | Event Key | Country | Importance | Estimate | Actual | Surprise | Score | Inclus |
|-------|-----------|---------|------------|----------|--------|----------|-------|--------|
| 14:15 | deposit facility rate | EU | 1 | 2.00 | 2.00 | +0.0% | 85.4 | ✅ OUI |
| 14:15 | ecb interest rate decision | EU | 1 | 2.15 | 2.15 | +0.0% | 85.4 | ✅ OUI |
| 14:15 | marginal lending rate | EU | 3 | NaN | 2.40 | NaN | 85.4 | ✅ OUI |
| 14:30 | continuing jobless claims | US | 3 | 1950.00 | 1939.00 | -0.6% | 54.8 | ✅ OUI |
| 14:30 | core inflation rate mom | US | 1 | 0.30 | 0.30 | +0.0% | 84.4 | ✅ OUI |
| 14:30 | core inflation rate yoy | US | 1 | 3.10 | 3.10 | +0.0% | 84.4 | ✅ OUI |
| 14:30 | **cpi** | US | 2 | 323.89 | 323.98 | +0.0% | 84.4 | ✅ OUI |
| 14:30 | **cpi sa** | US | 2 | NaN | 323.36 | NaN | 71.2 | ✅ OUI |
| 14:30 | **inflation rate mom** | US | 1 | 0.30 | 0.40 | **+33.3%** | 84.4 | ✅ OUI |
| 14:30 | **inflation rate yoy** | US | 1 | 2.90 | 2.90 | +0.0% | 84.4 | ✅ OUI |
| 14:30 | initial jobless claims | US | 2 | 235.00 | 263.00 | +11.9% | 54.8 | ✅ OUI |
| 14:30 | jobless claims 4week average | US | 3 | NaN | 240.50 | NaN | 54.8 | ✅ OUI |

---

## 🎯 ÉVÉNEMENTS COMPOSANT LE NOYAU DUR CPI (6 événements)

Le noyau dur CPI est composé des **6 événements CPI/Inflation** suivants :

| Heure | Event Key | Country | Importance | Estimate | Actual | Surprise | Score | Type |
|-------|-----------|---------|------------|----------|--------|----------|-------|------|
| 14:30 | **core inflation rate mom** | US | 1 | 0.30 | 0.30 | +0.0% | 84.4 | CPI |
| 14:30 | **core inflation rate yoy** | US | 1 | 3.10 | 3.10 | +0.0% | 84.4 | CPI |
| 14:30 | **cpi** | US | 2 | 323.89 | 323.98 | +0.0% | 84.4 | CPI |
| 14:30 | **cpi sa** | US | 2 | NaN | 323.36 | NaN | 71.2 | CPI |
| 14:30 | **inflation rate mom** | US | 1 | 0.30 | 0.40 | **+33.3%** | 84.4 | CPI |
| 14:30 | **inflation rate yoy** | US | 1 | 2.90 | 2.90 | +0.0% | 84.4 | CPI |

### Caractéristiques

1. **Tous à 14:30** : Événements US synchronisés
2. **Tous avec estimate** : Permettent calcul de surprise
3. **Surprise principale :** Inflation Rate MoM = +33.3% (0.40 vs 0.30)
4. **Scores élevés :** 71.2-84.4 (événements importants)

---

## 📋 ÉVÉNEMENTS NON-CPI DANS LE CLUSTER (6 événements)

Ces événements sont dans le cluster mais **ne font pas partie du noyau dur** :

| Heure | Event Key | Country | Importance | Type | Raison Exclusion |
|-------|-----------|---------|------------|------|------------------|
| 14:15 | deposit facility rate | EU | 1 | ECB | Pas CPI |
| 14:15 | ecb interest rate decision | EU | 1 | ECB | Pas CPI |
| 14:15 | marginal lending rate | EU | 3 | ECB | Pas CPI |
| 14:30 | continuing jobless claims | US | 3 | Jobless | Pas CPI |
| 14:30 | initial jobless claims | US | 2 | Jobless | Pas CPI |
| 14:30 | jobless claims 4week average | US | 3 | Jobless | Pas CPI |

**Note :** Ces événements sont inclus dans le cluster (fenêtre 30 min) mais ne sont **pas core** car ils ne correspondent pas au pattern CPI.

---

## 🔍 PROCESSUS D'IDENTIFICATION

### Étape 1 : Détection Pattern CPI

**Pattern utilisé :**
```python
CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
```

**Résultat :** 6 événements match le pattern CPI

### Étape 2 : Vérification Seuil

**Condition :** `cpi_count >= 2`

**Résultat :** ✅ 6 ≥ 2 → Core Type = CPI

### Étape 3 : Sélection Événements Core

**Logique :**
- Tous les événements CPI → **core** (support = 1.0)
- Tous les autres événements → **non-core** (support = 0.0)

**Résultat :** 6 événements CPI = core, 6 autres = non-core

---

## 💡 CONTRIBUTION AU CALCUL DU SCORE core_scores

### Pour 2025-09-11 Spécifiquement

**Impact réel mesuré :** 62.40 pips

**Contribution au score CPI (US) :**
- Fait partie des **32 occurrences** utilisées pour calculer le score
- Position : Au-dessus de la moyenne (59.83), en dessous du P80 (90.28)
- Contribution modeste (proche de la moyenne)

### Pour le Score CPI (US) = 75.06

**Basé sur 32 mouvements forts** où le noyau dur était CPI, incluant :
- 2025-09-11 : 62.40 pips (6 événements CPI)
- 2023-07-12 : 109.30 pips (événements CPI)
- 2023-10-12 : 93.60 pips (événements CPI)
- ... et 29 autres dates

**Chaque date contribue avec :**
- Son impact réel mesuré
- Son noyau dur identifié (CPI dans ce cas)
- Sa direction (UP/DOWN)

---

## 🎯 UTILISATION DANS LE PIPELINE

### Étape 3 : Définir Noyau Dur

**Input :** Cluster avec 12 événements  
**Output :** 6 événements CPI identifiés comme core

**Utilisation :**
- Identifier le cluster comme CPI
- Rechercher clusters identiques dans l'historique (Étape 4)
- Calculer le score de qualité du cluster

### Étape 4 : Rechercher Clusters Identiques

**Critère :** Clusters avec même noyau dur (6 événements CPI)

**Résultat :** Trouve 32 clusters historiques avec CPI comme noyau dur

### Calcul Score core_scores

**Basé sur :** 32 impacts réels mesurés pour ces clusters CPI  
**Score final :** 75.06

---

## 📊 TABLEAU RÉCAPITULATIF

| Catégorie | Nombre | Détails |
|-----------|--------|---------|
| **Événements totaux** | 12 | Tous les événements dans fenêtre 30 min |
| **Événements avec estimate** | 12 | Tous ont estimate (aucun exclu) |
| **Événements CPI** | 6 | Composent le noyau dur |
| **Événements non-CPI** | 6 | Dans cluster mais pas core |
| **Surprise principale** | +33.3% | Inflation Rate MoM (0.40 vs 0.30) |
| **Impact réel** | 62.40 pips | Mesuré depuis prix |
| **Contribution score** | 1/32 | Fait partie des 32 occurrences CPI (US) |

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




