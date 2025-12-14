# 📚 KNOWLEDGE BASE UPDATE - SESSION 26

**Date :** 21 octobre 2025  
**Session :** 26  
**Type :** DÉCOUVERTE CRITIQUE - Tables corrompues + Plan reconstruction

---

## 🚨 DÉCOUVERTE MAJEURE SESSION 26

### PROBLÈME IDENTIFIÉ

**Toutes les tables d'impact calculées sont CORROMPUES.**

Elles ont été calculées avec les **anciennes sources** (EODHD/HistData) qui sous-estiment les mouvements ×10 à ×300.

### VALIDATION EFFECTUÉE

#### ✅ Ce qui est CORRECT

**Table `prices_1m` (Dukascopy) :**
- Source : Dukascopy (données institutionnelles)
- Période : 2022-10-23 → 2025-10-20
- Lignes : 1,114,260
- Timezone : UTC (corrigé -2h en Session 25)

**Validation cas référence 11 septembre 2025 :**
```
Requête directe sur prices_1m :
- Datetime : 2025-09-11 12:30:00 UTC
- Prix départ : 1.16874
- Phase 1 calculée : 33.7 pips
- Attendu (MT5 André) : 37.4 pips
- Écart : 3.7 pips (9.9%)
- Statut : ✅ EXCELLENT
```

#### ❌ Ce qui est CORROMPU

**Table `event_group_impacts` (19,653 lignes) :**
- Calculée avec anciennes sources
- MFE sous-estimés

**Validation cas référence 11 septembre 2025 :**
```
Requête sur event_group_impacts :
- Datetime : 2025-09-11 14:30:00
- MFE stocké : 14.3 pips
- Attendu (MT5 André) : 37.4 pips
- Écart : 23.1 pips (61.8%)
- Statut : ❌ CORROMPU
```

**Table `event_impacts_calculated` (4,124 lignes) :**
- Contient `surprise_index_corrected` ✅
- Mais MFE calculés avec anciennes sources
- Seulement 3 événements avec surprise > 30%
- Incomplet et corrompu

**Fichier `events_extreme_surprise_dukascopy_session25.csv` :**
- Généré depuis tables corrompues
- Phase 1 pour 11 sept : 6.6 pips (vs 37.4 attendu)
- Statut : ❌ INVALIDE

---

## 📊 STRUCTURE BASE DE DONNÉES ACTUELLE

### Tables VALIDES (à conserver) ✅

**1. `events` (58,449 lignes)**
```sql
Colonnes principales :
- ts_utc (TIMESTAMP WITH TIME ZONE)
- event_key (VARCHAR)
- event_title (VARCHAR)
- country (VARCHAR)
- actual (DOUBLE)
- forecast (DOUBLE)
- previous (DOUBLE)
- estimate (DOUBLE)
- importance_n (BIGINT)
- period (VARCHAR)
- change (DOUBLE)
- change_percentage (DOUBLE)

Note : PAS de colonne surprise (doit être calculée)
```

**2. `event_families` (747 lignes)**
```sql
Colonnes :
- event_key (VARCHAR)
- family_name (VARCHAR)
- importance (INTEGER)

Statut : Mappings manuels validés
```

**3. `scores` (991 lignes)**
```sql
Colonnes :
- event_key ou family (VARCHAR)
- score (DOUBLE)

Statut : Scores calculés validés
```

**4. `prices_1m` (1,114,260 lignes)** ⭐
```sql
Colonnes :
- datetime (TIMESTAMP WITH TIME ZONE)
- open (DOUBLE)
- high (DOUBLE)
- low (DOUBLE)
- close (DOUBLE)

Source : Dukascopy (tick-by-tick agrégé M1)
Timezone : UTC strict
Période : 2022-10-23 21:00 UTC → 2025-10-20 21:59 UTC
Statut : ✅ VALIDÉ Session 26
```

### Tables CORROMPUES (à supprimer) ❌

**1. `event_impacts_calculated`**
- Raison : Calculé avec anciennes sources
- Action : DROP TABLE

**2. `event_group_impacts`**
- Raison : MFE sous-estimés (anciennes sources)
- Action : DROP TABLE

**3. `event_group_impacts_backup_session22`**
- Raison : Backup de table corrompue
- Action : DROP TABLE

**4. Toutes les tables `prices_*_v` (vues)**
- Raison : Vues sur données peut-être corrompues
- Action : À vérifier, probablement OK car vues sur prices_1m

---

## 🔧 PLAN DE RECONSTRUCTION

### Stratégie CLEAN START

**Principe :** Garder application Streamlit + Reconstruire données depuis zéro

### Tables à créer

**1. `event_impacts_v2`**
```sql
CREATE TABLE event_impacts_v2 (
    ts_utc TIMESTAMP WITH TIME ZONE,
    event_key VARCHAR,
    event_title VARCHAR,
    country VARCHAR,
    actual DOUBLE,
    forecast DOUBLE,
    previous DOUBLE,
    surprise_pct DOUBLE,        -- Calculé : ABS((actual - forecast) / forecast) * 100
    importance INTEGER,
    phase1_pips DOUBLE,         -- Calculé depuis prices_1m
    ttr_minutes INTEGER,        -- Temps jusqu'au pic
    direction VARCHAR,          -- UP ou DOWN
    start_price DOUBLE,         -- Prix open première minute
    ttr_price DOUBLE,           -- Prix au TTR
    pullback_pips DOUBLE,       -- Si applicable
    source VARCHAR DEFAULT 'dukascopy_session26',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. `event_groups_v2`**
```sql
CREATE TABLE event_groups_v2 (
    group_id VARCHAR PRIMARY KEY,           -- UUID ou hash
    ts_utc TIMESTAMP WITH TIME ZONE,        -- Premier événement du groupe
    num_events INTEGER,
    event_keys VARCHAR,                     -- JSON array ou CSV
    event_titles VARCHAR,
    countries VARCHAR,
    max_surprise_pct DOUBLE,
    avg_surprise_pct DOUBLE,
    phase1_pips DOUBLE,                     -- Calculé depuis prices_1m
    ttr_minutes INTEGER,
    direction VARCHAR,
    max_score DOUBLE,
    start_price DOUBLE,
    ttr_price DOUBLE,
    source VARCHAR DEFAULT 'dukascopy_session26',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Méthode de calcul CORRECTE

**Calcul surprise :**
```python
def calculate_surprise(actual, forecast, previous):
    """Calcule surprise en %"""
    if forecast is not None and forecast != 0:
        return abs((actual - forecast) / forecast) * 100
    elif previous is not None and previous != 0:
        return abs((actual - previous) / previous) * 100
    else:
        return None
```

**Calcul Phase 1 :**
```python
def calculate_phase1(event_datetime, prices_df):
    """
    Calcule Phase 1 depuis prices_1m
    
    Args:
        event_datetime: Timestamp UTC de l'événement
        prices_df: DataFrame prices_1m pour la période
    
    Returns:
        dict avec phase1_pips, ttr_minutes, direction, etc.
    """
    # Fenêtre : event_time → event_time + 15 min
    window_start = event_datetime
    window_end = event_datetime + timedelta(minutes=15)
    
    # Filtrer prix
    window_prices = prices_df[
        (prices_df['datetime'] >= window_start) &
        (prices_df['datetime'] <= window_end)
    ].copy()
    
    if len(window_prices) == 0:
        return None
    
    # Prix départ = OPEN première minute
    start_price = window_prices.iloc[0]['open']
    
    # Trouver pic
    max_high = window_prices['high'].max()
    min_low = window_prices['low'].min()
    
    # Phase 1 = mouvement maximum
    phase1_up = (max_high - start_price) * 10000
    phase1_down = (start_price - min_low) * 10000
    
    if phase1_up > phase1_down:
        phase1_pips = phase1_up
        direction = 'UP'
        ttr_price = max_high
        ttr_idx = window_prices['high'].idxmax()
    else:
        phase1_pips = phase1_down
        direction = 'DOWN'
        ttr_price = min_low
        ttr_idx = window_prices['low'].idxmin()
    
    # TTR en minutes = index de la ligne où le pic est atteint
    ttr_minutes = ttr_idx
    
    return {
        'phase1_pips': phase1_pips,
        'ttr_minutes': ttr_minutes,
        'direction': direction,
        'start_price': start_price,
        'ttr_price': ttr_price
    }
```

**Groupement multi-événements :**
```python
def group_events(events_df, window_minutes=5):
    """
    Groupe événements dans une fenêtre temporelle
    
    Args:
        events_df: DataFrame événements triés par ts_utc
        window_minutes: Taille fenêtre en minutes (défaut 5)
    
    Returns:
        Liste de groupes
    """
    groups = []
    current_group = []
    
    for idx, event in events_df.iterrows():
        if not current_group:
            current_group.append(event)
        else:
            time_diff = (event['ts_utc'] - current_group[0]['ts_utc']).total_seconds() / 60
            
            if time_diff <= window_minutes:
                current_group.append(event)
            else:
                groups.append(current_group)
                current_group = [event]
    
    if current_group:
        groups.append(current_group)
    
    return groups
```

---

## 📋 SCRIPTS À CRÉER SESSION 26

### 1. Nettoyage
```
clean_corrupted_tables_session26.py
- DROP TABLE event_impacts_calculated
- DROP TABLE event_group_impacts
- DROP TABLE event_group_impacts_backup_session22
- Backup warehouse.duckdb avant
```

### 2. Reconstruction événements individuels
```
build_event_impacts_v2_session26.py
- Lit events
- Calcule surprise pour chaque événement
- Filtre surprise > 30% (optionnel)
- Pour chaque événement, calcule Phase 1 depuis prices_1m
- Insert dans event_impacts_v2
```

### 3. Reconstruction groupes multi-événements
```
build_event_groups_v2_session26.py
- Lit events
- Groupe par fenêtre 5 min
- Pour chaque groupe, calcule Phase 1 depuis prices_1m
- Insert dans event_groups_v2
```

### 4. Validation
```
validate_v2_tables_session26.py
- Vérifie 11 septembre 2025 dans event_impacts_v2
- Phase 1 doit être 33-37 pips
- Vérifie 11 septembre dans event_groups_v2
- MFE du groupe doit être 33-37 pips
```

### 5. Génération CSV propre
```
generate_csv_v2_session26.py
- Export event_impacts_v2 avec surprise > 30%
- Fichier : events_surprise30_v2_session26.csv
- Validation 11 septembre incluse
```

---

## ✅ CRITÈRES DE VALIDATION

### Validation obligatoire cas référence 11 septembre 2025

**Événement individuel :**
```
ts_utc: 2025-09-11 12:30:00 UTC
phase1_pips: 33-37 pips (tolérance ±5 pips autour de 33.7)
start_price: ~1.16874 (tolérance ±0.0005)
```

**Groupe multi-événements :**
```
ts_utc: 2025-09-11 12:30:00 UTC (ou 14:30 selon timezone display)
num_events: 15
phase1_pips: 33-37 pips
max_score: ~46
```

### Critères globaux

```python
# Après reconstruction
assert event_impacts_v2.count() > 10000  # Au moins 10k événements
assert event_groups_v2.count() > 15000   # Au moins 15k groupes

# Distribution Phase 1
assert event_impacts_v2['phase1_pips'].median() between 5-10 pips
assert event_impacts_v2['phase1_pips'].mean() between 6-12 pips

# Cas référence
sept11 = event_impacts_v2[ts_utc == '2025-09-11 12:30:00']
assert 30 <= sept11['phase1_pips'] <= 40
```

---

## 🎯 LEÇONS APPRISES SESSION 26

### 1. Toujours valider données sources AVANT calculs

**Erreur Session 25 :**
- Généré CSV depuis event_group_impacts
- Pas vérifié que event_group_impacts était correct
- Résultat : 4h30 pour découvrir que tout était faux

**Bonne pratique :**
```python
# Avant d'utiliser une table
1. Vérifier cas référence connu
2. Si erreur > 10% → Table corrompue
3. Remonter à la source (prices_1m)
```

### 2. Tables dérivées = Point de défaillance unique

**Problème :**
- event_impacts_calculated dépend de prices_X
- Si prices_X change → event_impacts_calculated invalide
- Mais rien ne le signale

**Solution :**
- Ajouter colonne `source` dans tables dérivées
- Ajouter colonne `created_at`
- Permet de tracer origine des calculs

### 3. CSV = Snapshot temporel

**Problème :**
- CSV généré Session 25 avec données corrompues
- Reste ensuite comme "référence" alors qu'invalide

**Solution :**
- Toujours dater CSV : `_session26.csv`
- Toujours inclure `source` en commentaire
- Valider AVANT de distribuer

### 4. Validation cas référence = NON NÉGOCIABLE

**Règle absolue :**
```python
# Avant toute analyse
assert validate_reference_case() == True
```

Si le cas référence connu (11 septembre) n'est pas validé → STOP immédiatement.

---

## 📁 FICHIERS OBSOLÈTES À NE PLUS UTILISER

### CSV invalides
- `events_extreme_surprise_dukascopy_session25.csv` ❌
- `extreme_cases_surprise30_session23.csv` ❌
- Tout CSV de sessions < 26 contenant "impact" ou "phase1"

### Tables à ne plus interroger
- `event_impacts_calculated` ❌
- `event_group_impacts` ❌

### Tables à utiliser
- `prices_1m` ✅ (source validée)
- `events` ✅ (données brutes)
- `event_families` ✅ (mappings validés)
- `scores` ✅ (scores validés)

---

## 🔄 WORKFLOW CORRECT POST-SESSION 26

### Pour analyser un événement

```python
# 1. Lire depuis events (données brutes)
event = db.query("SELECT * FROM events WHERE ts_utc = ?", timestamp)

# 2. Calculer surprise
surprise = calculate_surprise(event.actual, event.forecast, event.previous)

# 3. Lire prices_1m directement
prices = db.query("""
    SELECT * FROM prices_1m 
    WHERE datetime >= ? AND datetime <= ?
""", event.ts_utc, event.ts_utc + 15min)

# 4. Calculer Phase 1
phase1 = calculate_phase1(event.ts_utc, prices)

# 5. Pas de cache, pas de table dérivée
# Calcul à la volée depuis sources validées
```

### Pour créer formule V4

```python
# Utiliser event_impacts_v2 après validation
df = db.query("""
    SELECT * FROM event_impacts_v2
    WHERE surprise_pct > 30
    AND source = 'dukascopy_session26'
""")

# Vérifier cas référence
assert validate_reference_case(df) == True

# Créer formule
formula_v4 = build_formula(df)
```

---

## 🎓 KNOWLEDGE BASE - STRUCTURE TABLES FINALE

### Tables de base (ne changent jamais)

```
events (58,449 lignes)
├── Source: EODHD API
├── Brut, pas de calculs
└── Timezone: UTC

event_families (747 lignes)
├── Mappings manuels
└── Validés Session 22

scores (991 lignes)
├── Scores empiriques
└── Validés multiple sessions

prices_1m (1,114,260 lignes) ⭐
├── Source: Dukascopy
├── Timezone: UTC
├── Période: Oct 2022 → Oct 2025
└── VALIDÉ Session 26
```

### Tables dérivées V2 (reconstruites Session 26)

```
event_impacts_v2
├── Calculs depuis prices_1m
├── Surprise calculée
├── Phase 1 validée
└── Source tracée

event_groups_v2
├── Groupements 5 min
├── Phase 1 groupes
└── Multi-événements
```

---

**FIN KNOWLEDGE BASE UPDATE SESSION 26**

**Date :** 21 octobre 2025  
**Session :** 26  
**Découverte :** Tables corrompues identifiées  
**Action :** Reconstruction propre planifiée  
**Impact :** Fondations solides pour V4
