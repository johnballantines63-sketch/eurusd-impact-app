# SESSION 111 - PLAN D'ACTION
**Objectif:** PRÉDICTION DYNAMIQUE VRAIE (pas pattern matching)
**Priorité:** CRITIQUE - L'âme du système
**Durée estimée:** 4-6 heures

---

## 🎯 OBJECTIF PRINCIPAL

**Transformer le système actuel qui REPRODUIT un pattern MT5...**
**...en un système qui PRÉDIT dynamiquement n'importe quel cas**

---

## 📋 ÉTAPES DÉTAILLÉES

### ÉTAPE 1: Module Calcul Impact Par Cluster (90 min)

**Créer:** `fx_impact_app/src/cluster_impact_calculator.py`

#### Fonction 1.1: `calculate_cluster_impact()`
```python
def calculate_cluster_impact(
    cluster_events: pd.DataFrame,
    amplification: float = 2.5
) -> dict:
    """
    Calcule impact d'un cluster isolé
    
    Utilise formules Session 51-55 sur événements du cluster uniquement
    
    Args:
        cluster_events: DataFrame événements du cluster
        amplification: Facteur amplification
    
    Returns:
        {
            'impact_pips': float,      # Impact prédit en pips
            'base_score': float,        # Score base moyen
            'adjusted_score': float,    # Score ajusté
            'max_surprise': float,      # Surprise max %
            'num_events': int,          # Nombre événements
            'cluster_weight': float     # Poids relatif (pour multi-clusters)
        }
    """
    # ALGORITHME:
    # 1. Calculer score base moyen cluster
    # 2. Calculer surprise max cluster
    # 3. Ajuster score (formule Session 55)
    # 4. Calculer impact (formule Session 51)
    # 5. Retourner résultats complets
```

**Tests validation:**
```python
# Test A: Cluster 1 seul (11 sept - CPI + Jobless)
# Expected: ~37-40 pips
cluster1_events = events[0:14]  # 14 events CPI
result = calculate_cluster_impact(cluster1_events)
assert 35 <= result['impact_pips'] <= 42

# Test B: Cluster 2 seul (11 sept - Current Account)
# Expected: ~15-20 pips (1 event, surprise forte)
cluster2_events = events[14:15]  # 1 event
result = calculate_cluster_impact(cluster2_events)
assert 12 <= result['impact_pips'] <= 22
```

#### Fonction 1.2: `calculate_cluster_ttr()`
```python
def calculate_cluster_ttr(
    cluster_impact: dict,
    cluster_latency_median: float
) -> float:
    """
    Calcule TTR adaptatif pour un cluster
    
    Basé sur formule Session 52 MAIS ajusté selon:
    - Impact magnitude
    - Latence médiane
    - Nombre événements
    
    Returns:
        ttr_minutes: float  # Time To Reversal en minutes
    """
    # OBSERVATIONS MT5:
    # - Petits clusters (1-3 events): TTR 3-5 min
    # - Moyens clusters (4-8 events): TTR 5-8 min
    # - Gros clusters (9+ events): TTR 8-12 min
    
    # ALGORITHME:
    # Base TTR = formule Session 52
    # Ajustement selon num_events et impact
```

**Tests validation:**
```python
# Cluster 1 (14 events, impact 37 pips): TTR ~5 min
# Cluster 2 (1 event, impact 15 pips): TTR ~3 min
```

#### Fonction 1.3: `calculate_pullback_characteristics()`
```python
def calculate_pullback_characteristics(
    peak_impact: float,
    peak_surprise: float,
    num_events: int
) -> dict:
    """
    Calcule caractéristiques pullback après peak
    
    Returns:
        {
            'pullback_pips': float,      # Amplitude pullback
            'pullback_duration': int,    # Durée en minutes
            'pullback_ratio': float      # % du peak
        }
    """
    # OBSERVATIONS MT5:
    # - Single cluster: pullback 20-30% du peak, durée 6-15 min
    # - Double cluster: pullback 60-80% du peak 1, durée jusqu'à cluster 2
    
    # ALGORITHME:
    # 1. Calculer pullback amplitude (formule Session 53)
    # 2. Estimer durée selon volatilité
    # 3. Calculer ratio pour validation
```

---

### ÉTAPE 2: Détection Pattern Cluster (45 min)

**Ajouter dans:** `cluster_impact_calculator.py`

#### Fonction 2.1: `analyze_cluster_pattern()`
```python
def analyze_cluster_pattern(
    clusters: list,
    clusters_impacts: list,
    temporal_tolerance: int = 5
) -> dict:
    """
    Analyse relation entre clusters
    
    Returns:
        {
            'pattern_type': str,  # "single", "sequential", "overlapping"
            'primary_cluster': int,  # Index cluster dominant
            'secondary_clusters': list,  # Indices autres clusters
            'expected_interactions': list  # Interactions prévues
        }
    """
    if len(clusters) == 1:
        return {'pattern_type': 'single'}
    
    # DÉTECTION OVERLAPPING:
    # Si délai entre clusters < durée pullback estimée
    # → Cluster 2 arrive PENDANT pullback cluster 1
    
    # DÉTECTION SEQUENTIAL:
    # Si délai entre clusters > durée pullback + récupération
    # → Clusters indépendants
    
    # DÉTECTION CUMULATIVE:
    # Si délai entre clusters < 5 min
    # → Impact combiné immédiat
```

**Tests:**
```python
# Cas A: 11 sept (CPI 14:30 + Current 14:45)
# Délai: 15 min
# Pullback estimé cluster 1: 10-15 min
# → Pattern: OVERLAPPING

# Cas B: CPI 14:30 + NFP 16:00
# Délai: 90 min
# → Pattern: SEQUENTIAL
```

---

### ÉTAPE 3: Timeline Vraiment Dynamique (90 min)

**Modifier:** `create_dynamic_timeline_chart()` dans Planificateur V27

#### Logique Nouvelle

**Pour chaque cluster:**
1. Calculer impact propre (fonction 1.1)
2. Calculer TTR propre (fonction 1.2)
3. Calculer pullback si dernier peak (fonction 1.3)

**Selon pattern détecté:**

**Pattern SINGLE:**
```python
t_peak = t_cluster + ttr_cluster
t_pullback_low = t_peak + pullback_duration
t_stabilization = t_pullback_low + 25
```

**Pattern OVERLAPPING (comme 11 sept):**
```python
# Cluster 1
t_peak1 = t_cluster1 + ttr_cluster1
t_pullback_start = t_peak1

# Cluster 2 arrive PENDANT pullback
# Pullback continue jusqu'à creux (X min après cluster 2)
delay_after_cluster2 = function(impact_cluster2, volatility)
t_pullback_low = t_cluster2 + delay_after_cluster2

# Reprise basée sur impact cluster 2
recovery_duration = function(impact_cluster2)
t_peak2 = t_pullback_low + recovery_duration
```

**Pattern SEQUENTIAL:**
```python
# Cluster 1 complet
t_peak1 = t_cluster1 + ttr_cluster1
t_pullback1 = t_peak1 + pullback1_duration
t_stabilization1 = t_pullback1 + 25

# Cluster 2 séparé (commence après stabilisation)
t_peak2 = t_cluster2 + ttr_cluster2
t_pullback2 = t_peak2 + pullback2_duration
t_stabilization2 = t_pullback2 + 25
```

---

### ÉTAPE 4: Validation Multi-Dates (60 min)

**Dates à tester:**

#### Test Set 1: Single Cluster
- **11 sept 2025 (CPI seul)** - Référence validée
- **Date CPI autre mois** - Vérifier généralisation
- **Date NFP seul** - Pattern similaire attendu

**Critères success:**
- MAE impact < 5 pips
- MAE TTR < 2 min
- Pattern détecté: "single"

#### Test Set 2: Double Cluster Overlapping
- **11 sept 2025 (CPI + Current Account)** - Référence
- **Autre date avec 2 clusters rapprochés**

**Critères success:**
- MAE impact total < 8 pips
- MAE peak 1 < 5 pips
- MAE peak 2 < 8 pips
- Pattern détecté: "overlapping"
- Timing creux ± 5 min

#### Test Set 3: Sequential
- **Date avec CPI + événement 60+ min après**

**Critères success:**
- 2 peaks distincts détectés
- Pattern détecté: "sequential"
- Impacts calculés séparément

---

## 🧪 PROTOCOLE VALIDATION

### Phase 1: Validation Unitaire
Chaque fonction testée isolément avec cas connus

### Phase 2: Validation Intégrée
Pipeline complet sur 11 sept référence

### Phase 3: Validation Multi-Dates
Tests sur 5+ dates variées

### Phase 4: Validation Production
Test avec sélection utilisateur réelle

---

## 📊 MÉTRIQUES SUCCESS SESSION 111

**Fonctions créées:**
- [ ] `calculate_cluster_impact()` - testé ✅
- [ ] `calculate_cluster_ttr()` - testé ✅
- [ ] `calculate_pullback_characteristics()` - testé ✅
- [ ] `analyze_cluster_pattern()` - testé ✅

**Timeline dynamique:**
- [ ] Utilise impacts calculés (pas ratios)
- [ ] Utilise timings calculés (pas fixes)
- [ ] Adaptatif selon pattern détecté

**Validation:**
- [ ] 11 sept CPI seul: MAE < 5 pips ✅
- [ ] 11 sept CPI + Current: MAE < 8 pips ✅
- [ ] 3 autres dates testées: MAE < 10 pips ✅
- [ ] Pattern détection: 100% correct ✅

---

## 🚨 POINTS CRITIQUES

### 1. Formules Empiriques
**Créer fonctions pour:**
- Durée pullback selon volatilité
- Délai creux après cluster 2 en overlapping
- Durée reprise selon impact cluster 2

**Méthode:** Analyser 10+ dates avec prix Dukascopy (DuckDB) pour trouver patterns

### 2. Interaction Clusters
**Comprendre comment cluster 2 affecte pullback cluster 1:**
- Le stoppe immédiatement ? Non (MT5 montré)
- Le prolonge ? Combien ?
- Fonction de quoi ? (Impact relatif ? Surprise ?)

### 3. Validation Continue
**Chaque formule doit être validée sur plusieurs dates**
**Pas d'assumption non testée !**

---

## 📁 STRUCTURE FICHIERS SESSION 111

```
fx_impact_app/src/
  └── cluster_impact_calculator.py  (NOUVEAU)
      ├── calculate_cluster_impact()
      ├── calculate_cluster_ttr()
      ├── calculate_pullback_characteristics()
      └── analyze_cluster_pattern()

streamlit_app/pages/
  └── 6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py  (MODIFIÉ)
      └── create_dynamic_timeline_chart()  (REFACTORÉ)

eurusd_clean/docs/
  ├── SESSION_111_RAPPORT.md  (À CRÉER en fin session)
  └── VALIDATION_MULTI_DATES.md  (À CRÉER)
```

---

## ⏱️ TIMELINE SESSION 111

**0:00-0:30** - Setup + lecture documentation
**0:30-2:00** - Étape 1 (Module cluster impact)
**2:00-2:45** - Étape 2 (Détection pattern)
**2:45-4:15** - Étape 3 (Timeline dynamique)
**4:15-5:15** - Étape 4 (Validation multi-dates)
**5:15-6:00** - Documentation + rapport final

**Total: 6 heures** (peut être fait en 2 sessions de 3h)

---

## 💬 MESSAGE POUR SESSION 111

**Objectif clair:** Prédiction vraie, pas reproduction pattern

**Méthode:** Formules empiriques + validation multi-dates

**Critère success:** Fonctionne sur N'IMPORTE quelle date, pas juste 11 sept

**Citation André (Session 110):**
> "la bonne prédiction est essentielle et c'est l'âme même de ce programme !!!"

**→ C'est EXACTEMENT ce qu'on va faire Session 111** 🎯

---

**Fin Plan Session 111**
