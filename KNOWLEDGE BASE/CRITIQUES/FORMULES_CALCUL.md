# 📐 FORMULES DE CALCUL (CERTIFIÉES)

**Dernière validation :** 21 octobre 2025 - Session 26

---

## 🎯 SURPRISE (Version validée)

```python
def calculate_surprise(actual, forecast):
    """
    Calcule surprise UNIQUEMENT avec forecast.
    
    RÈGLE ABSOLUE : Ne JAMAIS utiliser previous
    """
    if forecast is None or forecast == 0:
        return None
    
    return abs((actual - forecast) / forecast) * 100
```

**Erreur historique :** Utilisé `previous` 6+ fois → Donne surprises < 10% au lieu de > 30%

---

## 📊 PHASE 1 (Mouvement jusqu'au TTR)

```python
def calculate_phase1(event_timestamp, prices_df):
    """
    Calcule Phase 1 depuis prices_1m
    
    Args:
        event_timestamp: Datetime événement (avec timezone)
        prices_df: DataFrame prices pour 15 min après événement
    
    Returns:
        dict: {phase1_pips, ttr_minutes, direction, start_price, ttr_price}
    """
    # Prix départ = OPEN première minute
    start_price = prices_df.iloc[0]['open']
    
    # Trouver pic dans les 15 minutes
    max_high = prices_df['high'].max()
    min_low = prices_df['low'].min()
    
    # Phase 1 = mouvement maximum
    phase1_up = (max_high - start_price) * 10000
    phase1_down = (start_price - min_low) * 10000
    
    if phase1_up > phase1_down:
        return {
            'phase1_pips': phase1_up,
            'direction': 'UP',
            'ttr_price': max_high,
            'ttr_minutes': prices_df['high'].idxmax(),
            'start_price': start_price
        }
    else:
        return {
            'phase1_pips': phase1_down,
            'direction': 'DOWN',
            'ttr_price': min_low,
            'ttr_minutes': prices_df['low'].idxmin(),
            'start_price': start_price
        }
```

---

## 🕐 CONVERSION TIMEZONE (Template safe)

```python
def query_prices_safe(event_timestamp):
    """
    Convertit timestamp événement en UTC pour requête DuckDB
    
    CRITIQUE : DuckDB ne convertit PAS automatiquement les timezones
    """
    import pandas as pd
    
    # Convertir en UTC
    if hasattr(event_timestamp, 'tz_convert'):
        utc_time = event_timestamp.tz_convert('UTC')
    else:
        utc_time = pd.to_datetime(event_timestamp, utc=True)
    
    # Format sans timezone pour DuckDB
    time_str = utc_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return time_str
```

---

## ✅ VALIDATION CAS RÉFÉRENCE

```python
def validate_reference_case(df):
    """
    Valide sur 11 septembre 2025 12:30 UTC
    
    OBLIGATOIRE avant tout calcul d'impact
    """
    sept11 = df[
        (df['ts_utc'].dt.date == pd.to_datetime('2025-09-11').date()) &
        (df['ts_utc'].dt.hour == 12) &
        (df['ts_utc'].dt.minute == 30)
    ]
    
    if len(sept11) == 0:
        raise ValueError("Cas référence 11 sept introuvable")
    
    phase1 = sept11['phase1_pips'].max()
    
    if not (28 <= phase1 <= 42):
        raise ValueError(f"Phase 1 invalide: {phase1:.2f} pips (attendu 33-37)")
    
    return True
```

---

**FIN DOCUMENT**
