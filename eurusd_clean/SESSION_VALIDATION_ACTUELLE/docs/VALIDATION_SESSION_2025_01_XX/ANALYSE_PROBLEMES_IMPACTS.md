# Analyse Problèmes Impacts Prédits

**Date** : 2025-01-XX  
**Problème** : Erreurs importantes pour 2025-11-26, 2025-10-10, 2025-06-23

---

## 🔍 PROBLÈMES IDENTIFIÉS

### 1. 2025-11-26

**CSV indique** :
- Pattern: `SINGLE_WAVE_STANDARD`
- Impact réel: 34.4 pips
- Pic réel: 15:01

**Pipeline détecte** :
- Pattern: `DOUBLE_WAVE` ✅ (corrigé par fallback)
- Impact réel mesuré: 202.66 pips ❌ (très différent de 34.4 pips)
- Wave1: 23.9 pips, Wave2: 34.4 pips (Wave2 correspond au CSV)

**Problème** : L'impact réel mesuré (202.66 pips) est calculé incorrectement. Il devrait être 34.4 pips (Wave2).

---

### 2. 2025-10-10

**CSV indique** :
- Pattern: `DOUBLE_WAVE`
- Impact réel: 56.7 pips
- Mouvement commence: **16:10** (pas 14:30 !)
- Wave1: 47.5 pips, Wave2: 17.2 pips

**Pipeline détecte** :
- Pattern: `DOUBLE_WAVE` ✅
- Impact réel mesuré: 6.26 pips ❌ (très différent de 56.7 pips)
- Wave1: 4.7 pips, Wave2: 12.2 pips
- Baseline: 14:29 (incorrect, devrait être 16:09)

**Problème** : Le détecteur utilise 14:30 comme heure de référence, alors que l'événement réel est à **16:10**. Le pattern détecté est donc incorrect.

---

### 3. 2025-06-23

**CSV indique** :
- Pattern: `DOUBLE_WAVE`
- Impact réel: 83.9 pips
- Mouvement commence: **15:47** (pas 14:30 !)
- Wave1: 49.4 pips, Wave2: 17.1 pips

**Pipeline détecte** :
- Pattern: `DOUBLE_WAVE` ✅ (grâce au fallback CSV)
- Impact réel mesuré: 4.39 pips ❌ (très différent de 83.9 pips)
- Wave1: 5.6 pips, pas de Wave2 détecté
- Baseline: 14:29 (incorrect, devrait être 15:46)

**Problème** : Le détecteur utilise 14:30 comme heure de référence, alors que l'événement réel est à **15:47**. Le pattern détecté est donc incorrect.

---

## ✅ SOLUTION PROPOSÉE

### Modifier le détecteur pour utiliser l'anchor_time réel

**Problème principal** : Le détecteur `detect_for_date_duckdb_rev12` force toujours 14:30 comme heure de référence, même si l'événement réel est à une heure différente.

**Solution** : Modifier `detect_for_date_duckdb_rev12` pour accepter un paramètre `event_time` ou `hint_ts` qui utilise l'`anchor_time` réel au lieu de toujours forcer 14:30.

**Code à modifier** :
```python
# Dans scripts/session120/double_wave_detector_rev12.py, ligne 93
# Avant :
hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)

# Après :
if event_time is not None:
    hint_ts = pd.Timestamp(event_time, tz=tz)
else:
    # Fallback : utiliser 14:30 par défaut
    hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)
```

**Dans le pipeline** :
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
    event_time=anchor_time  # NOUVEAU : Passer l'anchor_time réel
)
```

---

## 📝 IMPACT ATTENDU

Avec cette correction :
- **2025-10-10** : Pattern détecté correctement à partir de 16:10 → Impact réel mesuré correct
- **2025-06-23** : Pattern détecté correctement à partir de 15:47 → Impact réel mesuré correct
- **2025-11-26** : Vérifier pourquoi l'impact réel mesuré est 202.66 pips au lieu de 34.4 pips

---

**Status** : ⚠️ **PROBLÈMES IDENTIFIÉS - SOLUTION PROPOSÉE**

