# 📘 GUIDE TIMEZONE DÉFINITIF - SESSION 86

**Créé :** 26 octobre 2025  
**Pour :** Session 87 et suivantes  
**Priorité :** ⭐⭐⭐ CRITIQUE - TOUJOURS CONSULTER

---

## 🎯 RÈGLE SIMPLE EN 1 PHRASE

> **Les tables `events` et `prices_1m` utilisent TOUTES DEUX le timezone `+02:00` (Bern/Zurich).  
> Donc : PAS de conversion, même heure dans les deux tables.**

---

## 📊 EXEMPLES CONCRETS

### Exemple 1 : Événement NFP 01.08.2025

**Dans la table `events` :**
```sql
SELECT event_title, ts_utc 
FROM events 
WHERE date_part('day', ts_utc) = 1 
  AND date_part('month', ts_utc) = 8;

-- Résultat :
-- event_title: "Nonfarm Payrolls"
-- ts_utc: 2025-08-01 14:30:00+02:00  ← Noter le +02:00
```

**Dans la table `prices_1m` :**
```sql
SELECT datetime, close 
FROM prices_1m 
WHERE datetime = '2025-08-01 14:30:00+02:00';

-- Résultat :
-- datetime: 2025-08-01 14:30:00+02:00  ← Même timezone !
-- close: 1.13988
```

**Conclusion :** L'événement à 14:30 Bern correspond aux prix à 14:30+02:00. **Même heure, pas de calcul.**

---

### Exemple 2 : Extraire prix autour d'un événement (PYTHON)

```python
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("/path/to/warehouse.duckdb")

def get_prices_around_event(date_str: str, event_time_bern: str, window_min: int = 60):
    """
    Extrait prix autour d'un événement
    
    TIMEZONE RÈGLE (SESSION 86) :
    ============================
    - events.ts_utc : +02:00 (Bern)
    - prices_1m.datetime : +02:00 (Bern)
    - → MÊME TIMEZONE, pas de conversion
    
    Args:
        date_str: '2025-08-01'
        event_time_bern: '14:30:00' (heure Bern)
        window_min: fenêtre en minutes (défaut 60)
    
    Returns:
        DataFrame avec colonnes [datetime, close, high, low]
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ÉTAPE 1 : Vérifier timezone (OBLIGATOIRE première fois)
    sample = conn.execute("SELECT datetime FROM prices_1m LIMIT 1").fetchdf()
    print(f"Timezone vérifié : {sample['datetime'].iloc[0]}")
    # Doit afficher : ...+02:00
    
    # ÉTAPE 2 : Query avec +02:00 EXPLICITE
    query = f"""
    SELECT 
        datetime,
        close,
        high,
        low
    FROM prices_1m
    WHERE datetime >= '{date_str} {event_time_bern}+02:00'::TIMESTAMP - INTERVAL '{window_min} minutes'
      AND datetime <= '{date_str} {event_time_bern}+02:00'::TIMESTAMP + INTERVAL '{window_min} minutes'
    ORDER BY datetime
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    # ÉTAPE 3 : Validation automatique (cas test 01.08.2025)
    if date_str == '2025-08-01' and event_time_bern == '14:30:00':
        min_price = df['low'].min()
        if min_price > 1.14000:
            raise ValueError(
                f"❌ TIMEZONE INCORRECT !\n"
                f"Min trouvé : {min_price:.5f}\n"
                f"Attendu : < 1.14000 (spike à ~1.13918)\n"
                f"→ Vérifier query timezone"
            )
        print(f"✅ Validation OK : Min={min_price:.5f}")
    
    return df


# UTILISATION
if __name__ == "__main__":
    # Événement 01.08.2025 à 14:30 Bern
    prices = get_prices_around_event(
        date_str='2025-08-01',
        event_time_bern='14:30:00',  # ← Pas besoin de convertir !
        window_min=60
    )
    
    print(f"Lignes extraites : {len(prices)}")
    print(f"Min price : {prices['low'].min():.5f}")
    print(f"Max price : {prices['high'].max():.5f}")
    print(f"Range : {(prices['high'].max() - prices['low'].min()) * 10000:.1f} pips")
```

**Output attendu :**
```
Timezone vérifié : 2024-06-17 18:12:00+02:00
✅ Validation OK : Min=1.13918
Lignes extraites : 121
Min price : 1.13918
Max price : 1.15726
Range : 180.8 pips
```

---

### Exemple 3 : Lier événement → prix (COMPLET)

```python
def validate_event_vs_prices(date_str: str):
    """
    Valide qu'événement et prix ont même timezone
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Récupérer événements du jour
    events = conn.execute(f"""
        SELECT 
            event_title,
            ts_utc,
            actual,
            forecast
        FROM events
        WHERE DATE(ts_utc) = '{date_str}'
          AND country = 'US'
        ORDER BY ts_utc
    """).fetchdf()
    
    print(f"\n📊 Événements {date_str} :")
    for idx, row in events.iterrows():
        event_time = row['ts_utc']
        
        # 2. Extraire juste l'heure (sans timezone pour query)
        # event_time ressemble à : 2025-08-01 14:30:00+02:00
        time_str = str(event_time).split('+')[0].split(' ')[1]  # '14:30:00'
        
        print(f"\n   Event : {row['event_title']}")
        print(f"   Heure DB : {event_time}")
        print(f"   → Chercher prix à : {date_str} {time_str}+02:00")
        
        # 3. Query prix à cette heure EXACTE
        prices = conn.execute(f"""
            SELECT datetime, close
            FROM prices_1m
            WHERE datetime >= '{date_str} {time_str}+02:00'::TIMESTAMP
              AND datetime < '{date_str} {time_str}+02:00'::TIMESTAMP + INTERVAL '1 minute'
        """).fetchdf()
        
        if len(prices) > 0:
            print(f"   ✅ Prix trouvé : {prices['close'].iloc[0]:.5f}")
        else:
            print(f"   ❌ Aucun prix à cette heure")
    
    conn.close()


# TEST
validate_event_vs_prices('2025-08-01')
```

**Output attendu :**
```
📊 Événements 2025-08-01 :

   Event : Nonfarm Payrolls
   Heure DB : 2025-08-01 14:30:00+02:00
   → Chercher prix à : 2025-08-01 14:30:00+02:00
   ✅ Prix trouvé : 1.13988
```

---

## ❌ ERREURS COURANTES À ÉVITER

### Erreur #1 : Oublier +02:00 dans la query

```python
# ❌ INCORRECT
query = """
WHERE datetime >= '2025-08-01 14:30:00'  -- Manque +02:00
"""

# Résultat : Données décalées ou vides

# ✅ CORRECT
query = """
WHERE datetime >= '2025-08-01 14:30:00+02:00'  -- Avec +02:00 explicite
"""
```

---

### Erreur #2 : Convertir inutilement UTC → Bern

```python
# ❌ INCORRECT (Session 85)
event_dt_utc = datetime.strptime("2025-08-01 14:30", "%Y-%m-%d %H:%M")
event_dt_bern = event_dt_utc + timedelta(hours=2)  # Conversion inutile !
```

**Pourquoi c'est faux :** L'événement est DÉJÀ en Bern dans la DB !

```python
# ✅ CORRECT (Session 86)
event_dt_bern = datetime.strptime("2025-08-01 14:30", "%Y-%m-%d %H:%M")
# Pas de conversion, même heure pour événement et prix
```

---

### Erreur #3 : Comparer tz-aware avec tz-naive

```python
# ❌ INCORRECT
event_dt = datetime.strptime("2025-08-01 14:30", "%Y-%m-%d %H:%M")  # tz-naive
prices_df['datetime']  # tz-aware (+02:00)

# Erreur : TypeError: Cannot compare tz-naive and tz-aware

# ✅ CORRECT
import pytz
bern_tz = pytz.timezone('Europe/Zurich')
event_dt = bern_tz.localize(datetime.strptime("2025-08-01 14:30", "%Y-%m-%d %H:%M"))
```

---

### Erreur #4 : Chercher à la mauvaise heure

```python
# ❌ INCORRECT
# Événement DB : 14:30+02:00
# Chercher prix à : 12:30+02:00  # -2h → Mauvais !

# ✅ CORRECT
# Événement DB : 14:30+02:00
# Chercher prix à : 14:30+02:00  # Même heure !
```

---

## 🔍 CHECKLIST OBLIGATOIRE (5 ÉTAPES)

**AVANT TOUTE QUERY PRIX, COCHER :**

```python
# [ ] 1. INSPECTER ÉCHANTILLON
sample = conn.execute("SELECT datetime FROM prices_1m LIMIT 3").fetchdf()
print(sample)
# Vérifier : +02:00 présent ?

# [ ] 2. DOCUMENTER TIMEZONE
"""
TIMEZONE VÉRIFIÉ :
- prices_1m.datetime : +02:00 (Bern/Zurich)
- events.ts_utc : +02:00 (Bern/Zurich)
- Conversion : Aucune (même timezone)
"""

# [ ] 3. QUERY AVEC +02:00 EXPLICITE
query = f"WHERE datetime >= '{date} {time}+02:00'::TIMESTAMP"

# [ ] 4. TESTER CAS CONNU
if date == '2025-08-01' and time == '14:30:00':
    assert df['low'].min() < 1.14000, "Spike non capturé !"

# [ ] 5. VALIDER VS MT5
print(f"Range trouvé : {range_pips:.1f} pips")
print(f"Range MT5    : ~195 pips")
# Cohérent ?
```

---

## 📋 CAS D'USAGE TYPIQUES

### Cas 1 : Script Validation (validate_predictions_vs_reality.py)

```python
def extract_real_prices(date_str: str, event_time_bern: str, window_minutes: int = 60):
    """
    TIMEZONE : Bern (+02:00) pour events ET prices
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Query avec +02:00
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{date_str} {event_time_bern}+02:00'::TIMESTAMP - INTERVAL '{window_minutes} minutes'
      AND datetime <= '{date_str} {event_time_bern}+02:00'::TIMESTAMP + INTERVAL '{window_minutes} minutes'
    ORDER BY datetime
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    # Convertir pour pandas compatibility
    import pytz
    bern_tz = pytz.timezone('Europe/Zurich')
    event_dt = bern_tz.localize(
        datetime.strptime(f"{date_str} {event_time_bern}", "%Y-%m-%d %H:%M:%S")
    )
    
    return df, event_dt
```

---

### Cas 2 : Planificateur (affichage graphique)

```python
def get_prices_for_chart(event_timestamp):
    """
    event_timestamp déjà en Bern (+02:00)
    """
    # Extraire date et heure
    date_str = event_timestamp.strftime('%Y-%m-%d')
    time_str = event_timestamp.strftime('%H:%M:%S')
    
    # Query directe (même timezone)
    prices = conn.execute(f"""
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime >= '{date_str} {time_str}+02:00'::TIMESTAMP - INTERVAL '2 hours'
          AND datetime <= '{date_str} {time_str}+02:00'::TIMESTAMP + INTERVAL '2 hours'
    """).fetchdf()
    
    return prices
```

---

### Cas 3 : Analyse historique (batch)

```python
def analyze_multiple_dates(dates: list):
    """
    Traiter plusieurs dates
    """
    results = []
    
    for date_str in dates:
        # 1. Récupérer événements du jour
        events = conn.execute(f"""
            SELECT ts_utc, event_title
            FROM events
            WHERE DATE(ts_utc) = '{date_str}'
        """).fetchdf()
        
        for _, event in events.iterrows():
            # 2. Extraire heure Bern (déjà dans ts_utc)
            event_time = event['ts_utc']
            time_str = event_time.strftime('%H:%M:%S')
            
            # 3. Query prix (même heure)
            prices = conn.execute(f"""
                SELECT datetime, close
                FROM prices_1m
                WHERE datetime >= '{date_str} {time_str}+02:00'::TIMESTAMP
                  AND datetime < '{date_str} {time_str}+02:00'::TIMESTAMP + INTERVAL '1 hour'
            """).fetchdf()
            
            results.append({
                'date': date_str,
                'event': event['event_title'],
                'prices_count': len(prices)
            })
    
    return results
```

---

## 🎓 RÉSUMÉ EN 3 POINTS

1. **`events.ts_utc` et `prices_1m.datetime` = MÊME TIMEZONE (+02:00)**

2. **PAS de conversion nécessaire**  
   Event 14:30 Bern → Chercher prix 14:30+02:00

3. **TOUJOURS spécifier +02:00 dans les queries SQL**

---

## 🔧 TESTS RAPIDES

### Test 1 : Vérifier timezone table

```python
conn = duckdb.connect(str(DB_PATH), read_only=True)
sample = conn.execute("SELECT datetime FROM prices_1m LIMIT 1").fetchdf()
print(sample['datetime'].iloc[0])
# Doit afficher : ...+02:00
conn.close()
```

### Test 2 : Vérifier cohérence event → prix

```python
# Événement 01.08.2025 14:30
prices = conn.execute("""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '2025-08-01 14:25:00+02:00'
      AND datetime <= '2025-08-01 14:35:00+02:00'
""").fetchdf()

assert len(prices) > 0, "Aucun prix trouvé !"
assert prices['close'].min() < 1.14000, "Spike non capturé !"
print("✅ Tests timezone OK")
```

---

## 📞 EN CAS DE DOUTE

**Symptôme :** Aucune donnée trouvée ou données incohérentes

**Solution :**
1. Vérifier échantillon : `SELECT datetime FROM prices_1m LIMIT 3`
2. Vérifier query : `+02:00` présent ?
3. Tester cas connu : 01.08.2025 14:30 → doit trouver 1.13918

**Si toujours problème :** Relire ce guide section "Erreurs courantes"

---

*Guide créé Session 86 - 26 octobre 2025*  
*Valide pour toutes sessions futures*  
*Toujours consulter en cas de manipulation prix/événements*
