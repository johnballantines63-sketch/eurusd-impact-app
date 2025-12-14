# SPÉCIFICATIONS INTÉGRATION SESSION 114

**Date:** 06 novembre 2025  
**Objectif:** Intégrer cluster_impact_calculator.py dans Planificateur V2  
**Tokens:** ~120,000 / 190,000 (63%)

---

## 🎯 OBJECTIF SESSION 114

Remplacer les ratios hardcodés du Planificateur par les calculs réels de Session 113.

### **CAS RÉFÉRENCE 11 SEPTEMBRE 2025**

```
Timeline réelle à reproduire:

14:30:00 → Cluster 1 (9 events CPI+Jobless)
           Impact calculé: 37.37 pips ✅ (Session 113)
           Impact réel MT5: 37.3 pips
           MAE: 0.07 pips

14:35:00 → PIC 1 = 37.3 pips (TTR validé)

14:35-49 → PULLBACK = -26.8 pips (72%)

14:45:00 → Event isolé (Current Account)
           PENDANT pullback Cluster 1
           Contribution: ~18-19 pips

14:49:00 → CREUX = 10.5 pips du départ

14:49-15:10 → REPRISE FORTE (propulsée par event 14:45)

15:10:00 → PIC 2 FINAL = 56.2 pips ✅
           Impact TOTAL = 37.37 + ~18.83 = 56.2 pips
```

---

## 📋 MODIFICATIONS NÉCESSAIRES

### **1. Imports (FAIT ✅)**

```python
# Ajouter après imports Single Wave
from core.cluster_impact_calculator import (
    calculate_cluster_impact,
    calculate_cluster_ttr,
    calculate_pullback_characteristics,
    analyze_cluster_pattern
)
```

### **2. Fonction Déduplication RÈGLE 0**

```python
def deduplicate_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    RÈGLE 0 Session 113: Exclure événements sans estimate.
    
    Example 11 sept:
    - Avant: 10 events
    - Après: 9 events (exclude 'real earnings_mom' sans estimate)
    """
    has_estimate = events_df['estimate'].notna()
    events_clean = events_df[has_estimate].copy()
    
    n_removed = len(events_df) - len(events_clean)
    if n_removed > 0:
        st.write(f"   🔧 RÈGLE 0: {n_removed} event(s) sans estimate exclu(s)")
    
    return events_clean
```

### **3. Fonction Groupement Clusters**

```python
def group_events_into_clusters(events_df: pd.DataFrame, 
                                tolerance_minutes: int = 5) -> List[Dict]:
    """
    Groupe événements en clusters temporels.
    
    Example 11 sept:
    - Cluster 1 (14:30): indices [0-8] = 9 events
    - Cluster 2 (14:45): indices [9] = 1 event
    
    Returns:
        [
            {'time': datetime(14:30), 'events_indices': [0,1,2,3,4,5,6,7,8]},
            {'time': datetime(14:45), 'events_indices': [9]}
        ]
    """
    if events_df.empty:
        return []
    
    events_df = events_df.copy()
    events_df['timestamp'] = pd.to_datetime(events_df['ts_utc'])
    events_df = events_df.sort_values('timestamp').reset_index(drop=True)
    
    clusters = []
    current_cluster = {
        'time': events_df.iloc[0]['timestamp'],
        'events_indices': [0]
    }
    
    for i in range(1, len(events_df)):
        current_time = events_df.iloc[i]['timestamp']
        cluster_time = current_cluster['time']
        diff_minutes = (current_time - cluster_time).total_seconds() / 60
        
        if diff_minutes <= tolerance_minutes:
            current_cluster['events_indices'].append(i)
        else:
            clusters.append(current_cluster)
            current_cluster = {
                'time': current_time,
                'events_indices': [i]
            }
    
    clusters.append(current_cluster)
    return clusters
```

### **4. Fonction calculate_predictions() NOUVELLE**

```python
def calculate_predictions(events_df: pd.DataFrame) -> dict:
    """
    Calcule prédictions avec cluster_impact_calculator (Session 113).
    """
    if events_df.empty:
        return None
    
    # ÉTAPE 1: Déduplication RÈGLE 0
    events_clean = deduplicate_events(events_df)
    
    # ÉTAPE 2: Groupement clusters
    clusters = group_events_into_clusters(events_clean, tolerance_minutes=5)
    st.write(f"🔍 Détecté: {len(clusters)} cluster(s)")
    
    # ÉTAPE 3: Calculer impact CHAQUE cluster
    clusters_impacts = []
    clusters_details = []
    
    for idx, cluster_info in enumerate(clusters, 1):
        cluster_events = events_clean.iloc[cluster_info['events_indices']]
        
        # Calculer avec Session 113
        impact_result = calculate_cluster_impact(
            cluster_events,
            amplification=2.8  # Validé Session 113
        )
        
        ttr_result = calculate_cluster_ttr(
            impact_result,
            impact_result['latency_median']
        )
        
        st.write(f"   📊 Cluster {idx} ({cluster_info['time'].strftime('%H:%M')}): "
                f"{len(cluster_events)} event(s) → {impact_result['impact_pips']:.1f} pips")
        
        clusters_impacts.append(impact_result)
        clusters_details.append({
            'index': idx,
            'time': cluster_info['time'],
            'num_events': len(cluster_events),
            'impact_pips': impact_result['impact_pips'],
            'ttr_minutes': ttr_result,
            'events': cluster_events
        })
    
    # ÉTAPE 4: Détecter pattern
    pattern_result = analyze_cluster_pattern(clusters, clusters_impacts)
    st.write(f"🎯 Pattern: **{pattern_result['pattern_type']}**")
    
    # ÉTAPE 5: Calculer impact TOTAL
    primary_idx = pattern_result['primary_cluster_index']
    primary_impact = clusters_details[primary_idx]['impact_pips']
    
    if pattern_result['pattern_type'] == 'overlapping':
        # Pullback du cluster primaire
        pullback_result = calculate_pullback_characteristics(
            peak_impact=primary_impact,
            peak_surprise=clusters_impacts[primary_idx]['max_surprise'],
            num_events=clusters_details[primary_idx]['num_events'],
            has_following_cluster=True,
            minutes_to_next_cluster=15
        )
        
        pullback_pips = pullback_result['pullback_pips']
        
        # Contribution secondaire
        secondary_contribution = sum(
            clusters_details[i]['impact_pips'] 
            for i in pattern_result['secondary_clusters']
        )
        
        # TOTAL = Primary - Pullback + Secondary
        impact_total = primary_impact - pullback_pips + secondary_contribution
        
        st.write(f"   📈 Calcul TOTAL overlapping:")
        st.write(f"      • Cluster primaire: +{primary_impact:.1f} pips")
        st.write(f"      • Pullback: -{pullback_pips:.1f} pips")
        st.write(f"      • Contribution secondaire: +{secondary_contribution:.1f} pips")
        st.write(f"      • **TOTAL: {impact_total:.1f} pips**")
    else:
        impact_total = primary_impact
        pullback_pips = primary_impact * 0.15
    
    # RETOUR
    return {
        'impact_pips': impact_total,
        'impact_primary_cluster': primary_impact,
        'ttr_minutes': clusters_details[primary_idx]['ttr_minutes'],
        'pullback_pips': pullback_pips,
        'num_clusters': len(clusters),
        'clusters_details': clusters_details,
        'pattern_type': pattern_result['pattern_type'],
        'pattern_confidence': pattern_result['confidence'],
        # Compatibilité ancienne interface
        'num_events': len(events_clean),
        'base_score_avg': clusters_impacts[0]['base_score'],
        'adjusted_score': clusters_impacts[0]['adjusted_score'],
        'max_surprise': clusters_impacts[0]['max_surprise'],
        'events': events_clean,
        'movement_type': pattern_result['pattern_type'].title(),
        'is_single_wave_strong': False,
        'is_double_wave': False
    }
```

---

## ✅ RÉSULTATS ATTENDUS 11 SEPTEMBRE

Après modification, le Planificateur devrait afficher :

```
🔍 Détecté: 2 cluster(s)

   📊 Cluster 1 (14:30): 9 event(s) → 37.4 pips
   📊 Cluster 2 (14:45): 1 event(s) → 18.8 pips

🎯 Pattern: **Overlapping**

   📈 Calcul TOTAL overlapping:
      • Cluster primaire: +37.4 pips
      • Pullback: -26.9 pips
      • Contribution secondaire: +18.8 pips
      • **TOTAL: 56.3 pips**

Validation MT5:
✅ Cluster 1: MAE 0.1 pips (37.4 vs 37.3)
✅ TOTAL: MAE 0.1 pips (56.3 vs 56.2)
```

---

## 🔧 INSTRUCTIONS EXÉCUTION

1. **Lancer script intégration** :
   ```bash
   cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
   python scripts/session114/integrate_cluster_calculator.py
   ```

2. **Relancer Streamlit** :
   ```bash
   streamlit run streamlit_app/pages/2_Planificateur_V2.py
   ```

3. **Tester 11 septembre 2025**

4. **Si problème, restaurer backup** :
   ```bash
   cp streamlit_app/pages/backups/2_Planificateur_V2_backup_session114_*.py streamlit_app/pages/2_Planificateur_V2.py
   ```

---

## 📊 CHECKLIST VALIDATION

- [ ] Planificateur démarre sans erreur
- [ ] Date 11 sept sélectionnée
- [ ] Déduplication appliquée (9 events au lieu de 10)
- [ ] 2 clusters détectés (14:30 et 14:45)
- [ ] Cluster 1 : ~37.4 pips
- [ ] Cluster 2 : ~18-19 pips
- [ ] Pattern overlapping détecté
- [ ] Impact TOTAL : ~56.2 pips
- [ ] MAE Cluster 1 < 1 pip
- [ ] MAE TOTAL < 1 pip

---

**Auteur:** André Valentin avec Claude  
**Session:** 114  
**Tokens restants:** ~70,000
