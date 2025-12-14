# 🔍 LOGIQUE DE RECHERCHE DE DATES - CLARIFICATION

## ❌ Problème Actuel

L'approche actuelle est **confuse** :
1. On cherche des dates futures/passées avec événements
2. Pour chaque date, on essaie de matcher avec le cache
3. On filtre par impact/occurrences **sans avoir défini quel cluster on cherche**

**Résultat :** "Aucune date avec cluster match" mais on n'a pas sélectionné de cluster de référence !

---

## ✅ Approches Possibles

### **Approche A : Recherche par Cluster de Référence** (Recommandée)

**Workflow :**
1. **Sélectionner un cluster de référence** :
   - Option 1 : Depuis le cache (liste des clusters historiques)
   - Option 2 : Depuis une date passée (ex: 2025-09-11)
   - Option 3 : Construire manuellement (sélectionner événements)

2. **Chercher ce cluster dans le futur/passé** :
   - Construire la signature du cluster de référence
   - Scanner les dates futures/passées
   - Pour chaque date, construire le cluster d'événements
   - Matcher avec la signature de référence (Jaccard ≥ 80%)
   - Afficher les dates où le cluster se reproduit

3. **Afficher prédictions** :
   - Pour chaque date trouvée, utiliser les stats du cluster (impact_median, pattern, etc.)
   - Calculer prédiction avec formules validées

**Avantages :**
- ✅ Logique claire : "Je cherche où ce cluster se reproduit"
- ✅ Impact prévisible : on connaît l'impact médian du cluster
- ✅ Pattern connu : on sait quel pattern ce cluster produit

**Interface :**
```
Mode de recherche :
[ ] Par cluster de référence
    → Sélectionner cluster depuis cache
    → OU Sélectionner date passée comme référence
    → Période de recherche (futur/passé)
    → Afficher dates où cluster se reproduit
```

---

### **Approche B : Recherche par Pattern**

**Workflow :**
1. **Sélectionner un pattern** :
   - DOUBLE_WAVE_UP
   - SINGLE_WAVE_FORT_UP
   - SINGLE_WAVE_STANDARD_DOWN
   - etc.

2. **Identifier clusters qui produisent ce pattern** :
   - Filtrer le cache par `dominant_pattern == pattern_sélectionné`
   - Lister les clusters correspondants avec leurs stats

3. **Chercher ces clusters dans le futur/passé** :
   - Pour chaque cluster identifié, chercher où il se reproduit
   - Afficher dates avec prédictions

**Avantages :**
- ✅ Logique : "Je cherche des dates avec pattern X"
- ✅ Plusieurs clusters peuvent produire le même pattern

**Interface :**
```
Mode de recherche :
[ ] Par pattern
    → Sélectionner pattern (DOUBLE_WAVE_UP, etc.)
    → Filtrer par impact/occurrences
    → Période de recherche
    → Afficher dates avec clusters correspondants
```

---

### **Approche C : Recherche par Impact/Pattern (Hybride)**

**Workflow :**
1. **Filtrer le cache** :
   - Par pattern (optionnel)
   - Par impact médian ≥ X pips
   - Par occurrences ≥ Y
   - Par pays

2. **Pour chaque cluster filtré** :
   - Chercher où il se reproduit dans le futur/passé
   - Afficher dates avec prédictions

**Avantages :**
- ✅ Flexible : combine plusieurs critères
- ✅ Permet de découvrir de nouveaux clusters intéressants

**Interface :**
```
Mode de recherche :
[ ] Par critères (impact/pattern/occurrences)
    → Filtres : Pattern, Impact min, Occurrences min, Pays
    → Période de recherche
    → Pour chaque cluster correspondant, chercher dates
    → Afficher toutes les dates trouvées
```

---

## 🎯 Recommandation : Approche A + C (Hybride)

### **Mode 1 : Recherche par Cluster de Référence**

**Cas d'usage :** "Je veux savoir quand le cluster du 11.09.2025 se reproduit"

**Interface :**
```
┌─────────────────────────────────────────┐
│ Mode de recherche                      │
│ ○ Par critères                         │
│ ● Par cluster de référence             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Cluster de référence                   │
│ ○ Depuis cache (sélectionner)          │
│ ● Depuis date passée                    │
│   Date : [2025-09-11]                  │
│   → Cluster détecté : 11 événements    │
│     (CPI_US, Core_CPI_US, ...)         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Période de recherche                   │
│ Direction : [Futur ▼]                  │
│ Nombre de jours : [30]                 │
│ OU Période manuelle : [2025-10-01] à   │
│                      [2025-12-31]      │
└─────────────────────────────────────────┘

[🔍 Rechercher]
```

**Résultat :**
```
✅ 3 dates trouvées où le cluster se reproduit :

1. 2025-11-15 - Impact médian: 52 pips (5 occ.)
   Pattern: DOUBLE_WAVE_UP
   Confiance: 85%

2. 2025-12-10 - Impact médian: 48 pips (3 occ.)
   Pattern: DOUBLE_WAVE_UP
   Confiance: 75%

3. 2025-12-20 - Impact médian: 45 pips (2 occ.)
   Pattern: SINGLE_WAVE_FORT_UP
   Confiance: 60%
```

---

### **Mode 2 : Recherche par Critères**

**Cas d'usage :** "Je cherche tous les clusters avec impact ≥ 50 pips et pattern DOUBLE_WAVE"

**Interface :**
```
┌─────────────────────────────────────────┐
│ Mode de recherche                      │
│ ● Par critères                         │
│ ○ Par cluster de référence             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Filtres clusters                       │
│ Pattern : [DOUBLE_WAVE ▼]              │
│ Impact médian min : [50] pips          │
│ Occurrences min : [3]                  │
│ Pays : [US, EU]                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Période de recherche                   │
│ [Période manuelle]                     │
│ De : [2025-10-01] à [2025-12-31]       │
└─────────────────────────────────────────┘

[🔍 Rechercher]
```

**Résultat :**
```
✅ 5 clusters trouvés correspondant aux critères :

Cluster 1: CPI_US + Core_CPI_US + ...
  - Impact médian: 52 pips (5 occ.)
  - Pattern: DOUBLE_WAVE_UP
  - Dates futures: 2025-11-15, 2025-12-10

Cluster 2: NFP_US + ...
  - Impact médian: 58 pips (4 occ.)
  - Pattern: DOUBLE_WAVE_UP
  - Dates futures: 2025-11-01, 2025-12-05

...
```

---

## 📊 Structure Cache

Le cache `cache_clusters.csv` contient :
- `cluster_signature` : "event_key1|event_key2|..." (normalisé)
- `n_samples` : Nombre d'occurrences historiques
- `impact_median` : Impact médian en pips
- `dominant_pattern` : Pattern dominant (DOUBLE_WAVE, SINGLE_WAVE_FORT, etc.)
- `dominant_direction` : Direction (UP/DOWN)
- `latency_median`, `ttr_median`, `pullback_median` : Métriques

**Chaque ligne = 1 cluster unique avec ses stats historiques**

---

## 🔄 Workflow Correct Intégré

### **Option 1 : Recherche par Cluster → Dates**

```
1. Sélectionner cluster de référence
2. Chercher dates futures/passées avec même cluster
3. Pour chaque date trouvée :
   - Charger prix
   - Détecter pattern (Workflow Correct)
   - Vérifier cohérence avec pattern attendu du cluster
   - Calculer prédiction
```

### **Option 2 : Recherche par Pattern → Clusters → Dates**

```
1. Sélectionner pattern souhaité
2. Filtrer cache par pattern
3. Pour chaque cluster correspondant :
   - Chercher dates futures/passées avec ce cluster
   - Afficher avec prédictions
```

---

## ❓ Questions à Clarifier

1. **Impact d'un event ou d'un cluster ?**
   - **Réponse attendue :** Impact d'un **cluster multi-event** (somme vectorielle)
   - Le cache stocke `impact_median` par cluster, pas par event individuel

2. **Quel cluster cherche-t-on ?**
   - **Réponse attendue :** 
     - Soit un cluster de référence spécifique (depuis date passée ou cache)
     - Soit tous les clusters correspondant à des critères (pattern, impact, etc.)

3. **Ordre de recherche ?**
   - **Option A :** Cluster → Dates (recommandé)
   - **Option B :** Dates → Clusters (actuel, moins logique)

---

## 🎯 Proposition d'Implémentation

**Mode 1 : Recherche par Cluster de Référence**
- Sélectionner date passée → extraire cluster → chercher dans futur/passé
- OU Sélectionner cluster depuis cache → chercher dans futur/passé

**Mode 2 : Recherche par Critères**
- Filtrer cache (pattern, impact, occurrences) → pour chaque cluster, chercher dates

**Les deux modes peuvent coexister dans l'interface**

---

**Quelle approche préfères-tu ?** Je peux implémenter les deux modes.


