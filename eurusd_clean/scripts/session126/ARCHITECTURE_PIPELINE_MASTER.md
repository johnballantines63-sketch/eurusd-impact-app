# ARCHITECTURE PIPELINE MASTER - Session 126

**Date :** 11 novembre 2025  
**Objectif :** Pipeline automatisé pour calibrer fonction amplification sur N'IMPORTE QUEL event_type

---

## 🎯 VISION GLOBALE

```
INPUT : python calibrate_universal_amplification.py --event_type="Retail Sales"
    ↓
PIPELINE AUTOMATISÉ (5 modules)
    ↓
OUTPUT : Fonction amp(R²) calibrée + Métriques + Décision (INTEGRATE/REJECT)
```

---

## 📦 ARCHITECTURE MODULAIRE

### **MODULE 1 : find_matching_clusters()**
**Rôle :** Trouve clusters identiques (composition + timing)

**Input :**
- event_type (string) : "Retail Sales", "NFP", etc.
- min_occurrences (int) : Minimum 3 répétitions
- time_window_minutes (int) : ±5 min

**Logique :**
1. Charger événements type spécifié depuis DB
2. Créer signature cluster (composition événements)
3. Grouper par fenêtres temporelles (±5 min)
4. Identifier clusters répétitifs (min_occurrences)
5. Mesurer impact réel pour chaque occurrence

**Output :**
```python
{
    'cluster_id': 'retail_sales_cluster_1',
    'signature': ['Retail Sales', ...],
    'occurrences': [
        {'date': '2023-01-13T13:30:00Z', 'impact_pips': 45.2},
        {'date': '2023-02-15T13:30:00Z', 'impact_pips': 52.8},
        ...
    ],
    'count': 12
}
```

**Réutilisation :** `scripts/session125/find_matching_clusters.py` (adapter event_type)

---

### **MODULE 2 : calculate_r2_trends()**
**Rôle :** Calcule R² tendance pré-cluster (dernière inversion)

**Input :**
- clusters (list) : Output Module 1
- window (int) : 240 min FIXE
- lookback_days (int) : 30 jours
- min_amplitude_pips (int) : 30 pips

**Logique :**
1. Pour chaque occurrence cluster :
   - Charger prix 30 jours avant
   - Détecter swing highs/lows (window 240)
   - Identifier dernière inversion (HIGH→LOW ou LOW→HIGH)
   - Calculer R² régression linéaire (inversion → cluster)
2. Enrichir cluster avec R² + durée + amplitude

**Output :**
```python
{
    'cluster_id': 'retail_sales_cluster_1',
    'occurrences': [
        {
            'date': '2023-01-13T13:30:00Z',
            'impact_pips': 45.2,
            'r2_trend': 0.65,
            'duration_hours': 3.2,
            'amplitude_pips': 38.5
        },
        ...
    ]
}
```

**Réutilisation :** `scripts/session125/calculate_r2_trends.py` (adapter input)

---

### **MODULE 3 : calibrate_amplification_function()**
**Rôle :** Calibre fonction amp = f(R²) (linéaire, quadratique, log)

**Input :**
- clusters_with_r2 (list) : Output Module 2
- event_families_scores (CSV) : Scores empiriques
- models (list) : ['linear', 'quadratic', 'logarithmic']

**Logique :**
1. Pour chaque occurrence :
   - Calculer amplification idéale : `amp_ideal = impact_measured / (total_score × sqrt(n))`
2. Créer dataset (R², amp_ideal)
3. Tester 3 modèles :
   - Linéaire : amp = a + b×R²
   - Quadratique : amp = a + b×R² + c×R²²
   - Logarithmique : amp = a + b×log(R²+ε)
4. Choisir meilleur (R² fit maximal)
5. Valider qualité (MAE fit)

**Output :**
```python
{
    'best_model': 'quadratic',
    'formula': 'amp = 0.041 + 0.050×R² - 0.007×R²²',
    'parameters': {
        'a': 0.040833,
        'b': 0.050220,
        'c': -0.006553
    },
    'metrics': {
        'r2_fit': 0.1394,
        'mae_fit': 0.0256
    }
}
```

**Réutilisation :** `scripts/session125/calibrate_amplification_function.py`

---

### **MODULE 4 : validate_predictions()**
**Rôle :** Valide prédictions avec fonction calibrée vs baseline

**Input :**
- amplification_function (Callable) : Fonction calibrée Module 3
- clusters_with_r2 (list) : Output Module 2
- baseline_amp (float) : 2.5 (référence)

**Logique :**
1. Pour chaque occurrence :
   - Prédire impact avec fonction calibrée
   - Calculer erreur vs impact mesuré
   - Prédire impact avec baseline (amp=2.5)
   - Calculer erreur baseline
2. Calculer métriques globales :
   - MAE fonction vs MAE baseline
   - RMSE fonction vs RMSE baseline
   - Amélioration % = (MAE_baseline - MAE_fonction) / MAE_baseline × 100

**Output :**
```python
{
    'n_samples': 12,
    'mae_function': 21.3,
    'mae_baseline': 145.8,
    'rmse_function': 28.5,
    'rmse_baseline': 162.4,
    'improvement_mae_pct': 85.4,
    'improvement_rmse_pct': 82.5
}
```

**Implémentation :** NOUVEAU (créer dans pipeline master)

---

### **MODULE 5 : decide_integration()**
**Rôle :** Décision automatique INTEGRATE / TEST_MORE / REJECT

**Input :**
- validation_metrics (dict) : Output Module 4

**Logique :**
```python
improvement = validation_metrics['improvement_mae_pct']

if improvement >= 50:
    decision = "INTEGRATE"
    message = "EXCELLENT - Intégration immédiate recommandée"
elif improvement >= 30:
    decision = "INTEGRATE"
    message = "BON - Amélioration significative, intégration OK"
elif improvement >= 10:
    decision = "TEST_MORE"
    message = "MODÉRÉ - Valider sur autre famille avant intégration"
else:
    decision = "REJECT"
    message = "FAIBLE - Fonction spécifique nécessaire pour cette famille"
```

**Output :**
```python
{
    'decision': 'INTEGRATE',
    'message': 'BON - Amélioration significative, intégration OK',
    'confidence': 'HIGH',
    'recommendation': 'Intégrer fonction universelle dans Planificateur V2.5'
}
```

**Implémentation :** NOUVEAU (créer dans pipeline master)

---

## 🚀 SCRIPT MASTER - calibrate_universal_amplification.py

### **Structure Globale**

```python
#!/usr/bin/env python3
"""
Pipeline Master - Calibration Universelle Amplification
Session 126 - André Valentin avec Claude

Usage:
    python calibrate_universal_amplification.py --event_type="Retail Sales"
    python calibrate_universal_amplification.py --event_type="Fed Interest Rate Decision" --min_occurrences=2
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

# Imports modules Session 125
from find_matching_clusters import find_matching_clusters
from calculate_r2_trends import calculate_r2_trends_for_clusters
from calibrate_amplification_function import calibrate_amplification

# Imports nouveaux modules
from validate_predictions import validate_predictions_with_baseline
from decide_integration import decide_integration


def calibrate_event_type_amplification(
    event_type: str,
    min_occurrences: int = 3,
    window: int = 240,
    lookback_days: int = 30,
    output_dir: Path = Path("./calibration_results")
) -> dict:
    """
    Pipeline complet calibration amplification pour un type d'événement.
    
    Args:
        event_type: Type événement ("Retail Sales", "NFP", "CPI", etc.)
        min_occurrences: Minimum répétitions cluster (default: 3)
        window: Window détection inversions en minutes (default: 240 FIXE)
        lookback_days: Historique prix en jours (default: 30)
        output_dir: Répertoire sortie résultats
        
    Returns:
        {
            'event_type': str,
            'function': dict (paramètres fonction),
            'metrics': dict (MAE, RMSE, amélioration),
            'decision': dict (INTEGRATE/REJECT + message),
            'clusters_analyzed': int,
            'timestamp': str
        }
    """
    
    print(f"
{'='*70}")
    print(f"PIPELINE CALIBRATION UNIVERSELLE - Session 126")
    print(f"Event Type: {event_type}")
    print(f"{'='*70}
")
    
    # ========================================
    # MODULE 1 : MATCHING CLUSTERS
    # ========================================
    print("
[1/5] MODULE 1 : Recherche clusters identiques...")
    
    clusters = find_matching_clusters(
        event_type=event_type,
        min_occurrences=min_occurrences,
        time_window_minutes=5
    )
    
    if not clusters or len(clusters) == 0:
        return {
            'event_type': event_type,
            'error': 'NO_CLUSTERS_FOUND',
            'message': f'Aucun cluster trouvé pour {event_type} (min_occurrences={min_occurrences})'
        }
    
    print(f"   ✓ {len(clusters)} clusters trouvés")
    total_occurrences = sum(len(c['occurrences']) for c in clusters)
    print(f"   ✓ {total_occurrences} occurrences totales")
    
    # ========================================
    # MODULE 2 : CALCUL R² TENDANCES
    # ========================================
    print("
[2/5] MODULE 2 : Calcul R² tendances pré-cluster...")
    
    clusters_with_r2 = calculate_r2_trends_for_clusters(
        clusters=clusters,
        window=window,
        lookback_days=lookback_days,
        min_amplitude_pips=30
    )
    
    # Statistiques R²
    all_r2 = [occ['r2_trend'] for c in clusters_with_r2 for occ in c['occurrences'] if 'r2_trend' in occ]
    avg_r2 = sum(all_r2) / len(all_r2) if all_r2 else 0
    print(f"   ✓ R² moyen : {avg_r2:.3f}")
    print(f"   ✓ R² min-max : [{min(all_r2):.3f}, {max(all_r2):.3f}]")
    
    # ========================================
    # MODULE 3 : CALIBRATION FONCTION
    # ========================================
    print("
[3/5] MODULE 3 : Calibration fonction amp(R²)...")
    
    function_result = calibrate_amplification(
        clusters_with_r2=clusters_with_r2,
        models=['linear', 'quadratic', 'logarithmic']
    )
    
    print(f"   ✓ Meilleur modèle : {function_result['best_model']}")
    print(f"   ✓ R² fit : {function_result['metrics']['r2_fit']:.4f}")
    print(f"   ✓ MAE fit : {function_result['metrics']['mae_fit']:.4f}")
    
    # ========================================
    # MODULE 4 : VALIDATION PRÉDICTIONS
    # ========================================
    print("
[4/5] MODULE 4 : Validation prédictions vs baseline...")
    
    validation_metrics = validate_predictions_with_baseline(
        amplification_function=function_result['function'],
        clusters_with_r2=clusters_with_r2,
        baseline_amp=2.5
    )
    
    print(f"   ✓ MAE fonction : {validation_metrics['mae_function']:.2f} pips")
    print(f"   ✓ MAE baseline : {validation_metrics['mae_baseline']:.2f} pips")
    print(f"   ✓ Amélioration : +{validation_metrics['improvement_mae_pct']:.1f}%")
    
    # ========================================
    # MODULE 5 : DÉCISION INTÉGRATION
    # ========================================
    print("
[5/5] MODULE 5 : Décision intégration...")
    
    decision_result = decide_integration(
        validation_metrics=validation_metrics
    )
    
    print(f"   ✓ Décision : {decision_result['decision']}")
    print(f"   ✓ Message : {decision_result['message']}")
    
    # ========================================
    # EXPORT RÉSULTATS
    # ========================================
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        'event_type': event_type,
        'parameters': {
            'min_occurrences': min_occurrences,
            'window': window,
            'lookback_days': lookback_days
        },
        'clusters_analyzed': len(clusters_with_r2),
        'total_occurrences': total_occurrences,
        'function': function_result,
        'validation': validation_metrics,
        'decision': decision_result,
        'timestamp': datetime.now().isoformat()
    }
    
    # JSON détaillé
    json_path = output_dir / f"{event_type.lower().replace(' ', '_')}_calibration.json"
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"
✓ Résultats exportés : {json_path}")
    
    # Rapport Markdown
    markdown_path = output_dir / f"{event_type.lower().replace(' ', '_')}_report.md"
    with open(markdown_path, 'w') as f:
        f.write(generate_markdown_report(result))
    
    print(f"✓ Rapport créé : {markdown_path}")
    
    print(f"
{'='*70}")
    print(f"PIPELINE COMPLÉTÉ - Décision : {decision_result['decision']}")
    print(f"{'='*70}
")
    
    return result


def generate_markdown_report(result: dict) -> str:
    """Génère rapport Markdown formaté"""
    
    event_type = result['event_type']
    function = result['function']
    validation = result['validation']
    decision = result['decision']
    
    report = f"""# Calibration Amplification - {event_type}

**Date :** {result['timestamp'][:10]}  
**Clusters analysés :** {result['clusters_analyzed']}  
**Occurrences totales :** {result['total_occurrences']}

---

## 🎯 FONCTION CALIBRÉE

**Modèle :** {function['best_model']}  
**Formule :** `{function['formula']}`

**Paramètres :**
```python
a = {function['parameters']['a']:.6f}
b = {function['parameters']['b']:.6f}
c = {function['parameters'].get('c', 'N/A')}
```

**Métriques Fit :**
- R² fit : {function['metrics']['r2_fit']:.4f}
- MAE fit : {function['metrics']['mae_fit']:.4f}

---

## 📊 VALIDATION

**Prédictions :**
- MAE fonction : {validation['mae_function']:.2f} pips
- MAE baseline : {validation['mae_baseline']:.2f} pips
- **Amélioration : +{validation['improvement_mae_pct']:.1f}%**

**RMSE :**
- RMSE fonction : {validation['rmse_function']:.2f} pips
- RMSE baseline : {validation['rmse_baseline']:.2f} pips
- **Amélioration : +{validation['improvement_rmse_pct']:.1f}%**

---

## 🎯 DÉCISION

**Statut :** {decision['decision']}  
**Message :** {decision['message']}  
**Confiance :** {decision['confidence']}

**Recommandation :** {decision['recommendation']}

---

**Généré par :** Pipeline Master Session 126
"""
    
    return report


def main():
    """CLI Entry Point"""
    
    parser = argparse.ArgumentParser(
        description="Pipeline Master - Calibration Universelle Amplification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python calibrate_universal_amplification.py --event_type="Retail Sales"
  python calibrate_universal_amplification.py --event_type="Fed Interest Rate Decision" --min_occurrences=2
  python calibrate_universal_amplification.py --event_type="CPI" --output_dir="./results_cpi"
        """
    )
    
    parser.add_argument(
        '--event_type',
        type=str,
        required=True,
        help='Type événement à calibrer (ex: "Retail Sales", "NFP", "CPI")'
    )
    
    parser.add_argument(
        '--min_occurrences',
        type=int,
        default=3,
        help='Minimum répétitions cluster (default: 3)'
    )
    
    parser.add_argument(
        '--window',
        type=int,
        default=240,
        help='Window détection inversions en minutes (default: 240 FIXE)'
    )
    
    parser.add_argument(
        '--lookback_days',
        type=int,
        default=30,
        help='Historique prix en jours (default: 30)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=Path,
        default=Path("./calibration_results"),
        help='Répertoire sortie résultats'
    )
    
    args = parser.parse_args()
    
    # Exécuter pipeline
    result = calibrate_event_type_amplification(
        event_type=args.event_type,
        min_occurrences=args.min_occurrences,
        window=args.window,
        lookback_days=args.lookback_days,
        output_dir=args.output_dir
    )
    
    # Exit code selon décision
    if 'error' in result:
        return 1
    elif result['decision']['decision'] == 'INTEGRATE':
        return 0
    elif result['decision']['decision'] == 'TEST_MORE':
        return 2
    else:  # REJECT
        return 3


if __name__ == "__main__":
    exit(main())
```

---

## 📋 DÉPENDANCES

**Scripts Session 125 (réutilisés) :**
```python
from find_matching_clusters import find_matching_clusters
from calculate_r2_trends import calculate_r2_trends_for_clusters
from calibrate_amplification_function import calibrate_amplification
```

**Nouveaux modules (à créer) :**
```python
from validate_predictions import validate_predictions_with_baseline
from decide_integration import decide_integration
```

---

## 🎯 USAGE

### **Exemple 1 : Retail Sales**
```bash
python calibrate_universal_amplification.py --event_type="Retail Sales"
```

### **Exemple 2 : Fed Decisions (rares)**
```bash
python calibrate_universal_amplification.py \
    --event_type="Fed Interest Rate Decision" \
    --min_occurrences=2
```

### **Exemple 3 : Test Non-Régression CPI**
```bash
python calibrate_universal_amplification.py \
    --event_type="CPI" \
    --output_dir="./test_cpi"
```

---

## 📊 OUTPUT

**Fichiers générés :**
```
calibration_results/
├── retail_sales_calibration.json       → Résultats complets JSON
└── retail_sales_report.md              → Rapport Markdown
```

**Structure JSON :**
```json
{
  "event_type": "Retail Sales",
  "parameters": {...},
  "clusters_analyzed": 12,
  "total_occurrences": 45,
  "function": {
    "best_model": "quadratic",
    "formula": "amp = a + b×R² + c×R²²",
    "parameters": {"a": 0.041, "b": 0.050, "c": -0.007},
    "metrics": {"r2_fit": 0.14, "mae_fit": 0.026}
  },
  "validation": {
    "mae_function": 21.3,
    "mae_baseline": 145.8,
    "improvement_mae_pct": 85.4
  },
  "decision": {
    "decision": "INTEGRATE",
    "message": "EXCELLENT - Intégration immédiate",
    "confidence": "HIGH"
  }
}
```

---

## 🚀 PROCHAINES ÉTAPES

1. **Créer modules nouveaux** :
   - `validate_predictions.py`
   - `decide_integration.py`

2. **Adapter modules Session 125** :
   - Rendre `find_matching_clusters()` paramétrable (event_type)
   - Rendre `calculate_r2_trends()` compatible avec liste clusters

3. **Tester pipeline** :
   - Test non-régression CPI (attendu : résultats Session 125)
   - Test non-régression NFP (attendu : +88% amélioration)

4. **Tester nouvelles familles** :
   - Retail Sales
   - Fed Interest Rate Decision

---

**Auteur :** André Valentin avec Claude  
**Date :** 11 novembre 2025  
**Session :** 126
