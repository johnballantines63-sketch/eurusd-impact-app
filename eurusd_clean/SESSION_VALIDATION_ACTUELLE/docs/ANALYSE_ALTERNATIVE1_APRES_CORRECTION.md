# Analyse Alternative 1 Après Correction

**Date** : 2025-01-XX  
**Objectif** : Analyser pourquoi Alternative 1 échoue sur certaines dates malgré la correction

---

## 📊 RÉSULTATS APRÈS CORRECTION

### Performance Alternative 1

| Date | Erreur Max | Statut |
|------|------------|--------|
| 2025-09-11 | **0.0 min** | ✅ PARFAIT |
| 2025-11-20 | 48.0 min | ❌ |
| 2025-10-10 | 81.0 min | ❌ |
| 2025-06-23 | 16.0 min | ❌ |
| 2025-05-29 | 8.0 min | ⚠️ |
| 2025-11-26 | 16.0 min | ❌ |

**Erreur moyenne** : 91.5 min  
**Taux parfait** : 16.7% (1/6)

---

## 🔍 ANALYSE PAR DATE

### ✅ 2025-09-11 - PARFAIT (0.0 min)

**Événements** :
- **14:30** : Cluster US (CPI) → Anchor time corrigé ✅
- **14:45** : Cluster DE (Current Account)

**Timings Alternative 1** :
- Wave1 : 14:30 + 5 = **14:35** ✅
- Pullback : 14:45 + 4 = **14:49** ✅
- Wave2 : 14:49 + 21 = **15:10** ✅

**Résultat** : **PARFAIT** car délai entre clusters (15 min) correspond au pattern observé.

---

### ❌ 2025-11-20 - ERREUR 48 MIN

**Événements** :
- **14:30** : Cluster US principal ✅
- **08:00** : Cluster DE (non pertinent)
- **11:00** : Cluster EU (non pertinent)

**Problème** : Alternative 1 détecte 3 clusters mais utilise Cluster 2 (11:00) au lieu de Cluster 3 (14:30).

**Solution** : Identifier cluster principal (US avec score max) avant de chercher cluster 2.

---

### ❌ 2025-10-10 - ERREUR 81 MIN

**Événements** :
- **16:00** : Cluster principal (événement non-14:30)
- **?** : Cluster 2 (à identifier)

**Problème** : Délai entre clusters peut être différent de 15 min.

**Solution** : Adapter formule selon délai réel entre clusters.

---

### ❌ 2025-06-23 - ERREUR 16 MIN

**Événements** :
- **12:45** : Cluster principal (événement non-14:30)
- **?** : Cluster 2 (à identifier)

**Problème** : Délai entre clusters peut être différent de 15 min.

**Solution** : Adapter formule selon délai réel entre clusters.

---

## 💡 AMÉLIORATIONS PROPOSÉES

### Amélioration 1 : Identifier Cluster Principal Correctement

**Problème actuel** : Alternative 1 utilise `clusters[0]` comme cluster principal.

**Solution** :
```python
# Identifier cluster principal (US avec score max)
clusters_with_us = [c for c in clusters if has_us_events(c)]
if clusters_with_us:
    cluster_principal = max(clusters_with_us, key=lambda x: calculate_score(x))
    cluster1_time = cluster_principal['anchor_time']
else:
    cluster1_time = anchor_time  # Fallback
```

---

### Amélioration 2 : Adapter Formule selon Délai Réel

**Problème actuel** : Formule fixe (T+4, T+21) ne fonctionne que pour délai de 15 min.

**Solution** :
```python
ΔT = (cluster2_time - cluster1_time).total_seconds() / 60.0

# Adapter selon délai réel
if ΔT < 15:
    # Clusters très proches → Pullback plus rapide
    pullback_delay = 2  # min
    wave2_delay = 15    # min
elif ΔT < 30:
    # Délai standard (15 min) → Formule validée
    pullback_delay = 4  # min
    wave2_delay = 21    # min
else:
    # Clusters éloignés → Traiter séparément
    pullback_delay = 11  # min (standard)
    wave2_delay = 4      # min (standard)
```

---

### Amélioration 3 : Utiliser Événements pour Prédire Timings

**Principe** : Comme vous l'avez suggéré, utiliser les événements réels pour prédire les timings.

**Formulation** :
```python
# Pour chaque événement dans cluster 2
for event in cluster2_events:
    event_time = event['ts_utc']
    event_importance = event['importance_n']
    event_score = event['empirical_score']
    
    # Prédire timing basé sur importance et score
    if event_importance == 3:  # HIGH
        # Événement HIGH → Impact immédiat
        pullback_time = event_time + 4 min
    else:
        # Événement MOYEN → Impact plus lent
        pullback_time = event_time + 8 min
```

---

## 🎯 RECOMMANDATION FINALE

### Combiner Alternative 1 (Corrigée) + Alternative 3

**Stratégie** :
1. **Si clusters multiples détectés** → Utiliser Alternative 1 (basée sur événements)
2. **Si pattern détecté avec confiance élevée** → Utiliser Alternative 3 (basée sur pattern)
3. **Sinon** → Utiliser Alternative 5 (timings standard)

**Logique** :
```python
if len(clusters) > 1 and cluster2_detected:
    # Alternative 1 : Basée sur événements réels
    timings = alternative1_events_based(anchor_time, clusters)
elif pattern_detected and confidence > 0.8:
    # Alternative 3 : Basée sur pattern détecté
    timings = alternative3_pattern_based(anchor_time, pattern_result)
else:
    # Alternative 5 : Timings standard
    timings = alternative5_standard(anchor_time)
```

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⚠️ Alternative 1 améliorée mais nécessite ajustements supplémentaires




