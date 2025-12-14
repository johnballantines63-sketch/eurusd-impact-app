# 📚 DOCUMENTATION CONSOLIDÉE - PROJET EUR/USD NEWS IMPACT

**Version :** 2.0 (Consolidée Session 28)  
**Date :** 21 octobre 2025  
**Statut :** ✅ Documentation de référence unique

---

## 🎯 OBJECTIF DU PROJET

Prédire l'impact des annonces économiques sur la paire EUR/USD avec précision, en se basant sur :
- Score événement (importance empirique)
- Surprise (écart actual vs forecast)
- Nombre d'événements simultanés

---

## 📊 ÉTAT ACTUEL (Session 28)

### Base de données : ✅ VALIDÉE

```
warehouse.duckdb (205 MB)
├── events (58,449)              ✅ Forecast corrigé Session 27
├── event_families (747)         ✅ Mappings validés
├── scores (991)                 ✅ Scores empiriques
├── prices_1m (1,114,260)        ✅ Dukascopy validé Session 25/26
└── event_impacts_v2 (8,344)     ✅ Surprise >30% vraie (forecast)
```

### Formule actuelle : V2 (à remplacer)

```python
# V2 : MAE ~24% sur cas référence
impact = base_formula(score) × 2.5 × synergy × 0.758
```

**Limitation :** Plafond fixe ×2.5, pas adaptatif

### Prochaine étape : V4

```python
# V4 : Basée sur 8,344 événements empiriques
# Objectif : MAE <30%
# Méthode : Régression empirique adaptative
```

---

## ✅ CAS DE RÉFÉRENCE VALIDÉ

**11 septembre 2025 - 12:30 UTC (14:30 Berne)**

| Métrique | Valeur |
|----------|--------|
| Événements | 15 simultanés |
| Surprise MAX | 33.3% (Inflation Rate MoM) |
| Score MAX | ~46 |
| **Phase 1** | **33.7 pips** |
| Direction | UP |
| Prix départ | 1.16874 |
| TTR | 5 minutes |

**Validation obligatoire :** Toute formule doit prédire 33.7 ±10 pips pour ce cas.

---

## 🚨 ERREURS CRITIQUES À ÉVITER

### 1. Calcul surprise avec `previous` ❌

```python
# ❌ FAUX (commis 6+ fois)
if forecast is None:
    surprise = abs((actual - previous) / previous)

# ✅ BON
if forecast is None or forecast == 0:
    return None  # Pas de surprise calculable
return abs((actual - forecast) / forecast) * 100
```

### 2. Confusion timezone ❌

```python
# ❌ FAUX
query = f"WHERE datetime = '14:30:00+02:00'"  # DuckDB cherche littéralement

# ✅ BON
event_time_utc = pd.to_datetime('2025-09-11 14:30:00+02:00', utc=True)
time_str = event_time_utc.strftime('%Y-%m-%d %H:%M:%S')  # '12:30:00'
query = f"WHERE datetime >= '{time_str}'::timestamp"
```

### 3. Utiliser tables obsolètes ❌

**❌ NE PLUS UTILISER :**
- `event_impacts_calculated` (supprimée Session 26)
- `event_group_impacts` (supprimée Session 26)
- Tout CSV avant Session 27

**✅ UTILISER :**
- `events` (brutes avec forecast corrigé)
- `prices_1m` (Dukascopy validé)
- `event_impacts_v2` (8,344 événements validés)

---

## 🔧 SOURCES DE DONNÉES

### ✅ Adoptées

**Dukascopy (prix) :**
- Source institutionnelle (banque suisse)
- Tick-by-tick agrégé M1
- Validé vs MT5 André (Swissquote)
- Import Sept 2022 → Oct 2025

**EODHD (événements) :**
- API gratuite événements économiques
- 58,449 événements
- ⚠️ Utilise "estimate" pas "forecast" (corrigé Session 27)

### ❌ Abandonnées

- **EODHD (prix)** : Sous-estime ×10
- **HistData** : Sous-estime ×100-300

---

## 📐 FORMULES VALIDÉES

### Calcul surprise

```python
def calculate_surprise(actual, forecast):
    """Surprise en % - UNIQUEMENT avec forecast"""
    if forecast is None or forecast == 0:
        return None
    return abs((actual - forecast) / forecast) * 100
```

### Calcul Phase 1

```python
def calculate_phase1(event_timestamp, prices_df):
    """
    Mouvement jusqu'au TTR (Time To Return)
    
    Args:
        event_timestamp: Datetime événement (UTC)
        prices_df: Prix 15 min après événement
    
    Returns:
        dict: {phase1_pips, ttr_minutes, direction, start_price}
    """
    start_price = prices_df.iloc[0]['open']
    max_high = prices_df['high'].max()
    min_low = prices_df['low'].min()
    
    phase1_up = (max_high - start_price) * 10000
    phase1_down = (start_price - min_low) * 10000
    
    if phase1_up > phase1_down:
        return {
            'phase1_pips': phase1_up,
            'direction': 'UP',
            'ttr_minutes': prices_df['high'].idxmax(),
            'start_price': start_price,
            'ttr_price': max_high
        }
    else:
        return {
            'phase1_pips': phase1_down,
            'direction': 'DOWN',
            'ttr_minutes': prices_df['low'].idxmin(),
            'start_price': start_price,
            'ttr_price': min_low
        }
```

---

## 🎯 APPROCHE TRADING

**Principe :** André NE trade PAS pendant la minute d'annonce

**Ce qui intéresse André :**
1. **Phase 1** - Mouvement global jusqu'au TTR (5-15 min)
2. **TTR** - Temps jusqu'au pic
3. **Pullback** - Correction après pic
4. **Phase 2** - Continuation ou stabilisation

**Formule V4 doit prédire ces phases exploitables.**

---

## 📂 STRUCTURE DOCUMENTATION

```
KNOWLEDGE BASE/
├── 00_START_HERE.md              ← Ce fichier
├── CRITIQUES/                    ← À lire AVANT tout code
│   ├── ERREURS_RECURRENTES.md
│   ├── TABLES_DATABASE.md
│   ├── FORMULES_CALCUL.md
│   └── CAS_REFERENCE.md
├── REFERENCE/
│   ├── HISTORIQUE_SESSIONS.md    ← Synthèse Sessions 1-27
│   └── DECISIONS_CLES.md         ← Décisions majeures
└── TECHNIQUES/
    ├── TIMEZONE_HANDLING.md      ← Gestion fuseaux horaires
    └── WORKFLOWS.md              ← Workflows standards
```

---

## 🚀 DÉMARRAGE RAPIDE

### Pour une nouvelle session

1. Lire `00_START_HERE.md` (ce fichier)
2. Lire les 4 fichiers dans `CRITIQUES/`
3. Vérifier état DB avec cas référence
4. Commencer à coder

**Temps total :** ~15 minutes

### Validation avant de continuer

```python
# Test obligatoire
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# Cas référence 11 septembre
result = con.execute("""
    SELECT phase1_pips FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11' 
    AND EXTRACT(HOUR FROM ts_utc) = 12
    ORDER BY phase1_pips DESC LIMIT 1
""").fetchone()

if result and 28 <= result[0] <= 42:
    print(f"✅ Validation OK : {result[0]:.2f} pips")
else:
    print("❌ Données corrompues - STOP")
```

---

## 📊 COMMANDES UTILES

### Vérifier état base

```bash
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
tables = con.execute('SHOW TABLES').df()['name'].tolist()
print('Tables:', tables)
for table in ['events', 'prices_1m', 'event_impacts_v2']:
    count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count:,}')
"
```

### Lancer application

```bash
cd fx_impact_app
streamlit run app.py
```

---

## 📞 CONTACT

**Développeur :** André  
**Assistant IA :** Claude (Anthropic)  
**Projet :** EUR/USD News Impact Calculator  

---

## 🔄 HISTORIQUE VERSIONS

| Version | Date | Changement |
|---------|------|------------|
| 2.0 | 21 oct 2025 | Consolidation Session 28 |
| 1.0 | 21 oct 2025 | Création structure (Session 26) |

---

**📌 Ce fichier est le POINT D'ENTRÉE UNIQUE de la documentation.**

**Dernière mise à jour :** 21 octobre 2025 - Session 28
