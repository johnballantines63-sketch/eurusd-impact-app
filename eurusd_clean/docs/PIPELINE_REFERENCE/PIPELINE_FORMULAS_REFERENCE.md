# Référence des Formules du Pipeline

## 1. Calcul d'Impact de Base

### Formule Principale
```
impact_base = Σ(score_empirique_event_i × importance_factor_i × surprise_factor_i)
```

### Score Empirique
Calculé depuis historique avec coefficients validés :
- Analyse de fréquence d'apparition
- Corrélation avec impacts réels
- Coefficients par type d'événement

### Importance Factor
```python
importance_factor = {
    1 (high): 1.0,
    2 (medium): 0.7,
    3 (low): 0.4
}
```

### Surprise Factor
```python
if actual and forecast:
    surprise = abs(actual - forecast) / abs(forecast) if forecast != 0 else 0
    surprise_factor = 1.0 + min(surprise, 0.5)  # Max 1.5x
else:
    surprise_factor = 1.0
```

### Correction Factor (Random Forest)
```python
correction_factor = predict_correction_factor_rf(
    scores_empiriques=...,
    surprises=...,
    num_events=...
)
# Range typique : 0.5 - 1.5x

impact_final = impact_base × correction_factor
```

## 2. Amplification Parfaite

### Définition
```
amplification_parfaite = impact_reel / impact_base
```

### Utilisation
- Calculée pour chaque cluster historique
- Utilisée comme target pour Random Forest
- Moyenne utilisée comme fallback

## 3. Prédiction d'Amplification

### Random Forest Features
```python
features = [
    trend_r2,              # R² de la tendance
    trend_duration_h,      # Durée en heures
    trend_amplitude_pips,  # Amplitude en pips
    impact_base_pips,      # Impact de base
    num_events,            # Nombre d'événements
    pattern_impact_pips,  # Impact pattern (si disponible)
    pattern_wave1_pips,    # Wave 1 pips (si disponible)
    pattern_wave2_pips     # Wave 2 pips (si disponible)
]
```

### Prédiction
```python
amplification_predite = rf_model.predict(features)
```

### Impact Prédit (Formules)
```python
impact_formules = impact_base × amplification_predite
```

## 4. Ajustements Support/Résistance

### Distance Normalisée
```
distance_norm = |distance_to_barrier| / ATR
```

### Ajustements
```python
if is_breakout and distance_norm < 0.15:
    adjustment = 1.15  # +15%
elif is_breakout and distance_norm < 0.40:
    adjustment = 1.05  # +5%
elif not is_breakout and distance_norm < 0.10:
    adjustment = 0.70  # -30%
elif not is_breakout and distance_norm < 0.20:
    adjustment = 0.90  # -10%
elif distance_norm > 1.40:
    adjustment = 1.15  # +15%
else:
    adjustment = 1.00  # Neutre

amplification_ajustee = amplification_predite × adjustment
```

## 5. Ajustements Patterns Finnhub

### Multiplicateur de Confiance
```python
if patterns_found > 0:
    if direction_validated:
        multiplier = 1.05 + (strong_patterns_count * 0.02)  # +5% à +10%
    else:
        multiplier = 0.90 - (strong_patterns_count * 0.02)  # -10% à -15%
else:
    multiplier = 0.95  # -5% (réduction confiance)

amplification_ajustee = amplification_predite × multiplier
```

## 6. Détection Pattern Double Wave

### Wave 1
```
wave1_pips = |wave1_price - baseline_price| × 10000
Condition : wave1_pips >= MIN_PHASE1_PIPS (20.0)
```

### Pullback
```
pullback_pips = |wave1_price - pullback_price| × 10000
pullback_ratio = pullback_pips / wave1_pips
Condition : MIN_PULLBACK_RATIO (0.20) <= pullback_ratio <= MAX_PULLBACK_RATIO (0.80)
```

### Wave 2
```
wave2_pips = |wave2_price - pullback_price| × 10000
Condition : wave2_pips >= MIN_PHASE2_PIPS (14.0)
Condition : wave2_pips >= wave1_pips × PHASE2_MIN_RATIO (0.3)
```

### Impact Pattern
```
impact_pips = |wave2_price - baseline_price| × 10000  # Wave 2 détecté
impact_absolute = |absolute_peak_price - baseline_price| × 10000  # Pic réel
```

## 7. Stratégie Hybride Pattern/Formules

### Condition d'Application
```python
ecart_absolu = |pattern_impact - impact_formules|

if ecart_absolu < 10:
    # Garder formules
    prediction_finale = impact_formules
else:
    # Utiliser pattern directement
    prediction_finale = pattern_impact  # Utilise pic absolu si disponible
```

## 8. Target de Sortie

### Calcul
```python
exit_target = min(
    impact_predicted × EXIT_PERCENTAGE (0.80),
    impact_predicted × MAX_IMPACT_MULTIPLIER (1.5)
)
```

### Exemple
```
Si impact_predicted = 100 pips :
    exit_target = min(100 × 0.80, 100 × 1.5) = min(80, 150) = 80 pips
```

## 9. Similarité Jaccard

### Formule
```
J(A, B) = |A ∩ B| / |A ∪ B|
```

### Application
```python
core_events_A = set([...])  # Noyau dur cluster A
core_events_B = set([...])  # Noyau dur cluster B

intersection = len(core_events_A & core_events_B)
union = len(core_events_A | core_events_B)

jaccard_score = intersection / union if union > 0 else 0

if jaccard_score >= JACCARD_THRESHOLD (0.60):
    # Clusters identiques
```

## 10. Détection de Tendance

### R² (Coefficient de Détermination)
```
R² = 1 - (SS_res / SS_tot)

SS_res = Σ(y_i - ŷ_i)²  # Somme résidus
SS_tot = Σ(y_i - ȳ)²    # Somme totale
```

### Validation
```python
trend_exists = (
    r2 >= MIN_R2 (0.15) and
    abs(tstat) >= 2.0 and
    abs(amplitude_pips) >= MIN_AMPLITUDE_PIPS (15.0)
)
```

### Amplitude
```
amplitude_pips = |price_extreme - price_start| × 10000
```

### Durée
```
duration_hours = (event_time - trend_start_time).total_seconds() / 3600
```

## 11. Mesure d'Impact Réel

### Algorithme
```python
df_after = prices[prices['datetime'] >= event_time]

max_price = df_after['high'].max()
min_price = df_after['low'].min()

impact_up = (max_price - baseline_price) × 10000
impact_down = (baseline_price - min_price) × 10000

impact_real = max(impact_up, impact_down)
direction = 'UP' if impact_up > impact_down else 'DOWN'
```

## 12. Erreur de Prédiction

### Erreur Absolue
```
error_absolu = |impact_predicted - impact_real|
```

### Erreur Relative
```
error_relative = error_absolu / impact_real × 100
```

### MAE (Mean Absolute Error)
```
MAE = (1/n) × Σ|impact_predicted_i - impact_real_i|
```

## Coefficients Validés

### Scores Empiriques
Voir : `docs/PROJECT_MANAGEMENT/03_FORMULAS/VALIDATED_FORMULAS.md`

### Correction Factor
- Range typique : 0.5 - 1.5x
- Prédit par Random Forest
- Basé sur scores empiriques, surprises, nombre d'événements

### Amplification
- Range typique : 0.3 - 3.0x
- Prédit par Random Forest
- Basé sur tendance, impact_base, pattern

