# Cause Racine : Baseline Incorrect pour Pic Absolu Étendu

**Date** : 2025-01-XX  
**Statut** : ✅ Cause identifiée

---

## 🔍 PROBLÈME IDENTIFIÉ

### Pour 2025-05-29

**Pipeline** :
- `baseline_price_pattern = 1.13698` (depuis pattern réel détecté)
- `peak_absolute_price = 1.13848`
- `wave2_absolute_extended = (1.13848 - 1.13698) * 10000 = 15.00 pips` ❌

**Investigation** :
- `baseline_price_pattern = 1.12954` (correct)
- `peak_absolute_price = 1.13698`
- `wave2_absolute_extended = (1.13698 - 1.12954) * 10000 = 74.40 pips` ✅

**Différence** : Le baseline utilisé dans le pipeline (1.13698) est **différent** de celui utilisé dans l'investigation (1.12954).

---

## 🔴 CAUSE RACINE

### Détection Pattern Réel avec Mauvais Baseline

Le pipeline appelle `detect_for_date_duckdb_rev12()` avec :
- `baseline_mode='prev_close_14_29'` (ligne 1900)
- `event_time=anchor_time` (ligne 1904)

**Pour 2025-05-29** :
- `anchor_time = 18:00` (depuis cluster)
- `baseline_mode='prev_close_14_29'` cherche le CLOSE de la bougie à 14:29
- Mais le pattern réel détecté utilise un baseline différent (1.13698 à 17:59)

**Problème** :
- Le baseline du pattern réel (1.13698) est calculé à partir d'une détection à 17:59
- Mais le baseline correct pour mesurer l'impact devrait être à 14:29 (1.12954)

---

## ✅ SOLUTION

### Option 1 : Utiliser Baseline Correct pour Pic Absolu Étendu

Au lieu d'utiliser `baseline_price_pattern` du pattern réel, utiliser le baseline correct (OPEN de la première bougie après l'événement) :

```python
# Au lieu de :
baseline_price_pattern = pattern_real_result.get('baseline_price', 0.0)

# Utiliser :
prices_at_event = df_extended[df_extended.index >= anchor_time]
if not prices_at_event.empty:
    baseline_price_correct = prices_at_event.iloc[0]['open']
    wave2_absolute_extended = (peak_absolute_price - baseline_price_correct) * 10000
```

### Option 2 : Corriger Baseline du Pattern Réel

Modifier la détection du pattern réel pour utiliser le bon baseline (`prev_close_14_29` pour événements à 14:30, ou OPEN de la première bougie après l'événement).

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Implémenter Option 1 (utiliser baseline correct pour pic absolu étendu)
2. ⏳ Tester sur 2025-05-29 et 2025-06-23
3. ⏳ Vérifier que `wave2_peak_pips_absolute = 74.40` au lieu de 15.00

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Cause identifiée, solution proposée




