# Guide Router Directionnel V6 - Dates Tradables

## 📋 Résumé

Le router directionnel V6 est une fonction standardisée pour prédire la direction EURUSD **après actuals connus**, pour dates avec clusters d'events historiquement associés à des mouvements forts.

**Convention corrigée** : Score S calculé en USD, mapping final USD→EURUSD (S>0 = USD up = EURUSD DOWN).

## 🎯 Recommandations Seuils (basées sur grille)

### Modèle Triggered (recommandé pour dates tradables)

**Rates-core (V6C)** :
- **|z| ≥ 0.8** : Accuracy **69.2%**, coverage_trig 14.6%, coverage_dir 14.9%
  - ✅ **Recommandé** : meilleur compromis précision/couverture
- |z| ≥ 1.0 : Accuracy 69.2%, coverage_trig 9.2% (trop restrictif)
- |z| ≥ 1.2 : Accuracy 57.9% (dégradation)

**Sparse (CPI+Jobs uniquement)** :
- **|z| ≥ 1.0** : Accuracy **73.3%**, coverage_trig 9.2%, coverage_dir 27.5%
  - ✅ **Recommandé** : meilleure précision si on accepte moins de triggers

**θ (neutralité)** : **0.05** (cohérent pour triggered)

### Modèle Always-on (fallback optionnel)

- θ = 0.00 : Accuracy 58.7%, coverage 37.8% (edge continu)
- θ = 0.02 : Accuracy 63.0%, coverage 15.9% (bon compromis)
- θ = 0.05 : Accuracy 81.0%, coverage 4.9% (très précis mais rare)

## 🚀 Usage

### 1. Import et utilisation basique

```python
from direction_router_v6 import predict_direction_for_cluster, load_direction_router_dependencies

# Charger dépendances
stats_map, alpha_map = load_direction_router_dependencies(
    db_path=Path('data/warehouse.duckdb'),
    alpha_file=Path('outputs/alpha_weights.csv'),
    horizon='1h'
)

# Events avec actuals connus (DataFrame avec colonnes: event_key, actual, estimate)
events_df = load_events_for_date('2024-11-15')

# Prédire direction
result = predict_direction_for_cluster(
    events_actuals=events_df,
    stats_map=stats_map,
    alpha_map=alpha_map,
    trigger_z=0.8,  # Seuil recommandé
    theta=0.05
)

print(f"Direction: {result.direction}")  # UP, DOWN, ou UNKNOWN
print(f"Score S: {result.score}")
print(f"Trigger activé: {result.has_trigger}")
```

### 2. CLI pour date spécifique

```bash
python predict_direction_tradable_date.py --date 2024-11-15 --trigger-z 0.8 --save-audit
```

### 3. Audit log complet

Chaque prédiction génère un audit log avec :
- Liste des events core présents
- Leur surprise_z
- Contribution signée dans S
- Flag trigger (|z| >= trigger_z)
- Direction finale

Format JSON sauvegardé dans `outputs/direction_audit/`.

## 📊 Interprétation Résultats

### Direction
- **UP** : EURUSD monte (USD baisse) → S < 0
- **DOWN** : EURUSD baisse (USD monte) → S > 0
- **UNKNOWN** : Pas de trigger OU |S| < theta

### Score S
- Convention USD : S>0 = USD bullish, S<0 = USD dovish
- Mapping final : S>0 → EURUSD DOWN, S<0 → EURUSD UP
- Normalisé par √n_active (F2)

### Trigger
- Activé si au moins un event core a |surprise_z| >= trigger_z
- Si pas de trigger et `use_fallback=False` → UNKNOWN
- Si `use_fallback=True` → utilise always-on (moins précis)

## 🔧 Intégration Pipeline

### Étape 1 : Sélection dates tradables

Dates avec clusters CPI/Jobs historiquement associés à moves forts :
- Au moins un event CPI ou Jobs
- Idéalement co-occurrence (CPI+Jobs, Jobs+Jobs)

### Étape 2 : Jour J - Après actuals

```python
# 1. Charger actuals du cluster
events_with_actuals = load_events_for_tradable_date(date_str, conn)

# 2. Prédire direction
result = predict_direction_for_cluster(
    events_actuals=events_with_actuals,
    stats_map=stats_map,
    alpha_map=alpha_map,
    trigger_z=0.8,
    theta=0.05
)

# 3. Logger audit
save_audit_log(result.to_dict())
```

### Étape 3 : Injection dans module impact

Une fois direction figée, injecter dans calculs d'impact :
- Single wave / Double wave / Zip-zag
- Conditionner sur direction prédite
- Conditionner sur force trigger (max|z|, |S_cluster|)

## 📈 Performance Validée

**Modèle triggered rates-core (|z|≥0.8, θ=0.05)** :
- Accuracy : **69.2%** sur mouvements forts
- Coverage triggers : 14.6% des dates
- Coverage directionnel : 14.9% (après filtrage neutralité)

**Modèle triggered sparse (|z|≥1.0, θ=0.05)** :
- Accuracy : **73.3%** sur mouvements forts
- Coverage triggers : 9.2% des dates
- Coverage directionnel : 27.5%

## ⚠️ Notes Importantes

1. **Convention USD→EURUSD** : Le mapping est maintenant corrigé partout (router + validate_on_new_dates.py)

2. **Familles core** : CPI, Jobless Claims, NFP, Unemployment, Retail Sales, GDP, PPI, Durable Goods, FOMC

3. **Stats requises** : Chaque event_key doit avoir (mu, sigma) dans stats_map. Si absent → skip (pas d'invention)

4. **Alpha weights** : Format `family_surp_pos` / `family_surp_neg` depuis alpha_weights.csv

5. **Fallback** : Si pas de trigger, le router retourne UNKNOWN par défaut. Activer `use_fallback_always_on=True` pour utiliser always-on (moins précis mais plus de coverage)

## 🔄 Prochaines Étapes

1. ✅ Router directionnel standardisé créé
2. ✅ Audit log implémenté
3. ✅ Seuils recommandés figés (trigger_z=0.8, theta=0.05)
4. ⏭️ Intégrer dans pipeline impact (single/double wave, etc.)
5. ⏭️ Conditionner impacts sur direction prédite

## 📁 Fichiers Créés

- `direction_router_v6.py` : Module router standardisé
- `predict_direction_tradable_date.py` : CLI pour prédiction date
- `cluster_grid_results.csv` : Grille complète résultats (seuils)
- `outputs/direction_audit/` : Logs audit par date

