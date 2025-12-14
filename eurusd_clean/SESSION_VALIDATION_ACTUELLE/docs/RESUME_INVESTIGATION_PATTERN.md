# Résumé Investigation : Pattern Prédit vs Pattern Réel

**Date** : 2025-01-XX  
**Statut** : ✅ Investigation complète, correction en cours

---

## 📊 RÉPONSE À LA QUESTION

**Question** : Le pattern utilisé est-il prédit ou comment est-il déterminé ?

**Réponse** : Le pipeline utilise **DEUX sources** pour déterminer le pattern :

1. **Pattern Réel** : **DÉTECTÉ** depuis les prix historiques (méthode préférée)
   - Fonction : `detect_for_date_duckdb_rev12()`
   - Source : Prix historiques M1 depuis `prices_finnhub_m1`
   - Méthode : Analyse des prix réels, détection des pics/creux, mesure des amplitudes réelles

2. **Pattern Prédit** : **PRÉDIT** avec formules (fallback)
   - Fonction : `predict_double_wave_timeline_s64()`
   - Source : Formules et calculs basés sur événements
   - Méthode : Calcule `base_impact * amplification`, applique des ratios fixes, utilise des timings fixes

---

## 🔍 PROBLÈME IDENTIFIÉ

### Pour 2025-05-29

**Symptôme** :
- `wave2_peak_pips_absolute = 15.00` pips (incorrect)
- Impact réel mesuré : **74.40 pips** (correct)

**Cause Racine** :
- Le baseline utilisé pour calculer le pic absolu étendu était incorrect
- `baseline_price_pattern = 1.13698` (depuis pattern réel détecté à 17:59)
- Baseline correct : `1.12954` (OPEN première bougie après événement à 14:30)
- Avec baseline incorrect : `(1.13848 - 1.13698) * 10000 = 15.00 pips` ❌
- Avec baseline correct : `(1.13698 - 1.12954) * 10000 = 74.40 pips` ✅

---

## ✅ CORRECTION IMPLÉMENTÉE

### Solution

Utiliser le baseline correct (OPEN de la première bougie après l'événement) au lieu du baseline du pattern réel :

```python
# Au lieu de :
baseline_price_pattern = pattern_real_result.get('baseline_price', 0.0)
wave2_absolute_extended = (peak_absolute_price - baseline_price_pattern) * 10000

# Utiliser :
prices_at_event = df_extended[df_extended.index >= anchor_time]
baseline_price_correct = prices_at_event.iloc[0]['open']
wave2_absolute_extended = (peak_absolute_price - baseline_price_correct) * 10000
```

**Statut** : ✅ Correction implémentée, tests en cours

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Tester la correction sur 2025-05-29 et 2025-06-23
2. ⏳ Vérifier que `wave2_peak_pips_absolute = 74.40` au lieu de 15.00
3. ⏳ Retirer les logs DEBUG une fois validé

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Investigation complète, correction implémentée




