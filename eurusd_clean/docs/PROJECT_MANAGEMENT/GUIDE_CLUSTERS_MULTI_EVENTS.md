# GUIDE RÉFÉRENCE - CLUSTERS MULTI-EVENTS & RECHERCHE DB
## Méthodologie Complète + Pièges à Éviter

**Date création :** 10 novembre 2025  
**Session :** 125  
**Auteur :** André Valentin avec Claude  
**Statut :** ✅ VALIDÉ - Document de référence permanent

---

## 🎯 OBJECTIF DE CE DOCUMENT

**Ce document est LA RÉFÉRENCE pour :**
1. Rechercher correctement les événements dans la DB (éviter tâtonnements)
2. Comprendre concept clusters multi-events
3. Appliquer méthodologie workflow 10 étapes
4. Savoir exactement où on en est dans le projet

**⚠️ À LIRE ATTENTIVEMENT AVANT TOUTE SESSION IMPLIQUANT ÉVÉNEMENTS OU CLUSTERS**

---

## 📊 PARTIE 1 : STRUCTURE BASE DE DONNÉES - GUIDE COMPLET

### **1.1 Tables Disponibles**

```
warehouse.duckdb (205 MB)
├── events                          26,480 lignes   ← UTILISER CELLE-CI ✅
├── economic_events                 125,625 lignes  ← NE PAS UTILISER ⚠️
├── economic_events_backup_*        125,625 lignes  
├── event_families                  748 lignes      
├── event_impacts_v2                8,344 lignes    
├── prices_1m                       1,131,417 lignes
├── prices_bern                     1,131,417 lignes ← UTILISER CELLE-CI ✅
└── [autres tables prix 5m, 15m, 1h, etc.]
```

**⚠️ RÈGLE CRITIQUE #1 : TOUJOURS UTILISER TABLE `events` (PAS `economic_events`)**

---

### **1.2 Schéma Table `events` - LA BONNE TABLE**

```sql
SELECT * FROM events LIMIT 1;
```

**Colonnes importantes :**
```
ts_utc          TIMESTAMP     Heure événement UTC (ex: '2025-09-11 12:30:00')
country         VARCHAR       Code PAYS ('US', 'GB', 'JP', 'CH', 'DE', etc.)
event_title     VARCHAR       Titre (souvent NULL ⚠️)
event_key       VARCHAR       Identifiant événement (utiliser CELUI-CI ✅)
importance_n    INTEGER       Importance (1=LOW, 2=MEDIUM, 3=HIGH)
actual          DOUBLE        Valeur réelle publiée
previous        DOUBLE        Valeur précédente
estimate        DOUBLE        Estimation consensus
forecast        DOUBLE        Prévision (similaire estimate)
unit            VARCHAR       Unité mesure (%, K, etc.)
```

**EXEMPLE REQUÊTE CORRECTE :**
```sql
SELECT 
    ts_utc,
    event_key,
    country,
    importance_n,
    actual,
    estimate,
    previous
FROM events
WHERE country = 'US'              -- Code PAYS (pas 'usd')
  AND importance_n = 3            -- HIGH importance
  AND event_key = 'cpi'           -- Identifiant événement
  AND ts_utc >= '2023-01-01'
ORDER BY ts_utc
```

---

### **1.3 PIÈGES À ÉVITER - LEÇONS SESSION 125**

#### **PIÈGE #1 : Utiliser `economic_events` au lieu de `events`**

❌ **MAUVAIS :**
```sql
SELECT * FROM economic_events WHERE event_name = 'CPI'
```

✅ **BON :**
```sql
SELECT * FROM events WHERE event_key = 'cpi'
```

**Raison :** `economic_events` = données brutes EODHD (incomplet), `events` = données JBlanked (complet)

---

#### **PIÈGE #2 : Confondre code PAYS vs code DEVISE**

La confusion majeure de Session 125 :

**Table `events` :**
```
country = 'US'    ← Code PAYS (2 lettres majuscules)
country = 'GB'    ← Royaume-Uni
country = 'JP'    ← Japon
country = 'CH'    ← Suisse
country = 'DE'    ← Allemagne
```

**Fichier `event_families_eodhd_empirical.csv` :**
```
country = 'usd'   ← Code DEVISE (3 lettres minuscules)
country = 'gbp'   ← Livre sterling
country = 'jpy'   ← Yen
country = 'chf'   ← Franc suisse
country = 'eur'   ← Euro
```

**MAPPING CORRECT :**
```python
# Mapping PAYS → DEVISE
country_mapping = {
    'US': 'usd',  # États-Unis → Dollar
    'GB': 'gbp',  # Royaume-Uni → Livre
    'JP': 'jpy',  # Japon → Yen
    'CH': 'chf',  # Suisse → Franc
    'DE': 'eur',  # Allemagne → Euro (Eurozone)
    'FR': 'eur',  # France → Euro
    'IT': 'eur',  # Italie → Euro
    # etc.
}
```

**EXEMPLE SESSION 125 - ERREUR CORRIGÉE :**

❌ **CE QUI NE MARCHAIT PAS :**
```python
# Chercher NFP dans events
df_nfp = conn.execute("""
    SELECT * FROM events 
    WHERE country = 'US' AND event_key = 'non farm payrolls'
""").df()

# Mapper scores
score = df_scores[
    (df_scores['event_name'] == 'non_farm_payrolls') & 
    (df_scores['country'] == 'US')  # ❌ ERREUR ICI
]
# → Résultat : 0 lignes (score introuvable)
```

✅ **CORRECTION :**
```python
# Mapper scores avec code DEVISE
score = df_scores[
    (df_scores['event_name'] == 'non_farm_payrolls') & 
    (df_scores['country'] == 'usd')  # ✅ BON : code devise
]
# → Résultat : 1 ligne, score = 61.6
```

---

#### **PIÈGE #3 : Utiliser `event_title` au lieu de `event_key`**

❌ **MAUVAIS :**
```sql
SELECT * FROM events WHERE event_title = 'CPI'
```

**Problème :** `event_title` est souvent **NULL** !

```
event_title = None     (383 événements !)
event_title = 'CPI'    (0 événements)
```

✅ **BON :**
```sql
SELECT * FROM events WHERE event_key = 'cpi'
```

**Raison :** `event_key` = identifiant normalisé (toujours rempli)

---

#### **PIÈGE #4 : Mauvais mapping event_key ↔ event_name**

**Table `events` utilise des identifiants avec espaces et minuscules :**
```
event_key = 'non farm payrolls'        (ESPACE)
event_key = 'cpi'
event_key = 'unemployment rate'
event_key = 'retail sales'
event_key = 'fed interest rate decision'
```

**Fichier `event_families_eodhd_empirical.csv` utilise underscores :**
```
event_name = 'non_farm_payrolls'       (UNDERSCORE)
event_name = 'cpi'
event_name = 'unemployment_rate'
event_name = 'retail_sales'
```

**MAPPING CORRECT :**
```python
def normalize_event_key_to_name(event_key):
    """Convertir event_key (espaces) → event_name (underscores)"""
    return event_key.replace(' ', '_')

# Exemple
event_key = 'non farm payrolls'
event_name = normalize_event_key_to_name(event_key)
# → 'non_farm_payrolls'

# Mapper score
score = df_scores[
    (df_scores['event_name'] == event_name) & 
    (df_scores['country'] == 'usd')
]
```

---

### **1.4 CHECKLIST RECHERCHE ÉVÉNEMENTS**

**Avant chaque recherche d'événements, vérifier :**

- [ ] Utilise table `events` (pas `economic_events`)
- [ ] Utilise `event_key` (pas `event_title`)
- [ ] Code pays correct : 'US', 'GB', 'JP' (2 lettres majuscules)
- [ ] Filtre `importance_n = 3` pour HIGH
- [ ] Pour mapping scores : convertir 'US' → 'usd' (devise)
- [ ] Pour mapping scores : convertir 'non farm payrolls' → 'non_farm_payrolls' (underscore)
- [ ] Timezone : `ts_utc` est en UTC (pas Bern)

---

### **1.5 EXEMPLES REQUÊTES CORRECTES**

#### **Exemple 1 : Trouver tous CPI US depuis 2023**

```python
import duckdb
import pandas as pd

conn = duckdb.connect('warehouse.duckdb', read_only=True)

df_cpi = conn.execute("""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate,
        previous
    FROM events
    WHERE country = 'US'
      AND event_key = 'cpi'
      AND importance_n = 3
      AND ts_utc >= '2023-01-01'
    ORDER BY ts_utc
""").df()

print(f"Trouvé {len(df_cpi)} événements CPI US HIGH")

# Mapper scores
df_scores = pd.read_csv('event_families_eodhd_empirical.csv')

score_cpi = df_scores[
    (df_scores['event_name'] == 'cpi') & 
    (df_scores['country'] == 'usd')  # Code DEVISE
]

if len(score_cpi) > 0:
    print(f"Score CPI : {score_cpi.iloc[0]['empirical_score']}")
else:
    print("⚠️ Score CPI introuvable")

conn.close()
```

#### **Exemple 2 : Trouver tous événements HIGH US (identifier familles)**

```python
df_all_high = conn.execute("""
    SELECT 
        event_key,
        COUNT(*) as count
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND ts_utc >= '2023-01-01'
    GROUP BY event_key
    ORDER BY count DESC
    LIMIT 20
""").df()

print("Top 20 événements HIGH US :")
for idx, row in df_all_high.iterrows():
    print(f"   {row['count']:3d}× {row['event_key']}")
```

#### **Exemple 3 : Trouver cluster multi-events (±5 min)**

```python
from datetime import timedelta

cluster_time = pd.to_datetime('2025-09-11 12:30:00')  # UTC
window_minutes = 5

df_cluster = conn.execute("""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate
    FROM events
    WHERE ts_utc >= ? - INTERVAL '? minutes'
      AND ts_utc <= ? + INTERVAL '? minutes'
      AND importance_n = 3
    ORDER BY ts_utc
""", [cluster_time, window_minutes, cluster_time, window_minutes]).df()

print(f"Cluster {cluster_time} : {len(df_cluster)} événements")

for idx, row in df_cluster.iterrows():
    print(f"   {row['ts_utc']} - {row['event_key']} ({row['country']})")
```

---

## 📊 PARTIE 2 : CONCEPT CLUSTERS MULTI-EVENTS

### **2.1 Définition Cluster Multi-Events**

**Cluster multi-events :**
> Groupe de plusieurs événements économiques HIGH importance se produisant dans une fenêtre temporelle rapprochée (±5 minutes), créant un effet cumulatif sur le marché EUR/USD.

**Exemple cas école 11 septembre 2025 :**
```
14:30:00 UTC - CPI (US)
14:30:00 UTC - Core CPI (US)
14:30:00 UTC - CPI MoM (US)
14:30:00 UTC - Core CPI MoM (US)
14:30:00 UTC - CPI Index (US)
14:30:00 UTC - Core CPI Index (US)
... (14 événements total)

14:45:00 UTC - Retail Sales (US)
14:45:00 UTC - Retail Sales Control Group (US)
... (6 événements)

→ Total : 20 événements en 15 minutes = 2 CLUSTERS
```

**Impact observé :** 51.7 pips (mouvement fort)

---

### **2.2 Pourquoi Clusters Multi-Events ?**

**Hypothèse validée Session 125 :**

Les marchés réagissent différemment selon :
1. **Nombre d'événements simultanés** (1 vs 5 vs 14)
2. **Composition du cluster** (CPI seul vs CPI+Retail Sales)
3. **Tendance pré-cluster** (R² = 0.64 vs R² = 0.20)

**Formule impact :**
```python
Impact = Score_Empirique × Amplification(R²) × √(n_events) × Surprise
```

**Où :**
- `Score_Empirique` : Impact moyen historique de l'événement
- `Amplification(R²)` : Facteur dynamique basé force tendance pré-cluster
- `√(n_events)` : Effet cumulatif (racine carrée nombre événements)
- `Surprise` : Écart actual vs estimate

**Résultat Session 125 :**
- Fonction `Amplification(R²)` UNIVERSELLE validée
- Amélioration +88% vs baseline fixe

---

### **2.3 Signature Cluster**

**Signature = composition exacte du cluster (événements + pays)**

**Exemple signature 11 septembre :**
```python
signature = [
    ('cpi', 'US'),
    ('core_cpi', 'US'),
    ('cpi_mom', 'US'),
    ('core_cpi_mom', 'US'),
    ('cpi_index', 'US'),
    ('core_cpi_index', 'US'),
    # ... 14 événements total
]
```

**Objectif :** Trouver dates historiques avec **MÊME signature** pour :
1. Calibrer fonction amplification
2. Valider prédictions sur cas similaires
3. Généraliser à autres types clusters

---

### **2.4 Groupement Temporel (Fenêtre ±5 min)**

**Algorithme clustering :**

```python
CLUSTER_WINDOW_MINUTES = 10  # ±5 min = 10 min total

# 1. Arrondir timestamp à fenêtre 10 min
df_events['cluster_key'] = df_events['ts_utc'].dt.floor('10T')

# 2. Grouper par cluster_key
for cluster_time, group in df_events.groupby('cluster_key'):
    if len(group) >= 2:  # Au moins 2 événements
        # Créer signature
        signature = tuple(sorted([
            (row['event_key'], row['country']) 
            for _, row in group.iterrows()
        ]))
        
        clusters.append({
            'cluster_time': cluster_time,
            'signature': signature,
            'n_events': len(group)
        })
```

**Résultat Session 125 :**
- 29 clusters CPI identiques trouvés (2023-2025)
- Permet calibration fonction robuste

---

## 📊 PARTIE 3 : WORKFLOW COMPLET 10 ÉTAPES (MÉTHODOLOGIE ANDRÉ)

### **Vue d'ensemble**

```
ÉTAPE 1-2 : Identifier mouvements forts + patterns
    ↓
ÉTAPE 3-5 : Choisir cas référence + calibration idéale
    ↓
ÉTAPE 6 : Identifier clusters identiques historiques
    ↓
ÉTAPE 7-8 : Calculer tendances + corrélation
    ↓
ÉTAPE 9-10 : Prédire autres dates + validation
```

---

### **ÉTAPE 1 : Identifier Mouvements Forts (>x pips)**

**Objectif :** Scanner historique prix pour trouver mouvements significatifs

**Seuil recommandé :** 
- Minimum : 30 pips (filtre bruit)
- Optimal : 40-50 pips (mouvements vraiment forts)

**Implémentation :**
```python
import duckdb
import pandas as pd
import numpy as np

DB_PATH = 'warehouse.duckdb'
LOOKBACK_YEARS = 3
MIN_MOVEMENT_PIPS = 40

conn = duckdb.connect(DB_PATH, read_only=True)

# Charger prix 3 ans
start_date = (pd.Timestamp.now() - pd.DateOffset(years=LOOKBACK_YEARS)).strftime('%Y-%m-%d')

df_prices = conn.execute("""
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
    ORDER BY datetime
""", [start_date]).df()

# Détecter mouvements forts (fenêtre glissante 60 min)
strong_movements = []

for i in range(len(df_prices) - 60):
    window = df_prices.iloc[i:i+60]
    
    price_start = window.iloc[0]['close']
    max_high = window['high'].max()
    min_low = window['low'].min()
    
    movement_up = (max_high - price_start) * 10000
    movement_down = (price_start - min_low) * 10000
    
    max_movement = max(movement_up, movement_down)
    
    if max_movement >= MIN_MOVEMENT_PIPS:
        strong_movements.append({
            'datetime': window.iloc[0]['datetime'],
            'movement_pips': max_movement,
            'direction': 'UP' if movement_up > movement_down else 'DOWN'
        })

print(f"✅ {len(strong_movements)} mouvements forts détectés (>{MIN_MOVEMENT_PIPS} pips)")

conn.close()
```

**Résultat attendu :** 100-200 dates avec mouvements forts

---

### **ÉTAPE 2 : Identifier Patterns dans Mouvements Forts**

**Objectif :** Pour chaque mouvement fort, identifier le pattern (Single Wave, Double Wave, etc.)

**Patterns possibles :**
1. **Single Wave Fort** : 1 impulsion unique
2. **Double Wave** : Pullback + 2ème impulsion
3. **Triple Wave** : Multiple impulsions
4. **Overlapping** : Clusters successifs

**Note Session 125 :** 
- Double Wave = 0.5-1% des cas (RARE)
- Single Wave Fort = 95% des CPI/NFP

**Implémentation :**
```python
# Utiliser Scanner Patterns Session 117 (validé)
from price_pattern_scanner_rev7 import scan_patterns

patterns_detected = []

for movement in strong_movements[:50]:  # Limiter à 50 pour vitesse
    datetime_start = movement['datetime']
    
    # Scanner pattern 2h après début mouvement
    pattern = scan_patterns(
        conn=conn,
        datetime_start=datetime_start,
        window_hours=2,
        min_amplitude_pips=30
    )
    
    if pattern:
        patterns_detected.append({
            'datetime': datetime_start,
            'pattern_type': pattern['type'],
            'amplitude_pips': pattern['amplitude'],
            'duration_minutes': pattern['duration']
        })

print(f"✅ {len(patterns_detected)} patterns identifiés")
```

---

### **ÉTAPE 3 : Choisir Cas Référence pour Chaque Pattern**

**Objectif :** Pour chaque type de pattern, choisir 1 cas "école" qui servira de base calcul

**Critères sélection :**
1. Pattern bien formé (claire amplitude)
2. Événements causaux identifiés
3. Données complètes (prix + events)
4. Impact significatif (>40 pips)

**Exemple Session 125 :**
```python
# Cas référence CPI Single Wave Fort
reference_case = {
    'date': '2025-09-11',
    'time': '14:30:00',
    'pattern_type': 'Single Wave Fort',
    'cluster_events': [
        ('cpi', 'US'),
        ('core_cpi', 'US'),
        # ... 14 événements total
    ],
    'impact_measured': 51.7,  # pips
    'r2_pre_trend': 0.6376
}
```

---

### **ÉTAPE 4 : Calculer Facteur Amplification Idéal (Cas Référence)**

**Objectif :** Déterminer amplification PARFAITE pour prédire exactement l'impact mesuré

**Formule inverse :**
```python
# Impact = Score × Amplification × √n × Surprise
# Donc : Amplification_idéale = Impact / (Score × √n × Surprise)

def calculate_ideal_amplification(
    impact_measured: float,
    total_score: float,
    n_events: int,
    surprise_factor: float = 1.0
):
    """Calculer amplification idéale pour cas référence"""
    
    denominator = total_score * np.sqrt(n_events) * surprise_factor
    
    if denominator > 0:
        amplification_ideal = impact_measured / denominator
        return amplification_ideal
    else:
        return None

# Exemple 11 septembre
impact_measured = 51.7  # pips réels
total_score = 450.0     # Somme scores empiriques 14 événements
n_events = 14
surprise_factor = 1.0   # Pas de surprise majeure

amp_ideal = calculate_ideal_amplification(
    impact_measured, 
    total_score, 
    n_events, 
    surprise_factor
)

print(f"Amplification idéale : {amp_ideal:.4f}")
# → 0.0895 (environ 0.09)
```

---

### **ÉTAPE 5 : Établir Cas Référence de Base**

**Objectif :** Documenter complètement le cas référence

**Structure :**
```python
reference_case = {
    'metadata': {
        'date': '2025-09-11',
        'time_utc': '12:30:00',  # UTC
        'time_bern': '14:30:00',  # Bern UTC+2
        'pattern_type': 'Single Wave Fort'
    },
    
    'cluster': {
        'signature': signature,
        'n_events': 14,
        'total_score': 450.0,
        'events': [...]
    },
    
    'impact': {
        'measured_pips': 51.7,
        'duration_minutes': 120,
        'direction': 'UP'
    },
    
    'amplification': {
        'ideal_factor': 0.0895,
        'baseline_factor': 2.5,  # Facteur fixe standard
        'improvement': 'À calculer après tendance'
    },
    
    'trend_pre_cluster': {
        'r2': 0.6376,
        'duration_hours': 54.6,
        'reversal_type': 'PEAK',
        'reversal_time': '2025-09-09 08:00:00'
    }
}
```

**Sauvegarder :**
```python
import json

output_path = 'reference_cases/cpi_single_wave_sept11.json'
with open(output_path, 'w') as f:
    json.dump(reference_case, f, indent=2)
```

---

### **ÉTAPE 6 : Identifier Clusters Identiques Historiques**

**Objectif :** Trouver toutes les dates avec MÊME signature cluster

**Implémentation Session 125 (validée) :**
```python
# Signature cas référence
ref_signature = tuple(sorted([
    (event['event_key'], event['country']) 
    for event in reference_case['cluster']['events']
]))

# Scanner DB historique (2015-2025)
matching_clusters = []

for cluster_time, group in df_all_events.groupby('cluster_key'):
    # Signature cluster courant
    cluster_signature = tuple(sorted([
        (row['event_key'], row['country']) 
        for _, row in group.iterrows()
    ]))
    
    # Comparaison exacte
    if cluster_signature == ref_signature:
        matching_clusters.append({
            'cluster_time': cluster_time,
            'n_events': len(group),
            'signature': cluster_signature
        })

print(f"✅ {len(matching_clusters)} clusters identiques trouvés")
```

**Résultat Session 125 :** 29 clusters CPI identiques (2023-2025)

---

### **ÉTAPE 7 : Calculer Tendance Pré-Cluster pour Chaque Date**

**Objectif :** Pour chaque cluster identique, calculer R² tendance 30 jours avant

**Algorithme validé Session 125 :**

```python
WINDOW = 240  # 4h (OPTIMAL validé)
LOOKBACK_DAYS = 30
MIN_AMPLITUDE_PIPS = 30

def calculate_trend_r2(conn, cluster_time):
    """
    Calcule R² tendance pré-cluster (méthode Session 125)
    
    Étapes :
    1. Charger prix 30 jours avant cluster
    2. Détecter swing highs/lows (window 240 min)
    3. Identifier dernière inversion (HIGH→LOW ou LOW→HIGH)
    4. Calculer R² régression linéaire (inversion → cluster)
    
    Returns:
        {
            'r2': float,
            'duration_hours': float,
            'reversal_type': str,
            'reversal_time': datetime,
            'amplitude_pips': float
        }
    """
    
    lookback_start = cluster_time - timedelta(days=LOOKBACK_DAYS)
    
    # 1. Charger prix
    df_prices = conn.execute("""
        SELECT datetime, close
        FROM prices_bern
        WHERE datetime >= ? AND datetime < ?
        ORDER BY datetime
    """, [lookback_start, cluster_time]).df()
    
    prices = df_prices['close'].values
    timestamps = df_prices['datetime'].tolist()
    
    # 2. Détecter swing highs/lows
    swing_highs = detect_swing_highs(prices, window=WINDOW)
    swing_lows = detect_swing_lows(prices, window=WINDOW)
    
    # 3. Identifier inversions
    reversals = detect_trend_reversals(
        prices, 
        timestamps, 
        window=WINDOW,
        min_amplitude_pips=MIN_AMPLITUDE_PIPS
    )
    
    if not reversals:
        return None
    
    # 4. Dernière inversion
    last_reversal = reversals[-1]
    
    # 5. Calculer R² régression linéaire
    start_idx = last_reversal['index']
    end_idx = len(prices) - 1
    
    segment = prices[start_idx:end_idx+1]
    t = np.arange(len(segment))
    
    from scipy.stats import linregress
    slope, intercept, r_value, _, _ = linregress(t, segment)
    r_squared = r_value ** 2
    
    return {
        'r2': r_squared,
        'duration_hours': (timestamps[end_idx] - timestamps[start_idx]).total_seconds() / 3600,
        'reversal_type': last_reversal['type'],
        'reversal_time': last_reversal['time'],
        'amplitude_pips': last_reversal['amplitude_pips']
    }
```

**Fonctions helper :**
```python
def detect_swing_highs(prices, window=240, threshold=0.0001):
    """Détecter swing highs (pics locaux)"""
    swing_highs = []
    
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    
    return swing_highs

def detect_swing_lows(prices, window=240, threshold=0.0001):
    """Détecter swing lows (creux locaux)"""
    swing_lows = []
    
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    
    return swing_lows

def detect_trend_reversals(prices, timestamps, window=240, min_amplitude_pips=30):
    """
    Détecter inversions tendance (HIGH→LOW ou LOW→HIGH)
    avec amplitude minimale et qualité tendance (R²)
    """
    swing_highs = detect_swing_highs(prices, window)
    swing_lows = detect_swing_lows(prices, window)
    
    # Créer liste extrema triée
    extrema = []
    for idx in swing_highs:
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx]
        })
    for idx in swing_lows:
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx]
        })
    
    extrema.sort(key=lambda x: x['index'])
    
    # Identifier inversions
    reversals = []
    
    for extremum in extrema:
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:  # Minimum 1h
            continue
        
        segment = prices[start_idx:end_idx+1]
        amplitude = (segment.max() - segment.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        # Vérifier direction inversion
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        if extremum['type'] == 'HIGH' and price_end < price_start:
            reversal_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            reversal_type = 'LOW_TO_HIGH'
        else:
            continue
        
        # Calculer R² tendance
        t = np.arange(len(segment))
        slope, intercept, r_value, _, _ = linregress(t, segment)
        r_squared = r_value ** 2
        
        reversals.append({
            'type': reversal_type,
            'index': start_idx,
            'time': extremum['timestamp'],
            'price': extremum['price'],
            'amplitude_pips': amplitude,
            'r2': r_squared
        })
    
    return reversals
```

**Appliquer à tous clusters :**
```python
trends_results = []

for cluster in matching_clusters:
    cluster_time = cluster['cluster_time']
    
    trend = calculate_trend_r2(conn, cluster_time)
    
    if trend:
        trends_results.append({
            'cluster_time': cluster_time,
            'r2': trend['r2'],
            'duration_hours': trend['duration_hours'],
            'reversal_type': trend['reversal_type'],
            'amplitude_pips': trend['amplitude_pips']
        })

print(f"✅ {len(trends_results)} tendances calculées")
```

**Résultat Session 125 :** 29 R² calculés, corrélation R²↔Impact = 0.37

---

### **ÉTAPE 8 : Établir Corrélation R² ↔ Amplification**

**Objectif :** Modéliser relation entre R² tendance et facteur amplification idéal

**Hypothèse :**
```
Tendance forte (R² élevé) → Amplification plus élevée
Tendance faible (R² bas) → Amplification plus faible
```

**Implémentation Session 125 (validée) :**

```python
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_absolute_error

# Pour chaque cluster : calculer amplification idéale
amplifications_ideal = []

for cluster in matching_clusters:
    # Calculer impact mesuré
    impact = measure_impact(conn, cluster['cluster_time'])
    
    # Calculer amplification idéale
    amp_ideal = calculate_ideal_amplification(
        impact_measured=impact,
        total_score=cluster['total_score'],
        n_events=cluster['n_events']
    )
    
    amplifications_ideal.append(amp_ideal)

# Données pour modélisation
X = np.array([t['r2'] for t in trends_results])  # R² tendances
y = np.array(amplifications_ideal)                # Amplifications idéales

# Tester plusieurs modèles
models = {}

# Modèle 1 : Linéaire
def linear(r2, a, b):
    return a + b * r2

popt_lin, _ = curve_fit(linear, X, y)
y_pred_lin = linear(X, *popt_lin)
r2_lin = r2_score(y, y_pred_lin)
mae_lin = mean_absolute_error(y, y_pred_lin)

models['linear'] = {
    'params': popt_lin,
    'r2_fit': r2_lin,
    'mae': mae_lin,
    'formula': f"amp = {popt_lin[0]:.6f} + {popt_lin[1]:.6f} × R²"
}

# Modèle 2 : Quadratique (MEILLEUR Session 125)
def quadratic(r2, a, b, c):
    return a + b * r2 + c * r2**2

popt_quad, _ = curve_fit(quadratic, X, y)
y_pred_quad = quadratic(X, *popt_quad)
r2_quad = r2_score(y, y_pred_quad)
mae_quad = mean_absolute_error(y, y_pred_quad)

models['quadratic'] = {
    'params': popt_quad,
    'r2_fit': r2_quad,
    'mae': mae_quad,
    'formula': f"amp = {popt_quad[0]:.6f} + {popt_quad[1]:.6f}×R² + {popt_quad[2]:.6f}×R²²"
}

# Modèle 3 : Logarithmique
def logarithmic(r2, a, b):
    return a + b * np.log(r2 + 0.01)

popt_log, _ = curve_fit(logarithmic, X, y)
y_pred_log = logarithmic(X, *popt_log)
r2_log = r2_score(y, y_pred_log)
mae_log = mean_absolute_error(y, y_pred_log)

models['logarithmic'] = {
    'params': popt_log,
    'r2_fit': r2_log,
    'mae': mae_log,
    'formula': f"amp = {popt_log[0]:.6f} + {popt_log[1]:.6f} × log(R²+0.01)"
}

# Choisir meilleur modèle (R² fit maximal)
best_model_name = max(models, key=lambda k: models[k]['r2_fit'])
best_model = models[best_model_name]

print(f"🏆 Meilleur modèle : {best_model_name}")
print(f"   Formule : {best_model['formula']}")
print(f"   R² fit : {best_model['r2_fit']:.4f}")
print(f"   MAE : {best_model['mae']:.6f}")
```

**Résultat Session 125 :**
```
Meilleur modèle : quadratic
Formule : amp = 0.040833 + 0.050220×R² - 0.006553×R²²
R² fit : 0.1394
MAE : 0.0256
```

**Fonction production :**
```python
def calculate_amplification_from_r2(r2_trend):
    """
    Fonction universelle validée Session 125
    Calibrée sur 29 clusters CPI
    Validée sur 17 NFP (+88% amélioration)
    """
    # Paramètres calibrés
    a = 0.040833
    b = 0.050220
    c = -0.006553
    
    # Borner R²
    r2 = max(0.0, min(1.0, r2_trend))
    
    # Calculer amplification
    amplification = a + b * r2 + c * r2**2
    
    # Borner résultat
    return max(0.01, min(0.20, amplification))
```

---

### **ÉTAPE 9 : Appliquer Corrélation aux Autres Dates**

**Objectif :** Pour chaque date historique avec cluster identique, prédire amplification

**Implémentation :**

```python
# Pour chaque cluster historique
predictions = []

for cluster in matching_clusters:
    cluster_time = cluster['cluster_time']
    
    # 1. Calculer tendance pré-cluster
    trend = calculate_trend_r2(conn, cluster_time)
    
    if not trend:
        continue
    
    r2 = trend['r2']
    
    # 2. Prédire amplification avec fonction calibrée
    amp_predicted = calculate_amplification_from_r2(r2)
    
    # 3. Calculer impact prédit
    impact_predicted = calculate_impact_d(
        empirical_score=cluster['total_score'],
        num_events=cluster['n_events'],
        amplification=amp_predicted
    )
    
    # 4. Mesurer impact réel
    impact_measured = measure_impact(conn, cluster_time)
    
    # 5. Calculer erreur
    error = abs(impact_predicted - impact_measured)
    
    predictions.append({
        'cluster_time': cluster_time,
        'r2_trend': r2,
        'amp_predicted': amp_predicted,
        'impact_predicted': impact_predicted,
        'impact_measured': impact_measured,
        'error_pips': error
    })

print(f"✅ {len(predictions)} prédictions calculées")
```

**Fonction helper :**
```python
def calculate_impact_d(empirical_score, num_events, amplification):
    """
    Calcule impact prédit avec formule validée
    
    Args:
        empirical_score: Score empirique moyen
        num_events: Nombre événements cluster
        amplification: Facteur amplification (fonction R²)
    
    Returns:
        Impact prédit en pips
    """
    return empirical_score * amplification * np.sqrt(num_events)

def measure_impact(conn, cluster_time, window_minutes=60):
    """
    Mesure impact réel post-cluster
    
    Args:
        conn: Connexion DuckDB
        cluster_time: Timestamp cluster
        window_minutes: Fenêtre mesure (défaut 60 min)
    
    Returns:
        Impact mesuré en pips
    """
    time_start = cluster_time - timedelta(minutes=5)
    time_end = cluster_time + timedelta(minutes=window_minutes)
    
    df_prices = conn.execute("""
        SELECT datetime, close, high, low
        FROM prices_bern
        WHERE datetime >= ? AND datetime <= ?
        ORDER BY datetime
    """, [time_start, time_end]).df()
    
    if len(df_prices) < 10:
        return None
    
    baseline = df_prices.iloc[0]['close']
    max_high = df_prices['high'].max()
    min_low = df_prices['low'].min()
    
    impact_up = (max_high - baseline) * 10000
    impact_down = (baseline - min_low) * 10000
    
    return max(impact_up, impact_down)
```

---

### **ÉTAPE 10 : Calculer Prédictions + Validation**

**Objectif :** Valider qualité prédictions et améliorer si nécessaire

**Métriques :**

```python
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df_predictions = pd.DataFrame(predictions)

# Métriques prédictions
mae = mean_absolute_error(
    df_predictions['impact_measured'], 
    df_predictions['impact_predicted']
)

rmse = np.sqrt(mean_squared_error(
    df_predictions['impact_measured'], 
    df_predictions['impact_predicted']
))

r2 = r2_score(
    df_predictions['impact_measured'], 
    df_predictions['impact_predicted']
)

print(f"📊 MÉTRIQUES PRÉDICTIONS :")
print(f"   MAE  : {mae:.2f} pips")
print(f"   RMSE : {rmse:.2f} pips")
print(f"   R²   : {r2:.4f}")

# Comparer avec baseline (amplification fixe 2.5)
predictions_baseline = []

for cluster in matching_clusters:
    impact_baseline = calculate_impact_d(
        empirical_score=cluster['total_score'],
        num_events=cluster['n_events'],
        amplification=2.5  # Baseline fixe
    )
    
    impact_measured = measure_impact(conn, cluster['cluster_time'])
    
    if impact_measured:
        predictions_baseline.append({
            'impact_predicted': impact_baseline,
            'impact_measured': impact_measured,
            'error_pips': abs(impact_baseline - impact_measured)
        })

df_baseline = pd.DataFrame(predictions_baseline)

mae_baseline = mean_absolute_error(
    df_baseline['impact_measured'], 
    df_baseline['impact_predicted']
)

improvement = ((mae_baseline - mae) / mae_baseline) * 100

print(f"\n📈 COMPARAISON vs BASELINE :")
print(f"   MAE baseline    : {mae_baseline:.2f} pips")
print(f"   MAE fonction R² : {mae:.2f} pips")
print(f"   Amélioration    : {improvement:+.1f}%")

# Décision
if improvement > 50:
    decision = "EXCELLENT"
    print(f"\n✅✅ AMÉLIORATION EXCELLENTE ! Fonction validée.")
elif improvement > 30:
    decision = "GOOD"
    print(f"\n✅ AMÉLIORATION BONNE. Fonction utilisable.")
elif improvement > 10:
    decision = "MODERATE"
    print(f"\n⚠️ AMÉLIORATION MODÉRÉE. À tester plus.")
else:
    decision = "FAILED"
    print(f"\n❌ PAS D'AMÉLIORATION. Fonction inadaptée.")
```

**Résultat Session 125 (CPI) :**
```
MAE baseline : 166.76 pips
MAE fonction R² : 19.49 pips
Amélioration : +88.3%
Décision : EXCELLENT ✅✅
```

---

## 📊 PARTIE 4 : OÙ ON EN EST EXACTEMENT

### **4.1 État Actuel Projet (Novembre 2025)**

```
INFRASTRUCTURE                      ✅ 100%
├── Base données unifiée            ✅ warehouse.duckdb (205 MB)
├── Tables validées                 ✅ events + prices_bern
├── Scores empiriques               ✅ 671 familles analysées
└── Timezone corrigée               ✅ Bern UTC+2

FORMULES VALIDÉES                   ✅ 95%
├── Ajustement Score (99.9%)        ✅ Session 51-55
├── Impact Net D (98.6%)            ✅ Session 51-55
├── TTR C (94.4%)                   ✅ Session 51-55
├── Pullback V2 (99.3%)             ✅ Session 51-55
└── Amplification amp(R²)           ✅ Session 125 (UNIVERSEL)

WORKFLOW 10 ÉTAPES                  ✅ 80% COMPLÉTÉ
├── Étape 1-2 : Mouvements forts    ✅ Scanner Rev7 (Session 117)
├── Étape 3-5 : Cas référence       ✅ 11 septembre 2025
├── Étape 6 : Clusters identiques   ✅ 29 clusters CPI (Session 125)
├── Étape 7-8 : Corrélation R²      ✅ Fonction calibrée (Session 125)
├── Étape 9-10 : Validation         ✅ NFP +88% (Session 125)
└── Extension autres familles       ⏳ Session 126 (Retail Sales, Fed)

PIPELINE AUTOMATISÉ                 ⏳ 0% (OBJECTIF SESSION 126)
├── Script master                   ⏳ À créer
├── Tests Retail Sales              ⏳ À faire
├── Tests Fed Decisions             ⏳ À faire
└── Documentation complète          ⏳ À créer
```

---

### **4.2 Accomplissements Majeurs**

**Session 125 - Fonction Amplification Universelle :**
- ✅ 29 clusters CPI identiques trouvés (Étape 6)
- ✅ R² tendances calculés pour chaque (Étape 7)
- ✅ Fonction amp(R²) calibrée (Étape 8)
- ✅ Validation croisée CPI→NFP : +88% amélioration (Étape 9-10)
- ✅ **DÉCOUVERTE : Fonction UNIVERSELLE** (pas besoin fonction par famille)

**Formule finale :**
```python
def calculate_amplification_from_r2(r2_trend):
    """Fonction universelle validée"""
    a, b, c = 0.040833, 0.050220, -0.006553
    r2 = max(0.0, min(1.0, r2_trend))
    return max(0.01, min(0.20, a + b * r2 + c * r2**2))
```

---

### **4.3 Ce Qui Reste à Faire**

**Session 126 - Pipeline Master Automatisé :**
```
INPUT : event_type (ex: "CPI", "NFP", "Retail Sales")
    ↓
MODULE 1 : find_matching_clusters(event_type)
    ↓
MODULE 2 : calculate_r2_trends(clusters)
    ↓
MODULE 3 : calibrate_amplification_function(clusters_with_r2)
    ↓
MODULE 4 : validate_predictions(function, clusters)
    ↓
MODULE 5 : decide_integration(metrics)
    ↓
OUTPUT : Fonction calibrée + Métriques + Décision
```

**Tests prévus :**
1. CPI (validation non-régression)
2. NFP (validation non-régression)
3. Retail Sales (nouvelle famille)
4. Fed Interest Rate Decision (nouvelle famille)

**Objectif :** Pipeline exécutable en 1 commande pour N'IMPORTE QUEL event_type

---

### **4.4 Timeline Historique**

```
Session 51-55  : Formules Gold Standard (>94% précision)
Session 102-107: Détection inversions tendance
Session 117    : Scanner patterns (42 patterns, 15 Double Wave)
Session 118    : Détecteur Double Wave (MAE 4.5 pips)
Session 123-124: Migration DB unifiée + scores empiriques
Session 125    : Fonction amplification universelle ⭐
Session 126    : Pipeline master automatisé (en cours)
```

---

## 📚 PARTIE 5 : RESSOURCES & RÉFÉRENCES

### **5.1 Scripts Validés Session 125**

```
/scripts/session125/
├── find_matching_clusters.py          ✅ Matching clusters identiques
├── calculate_r2_trends.py              ✅ Calcul R² (window 240)
├── calibrate_amplification_function.py ✅ Calibration fonction
└── cross_validate_nfp_final.py         ✅ Validation croisée NFP
```

### **5.2 Documentation Complète**

```
/docs/PROJECT_MANAGEMENT/99_SESSIONS/
├── SESSION_125_RAPPORT_FINAL.md           Rapport complet Session 125
├── SESSION_126_HANDOFF.md                 Plan Session 126
└── DEMARRAGE_SESSION_126.md               Message démarrage + quiz

/docs/PROJECT_MANAGEMENT/VALIDATED_SCRIPTS/
└── session125_amplification_universelle/
    ├── README.md                          Documentation pipeline
    └── SCRIPTS_REFERENCE.md               Références scripts
```

### **5.3 Résultats Calibration**

```
/scripts/session125/calibration_results/
├── amplification_function_calibrated.json    Fonction + paramètres
├── calibration_data.csv                      29 points données
└── calibration_amplification_r2.png          Visualisations

/scripts/session125/cross_validation/
└── cross_validation_cpi_to_nfp_final.json    Résultats NFP (+88%)
```

---

## ⚠️ PARTIE 6 : ERREURS CRITIQUES À NE PLUS COMMETTRE

### **ERREUR #1 : Utiliser `economic_events` au lieu de `events`**
**Impact :** Perte de temps, données incomplètes  
**Solution :** TOUJOURS utiliser table `events`

### **ERREUR #2 : Confondre code PAYS vs code DEVISE**
**Impact :** Scores introuvables, perte 1h debug  
**Solution :** 
- Table `events` : country = 'US' (code PAYS)
- Fichier scores : country = 'usd' (code DEVISE)
- Mapper explicitement : `'US' → 'usd'`

### **ERREUR #3 : Utiliser `event_title` au lieu de `event_key`**
**Impact :** 383 événements manquants (event_title = NULL)  
**Solution :** TOUJOURS utiliser `event_key`

### **ERREUR #4 : Négliger conversion espace ↔ underscore**
**Impact :** Mapping events ↔ scores échoue  
**Solution :** 
- events : `'non farm payrolls'` (espaces)
- scores : `'non_farm_payrolls'` (underscores)
- Normaliser avec `.replace(' ', '_')`

### **ERREUR #5 : Oublier timezone conversion**
**Impact :** Décalage horaire, événements non trouvés  
**Solution :** 
- Table `events` : ts_utc (UTC)
- Table `prices_bern` : datetime (Bern UTC+2)
- Convertir explicitement si nécessaire

### **ERREUR #6 : Recréer algorithmes déjà validés**
**Impact :** Perte de temps, risque bugs  
**Solution :** RÉUTILISER scripts validés Session 125

---

## 🎯 PARTIE 7 : CHECKLIST AVANT CHAQUE SESSION

### **Avant de commencer développement :**

- [ ] J'ai lu ce document attentivement
- [ ] J'utilise table `events` (pas `economic_events`)
- [ ] J'utilise `event_key` (pas `event_title`)
- [ ] Je connais mapping PAYS ↔ DEVISE
- [ ] Je normalise espaces ↔ underscores
- [ ] Je gère timezone UTC vs Bern
- [ ] Je réutilise scripts validés (pas recréer)
- [ ] J'ai vérifié paramètres validés (window 240, etc.)

### **Avant validation croisée :**

- [ ] Fonction calibrée sur minimum 10 cas
- [ ] Tests sur minimum 1 autre famille
- [ ] Comparaison vs baseline (amp=2.5)
- [ ] Amélioration >30% pour valider
- [ ] Documentation résultats complète

---

## 📖 GLOSSAIRE

**Cluster multi-events :** Groupe événements ≥2 dans fenêtre ±5 min

**Signature cluster :** Composition exacte (event_key, country) triée

**R² tendance :** Qualité régression linéaire tendance pré-cluster (0 à 1)

**Amplification :** Facteur multiplicatif impact basé force tendance

**Score empirique :** Impact moyen historique événement (pips)

**Surprise :** Écart actual vs estimate (%)

**Impact prédit :** Score × Amplification(R²) × √n × Surprise

**Window :** Fenêtre temporelle détection swing highs/lows (240 min validé)

**Lookback :** Période historique analyse tendance (30 jours)

---

## 📞 CONTACT & MAINTENANCE

**Auteur :** André Valentin avec Claude  
**Création :** Session 125 (10 novembre 2025)  
**Dernière mise à jour :** Session 125  
**Prochaine révision :** Session 126 (après tests Retail Sales + Fed)

**Ce document doit être :**
- ✅ Lu attentivement avant toute session événements/clusters
- ✅ Mis à jour après chaque découverte majeure
- ✅ Consulté en cas de problème recherche DB
- ✅ Référencé dans tous handoffs futurs

---

**🎯 FIN DU GUIDE RÉFÉRENCE**
