# Exemples Dates - Stratégie Hybride

**Date** : 2025-01-XX  
**Objectif** : Fournir des exemples concrets de dates pour chaque cas de la stratégie hybride

---

## 🎯 STRATÉGIE HYBRIDE PROPOSÉE

### CAS 1 : Clusters Multiples avec Délai ~15 min → Alternative 1

**Critères** :
- 2+ clusters détectés
- Cluster principal (US) à 14:30
- Cluster 2 (DE/EU) à 14:45 (±5 min)
- Délai entre clusters : 10-20 min

**Alternative utilisée** : Alternative 1 (basée sur événements réels)

**Formule** :
```
Wave1 = Cluster1 (14:30) + 5 min = 14:35
Pullback = Cluster2 (14:45) + 4 min = 14:49
Wave2 = Pullback (14:49) + 21 min = 15:10
```

**Exemples de dates** :
- **2025-09-11** ✅ (si anchor_time corrigé à 14:30)
  - Cluster 1 : 14:30 (US CPI)
  - Cluster 2 : 14:45 (DE Current Account)
  - ΔT = 15 min → **CAS 1**

---

### CAS 2 : Pattern Détecté avec Confiance Élevée → Alternative 3

**Critères** :
- Pattern DOUBLE_WAVE détecté dans les prix
- Confiance > 80%
- Utiliser timings réels du pattern détecté

**Alternative utilisée** : Alternative 3 (basée sur pattern détecté)

**Exemples de dates** :
- **2025-11-20** ✅
  - Pattern détecté : Oui
  - Confiance : 85.0%
  - → **CAS 2**

- **2025-06-23** ✅
  - Pattern détecté : Oui
  - Confiance : 85.0%
  - → **CAS 2**

- **2025-10-10** ⚠️
  - Pattern détecté : Oui
  - Confiance : 75.0% (< 80%)
  - → **CAS 3** (confiance trop faible)

---

### CAS 3 : Autres Cas → Alternative 5 (Timings Standard)

**Critères** :
- Pas de clusters multiples avec délai standard
- Pattern non détecté OU confiance faible (< 80%)
- Utiliser timings standard Session 64

**Alternative utilisée** : Alternative 5 (timings standard)

**Formule** :
```
Wave1 = Anchor_time + 5 min
Pullback = Anchor_time + 11 min
Wave2 = Anchor_time + 15 min
```

**Exemples de dates** :
- **2025-10-10** ⚠️
  - Clusters multiples mais délai non standard (ΔT = 180 min)
  - Pattern détecté mais confiance faible (75%)
  - → **CAS 3**

- **2025-05-29** ⚠️
  - Clusters multiples mais délai non standard (ΔT = 60 min)
  - Pattern détecté mais confiance limite (80%)
  - → **CAS 3** (ou CAS 2 si on accepte 80%)

- **2025-11-26** ⚠️
  - Clusters multiples mais délai non standard (ΔT = 90 min)
  - Pattern détecté avec confiance élevée (95%)
  - → **CAS 2** (confiance > 80%)

---

## 📊 RÉSUMÉ PAR DATE

| Date | Clusters | ΔT (min) | Pattern | Confiance | CAS | Alternative |
|------|----------|----------|---------|----------|-----|-------------|
| **2025-09-11** | 2 | 30* | Oui | 95% | **1** | **Alternative 1** |
| **2025-11-20** | 3 | - | Oui | 85% | **2** | **Alternative 3** |
| **2025-10-10** | 3 | 180 | Oui | 75% | **3** | **Alternative 5** |
| **2025-06-23** | 4 | - | Oui | 85% | **2** | **Alternative 3** |
| **2025-05-29** | 7 | 60 | Oui | 80% | **2/3** | **Alternative 3/5** |
| **2025-11-26** | 10 | 90 | Oui | 95% | **2** | **Alternative 3** |

*Note : Pour 2025-09-11, ΔT réel entre 14:30 (US) et 14:45 (DE) = 15 min, mais détecté comme 30 min car cluster principal à 14:15.

---

## 🔍 CAS SPÉCIAUX

### CAS 1B : Clusters Multiples mais Délai Non Standard

**Dates** :
- **2025-09-11** : ΔT = 30 min (devrait être 15 min si anchor_time corrigé)
- **2025-10-10** : ΔT = 180 min (3 heures)
- **2025-05-29** : ΔT = 60 min (1 heure)
- **2025-11-26** : ΔT = 90 min (1.5 heures)

**Solution proposée** :
- Si ΔT < 30 min → Utiliser Alternative 1 avec formule adaptée
- Si ΔT ≥ 30 min → Utiliser Alternative 3 (pattern) si confiance élevée, sinon Alternative 5

---

## 💡 RECOMMANDATION FINALE

### Stratégie Hybride Améliorée

```python
def select_alternative(date_str, clusters, pattern_result, anchor_time):
    # CAS 1 : Clusters multiples avec délai standard (10-20 min)
    if len(clusters) > 1:
        cluster2 = find_cluster2(clusters, anchor_time)
        if cluster2:
            ΔT = (cluster2['anchor_time'] - anchor_time).total_seconds() / 60.0
            if 10 <= ΔT <= 20:
                return "ALTERNATIVE_1"  # Basée sur événements
    
    # CAS 2 : Pattern détecté avec confiance élevée (> 80%)
    if pattern_result and pattern_result.get('double_wave', False):
        confidence = pattern_result.get('confidence', 0.0)
        if confidence > 80:
            return "ALTERNATIVE_3"  # Basée sur pattern
    
    # CAS 3 : Fallback timings standard
    return "ALTERNATIVE_5"  # Timings standard
```

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Classification terminée, exemples identifiés




