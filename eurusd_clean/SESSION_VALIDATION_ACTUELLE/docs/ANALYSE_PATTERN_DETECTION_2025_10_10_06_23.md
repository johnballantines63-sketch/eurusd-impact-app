# Analyse Détection Pattern - 2025-10-10 et 2025-06-23

**Date** : 2025-01-XX  
**Problème** : Patterns non détectés pour ces dates  
**Objectif** : Comprendre pourquoi et proposer solution

---

## 🔍 PROBLÈME IDENTIFIÉ

### 2025-10-10

**Cluster détecté** :
- Anchor time : 16:00:00 (événements Michigan)
- Nombre événements : 4
- Événements : Michigan Consumer Sentiment, Expectations, etc. (score 30.2)

**Pattern détection** :
- Baseline : 1.15694 @ 15:59
- Wave1 : 8.2 pips (peak @ 16:10)
- Pullback1 : -12.0 pips (ratio 146.3%) ❌
- Wave2 : 61.4 pips (peak @ 17:36)
- Pullback2 : -22.2 pips (ratio 36.2%)
- **Pattern rejeté** : Pullback ratio > 100% (146.3%)

**Cause** : Pullback1 va sous la baseline → Impossible selon logique actuelle

---

### 2025-06-23

**Cluster détecté** :
- Anchor time : 12:45:00 (événements EU)
- Nombre événements : 4
- Événements : EU Bond Auction (score 11.2)

**Pattern détection** :
- Baseline : 1.14666 @ 12:44
- Wave1 : 1.8 pips (peak @ 12:50)
- Pullback1 : -8.8 pips (ratio 488.9%) ❌
- Wave2 : 6.3 pips (peak @ 13:16)
- Pullback2 : -7.5 pips (ratio 119.0%)
- **Pattern rejeté** : Pullback ratio > 100% (488.9%)

**Cause** : Pullback1 va largement sous la baseline → Impossible selon logique actuelle

---

## 📊 ANALYSE ROOT CAUSE

### Problème 1 : Anchor Time Non Standard

**Observation** :
- 2025-10-10 : Anchor time 16:00 (au lieu de 14:30)
- 2025-06-23 : Anchor time 12:45 (au lieu de 14:30)

**Cause** :
- Pas d'événements US HIGH impact (score > 50) à 14:30 pour ces dates
- Code ajuste anchor_time uniquement si événement US HIGH impact autour de 14:30
- Pour ces dates, anchor_time reste celui du premier événement du cluster

**Impact** :
- Détection pattern utilise anchor_time réel (16:00, 12:45) ✅
- Mais baseline peut être incorrecte si calculée pour 14:30

---

### Problème 2 : Pullback Ratio > 100%

**Observation** :
- Pullback ratio > 100% indique que le prix retombe sous la baseline
- Cela est considéré comme "impossible" dans la logique actuelle

**Causes possibles** :
1. **Baseline incorrecte** : Baseline calculée à partir d'un prix trop élevé
2. **Mouvement réel faible** : Le mouvement est réellement faible, pas de pattern DOUBLE_WAVE
3. **Mouvement dans direction opposée** : Le mouvement va dans la direction opposée à celle attendue

**Pour 2025-10-10** :
- Baseline : 1.15694 @ 15:59
- Peak1 : 1.15776 @ 16:10 (+8.2 pips)
- Pullback1 : 1.15656 @ 16:18 (-12.0 pips, sous baseline)
- → Le prix retombe sous la baseline après le peak1

**Pour 2025-06-23** :
- Baseline : 1.14666 @ 12:44
- Peak1 : 1.14684 @ 12:50 (+1.8 pips)
- Pullback1 : 1.14578 @ 12:56 (-8.8 pips, largement sous baseline)
- → Le prix retombe largement sous la baseline après le peak1

---

## 💡 SOLUTIONS PROPOSÉES

### Solution 1 : Ajuster Logique Pullback Ratio

**Problème actuel** : Pullback ratio > 100% → Pattern rejeté

**Solution proposée** : Accepter pullback ratio > 100% si :
1. Le mouvement est réellement faible (peak1 < 10 pips)
2. Le pullback est dans la direction opposée (mouvement inverse)

**Code proposé** :
```python
# Accepter pullback ratio > 100% si mouvement faible
if pullback_ratio > 1.0:
    if wave1_pips < 10:
        # Mouvement faible, accepter pattern
        pass
    else:
        # Mouvement significatif mais pullback > 100% → Rejeter
        return None
```

---

### Solution 2 : Utiliser SINGLE_WAVE au lieu de DOUBLE_WAVE

**Problème actuel** : Tentative de détecter DOUBLE_WAVE même si mouvement faible

**Solution proposée** : Si pullback ratio > 100% et mouvement faible, détecter SINGLE_WAVE

**Code proposé** :
```python
if pullback_ratio > 1.0 and wave1_pips < 10:
    # Détecter SINGLE_WAVE au lieu de DOUBLE_WAVE
    pattern_type = 'SINGLE_WAVE'
    pattern_impact = wave2_pips  # Utiliser wave2 comme impact final
```

---

### Solution 3 : Ajuster Baseline pour Anchor Time Non Standard

**Problème actuel** : Baseline calculée pour 14:30 même si anchor_time différent

**Solution proposée** : Utiliser baseline_mode adaptatif selon anchor_time

**Code proposé** :
```python
# Si anchor_time autour de 14:30, utiliser prev_close_14_29
# Sinon, utiliser local_minmax
if anchor_time.hour == 14 and 25 <= anchor_time.minute <= 35:
    baseline_mode = 'prev_close_14_29'
else:
    baseline_mode = 'local_minmax'
```

---

## 🎯 RECOMMANDATION

### Pour 2025-10-10

**Observation** :
- Impact réel : 12.30 pips (faible)
- Pattern détecté : Wave2 = 61.4 pips (trop élevé)
- Prédiction formules : 33.94 pips (trop élevé)

**Conclusion** : Le mouvement réel est faible, pas de pattern DOUBLE_WAVE significatif

**Solution recommandée** : Accepter pattern SINGLE_WAVE avec impact faible

---

### Pour 2025-06-23

**Observation** :
- Impact réel : 76.50 pips (modéré)
- Pattern détecté : Wave2 = 6.3 pips (trop faible)
- Prédiction formules : nan (surprise 0%)

**Conclusion** : Le mouvement réel est modéré mais pattern non détecté correctement

**Solution recommandée** : Ajuster baseline ou accepter pullback ratio > 100% pour mouvements faibles

---

## ✅ CONCLUSION

**Problème principal** : Pullback ratio > 100% pour mouvements faibles

**Solutions** :
1. ✅ Ajuster logique pullback ratio pour accepter mouvements faibles
2. ✅ Détecter SINGLE_WAVE au lieu de DOUBLE_WAVE si mouvement faible
3. ✅ Ajuster baseline selon anchor_time réel

**Action requise** : Implémenter Solution 2 (SINGLE_WAVE pour mouvements faibles)

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Analyse complète, solutions proposées




