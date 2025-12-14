# REF-010 : Correction Extraction Core Type

**Date :** 2025-12-06  
**Statut :** ✅ **CORRIGÉ**

---

## 🐛 PROBLÈME IDENTIFIÉ

Le `core_type` n'était pas correctement extrait dans les tests, retournant "UNKNOWN" au lieu de "JOBLESS_PCE", "CPI", etc.

### Cause

1. **Accès incorrect aux résultats** : Le test accédait à `result.get('etape3_noyau_dur', {})` alors que les résultats sont dans `result.get('results', {}).get('etape3_noyau_dur', {})`

2. **Country manquant** : Le `country` n'était pas retourné par `etape3_definir_noyau_dur`, nécessaire pour utiliser les scores de `core_scores`

---

## ✅ CORRECTIONS APPLIQUÉES

### 1. Ajout de `country` dans `etape3_definir_noyau_dur`

**Fichier :** `scripts/run_pipeline_complete.py`

**Modification :**
```python
# Déterminer country principal (US par défaut pour EUR/USD, sinon premier événement core)
country = 'US'  # Par défaut pour EUR/USD
if not cluster_events.empty:
    # Chercher événements core pour déterminer country
    core_events_df = cluster_events[cluster_events.index.isin([idx for idx, eid in enumerate(event_ids) if eid in core_events_filtered])]
    if not core_events_df.empty:
        # Prioriser US, sinon premier country trouvé
        us_core_events = core_events_df[core_events_df['country'] == 'US']
        if not us_core_events.empty:
            country = 'US'
        else:
            country = core_events_df.iloc[0].get('country', 'US')

cluster_info = {
    'cluster': cluster,
    'core_events': core_events_filtered,
    'n_core_events': len(core_events_filtered),
    'n_total_events': n_total_events,
    'support_scores': support_scores,
    'core_type': core_type,
    'country': country  # ✅ AJOUT: Country pour utilisation dans core_scores
}
```

### 2. Ajout de `etape3_noyau_dur` dans les résultats

**Fichier :** `scripts/run_pipeline_complete.py`

**Modification :**
```python
'etape3_noyau_dur': {  # ✅ CORRECTION: Format standardisé pour accès facile
    'core_events': cluster_info.get('core_events', []),
    'n_core_events': cluster_info.get('n_core_events', 0),
    'n_total_events': cluster_info.get('n_total_events', 0),
    'support': cluster_info.get('n_core_events', 0) / cluster_info.get('n_total_events', 1) if cluster_info.get('n_total_events', 0) > 0 else 0.0,
    'core_type': cluster_info.get('core_type', 'GENERIC'),
    'country': cluster_info.get('country', 'US')  # ✅ CORRECTION: Utiliser country depuis cluster_info
},
```

### 3. Correction de l'accès aux résultats dans le test

**Fichier :** `SESSION_VALIDATION_ACTUELLE/scripts/test_predictions_nouveaux_scores.py`

**Modification :**
```python
# ✅ CORRECTION: Accéder via results.etape3_noyau_dur
results_dict = result.get('results', {})
etape3 = results_dict.get('etape3_noyau_dur', {})
core_type = etape3.get('core_type', 'UNKNOWN')
country = etape3.get('country', 'US')
```

---

## 📊 RÉSULTATS APRÈS CORRECTION

### Test sur Dates de Validation

| Date | Core Type | Country | Score core_scores | Impact Prédit |
|------|-----------|---------|------------------|---------------|
| 2025-05-29 | **JOBLESS_PCE** | US | **53.51** | 74.40 pips |
| 2025-09-11 | **CPI** | US | **75.06** | 60.70 pips |
| 2025-08-01 | **NFP** | US | **80.13** | 188.40 pips |
| 2025-11-20 | **NFP** | US | **80.13** | 36.60 pips |

### Validation

✅ **Core Type** : Correctement identifié (JOBLESS_PCE, CPI, NFP)  
✅ **Country** : Correctement extrait (US)  
✅ **Score core_scores** : Accessible et correct (53.51, 75.06, 80.13)

---

## 🎯 PROCHAINE ÉTAPE

Maintenant que le `core_type` et le `country` sont correctement extraits, on peut intégrer les scores de `core_scores` dans le calcul de l'impact base.

**Action :** Modifier `etape6_calculer_impacts_base_amplifications` et `etape8_appliquer_cluster_cible` pour utiliser les scores de `core_scores` quand disponibles.

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




