# ✅ CAS DE RÉFÉRENCE - 11 SEPTEMBRE 2025

**Validation obligatoire avant tout calcul**

---

## 📊 DONNÉES VALIDÉES

| Métrique | Valeur | Tolérance |
|----------|--------|-----------|
| **Date** | 2025-09-11 | Exact |
| **Heure UTC** | 12:30:00 | Exact |
| **Heure Berne** | 14:30:00 (CEST) | +02:00 |
| **Phase 1** | 33.7 pips | ±5 pips (28-42) |
| **Prix départ** | 1.16874 | ±0.0005 |
| **Prix TTR** | 1.17211 | ±0.001 |
| **Direction** | UP | Exact |
| **TTR** | 5 minutes | ±2 min |

---

## 🎯 VALIDATION

### Dans `prices_1m`

```sql
SELECT datetime, open FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00'
AND datetime <= '2025-09-11 12:35:00'
ORDER BY datetime LIMIT 1
```

**Résultat attendu :** `open ≈ 1.16874`

### Dans `event_impacts_v2`

```sql
SELECT ts_utc, phase1_pips, start_price
FROM event_impacts_v2
WHERE ts_utc::DATE = '2025-09-11'
AND EXTRACT(HOUR FROM ts_utc) = 12
ORDER BY phase1_pips DESC LIMIT 1
```

**Résultat attendu :** `phase1_pips ≈ 33.7 pips`

---

## 🔍 CRITÈRES DE SUCCÈS

- ✅ **EXCELLENT** : Écart < 5 pips (28-38 pips)
- ⚠️  **ACCEPTABLE** : Écart 5-10 pips (23-43 pips)
- ❌ **PROBLÈME** : Écart > 10 pips → STOP et investiguer

---

## 💻 CODE VALIDATION

```python
def validate_11_septembre(con):
    """Valide le cas référence"""
    query = """
    SELECT phase1_pips, start_price
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    AND EXTRACT(HOUR FROM ts_utc) = 12
    ORDER BY phase1_pips DESC LIMIT 1
    """
    
    result = con.execute(query).fetchone()
    
    if result is None:
        raise ValueError("11 sept introuvable")
    
    phase1, start = result
    
    # Validation Phase 1
    if not (28 <= phase1 <= 42):
        raise ValueError(f"Phase 1: {phase1:.2f} (attendu 33-37)")
    
    # Validation prix
    if abs(start - 1.16874) > 0.001:
        raise ValueError(f"Prix: {start:.5f} (attendu 1.16874)")
    
    print(f"✅ Validation OK: {phase1:.2f} pips")
    return True
```

---

**FIN DOCUMENT**
