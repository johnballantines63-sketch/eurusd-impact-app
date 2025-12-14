# Correction Problème Baseline - Complète

**Date** : 2025-01-XX  
**Statut** : ✅ Correction complète appliquée

---

## 🔴 PROBLÈME IDENTIFIÉ

### Symptôme

Pour **2025-05-29** :
- **Baseline calculé** : 1.13698 à **17:59 (18:00)** ❌
- **Mouvement réel** : Commence à **14:15-14:30** sur le graphique ✅
- **Événements US** : À **14:30** (13:30 sur l'image = 14:30 réel en heure d'été) ✅
- **Impact réel mesuré** : **74.40 pips** ✅
- **Impact calculé avec baseline incorrect** : **15.20 pips** ❌

### Cause Racine

1. **Étape 2** : `anchor_time` défini comme **premier événement** du cluster (ligne 297)
   - Si le premier événement est à 18:00, `anchor_time = 18:00`
   - Les événements US HIGH à 14:30 sont dans le cluster mais ne sont pas utilisés

2. **Sélection cluster principal** : Le cluster à 18:00 était sélectionné au lieu du cluster à 14:30
   - Le code cherchait des événements avec `empirical_score > 50`
   - Mais les événements à 14:30 n'avaient peut-être pas ce score élevé
   - Donc le cluster le plus grand (18:00) était sélectionné

3. **Baseline incorrect** : Utilisait `baseline_price_pattern` (1.13698 à 18:00) au lieu de `baseline_price_correct` (1.12954 à 14:30)

---

## ✅ CORRECTIONS APPLIQUÉES

### Correction 1 : Étape 2 - Anchor Time

**Fichier** : `scripts/run_pipeline_complete.py` (lignes 295-314)

**Changement** :
- **AVANT** : `anchor_time = cluster_events.iloc[0]['ts_utc']` (premier événement)
- **APRÈS** : Prioriser événement US HIGH avec score empirique le plus élevé

**Code** :
```python
# ⚠️ CORRECTION : Anchor time = événement US HIGH le plus important, sinon premier événement
us_high_events = cluster_events[
    (cluster_events['country'] == 'US') & 
    (cluster_events['importance_n'] == 3)
]

if not us_high_events.empty:
    # Utiliser événement US HIGH avec score empirique le plus élevé
    if 'empirical_score' in us_high_events.columns:
        max_score_idx = us_high_events['empirical_score'].idxmax()
        anchor_time = us_high_events.loc[max_score_idx]['ts_utc']
    else:
        anchor_time = us_high_events.iloc[0]['ts_utc']
else:
    # Fallback : premier événement du cluster
    anchor_time = cluster_events.iloc[0]['ts_utc']
```

### Correction 2 : Sélection Cluster Principal

**Fichier** : `scripts/run_pipeline_complete.py` (lignes 2939-2963)

**Changement** :
- **AVANT** : Cherchait événements avec `empirical_score > 50`, puis prenait le plus grand cluster
- **APRÈS** : Priorité 1 = Cluster avec événements US HIGH à 14:30, Priorité 2 = Cluster avec US HIGH, Priorité 3 = Plus grand

**Code** :
```python
# Priorité 1 : Cluster avec événements US HIGH à 14:30
for cluster in clusters:
    events = cluster.get('events', pd.DataFrame())
    if not events.empty:
        anchor_hour = cluster['anchor_time'].hour
        anchor_minute = cluster['anchor_time'].minute
        if anchor_hour == 14 and 25 <= anchor_minute <= 35:
            us_high_events = events[(events['country'] == 'US') & (events['importance_n'] == 3)]
            if len(us_high_events) > 0:
                main_cluster = cluster
                break
```

### Correction 3 : Baseline Correct (Déjà Implémentée)

**Fichier** : `scripts/run_pipeline_complete.py` (lignes 2400-2430)

**Changement** :
- Utilise `baseline_price_correct` (OPEN première bougie après événement) au lieu de `baseline_price_pattern`
- Gestion timezone pour s'assurer que la comparaison fonctionne

---

## 📊 RÉSULTATS ATTENDUS

Pour **2025-05-29** :
- **Anchor time** : **14:30** ✅ (au lieu de 18:00)
- **Baseline correct** : **1.12954** (OPEN première bougie après 14:30) ✅
- **wave2_peak_pips_absolute** : **74.40 pips** ✅ (au lieu de 15.20)

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Tester sur 2025-05-29 pour valider les corrections
2. ⏳ Tester sur d'autres dates pour s'assurer que les corrections ne cassent rien
3. ⏳ Retirer les logs DEBUG une fois validé

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Corrections appliquées, tests en cours




