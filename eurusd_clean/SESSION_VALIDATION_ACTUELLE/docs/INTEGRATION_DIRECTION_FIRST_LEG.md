# Intégration Direction First-Leg dans Module Impact

## Résumé

Intégration du router directionnel first-leg (`direction_router_v6.py`) dans le module de calcul d'impact (`cluster_impact_calculator.py`) pour conditionner les prédictions d'impact sur la direction de la première jambe.

## Validation First-Leg (300 dates)

✅ **Résultats validés** :
- Coverage : 27.7% (zone cible 20-30%)
- Balanced accuracy : 56.6% (≥ 55% ✅)
- Accuracy UP : 57.1% (n=42)
- Accuracy DOWN : 56.1% (n=82)
- Symétrie UP/DOWN : excellente

✅ **Paramètres prod figés** :
- `trigger_z = 1.0` (trigger resserré sur CPI/Jobs uniquement)
- `theta = 0.05` (seuil neutralité)
- Mode : `first_leg_mode = True` (score empirique sans alpha_weights)
- Mapping USD→EURUSD : corrigé

## Architecture d'Intégration

### Point d'entrée : `calculate_cluster_impact_with_direction()`

Nouvelle fonction wrapper qui :
1. Appelle le router first-leg pour obtenir `direction_first_leg_pred`
2. Calcule l'impact avec `calculate_cluster_impact()`
3. Conditionne l'impact selon la direction prédite

### Flux de données

```
Date tradable (cluster d'events)
    ↓
Router First-Leg (`predict_direction_for_cluster`)
    ↓
DirectionResult {
    direction: 'UP' | 'DOWN' | 'UNKNOWN',
    score: S_cluster,
    has_trigger: bool,
    trigger_strength: max|z_core|,
    audit_log: [...]
}
    ↓
Module Impact (`calculate_cluster_impact_with_direction`)
    ↓
ImpactResult {
    impact_pips: float,
    direction_first_leg: 'UP' | 'DOWN' | 'UNKNOWN',
    pattern_type: 'single_wave' | 'double_wave' | 'zig_zag',
    ...
}
```

## Implémentation

### 1. Fonction wrapper principale

```python
def calculate_cluster_impact_with_direction(
    cluster_events: pd.DataFrame,
    stats_map: Dict[str, Tuple[float, float]],
    alpha_map: Dict[str, float],  # Optionnel si first_leg_mode=True
    trigger_z: float = 1.0,
    theta: float = 0.05,
    first_leg_mode: bool = True,
    use_linear_formula: bool = True
) -> Dict:
    """
    Calcule l'impact d'un cluster avec direction first-leg conditionnée.
    
    Args:
        cluster_events: DataFrame avec colonnes ['event_key', 'actual', 'estimate', 'family']
        stats_map: Map stats surprises (mu, sigma) par event_key
        alpha_map: Map alpha weights (optionnel si first_leg_mode=True)
        trigger_z: Seuil trigger |z| (défaut: 1.0)
        theta: Seuil neutralité (défaut: 0.05)
        first_leg_mode: Utiliser score empirique (défaut: True)
        use_linear_formula: Utiliser formule linéaire (défaut: True)
    
    Returns:
        dict: {
            'impact_pips': float,
            'direction_first_leg': 'UP' | 'DOWN' | 'UNKNOWN',
            'direction_score': float,  # S_cluster
            'trigger_strength': float,  # max|z_core|
            'has_trigger': bool,
            'pattern_type': str,  # À déterminer par détection pattern
            'impact_details': dict,  # Résultat calculate_cluster_impact()
            'direction_audit': List[EventContribution]  # Audit log router
        }
    """
    from direction_router_v6 import predict_direction_for_cluster, CORE_FAMILIES_V6
    from cluster_impact_calculator import calculate_cluster_impact
    
    # 1) Prédire direction first-leg
    direction_result = predict_direction_for_cluster(
        events_actuals=cluster_events,
        stats_map=stats_map,
        alpha_map=alpha_map,
        core_families=CORE_FAMILIES_V6,
        trigger_z=trigger_z,
        theta=theta,
        use_fallback_always_on=False,
        first_leg_mode=first_leg_mode
    )
    
    # 2) Calculer trigger_strength (max|z| des events core)
    trigger_strength = 0.0
    if direction_result.audit_log:
        trigger_strength = max(abs(contrib.surprise_z) for contrib in direction_result.audit_log)
    
    # 3) Calculer impact (indépendant de direction pour l'instant)
    impact_result = calculate_cluster_impact(
        cluster_events=cluster_events,
        use_linear_formula=use_linear_formula
    )
    
    # 4) Conditionner impact selon direction (à implémenter selon patterns)
    # Pour l'instant, on retourne les deux informations séparément
    
    return {
        'impact_pips': impact_result['impact_pips'],
        'direction_first_leg': direction_result.direction,
        'direction_score': direction_result.score,
        'trigger_strength': trigger_strength,
        'has_trigger': direction_result.has_trigger,
        'pattern_type': None,  # À déterminer par détection pattern
        'impact_details': impact_result,
        'direction_audit': direction_result.audit_log
    }
```

### 2. Conditionnement par pattern

#### Single Wave
- Direction impact = `direction_first_leg`
- Si `direction_first_leg == 'UNKNOWN'` → utiliser direction empirique (basée sur surprise signée)

#### Double Wave / Zig-Zag
- Jambe 1 : `direction_first_leg` (router)
- Jambe 2 / Retrace : pipeline pattern existant (à recalibrer si besoin)

### 3. Points d'intégration dans le code existant

#### A. `cluster_impact_calculator.py`
- Ajouter `calculate_cluster_impact_with_direction()` comme wrapper
- Modifier `calculate_double_wave_overlapping()` pour utiliser `direction_first_leg` pour jambe 1

#### B. `doublewave_prediction.py`
- Injecter `direction_first_leg` dans `predict_doublewave_overlap()`
- Conditionner momentum_factor selon convergence directionnelle

#### C. Scripts de planification
- Utiliser `calculate_cluster_impact_with_direction()` au lieu de `calculate_cluster_impact()`
- Afficher `direction_first_leg` dans les outputs

## Tests de validation

### Test 1 : Intégration basique
- Vérifier que `calculate_cluster_impact_with_direction()` retourne les bonnes clés
- Vérifier que `direction_first_leg` est cohérent avec les actuals

### Test 2 : Conditionnement single wave
- Tester sur dates avec pattern single wave
- Vérifier que direction impact = direction first-leg

### Test 3 : Conditionnement double wave
- Tester sur dates avec pattern double wave (ex: 11 sept 2025)
- Vérifier que jambe 1 utilise direction first-leg
- Vérifier que jambe 2 utilise pipeline pattern existant

## Prochaines étapes

1. ✅ **Implémenter wrapper** `calculate_cluster_impact_with_direction()`
2. ⏳ **Tester intégration** sur dates tradables historiques
3. ⏳ **Conditionner single wave** sur direction first-leg
4. ⏳ **Conditionner double wave** (jambe 1 = first-leg, jambe 2 = pattern)
5. ⏳ **Recalibrer patterns** sur univers "tradable dates + direction correcte"

## Notes

- Le router first-leg est indépendant du calcul d'impact → pas de modification des formules existantes
- La direction first-leg sert de **conditionnement**, pas de remplacement des formules d'impact
- Pour les cas `UNKNOWN`, on peut utiliser un fallback directionnel empirique (surprise signée)

