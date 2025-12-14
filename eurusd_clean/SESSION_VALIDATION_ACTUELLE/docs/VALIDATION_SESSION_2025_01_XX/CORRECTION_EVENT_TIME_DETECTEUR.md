# Correction Détecteur pour Utiliser Event Time Réel

**Date** : 2025-01-XX  
**Problème** : Le détecteur force toujours 14:30, alors que certains événements sont à d'autres heures  
**Solution** : Ajouter paramètre `event_time` au détecteur

---

## ✅ CORRECTIONS APPLIQUÉES

### 1. Modification `detect_double_wave_on_df_rev12`

**Fichier** : `scripts/session120/double_wave_detector_rev12.py`

**Ajout** : Paramètre `hint_ts` optionnel

```python
def detect_double_wave_on_df_rev12(
    df: pd.DataFrame,
    date_label: str,
    symbol: str = "EURUSD",
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    max_idle_bars: int = MAX_IDLE_BARS,
    local_width: int = LOCAL_WIDTH,
    debug: bool = False,
    hint_ts: Optional[pd.Timestamp] = None  # NOUVEAU
) -> Optional[Dict]:
    # ...
    if hint_ts is None:
        hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)
    else:
        # S'assurer que hint_ts a la même timezone que df
        if hint_ts.tz is None:
            hint_ts = pd.Timestamp(hint_ts, tz=tz)
        elif hint_ts.tz != df.index.tz:
            hint_ts = hint_ts.tz_convert(df.index.tz)
```

### 2. Modification `detect_for_date_duckdb_rev12`

**Fichier** : `scripts/session120/double_wave_detector_rev12.py`

**Ajout** : Paramètre `event_time` optionnel

```python
def detect_for_date_duckdb_rev12(
    db_path: str, table: str, date: datetime,
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    trading_window: bool = True,
    debug: bool = False,
    event_time: Optional[datetime] = None  # NOUVEAU
) -> Optional[Dict]:
    # Ajuster la fenêtre de trading si event_time est fourni
    if event_time is not None:
        # Convertir event_time en Timestamp avec timezone
        if isinstance(event_time, datetime):
            if event_time.tzinfo is None:
                event_ts = pd.Timestamp(event_time, tz=tz)
            else:
                event_ts = pd.Timestamp(event_time).tz_convert(tz)
        else:
            event_ts = pd.Timestamp(event_time, tz=tz)
        # Fenêtre : 1h avant l'événement jusqu'à 2h après
        start_dt = event_ts - pd.Timedelta(hours=1)
        end_dt = event_ts + pd.Timedelta(hours=2)
    
    # Préparer hint_ts pour detect_double_wave_on_df_rev12
    hint_ts_param = None
    if event_time is not None:
        # Convertir event_time en Timestamp avec timezone
        if isinstance(event_time, datetime):
            if event_time.tzinfo is None:
                hint_ts_param = pd.Timestamp(event_time, tz=tz)
            else:
                hint_ts_param = pd.Timestamp(event_time).tz_convert(tz)
        else:
            hint_ts_param = pd.Timestamp(event_time, tz=tz)
    
    return detect_double_wave_on_df_rev12(
        df, date_label=ts.strftime("%Y-%m-%d"), symbol="EURUSD", tz=tz,
        baseline_mode=baseline_mode, minutes_after_hint=minutes_after_hint,
        debug=debug, hint_ts=hint_ts_param
    )
```

### 3. Modification Pipeline

**Fichier** : `scripts/run_pipeline_complete.py`

**Ajout** : Passer `anchor_time` au détecteur

```python
pattern_real_result = detect_for_date_duckdb_rev12(
    db_path=str(self.db_path),
    table='prices_finnhub_m1',
    date=pattern_date,
    tz='Europe/Zurich',
    baseline_mode='prev_close_14_29',
    minutes_after_hint=120,
    trading_window=True,
    debug=False,
    event_time=anchor_time  # NOUVEAU : Utiliser l'anchor_time réel
)
```

---

## ⚠️ PROBLÈME RESTANT

Le `baseline_mode='prev_close_14_29'` cherche toujours la baseline à 14:29, même si l'événement est à une autre heure. Pour les événements à 15:47 ou 16:10, la baseline devrait être cherchée juste avant l'événement (par exemple, 15:46 ou 16:09).

**Solution proposée** : Utiliser un mode adaptatif :
- Si événement à 14:30 → `prev_close_14_29`
- Sinon → `prev_close` (cherche la baseline juste avant l'événement)

---

**Status** : ✅ **CORRECTION APPLIQUÉE** | ⚠️ **BASELINE MODE À ADAPTER**

