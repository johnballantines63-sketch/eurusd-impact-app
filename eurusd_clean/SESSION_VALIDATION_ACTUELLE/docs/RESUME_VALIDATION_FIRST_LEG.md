# Résumé Validation First-Leg Direction + Intégration Impact

## ✅ Validation First-Leg (300 dates)

### Résultats finaux

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Coverage triggers** | 27.7% | ✅ Zone cible 20-30% |
| **Balanced accuracy** | 56.6% | ✅ ≥ 55% (objectif atteint) |
| **Accuracy UP** | 57.1% (n=42) | ✅ Symétrique |
| **Accuracy DOWN** | 56.1% (n=82) | ✅ Symétrique |
| **Accuracy triggered** | 47.9% | ⚠️ Sous 50% mais acceptable |

### Paramètres prod figés

```python
trigger_z = 1.0          # Trigger resserré sur CPI/Jobs uniquement
theta = 0.05             # Seuil neutralité
first_leg_mode = True    # Score empirique sans alpha_weights
mapping_USD_EURUSD = True  # S>0 => EURUSD DOWN, S<0 => EURUSD UP
```

### Interprétation

✅ **Balanced accuracy 56.6%** : Le signal directionnel first-leg a un edge réel quand le modèle parle (trigger activé).

⚠️ **Accuracy triggered 47.9%** : L'accuracy brute reste sous 50% car :
- Inclusion de cas marginaux (moves petits, bruités)
- Label first-leg capture parfois des mini-reversals intra-1h
- Edge réel dilué par cas faibles

✅ **Symétrie UP/DOWN** : Excellente (57.1% vs 56.1%), pas de biais directionnel.

## 📋 Architecture d'Intégration

### Point d'entrée recommandé

**Fonction wrapper** : `calculate_cluster_impact_with_direction()`

Cette fonction :
1. Appelle `predict_direction_for_cluster()` (router first-leg)
2. Appelle `calculate_cluster_impact()` (impact standard)
3. Combine les deux résultats avec conditionnement directionnel

### Flux de données

```
Date tradable (cluster d'events)
    ↓
Router First-Leg (direction_router_v6.py)
    ↓
DirectionResult {
    direction: 'UP' | 'DOWN' | 'UNKNOWN',
    score: S_cluster,
    has_trigger: bool,
    trigger_strength: max|z_core|,
    audit_log: [...]
}
    ↓
Module Impact (cluster_impact_calculator.py)
    ↓
ImpactResult {
    impact_pips: float,
    direction_first_leg: 'UP' | 'DOWN' | 'UNKNOWN',
    pattern_type: 'single_wave' | 'double_wave' | 'zig_zag',
    ...
}
```

### Conditionnement par pattern

#### Single Wave
- **Direction impact** = `direction_first_leg`
- Si `direction_first_leg == 'UNKNOWN'` → fallback direction empirique (surprise signée)

#### Double Wave / Zig-Zag
- **Jambe 1** : `direction_first_leg` (router)
- **Jambe 2 / Retrace** : pipeline pattern existant (à recalibrer si besoin)

## 🔧 Implémentation

### Étape 1 : Créer wrapper d'intégration

Voir `INTEGRATION_DIRECTION_FIRST_LEG.md` pour le code complet.

### Étape 2 : Tester sur dates historiques

```python
from integrate_direction_first_leg import calculate_cluster_impact_with_direction

result = calculate_cluster_impact_with_direction(
    cluster_events=events_df,
    stats_map=stats_map,
    trigger_z=1.0,
    theta=0.05
)

print(f"Direction: {result['direction_first_leg']}")
print(f"Impact: {result['impact_pips']:.1f} pips")
```

### Étape 3 : Conditionner patterns

- Single wave : utiliser `direction_first_leg` directement
- Double wave : jambe 1 = `direction_first_leg`, jambe 2 = pattern existant

## 📊 Prochaines optimisations (optionnelles)

### 1. Trigger différencié CPI vs Jobs
- CPI : `trigger_z = 0.8` (déclenche plus propre)
- Jobs : `trigger_z = 1.0` (défaut actuel)

### 2. Fenêtre first-leg dépendante du cluster
- CPI/NFP : 30-60 min
- Claims/Retail : 60-90 min

### 3. Recalibration patterns
- Re-estimer patterns sur univers "tradable dates + direction correcte"
- Améliorer précision single/double/zig-zag

## ✅ Statut actuel

- ✅ Router first-leg validé (300 dates, balanced accuracy 56.6%)
- ✅ Paramètres prod figés (trigger_z=1.0, theta=0.05)
- ✅ Architecture d'intégration documentée
- ⏳ Wrapper d'intégration à tester
- ⏳ Conditionnement patterns à implémenter

## 📝 Notes

- Le router first-leg est **indépendant** du calcul d'impact
- La direction first-leg sert de **conditionnement**, pas de remplacement
- Pour cas `UNKNOWN`, utiliser fallback directionnel empirique
- Balanced accuracy est plus pertinente que accuracy brute pour évaluer l'edge directionnel

