# Proposition : Version Restaurée du Pipeline (1er décembre 2025)

**Date** : 3 décembre 2025  
**Objectif** : Proposer une version restaurée du pipeline tel qu'il était il y a 2 jours (avant les modifications du 3 décembre)

---

## 📋 MODIFICATIONS À RETIRER

### 1. ÉTAPE 3 : Retirer Seuil Adaptatif et Support Tous Clusters

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : 251-550 (méthode `_calculate_historical_support` et `etape3_definir_noyau_dur`)

**Modifications à appliquer** :

#### A. Dans `_calculate_historical_support` :
- ❌ Retirer le calcul support sur TOUS les clusters pour événements génériques
- ✅ Garder uniquement le calcul support dans clusters du même type (CPI/NFP)

#### B. Dans `etape3_definir_noyau_dur` :
- ❌ Retirer le seuil adaptatif (support >= 40% ET importance <= 2)
- ❌ Retirer le seuil adaptatif pour GENERIC (support >= 20% ET importance <= 3)
- ✅ Utiliser uniquement le seuil fixe : `support >= support_threshold` (0.60)

**Code à restaurer** :
```python
# Version restaurée (seuil fixe uniquement)
for event_id, support in support_scores.items():
    if support >= support_threshold:  # 0.60 par défaut
        core_events.append(event_id)
```

---

### 2. ÉTAPE 8.1 : Retirer Méthode Session 88

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : 1185-1234 (méthode `etape8_appliquer_cluster_cible`)

**Modifications à appliquer** :

- ❌ Retirer la méthode Session 88 (score moyen ajusté avec surprise MAX)
- ✅ Restaurer le calcul individuel pour chaque événement (comme dans Étape 6)

**Code à restaurer** :
```python
# Version restaurée (calcul individuel)
total_impact_base = 0.0
num_events = len(cluster_events)

for _, event in cluster_events.iterrows():
    base_score = event.get('empirical_score', 44.0)
    actual = event.get('actual')
    estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
    
    # Calculer surprise individuelle
    surprise_pct = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_pct = abs(actual - estimate) / abs(estimate) * 100
    
    # Ajuster score individuel
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score,
        surprise_pct=surprise_pct
    )
    
    # Calculer impact individuel
    impact_individuel = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=1,  # Impact individuel
        amplification=1.0,
        correction_factor=1.0  # Pas de correction vectorielle ici
    )
    
    total_impact_base += impact_individuel

# Correction vectorielle après
if num_events >= 2:
    total_impact_base = total_impact_base * 0.758

impact_base = total_impact_base
```

---

### 3. ÉTAPE 8.3 : Retirer Stratégie Conditionnelle Double Wave

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : 2067-2101 (méthode `etape8_appliquer_cluster_cible`)

**Modifications à appliquer** :

- ❌ Retirer la logique conditionnelle selon pattern type (Single Wave vs Double Wave)
- ✅ Restaurer la stratégie identique pour tous les patterns

**Code à restaurer** :
```python
# Version restaurée (stratégie identique pour tous)
ecart_absolu = abs(pattern_impact - impact_formules) if pattern_impact > 0 else 0

if ecart_absolu < 10 or pattern_impact == 0:
    prediction_finale = impact_formules
    prediction_method = 'formulas'
    self._log(f"   ✅ Stratégie: Formules (écart: {ecart_absolu:.1f} pips < 10)", "INFO")
else:
    prediction_finale = pattern_impact
    prediction_method = 'pattern'
    self._log(f"   ✅ Stratégie: Pattern (écart: {ecart_absolu:.1f} pips >= 10)", "INFO")
```

---

### 4. ÉTAPE 8.6 : Retirer Timings Parfaits Session 64

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : 1665-1916 (méthode `etape8_appliquer_cluster_cible`)

**Modifications à appliquer** :

- ❌ Retirer `predict_double_wave_timeline_s64()` et timings fixes (T+5, T+11, T+15, T+40)
- ❌ Retirer la détection pattern réel vs critères événements
- ✅ Utiliser uniquement la détection pattern depuis prix réels

**Code à restaurer** :
```python
# Version restaurée (détection pattern depuis prix uniquement)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'session120'))
    from double_wave_detector_rev12 import detect_for_date_duckdb_rev12
    
    pattern_date = anchor_time
    if pattern_date.tzinfo is not None:
        pattern_date = pattern_date.replace(tzinfo=None)
    
    pattern_result = detect_for_date_duckdb_rev12(
        db_path=str(self.db_path),
        table='prices_finnhub_m1',
        date=pattern_date,
        tz='Europe/Zurich',
        baseline_mode='local_minmax',
        minutes_after_hint=180,
        trading_window=True,
        debug=False
    )
    
    if pattern_result:
        pattern_type = 'DOUBLE_WAVE' if pattern_result.get('double_wave', False) else 'SINGLE_WAVE'
        
        direction_str = pattern_result.get('direction', 'UNKNOWN')
        if direction_str == 'bullish':
            pattern_direction = 'UP'
        elif direction_str == 'bearish':
            pattern_direction = 'DOWN'
        else:
            pattern_direction = 'UNKNOWN'
        
        baseline_price = pattern_result.get('baseline_price')
        wave1_pips = pattern_result.get('wave1_amp_pips', 0.0)
        wave2_pips = pattern_result.get('wave2_amp_pips', 0.0)
        pullback_pips = abs(pattern_result.get('pullback1_ratio', 0.0) * wave1_pips) if wave1_pips > 0 else 0.0
        wave2_peak_pips_absolute = wave2_pips
        
        pattern_info = {
            'pattern_type': pattern_type,
            'direction': pattern_direction,
            'confidence': pattern_result.get('confidence', 0.0),
            'wave1_pips': wave1_pips,
            'wave2_pips': wave2_pips,
            'pullback_pips': pullback_pips,
            'baseline_price': baseline_price,
            'wave2_peak_pips_absolute': wave2_peak_pips_absolute,
            'timings_predicted': False,  # Timings détectés, pas prédits
            'wave1_peak_time': pd.to_datetime(pattern_result.get('peak1_time')) if pattern_result.get('peak1_time') else None,
            'wave2_peak_time': pd.to_datetime(pattern_result.get('peak2_time')) if pattern_result.get('peak2_time') else None
        }
        
        self._log(f"   ✅ Pattern détecté: {pattern_type} ({pattern_direction}), confiance: {pattern_info['confidence']:.1f}%", "SUCCESS")
except Exception as e:
    self._log(f"   ⚠️ Erreur détection pattern: {e}", "WARNING")
    pattern_info = {
        'pattern_type': 'NONE',
        'direction': 'UNKNOWN',
        'confidence': 0.0,
        'wave1_pips': 0.0,
        'wave2_pips': 0.0,
        'pullback_pips': 0.0,
        'baseline_price': None,
        'wave2_peak_pips_absolute': 0.0,
        'timings_predicted': False,
        'wave1_peak_time': None,
        'wave2_peak_time': None
    }
```

---

## 📝 RÉSUMÉ DES MODIFICATIONS

### Modifications à Retirer

| Étape | Modification | Lignes | Impact |
|-------|-------------|--------|--------|
| **Étape 3** | Seuil adaptatif + support tous clusters | 251-550 | ❌ Jobless Claims exclus |
| **Étape 8.1** | Méthode Session 88 | 1185-1234 | ❌ Erreur augmentée (~126 pips) |
| **Étape 8.3** | Stratégie conditionnelle Double Wave | 2067-2101 | ❌ Pas de correction 11 sept |
| **Étape 8.6** | Timings parfaits Session 64 | 1665-1916 | ❌ Timings moins précis |

---

## ⚠️ AVERTISSEMENTS

### Performance Attendue

**Version Actuelle** (avec améliorations) :
- MAE : ~8.4 pips
- Méthode Session 88 : Erreur 16.62 pips (vs 126.83 pips avant)

**Version Restaurée** (sans améliorations) :
- MAE : Probablement > 10 pips
- Méthode standard : Erreur probablement ~126 pips (comme avant Session 88)

### Recommandation

**⚠️ ATTENTION** : La version restaurée sera probablement **moins performante** que la version actuelle.

**Utilisation recommandée** :
- ✅ Pour comparaison uniquement
- ✅ Pour comprendre l'évolution
- ✅ Pour identifier ce qui a changé
- ❌ **NE PAS utiliser en production** (performance dégradée)

---

## 🔧 FICHIER À CRÉER

**Nom** : `scripts/run_pipeline_complete_restored_1dec.py`

**Méthode** :
1. Copier `scripts/run_pipeline_complete.py`
2. Appliquer toutes les modifications listées ci-dessus
3. Ajouter un commentaire en en-tête indiquant que c'est une version restaurée

---

## ✅ CHECKLIST RESTAURATION

- [ ] Copier `run_pipeline_complete.py` vers `run_pipeline_complete_restored_1dec.py`
- [ ] Modifier `_calculate_historical_support` : Retirer support tous clusters
- [ ] Modifier `etape3_definir_noyau_dur` : Retirer seuil adaptatif
- [ ] Modifier `etape8_appliquer_cluster_cible` : Retirer méthode Session 88
- [ ] Modifier `etape8_appliquer_cluster_cible` : Retirer stratégie conditionnelle
- [ ] Modifier `etape8_appliquer_cluster_cible` : Retirer timings parfaits Session 64
- [ ] Tester la version restaurée sur 2025-08-01
- [ ] Comparer résultats avec version actuelle
- [ ] Documenter les différences de performance

---

**Date création** : Proposition version restaurée  
**Status** : ✅ Modifications identifiées, prêt pour restauration




