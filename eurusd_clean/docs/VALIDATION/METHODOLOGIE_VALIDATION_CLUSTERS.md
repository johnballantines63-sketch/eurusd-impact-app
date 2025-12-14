# 📊 MÉTHODOLOGIE VALIDATION SCIENTIFIQUE - CLUSTERS RÉCURRENTS

**Date :** 31 octobre 2025 - Session 104  
**Status :** 🎯 MÉTHODOLOGIE DÉFINIE - Approche cluster par cluster

---

## 🎯 PRINCIPE FONDAMENTAL

**Hypothèse à valider :**
> Le facteur d'amplification amp optimal varie selon contexte (surprise, R², amplitude, durée)

**Approche scientifique :**
> Valider sur clusters IDENTIQUES (même composition événements) qui se répètent

**⚠️ PRINCIPE CRITIQUE :**
> **Chaque cluster a SA PROPRE baseline empirique !**
> 
> Ne JAMAIS supposer qu'une baseline s'applique à tous les clusters.
> 
> Exemples :
> - Cluster #3 (CPI, 11 events) : baseline = 2.5 (déjà calculé)
> - Cluster #2 (NFP, 12 events) : baseline = ? (à calculer)
> - Cluster #1 (Mfg, 8 events)  : baseline = ? (à calculer)
> 
> Raison : Compositions différentes = Dynamiques marché différentes
> CPI ≠ NFP ≠ Manufacturing ≠ Jobless

---

## ❌ APPROCHE INCORRECTE (à éviter)

**Mélanger tous les clusters ensemble :**
```
❌ Comparer :
   - 8 events Consumer @ 15:45
   - 11 events Inflation @ 14:30  
   - 12 events Employment @ 14:30
   - etc.

Problème : Trop de variables confondantes
- Composition différente
- Familles différentes
- Heures différentes
→ Impossible d'isoler effet de surprise/R² sur amp
```

---

## ✅ APPROCHE CORRECTE (méthodologie validée)

**Cluster par cluster, intra-groupe :**

```
✅ Pour CHAQUE cluster séparément :

1. Établir baseline du cluster
   - Choisir UNE date de référence
   - Valider empiriquement son impact (comme 11.09)
   - Calculer amp_optimal pour cette date
   - CE amp devient la BASELINE du cluster

2. Tester autres dates du cluster
   - Prédiction avec baseline du cluster
   - Mesurer impact réel
   - Calculer amp_optimal par date
   - Delta vs baseline du cluster

3. Régression intra-cluster
   - delta_amp = f(surprise, R², amplitude)
   - Formule : amp = baseline_cluster × (1 + correction)
   - Validation Leave-One-Out

4. Décision par cluster
   - Si formule améliore baseline → Adopter
   - Si amélioration marginale → Garder baseline
```

**Avantage :**
- Même composition → Variable constante ✅
- Seules changent : surprise, R², amplitude, durée
- **Isolation parfaite des facteurs** ✅

---

## 📊 CLUSTERS IDENTIFIÉS (Session 104)

**5 clusters récurrents trouvés :**

### Cluster #1 : 11 occurrences
```
Composition : 8 événements (Manufacturing, Consumer, Employment)
Dates       : 2025-10-01, 2025-09-02, 2025-07-01, 2025-06-02...
Impact moyen: 15.6 pips (σ=7.1)
```

### Cluster #2 : 7 occurrences
```
Composition : 12 événements (Employment - NFP)
Dates       : 2025-09-05, 2025-07-03, 2025-06-06, 2025-05-02...
Impact moyen: 27.8 pips (σ=13.5)
```

### Cluster #3 : 6 occurrences ⭐ (PRIORITAIRE)
```
Composition : 11 événements (CPI/Inflation)
Dates       : 2025-09-11 🎯, 2025-08-12, 2025-07-15, 2025-06-11...
Impact moyen: 37.1 pips (σ=28.3)
Référence   : 2025-09-11 (validé Session 103)
```

### Cluster #4 : 3 occurrences
```
Composition : 8 événements (Employment - Jobless)
Dates       : 2025-03-07, 2025-02-07, 2024-12-06
Impact moyen: 32.9 pips (σ=20.4)
```

### Cluster #5 : 2 occurrences
```
Composition : 10 événements (Employment mix)
Dates       : 2025-04-04, 2025-01-10
Impact moyen: 37.0 pips (σ=4.2)
```

---

## 🎯 PLAN D'EXÉCUTION

### Phase 1 : Cluster #3 (CPI/Inflation) - PRIORITAIRE ⭐⭐⭐

**Raison :** 
- Cas 11.09 déjà validé Session 103 (référence solide)
- 6 occurrences (statistiquement significatif)
- Composition stable (CPI mensuel)

**Étapes :**

**2.3 - Extraction Cluster #3** (6 dates)
```python
dates = [
    '2025-09-11',  # Référence (amp=2.5, impact=56.8 pips validé)
    '2025-08-12',  # Test 1
    '2025-07-15',  # Test 2
    '2025-06-11',  # Test 3
    '2025-05-13',  # Test 4
    '2025-04-10'   # Test 5
]
```

**Étape 2.4 - Mesure impact réel** (méthode Session 92.5)
```python
for date in dates:
    impact_real = measure_impact_session92_5(date)
    # Vérification date référence (ex: 11.09 = 56.8 pips) ✅
```

**3.1 - Calcul amp_optimal date référence**
```python
# Date référence du cluster (ex: 11.09 pour Cluster #3)
date_ref = dates[0]
impact_real_validated = 56.8  # Validé empiriquement

amp_optimal_ref = optimize_amp(score, n, impact_real_validated)
# Résultat : 2.524 pour Cluster #3

baseline_cluster = amp_optimal_ref  # ✅ BASELINE du cluster
# Ex: Cluster #3 baseline = 2.524 ≈ 2.5
```

**3.2 - Calcul amp_optimal autres dates**
```python
# Pour les autres dates du cluster
for date in dates[1:]:  # Sauf date référence
    impact_real = measure_impact(date)
    amp_opt = optimize_amp(score, n, impact_real)
    
    # Delta vs BASELINE DU CLUSTER
    delta_amp = (amp_opt - baseline_cluster) / baseline_cluster
```

**3.3 - Collecte métriques**
```python
for date in dates:
    metrics = {
        'surprise': surprise_max,
        'R2_72h': calculate_R2(date),
        'amplitude': volatility_amplitude(date),
        'duration': time_to_reversal(date)
    }
```

**4.1 - Régression intra-cluster**
```python
# Sur les 6 dates Cluster #3
delta_amp = f(surprise, R2, amplitude, duration)

# Exemple formule (si baseline_cluster = 2.5) :
amp = baseline_cluster × (1 + α×surprise + β×R² + γ×amplitude)
# Ex: amp = 2.5 × (1 + 0.15×surprise - 0.08×R² + 0.02×amplitude)
```

**4.2 - Validation Leave-One-Out**
```python
for test_date in dates:
    train_dates = dates - {test_date}
    model = train_regression(train_dates)
    mae_test = test(model, test_date)

# MAE cible : < 5 pips amélioration vs baseline du cluster
```

**4.3 - Décision**
```python
if mae_cluster_model < mae_baseline_cluster:
    print("✅ Formule cluster améliore baseline du cluster")
    adopt_cluster_formula()
else:
    print("✅ Baseline du cluster suffisante")
    keep_baseline_cluster()
```

---

### Phase 2 : Cluster #1 (Manufacturing/Consumer) ⭐⭐

**Après validation Cluster #3 :**
- 11 occurrences (excellent échantillon)
- Répéter méthodologie complète
- Comparer formule vs Cluster #3

---

### Phase 3 : Cluster #2 (NFP) ⭐⭐

**Après Clusters #3 et #1 :**
- 7 occurrences (bon échantillon)
- NFP = événement majeur
- Potentiellement comportement différent

---

### Phase 4+ : Clusters #4, #5 (optionnel) ⭐

**Si temps disponible :**
- Échantillons plus petits (2-3 occurrences)
- Validation moins robuste
- Vérification patterns vs clusters majeurs

---

## 📊 RÉSULTATS ATTENDUS

**Pour chaque cluster :**

**Scénario A : Formule améliore (MAE < baseline du cluster)**
```python
# Exemple Cluster #3 (baseline = 2.5)
amp_cluster3 = 2.5 × (1 + 0.15×surprise - 0.08×R² + 0.02×amplitude)

# Exemple Cluster #2 (baseline = X, à déterminer)
amp_cluster2 = X × (1 + α×surprise + β×R² + γ×amplitude)

Planificateur v2.7 :
- Détecte type cluster (CPI/NFP/Manufacturing/etc)
- Applique formule spécifique au cluster
- Amélioration précision : 5-10 pips
```

**Scénario B : Baseline du cluster suffisante**
```python
# Pas d'amélioration significative
amp_cluster3 = 2.5  # Garder baseline Cluster #3
amp_cluster2 = X    # Garder baseline Cluster #2

Planificateur v2.6 :
- Utilise baseline du cluster détecté
- Précision déjà excellente
```

**⚠️ IMPORTANT :**
Chaque cluster a **SA PROPRE baseline** !
- Cluster #3 (CPI) : baseline = 2.5 (déjà calculé)
- Cluster #1 (Manufacturing) : baseline = ? (à calculer Phase 2)
- Cluster #2 (NFP) : baseline = ? (à calculer Phase 3)
- Cluster #4 (Jobless) : baseline = ? (à calculer Phase 4)

---

## 🎓 AVANTAGES MÉTHODOLOGIE

**1. Rigueur scientifique ✅**
- Variables contrôlées (composition constante)
- Isolation facteurs (surprise, R², amplitude)
- Comparaison intra-groupe valide

**2. Validation robuste ✅**
- Leave-One-Out par cluster
- Échantillons 3-11 occurrences
- Test multi-clusters

**3. Décision éclairée ✅**
- MAE quantifié pour chaque cluster
- Amélioration vs baseline mesurée
- Adoption conditionnelle (si bénéfice prouvé)

**4. Évolutivité ✅**
- Ajouter nouveaux clusters facilement
- Méthodologie réplicable
- Documentation claire pour sessions futures

---

## ⚠️ POINTS CRITIQUES

**1. Mesure impact DOIT être correcte**
```
Session 103 : 11.09 = 56.8 pips validé
Script actuel : 11.09 = 12.7 pips ❌

→ CORRIGER avant continuer étapes 3.x
```

**2. Timestamps DB critiques**
```
Événement 14:30 Bern = 12:30:00+02:00 dans DB
Référence Session 92.5 TOUJOURS
```

**3. Filtre clusters ≥3 occurrences**
```
2 occurrences = insuffisant statistiquement
≥3 = minimum acceptable
≥6 = excellent (Cluster #3)
```

---

## 📝 PROCHAINES SESSIONS

**Session 105 : Cluster #3 complet**
1. Corriger mesure impact 11.09 (56.8 pips)
2. Baseline Cluster #3 déjà établie : 2.5 ✅
3. Mesurer 5 autres dates Cluster #3
4. Calculer amp_optimal pour chaque date
5. Régression + validation

**Session 106 : Cluster #1 (Manufacturing)**
1. ÉTABLIR baseline Cluster #1 d'abord :
   - Choisir 1 date référence parmi les 11
   - Valider empiriquement son impact
   - Calculer amp_optimal → baseline_cluster1
2. Mesurer 10 autres dates
3. Delta vs baseline_cluster1 (PAS 2.5 !)
4. Régression + validation

**Session 107 : Cluster #2 (NFP)**
1. ÉTABLIR baseline Cluster #2 d'abord :
   - Choisir 1 date référence parmi les 7
   - Valider empiriquement son impact
   - Calculer amp_optimal → baseline_cluster2
2. Mesurer 6 autres dates
3. Delta vs baseline_cluster2 (PAS 2.5 !)
4. Régression + validation

**Session 108 : Synthèse & Production**
- Comparer formules de CHAQUE cluster
- Décision par cluster (formule dynamique ou baseline)
- Intégration Planificateur v2.7

---

*Méthodologie définie : 31 octobre 2025 - Session 104*  
*Application : Session 105+ sur Cluster #3 puis autres*
