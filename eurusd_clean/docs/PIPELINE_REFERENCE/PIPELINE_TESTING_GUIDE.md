# Guide de Test du Pipeline

## Tests de Validation

### Test Complet sur Date
```bash
python3 scripts/test_pipeline_validation_finale.py
```

**Dates testées** :
- 2025-09-11 (référence)
- 2025-08-01 (référence)
- 2025-11-26 (complexe)
- 2025-10-10 (nouveau)
- 2025-06-23 (problématique résolu)

### Test Pic Absolu
```bash
python3 scripts/test_pic_absolu_multiples_dates.py
```

**Résultats attendus** :
- MAE < 10 pips
- Cas améliorés > 40%
- Cas dégradés = 0%

### Test Erreur Spécifique
```bash
python3 scripts/analyser_erreur_23_06.py
```

**Objectif** : Analyser en détail une date problématique.

## Tests Unitaires

### Test Détection Pattern
```python
from scripts.phase_a_robust_validation import detect_double_wave_pattern, load_price_window

price_window = load_price_window(DB_PATH, event_time, minutes_before=120, minutes_after=240)
pattern_info = detect_double_wave_pattern(price_window, event_time, pattern_mode="early")

assert pattern_info['pattern_type'] != 'NONE'
assert pattern_info['wave2_peak_pips_absolute'] >= pattern_info['impact_pips']
```

### Test Détection Tendance
```python
from core.trend_detection_pre_event import detect_trend_pre_event_robust

trend_result = detect_trend_pre_event_robust(
    db_path=DB_PATH,
    event_datetime=event_time,
    min_hours_before_event=12,
    min_duration_hours=6.0,
    force_timeframe='M30'
)

assert trend_result.get('trend_exists') == True
assert trend_result.get('r2', 0) >= 0.15
```

### Test Calcul Impact
```python
from scripts.validate_coefficients_empirical import calculate_impact_d

impact_base = calculate_impact_d(events_df, db_path=DB_PATH)
assert impact_base > 0
```

## Tests d'Intégration

### Pipeline Complet
```python
from scripts.run_pipeline_complete import PipelineExecutor

executor = PipelineExecutor(DB_PATH, verbose=True)
result = executor.execute_complete_pipeline('2025-09-11')

assert result['success'] == True
assert result['final_prediction']['prediction_finale'] > 0
```

## Validation des Résultats

### Vérifications Essentielles
1. **Impact prédit > 0** : Toujours positif
2. **Exit target <= 1.5x prédit** : Limite respectée
3. **Pattern type valide** : DOUBLE_WAVE, SINGLE_WAVE_FORT, SINGLE_WAVE_STANDARD, ou NONE
4. **Timings cohérents** : wave1 < pullback < wave2 (si DOUBLE_WAVE)
5. **Pic absolu >= Wave 2** : Toujours vrai

### Métriques de Performance
- **MAE** : Doit être < 10 pips
- **Taux acceptable** : Doit être > 60%
- **Taux excellent** : Doit être > 50%

## Cas de Test

### Cas de Référence
- **2025-09-11** : SINGLE_WAVE, 63.8 pips réel
- **2025-08-01** : SINGLE_WAVE_FORT, 188.3 pips réel
- **2025-06-23** : DOUBLE_WAVE avec continuation, 89.6 pips réel
- **2025-08-12** : DOUBLE_WAVE, 92.1 pips réel

### Cas Problématiques Résolus
- **2025-06-23** : Pattern incomplet → Résolu avec pic absolu
- **2025-04-24** : Pas de tendance → Résolu avec critères assouplis
- **2025-11-26** : Mouvement complexe → Résolu avec priorisation premier mouvement

## Debugging

### Mode Verbose
```python
executor = PipelineExecutor(DB_PATH, verbose=True)
```

### Logs Détaillés
Chaque étape log :
- ✅ Succès
- ⚠️ Avertissement
- ❌ Erreur
- ℹ️ Information

### Points de Contrôle
1. Nombre de clusters identiques trouvés
2. Nombre de tendances détectées
3. Amplification prédite
4. Pattern détecté
5. Impact final

## Tests de Régression

### Avant/Après Modifications
```bash
# Avant modification
python3 scripts/test_pic_absolu_multiples_dates.py > results_before.txt

# Après modification
python3 scripts/test_pic_absolu_multiples_dates.py > results_after.txt

# Comparer
diff results_before.txt results_after.txt
```

### Validation Non-Régression
- MAE ne doit pas augmenter
- Cas améliorés ne doivent pas diminuer
- Cas dégradés ne doivent pas augmenter

