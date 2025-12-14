# Architecture Détaillée du Pipeline

## Flux de Données

```
Événements → Clusters → Noyau Dur → Clusters Identiques → Tendances → Impacts → Analyse → Prédiction
```

## Diagramme de Flux

```
┌─────────────────┐
│  Événements DB  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 1:       │
│  Charger Events │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 2:       │
│  Détecter       │
│  Clusters       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 3:       │
│  Définir        │
│  Noyau Dur      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 4:       │
│  Rechercher     │
│  Clusters       │
│  Identiques     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 5:       │
│  Calculer       │
│  Tendances      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 6:       │
│  Calculer       │
│  Impacts Base   │
│  & Amplif.      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 7:       │
│  Analyser       │
│  Relation       │
│  Tendance →     │
│  Amplification  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Étape 8:       │
│  Appliquer      │
│  Cluster Cible  │
│  + Pattern      │
│  + Ajustements  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prédiction     │
│  Finale         │
└─────────────────┘
```

## Structures de Données

### Cluster Info
```python
{
    'cluster': {
        'events': DataFrame,
        'anchor_time': datetime,
        'n_events': int
    },
    'core_events': List[str],
    'n_core_events': int,
    'support_scores': Dict[str, float]
}
```

### Trend Result
```python
{
    'trend_exists': bool,
    'r2': float,
    'amplitude_pips': float,
    'duration_minutes': int,
    'direction': 'UP' | 'DOWN',
    'timeframe_used': str,
    't_start_datetime': datetime,
    'price_start': float,
    'price_extreme': float,
    'price_before_event': float
}
```

### Pattern Info
```python
{
    'pattern_type': 'DOUBLE_WAVE' | 'SINGLE_WAVE_FORT' | 'SINGLE_WAVE_STANDARD' | 'NONE',
    'confidence': float,
    'direction': 'UP' | 'DOWN',
    'baseline_price': float,
    'wave1_pips': float,
    'wave1_peak_time': datetime,
    'pullback_pips': float,
    'pullback_time': datetime,
    'wave2_pips': float,
    'wave2_peak_time': datetime,
    'impact_pips': float,  # Basé sur Wave 2 détecté
    'wave2_peak_pips_absolute': float,  # Pic réel dans toute fenêtre
    'wave2_peak_time_absolute': datetime,
    'wave2_peak_price_absolute': float
}
```

### Final Prediction
```python
{
    'impact_base': float,
    'amplification_predite': float,
    'prediction_finale': float,
    'exit_target': float,
    'pattern_type': str,
    'pattern_wave1_peak_time': datetime,
    'pattern_wave2_peak_time': datetime,
    'trend_exists': bool,
    'trend_r2': float,
    'trend_duration_h': float,
    'trend_amplitude_pips': float,
    'cluster_direction': 'UP' | 'DOWN',
    'is_breakout': bool,
    'tradable': bool,
    'trading_reason': str
}
```

## Dependencies

### Modules Principaux
- `duckdb` : Base de données
- `pandas` : Manipulation données
- `numpy` : Calculs numériques
- `scikit-learn` : Random Forest
- `scipy` : Détection extrema (find_peaks)

### Modules Personnalisés
- `core.trend_detection_pre_event` : Détection tendance
- `core.amplification_random_forest` : RF global
- `core.amplification_random_forest_per_date` : RF par date
- `core.finnhub_amplification_adjustment` : Ajustements Finnhub
- `core.exit_strategy` : Stratégie sortie
- `core.impact_measurement` : Mesure impact réel

## Points d'Entrée

### Pipeline Complet
```python
from scripts.run_pipeline_complete import PipelineExecutor

executor = PipelineExecutor(db_path=DB_PATH, verbose=True)
result = executor.execute_complete_pipeline(
    date_str='2025-09-11',
    window_minutes=30,
    support_threshold=0.8,
    jaccard_threshold=0.60,
    years_lookback=5
)
```

### Détection Pattern Seule
```python
from scripts.phase_a_robust_validation import detect_double_wave_pattern, load_price_window

price_window = load_price_window(DB_PATH, event_time, minutes_before=120, minutes_after=240)
pattern_info = detect_double_wave_pattern(price_window, event_time, pattern_mode="early")
```

### Détection Tendance Seule
```python
from core.trend_detection_pre_event import detect_trend_pre_event_robust

trend_result = detect_trend_pre_event_robust(
    db_path=DB_PATH,
    event_datetime=event_time,
    min_hours_before_event=12,
    min_duration_hours=6.0,
    force_timeframe='M30'
)
```

## Gestion d'Erreurs

### Fallbacks
1. **Pas de tendance** : Random Forest avec R²=0.0
2. **Pas de clusters identiques** : Random Forest global
3. **Pas de pattern** : Utiliser formules uniquement
4. **Erreur Random Forest** : Modèle linéaire
5. **Erreur modèle linéaire** : Moyenne historique

### Validations
- Chaque étape valide ses résultats
- Logs détaillés en mode verbose
- Exceptions capturées avec fallbacks

## Performance

### Temps d'Exécution
- Pipeline complet : ~5-10 secondes par date
- Détection pattern : ~1-2 secondes
- Détection tendance : ~2-3 secondes
- Random Forest : < 1 seconde

### Optimisations
- Requêtes SQL optimisées avec index
- Cache des résultats intermédiaires
- Lazy loading des modules

## Tests

### Tests Unitaires
- Chaque étape testée indépendamment
- Validation des structures de données
- Tests de fallbacks

### Tests d'Intégration
- Pipeline complet sur dates de référence
- Validation des prédictions
- Comparaison avec impacts réels

### Tests de Validation
- 15 dates avec mouvements forts
- MAE mesuré et comparé
- Statistiques de performance

