# 📊 CAS DE RÉFÉRENCE - 11 SEPTEMBRE 2025

**Date :** 11 septembre 2025  
**Source :** Graphiques MT5 d'André (valeurs confirmées)  
**Utilisation :** Validation import Dukascopy + Calibration formule V4

---

## 🎯 VALEURS DE RÉFÉRENCE (Heure Berne CEST = UTC+2)

### Point 1 : Annonce initiale - 14:30 Berne (12:30 UTC)
- **Prix :** 1.16816
- **Événements :** 15 événements simultanés dont Inflation MoM (Surprise: 33.3%)
- **Rôle :** Point de départ

### Point 2 : TTR (Time To Return) - 14:35 Berne (12:35 UTC)
- **Prix :** 1.17190
- **Rôle :** Pic du mouvement Phase 1

### Point 3 : Après pullback - 14:45 Berne (12:45 UTC)
- **Prix :** 1.16919
- **Événement :** Nouveau event Compte Courant (FAIBLE importance)
- **Rôle :** Fin du pullback

### Point 4 : Stabilisation - 15:10 Berne (13:10 UTC)
- **Prix :** 1.17378
- **Rôle :** Phase 2 stabilisée

---

## 📈 PHASES CALCULÉES

### 🚀 PHASE 1 (Annonce → TTR)
```
Période:    14:30 → 14:35 Berne (12:30 → 12:35 UTC)
Durée:      5 minutes
Départ:     1.16816
Arrivée:    1.17190
Mouvement:  +37.40 pips (UP)
```

### 📉 PULLBACK (TTR → Après nouvel event)
```
Période:    14:35 → 14:45 Berne (12:35 → 12:45 UTC)
Durée:      10 minutes
Départ:     1.17190
Arrivée:    1.16919
Mouvement:  -27.10 pips (DOWN)
Ratio:      72.5% de Phase 1
```

### 📈 PHASE 2 (Reprise → Stabilisation)
```
Période:    14:45 → 15:10 Berne (12:45 → 13:10 UTC)
Durée:      25 minutes
Départ:     1.16919
Arrivée:    1.17378
Mouvement:  +45.90 pips (UP)
```

### 📊 RÉSUMÉ GLOBAL (14:30 → 15:10)
```
Durée totale:       40 minutes
Prix départ:        1.16816
Prix stabilisation: 1.17378
Mouvement net:      +56.20 pips
```

---

## ✅ CRITÈRES DE VALIDATION DUKASCOPY

Pour valider que l'import Dukascopy est correct, on doit retrouver ces valeurs (±5 pips acceptable) :

| Moment | Heure UTC | Prix attendu | Tolérance |
|--------|-----------|--------------|-----------|
| **Annonce** | 12:30:00 | 1.16816 | ±5 pips |
| **TTR** | 12:35:00 | 1.17190 | ±5 pips |
| **Pullback** | 12:45:00 | 1.16919 | ±5 pips |
| **Stabilisation** | 13:10:00 | 1.17378 | ±5 pips |

**Phase 1 (12:30→12:35) :** 37 ±5 pips

### Critères de validation :

✅ **Validation OK :** Tous les points dans la tolérance ±5 pips  
⚠️ **Investigation :** Écarts de 5-10 pips sur plusieurs points  
❌ **Validation échouée :** Écarts >10 pips ou données manquantes

---

## 📝 SCRIPT DE VALIDATION

```python
# À exécuter dès que Dukascopy importé à 100%
import duckdb
from pathlib import Path

db_path = Path("fx_impact_app/data/warehouse.duckdb")
con = duckdb.connect(str(db_path))

# Points de validation
validation_points = [
    ("12:30:00", 1.16816, "Annonce"),
    ("12:35:00", 1.17190, "TTR"),
    ("12:45:00", 1.16919, "Pullback"),
    ("13:10:00", 1.17378, "Stabilisation")
]

results = []
for time, expected_price, label in validation_points:
    query = f"""
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime = '2025-09-11 {time}'
    """
    result = con.execute(query).fetchone()
    
    if result:
        actual_price = result[1]
        diff_pips = abs(actual_price - expected_price) * 10000
        status = "✅" if diff_pips <= 5 else ("⚠️" if diff_pips <= 10 else "❌")
        
        print(f"{status} {label} ({time}): {actual_price:.5f} vs {expected_price:.5f} ({diff_pips:.1f} pips)")
        results.append(diff_pips <= 10)
    else:
        print(f"❌ {label} ({time}): DONNÉE MANQUANTE")
        results.append(False)

# Phase 1
query_phase1 = """
    SELECT datetime, high, low, close
    FROM prices_1m
    WHERE datetime >= '2025-09-11 12:30:00'
      AND datetime < '2025-09-11 12:35:00'
    ORDER BY datetime
"""
df = con.execute(query_phase1).df()

if not df.empty:
    start = df.iloc[0]['close']
    high = df['high'].max()
    low = df['low'].min()
    phase1_pips = max((high - start) * 10000, (start - low) * 10000)
    phase1_diff = abs(phase1_pips - 37.4)
    phase1_ok = phase1_diff <= 5
    
    status = "✅" if phase1_ok else ("⚠️" if phase1_diff <= 10 else "❌")
    print(f"\n{status} Phase 1: {phase1_pips:.2f} pips vs 37.4 attendu ({phase1_diff:.1f} pips diff)")
    results.append(phase1_ok)

if all(results):
    print("\n✅✅✅ VALIDATION COMPLÈTE RÉUSSIE - Dukascopy OK ✅✅✅")
else:
    print("\n⚠️ VALIDATION PARTIELLE - Investigation nécessaire")

con.close()
```

---

## 🔴 CORRECTION HISTORIQUE

**IMPORTANT :** Les sessions précédentes mentionnaient incorrectement "522 pips" ou "600 pips" pour le 11 septembre. 

**Valeur correcte :** 37.4 pips jusqu'au TTR (Phase 1)

Cette erreur de calcul de l'ancien Claude est maintenant corrigée. Les valeurs de ce document sont les références officielles confirmées par André.

---

**Fin du document de référence**

**Date de création :** 20 octobre 2025  
**Session :** 25  
**Statut :** ✅ Validé par André
