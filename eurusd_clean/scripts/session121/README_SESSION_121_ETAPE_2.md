# 📋 SESSION 121 - VALIDATION SINGLE WAVE V2

**Date :** 08 novembre 2025  
**Objectif :** Valider détecteurs Single Wave V2 sur cas réels (ÉTAPE 2)  
**Tokens estimés :** 80-100k / 190k

---

## 🎯 OBJECTIF ÉTAPE 2

Valider `SingleWaveFortDetectorV2` et `SingleWaveIntermediateDetectorV2` sur 5+ cas réels

**Critères succès :**
- MAE moyen < 10 pips
- 3+ cas Single Fort validés (> 40 pips)
- 2+ cas Single Intermediate validés (20-40 pips)

---

## 📁 ARCHITECTURE VALIDATION

### **1. Scanner DB → Identifier Cas**
**Script :** `find_single_wave_cases_v2.py`

**Fonctionnalités :**
- Scanner événements HIGH importance (2024-2025)
- Détecter extrema locaux adaptatifs (width=2, validé rev10/rev12)
- Filtrer avec seuils ATR-based : `max(0.5 * ATR, 5 pips)`
- Identifier 1 pic dominant (> 50% amplitude totale)
- Classifier :
  - **Fort** : impact > 40 pips, pullback < 20%
  - **Intermediate** : impact 20-40 pips, pullback < 30%

**Sortie :** `single_wave_candidates.json`

```json
{
  "scan_date": "2025-11-08T...",
  "period": {"start": "2024-01-01", "end": "2025-12-31"},
  "summary": {
    "total_candidates": 15,
    "fort_count": 8,
    "intermediate_count": 7
  },
  "candidates": [
    {
      "date": "2025-09-11",
      "time": "14:30:00",
      "event_name": "US CPI MoM",
      "currency": "US",
      "pattern_type": "fort",
      "impact_pips": 45.2,
      "peak_time": "14:35:00",
      "pullback_ratio": 15.3,
      "dominance": 85.2,
      "quality_score": 0.724
    }
  ]
}
```

### **2. Validation → Tester Détecteurs V2**
**Script :** `validate_single_wave_v2.py`

**Fonctionnalités :**
- Charger cas candidats (JSON scanner)
- Pour chaque cas :
  1. Charger OHLC 1-min (event - 30min → event + 2h)
  2. Calculer baseline = close(t-1)
  3. Calculer référence MT5 (peak maximum post-event)
  4. Appliquer détecteur V2 approprié (Fort / Intermediate)
  5. Comparer impact détecté vs MT5
  6. Calculer MAE = abs(detected - mt5)
- Statistiques globales :
  - MAE moyen / écart-type / min / max
  - MAE par type (Fort / Intermediate)
  - Taux succès détection
  - Meilleur / pire cas

**Sortie :** `single_wave_validation_results.json`

```json
{
  "validation_date": "2025-11-08T...",
  "summary": {
    "total_cases": 15,
    "successful_detections": 13,
    "failed_detections": 2,
    "success_rate": 86.7,
    "mae_mean": 6.3,
    "mae_std": 2.1,
    "mae_min": 1.2,
    "mae_max": 12.5,
    "fort": {
      "total": 8,
      "successful": 7,
      "mae_mean": 5.8
    },
    "intermediate": {
      "total": 7,
      "successful": 6,
      "mae_mean": 6.9
    }
  },
  "validations": [...]
}
```

---

## 🚀 UTILISATION

### **Étape 1 : Scanner DB**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121

# Exécuter scanner
python3 find_single_wave_cases_v2.py

# OU utiliser script bash
chmod +x run_scanner.sh
./run_scanner.sh
```

**Sortie attendue :**
```
════════════════════════════════════════════════════════════════════
SCANNER SINGLE WAVE V2 - SESSION 121
════════════════════════════════════════════════════════════════════

Période: 2024-01-01 → 2025-12-31
Database: .../warehouse.duckdb

Chargement événements HIGH importance...
  → 458 événements trouvés

Analyse événements...

🟢 2025-09-11 14:30:00 - US CPI MoM                      | FORT         |  45.2 pips | Pullback 15.3% | Quality 0.724
🟡 2025-08-15 14:30:00 - US Retail Sales MoM             | INTERMEDIATE |  32.5 pips | Pullback 28.1% | Quality 0.516
...

════════════════════════════════════════════════════════════════════
RÉSULTATS SCAN
════════════════════════════════════════════════════════════════════
Candidats Single Wave trouvés: 15
  - Single Fort (> 40 pips):        8
  - Single Intermediate (20-40):    7

Objectif Session 121:
  - Single Fort:        ✅ 8/3+ requis
  - Single Intermediate: ✅ 7/2+ requis
════════════════════════════════════════════════════════════════════

Résultats sauvegardés: single_wave_candidates.json

✅ Scanner terminé avec succès!
```

### **Étape 2 : Validation Détecteurs V2**

```bash
# Exécuter validation
python3 validate_single_wave_v2.py
```

**Sortie attendue :**
```
════════════════════════════════════════════════════════════════════
VALIDATION SINGLE WAVE V2 - SESSION 121
════════════════════════════════════════════════════════════════════

Candidats chargés: 15
  - Single Fort:        8
  - Single Intermediate: 7

Validation cas...

✅ 2025-09-11 14:30:00 - US CPI MoM                      | FORT         | MAE   4.2 pips
✅ 2025-08-15 14:30:00 - US Retail Sales MoM             | INTERMEDIATE | MAE   6.8 pips
❌ 2025-07-20 14:30:00 - US Building Permits             | FORT         | Pattern non détecté par V2
...

════════════════════════════════════════════════════════════════════
RÉSULTATS VALIDATION
════════════════════════════════════════════════════════════════════
Cas testés:              15
Détections réussies:     13
Détections échouées:     2
Taux succès:             86.7%

MAE GLOBAL:
  Moyen:                 6.3 pips
  Écart-type:            2.1 pips
  Minimum:               1.2 pips
  Maximum:               12.5 pips

MAE PAR TYPE:
  Single Fort:           5.8 pips (7/8 cas)
  Single Intermediate:   6.9 pips (6/7 cas)

OBJECTIF SESSION 121:
  MAE < 10 pips:         ✅ ATTEINT (6.3 pips)
  3+ Fort validés:       ✅ ATTEINT (7 cas)
  2+ Intermediate:       ✅ ATTEINT (6 cas)
════════════════════════════════════════════════════════════════════

Résultats sauvegardés: single_wave_validation_results.json

✅ Validation terminée avec succès!
```

---

## 🔍 ANALYSE RÉSULTATS

### **Si MAE < 10 pips → ✅ ÉTAPE 2 VALIDÉE**

Passer à ÉTAPE 3 (Système validation global)

### **Si MAE > 10 pips → ⚠️ AJUSTEMENTS NÉCESSAIRES**

**Actions :**
1. Analyser cas avec MAE > 10 pips
2. Identifier cause :
   - Seuils ATR trop stricts/laxes ?
   - Garde temporelle insuffisante ?
   - Pullback ratio non adapté ?
   - Problème baseline ?
3. Ajuster paramètres V2
4. Re-valider sur tous cas

**Fichiers à modifier :**
- `scripts/session120/single_wave_detectors_v2.py`
- `scripts/session120/base_pattern_detector_v2.py`

---

## 📊 MÉTRIQUES ATTENDUES

**Objectifs Session 121 :**
- MAE moyen : < 10 pips
- Taux succès : > 80%
- Fort MAE : < 8 pips
- Intermediate MAE : < 12 pips

**Comparaison benchmarks :**
- Rev12 Double Wave : MAE 4.5 pips ✅
- Session 118 Double Wave : MAE 4.5 pips ✅
- **Single Wave V2 cible : < 10 pips**

---

## 🧪 TESTS UNITAIRES

### **Test Scanner**

```bash
# Test sur période courte (1 mois)
python3 -c "
from find_single_wave_cases_v2 import scan_single_wave_cases
candidates = scan_single_wave_cases(
    db_path='../../data/warehouse.duckdb',
    start_date='2025-09-01',
    end_date='2025-09-30'
)
print(f'Candidats trouvés: {len(candidates)}')
"
```

### **Test Validation (1 cas)**

```bash
# Test sur cas unique (11 septembre 2025)
python3 -c "
import json
from validate_single_wave_v2 import validate_single_case
from single_wave_detectors_v2 import SingleWaveFortDetectorV2, SingleWaveIntermediateDetectorV2

detector_fort = SingleWaveFortDetectorV2()
detector_int = SingleWaveIntermediateDetectorV2()

case = {
    'date': '2025-09-11',
    'time': '14:30:00',
    'event_name': 'US CPI MoM',
    'currency': 'US',
    'pattern_type': 'fort',
    'impact_pips': 45.2
}

result = validate_single_case(
    case,
    '../../data/warehouse.duckdb',
    detector_fort,
    detector_int
)

print(json.dumps(result['validation'], indent=2))
"
```

---

## 📝 PROCHAINES ÉTAPES

**Si ÉTAPE 2 réussie :**

1. ✅ Créer `SINGLE_WAVE_VALIDATION_REPORT.md`
2. ✅ Passer ÉTAPE 3 : Système validation global
   - `validate_all_patterns_v2.py`
   - Intégrer tous détecteurs (Fort, Intermediate, ZigZag, DoubleWave Rev12)
   - 10+ cas testés (mix patterns)
   - Statistiques globales (MAE, RMSE, R²)
   - Graphiques (scatter plot, distribution erreurs)

**Si ÉTAPE 2 échoue (MAE > 10 pips) :**

1. ⚠️ Analyser cas problématiques
2. ⚠️ Ajuster paramètres V2
3. ⚠️ Re-tester validation
4. ⚠️ Documenter ajustements

---

## 🎯 VALIDATION SUCCÈS ÉTAPE 2

**Checklist :**
- [ ] 5+ cas Single Wave identifiés (3 Fort + 2 Intermediate)
- [ ] MAE moyen < 10 pips
- [ ] Taux succès > 80%
- [ ] Fort MAE < 10 pips
- [ ] Intermediate MAE < 12 pips
- [ ] Résultats JSON sauvegardés
- [ ] Rapport validation créé

**Si tous ✅ → ÉTAPE 2 VALIDÉE → Passer ÉTAPE 3**

---

**Auteur :** André Valentin avec Claude  
**Date :** 08 novembre 2025  
**Session :** 121 (ÉTAPE 2)  
**Version :** 1.0
