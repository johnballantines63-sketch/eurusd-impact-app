# Rapport de Validation Panel — Backtest Engine V1

**Date :** 2025-12-13  
**Version :** V1  
**Objectif :** Infrastructure de validation empirique indépendante de l'UI

---

## 📋 Vue d'ensemble

Ce système permet de valider scientifiquement le moteur de prédiction sur un panel de dates, **sans dépendance à Streamlit**.

### Fichiers créés

1. **`app/backtest_engine_v1.py`** : Module Python réutilisable avec fonctions core
2. **`notebooks/validate_events_vs_price_patterns_v2.ipynb`** : Notebook de validation interactive
3. **`docs/VALIDATION_PANEL_REPORT.md`** : Ce document

---

## 🚀 Commandes d'exécution

### 1. Lancer le notebook

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
jupyter notebook notebooks/validate_events_vs_price_patterns_v2.ipynb
```

Ou avec JupyterLab :

```bash
jupyter lab notebooks/validate_events_vs_price_patterns_v2.ipynb
```

### 2. Exécuter via Python (sans notebook)

```python
from pathlib import Path
import duckdb
from app.backtest_engine_v1 import compute_day_prediction

DB_PATH = Path("data/warehouse.duckdb")
conn = duckdb.connect(str(DB_PATH), read_only=True)

result = compute_day_prediction("2025-08-01", conn)
print(result)

conn.close()
```

---

## 📊 Description des colonnes standardisées

### DataFrame `events_enriched`

Retourné par `load_events_enriched(date_str, conn)` :

| Colonne | Type | Description |
|---------|------|-------------|
| `ts_utc` | datetime | Timestamp UTC de l'événement |
| `ts_local` | datetime | Timestamp local (timezone du pays) |
| `country` | str | Code pays (ex: 'US', 'EU') |
| `event_key` | str | Clé canonique de l'événement (ou `event_title` si absent) |
| `event_title` | str | Titre descriptif |
| `actual` | float | Valeur publiée (actual) |
| `consensus` | float | Consensus = `COALESCE(estimate, forecast)` |
| `previous` | float | Valeur précédente = `COALESCE(previous, prev)` |
| `importance_n` | int | Importance numérique (1-5) |
| `is_core` | bool | `True` si `importance_n >= 4` ou `country == 'US'` |

### Résultat `compute_day_prediction()`

Dict Python avec :

| Clé | Type | Description |
|-----|------|-------------|
| `date` | str | Date analysée ('YYYY-MM-DD') |
| `t0` | str | ISO timestamp du premier événement core |
| `n_events` | int | Nombre total d'événements |
| `n_core_events` | int | Nombre d'événements core |
| `direction_pred` | int | +1 (EUR/USD UP), -1 (EUR/USD DOWN), 0 (NO_TRADE) |
| `impact_pred` | float | Impact prédit en pips (positif) |
| `n_events_with_surprise` | int | Nombre d'événements avec surprise calculable |
| `pred_vol_pips` | float | Volatilité prédite en pips |
| `pattern_type` | str | 'single_wave', 'double_wave', 'zigzag', 'none' |
| `turning_points` | list | Liste de (timestamp, price, type) des turning points |
| `max_movement_pips` | float | Mouvement maximum en pips depuis baseline |
| `baseline_price` | float | Prix de référence (avant t0) |
| `threshold_pips` | float | Seuil utilisé pour détecter mouvements significatifs |

---

## 🔧 Logique de fonctionnement

### 1. Chargement événements enrichis

1. **Source principale** : `events_with_ts_local_v1`
   - Colonnes utilisées : `ts_utc`, `ts_local`, `country`, `event_key`, `event_title`, `actual`, `estimate`, `forecast`, `previous`, `prev`, `importance_n`
   
2. **Enrichissement** : `economic_events` (si consensus manquant)
   - Join 1 : `(country, ts_utc arrondi à la minute)`
   - Join 2 (fallback) : `(country, texte normalisé)`
   
3. **Standardisation** :
   - `consensus = COALESCE(estimate, forecast)`
   - `previous = COALESCE(previous, prev)`
   - `is_core = (importance_n >= 4) OR (country == 'US')`

### 2. Calcul direction/impact

- **Surprise** : `surprise_value = actual - consensus`
- **Direction** : Somme vectorielle pondérée par `importance_n`
  - Simplifié : surprise > 0 → EUR/USD DOWN, surprise < 0 → EUR/USD UP
- **Impact** : Moyenne pondérée des surprises absolues

### 3. Volatilité prédite

1. **Source 1** : `daily_risk_signal_v3_2_1.pred_vol_pips`
2. **Source 2** (fallback) : `daily_eurusd_volatility_v1.realized_vol_pips`
3. **Valeur par défaut** : 80 pips

### 4. Détection pattern depuis prix

1. **Chargement prix** : `prices_finnhub_m5` (col `datetime`, `close`, `high`, `low`)
2. **Baseline** : Prix juste avant `t0`
3. **ATR** : Calculé depuis ranges intraday (ou approximation)
4. **Seuil** : `max(min_movement_pips, ATR * atr_multiplier)`
5. **Turning points** : Extrema locaux avec valeur absolue > seuil
6. **Classification** :
   - `single_wave` : 0-1 turning points
   - `double_wave` : 2 turning points même type
   - `zigzag` : 2+ turning points alternés

---

## 📈 Résultats attendus

### Panel dates actuel

- **2025-08-01** : Single wave forte (NFP)
- **2025-09-11** : Pattern différent

### Export CSV

Les exports sont sauvegardés dans `exports/validation_panel_v2/` :

- `results_panel_YYYYMMDD_HHMMSS.csv` : Tableau récapitulatif
- `events_enriched_YYYY-MM-DD_YYYYMMDD_HHMMSS.csv` : Événements enrichis par date
- `prices_YYYY-MM-DD_YYYYMMDD_HHMMSS.csv` : Prix EURUSD par date

---

## ⚠️ Limites connues

### 1. Détection pattern simplifiée

- Algorithme de détection de turning points basique (extrema locaux)
- Pas de validation temporelle stricte (durée entre pics)
- Classification peut être améliorée avec règles plus sophistiquées

### 2. Direction/impact simplifiés

- Pas de mapping de sentiment par famille d'événements (NFP vs CPI)
- Somme vectorielle simple, pas d'amplification selon nombre d'événements
- Impact en pips approximatif (pas de calibration empirique)

### 3. Volatilité

- Fallback sur realized volatility si prédiction absente
- Valeur par défaut fixe (80 pips) si aucune vol disponible

### 4. Join événements

- Matching texte normalisé peut créer faux positifs
- Pas de validation de qualité du match (score de confiance)

### 5. Dates passées

- Actuals auto-chargés depuis DB (pas de vérification de qualité)
- Pas de détection de données manquantes/corrompues

---

## 🔄 Améliorations futures

1. **Détection pattern avancée**
   - Intégrer détecteurs Session 119 (SingleWaveFort, ZigZag, etc.)
   - Validation temporelle stricte (durées entre pics)

2. **Mapping sentiment**
   - Intégrer `FAMILY_SENTIMENT` depuis `compute_real_prediction.py`
   - Calcul direction plus précis

3. **Calibration impact**
   - Utiliser scores empiriques depuis `event_families`
   - Amplification selon nombre d'événements

4. **Qualité données**
   - Validation de cohérence actuals vs consensus
   - Détection d'anomalies (actuals > 3 std du consensus)

5. **Métriques de validation**
   - Comparaison pattern prédit vs pattern réel
   - Score de précision direction
   - Score de précision impact (MAPE)

---

## 📝 Notes techniques

### Dépendances

- `duckdb` : Base de données (read-only)
- `pandas`, `numpy` : Manipulation données
- `pathlib` : Gestion chemins
- **Aucune dépendance Streamlit**

### Conventions

- **Warnings explicites** : Tous les logs via `warnings.warn()`, jamais de `except: pass`
- **Colonnes standardisées** : Toujours utiliser les noms canoniques
- **Chemins relatifs** : Depuis `PROJECT_ROOT`, pas de chemins absolus codés en dur

### Structure DB

- `events_with_ts_local_v1` : Vue principale événements
- `economic_events` : Table consensus (colonnes: `datetime_utc`, `event_name`, `forecast`, `previous`)
- `prices_finnhub_m5` : Prix EURUSD (colonnes: `datetime`, `close`, `high`, `low`)
- `daily_risk_signal_v3_2_1` : Volatilité prédite
- `daily_eurusd_volatility_v1` : Volatilité réalisée (fallback)

---

## ✅ Checklist validation

- [x] Module Python créé (`app/backtest_engine_v1.py`)
- [x] Notebook créé (`notebooks/validate_events_vs_price_patterns_v2.ipynb`)
- [x] Documentation créée (`docs/VALIDATION_PANEL_REPORT.md`)
- [x] Aucune dépendance Streamlit
- [x] Colonnes standardisées (consensus, previous)
- [x] Join robuste (temporel + texte)
- [x] Détection pattern depuis prix
- [x] Export CSV automatique
- [ ] Tests unitaires (à faire)
- [ ] Validation sur panel étendu (à faire)

---

**Document créé le :** 2025-12-13  
**Dernière mise à jour :** 2025-12-13

