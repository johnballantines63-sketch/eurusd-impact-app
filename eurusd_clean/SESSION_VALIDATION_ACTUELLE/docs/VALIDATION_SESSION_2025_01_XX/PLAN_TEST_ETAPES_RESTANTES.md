# Plan de Test - Étapes Restantes du Pipeline

**Date** : 2025-01-XX  
**Objectif** : Tester les étapes du pipeline qui n'ont pas encore été testées isolément

---

## 📊 ÉTAT ACTUEL DES TESTS

### ✅ Étapes Déjà Testées

| Étape | Script de Test | Statut |
|-------|----------------|--------|
| **Étape 1** : Charger Événements | `test_pipeline_etapes_1_5.py` | ✅ Testé |
| **Étape 2** : Détecter Clusters | `test_pipeline_etapes_1_5.py` | ✅ Testé |
| **Étape 3** : Définir Noyau Dur | `test_pipeline_etapes_1_5.py` | ✅ Testé |
| **Étape 4** : Rechercher Clusters Identiques | `test_etape4_clusters_identiques.py` | ✅ Testé isolément |
| **Étape 5** : Calculer Tendances | `test_etape5_tendances.py` | ✅ Testé isolément |
| **Étape 6** : Calculer Impacts Base & Amplifications | `test_corrections_etape6_8_1_8_2.py` | ✅ Testé |
| **Étape 8.1** : Calcul Impact Base (Cluster Cible) | `test_corrections_etape6_8_1_8_2.py` | ✅ Testé |
| **Étape 8.2** : Détection Tendance (Cluster Cible) | `test_corrections_etape6_8_1_8_2.py` | ✅ Testé |
| **Étape 8.4** : Ajustements Support/Résistance | `test_etapes_8_4_8_8.py` | ✅ Testé |
| **Étape 8.5** : Ajustements Patterns Finnhub | `test_etapes_8_4_8_8.py` | ✅ Testé |
| **Étape 8.6** : Détection Pattern de Prix | `test_etapes_8_4_8_8.py` | ✅ Testé |
| **Étape 8.7** : Stratégie Hybride Pattern/Formules | `test_etapes_8_4_8_8.py` | ✅ Testé |
| **Étape 8.8** : Calcul Target de Sortie | `test_etapes_8_4_8_8.py` | ✅ Testé |
| **Pipeline Complet** | `test_cas_base_pipeline_complet.py` | ✅ Testé |
| **Pipeline Multi-Dates** | `test_validation_multi_dates.py` | ✅ Testé |

### ⚠️ Étapes Non Testées Isolément

| Étape | Description | Raison |
|-------|-------------|--------|
| **Étape 7** : Analyser Relation Tendance → Amplification | Analyse corrélations entre tendance et amplification | Simple mais pas testée isolément |
| **Étape 8.3** : Prédiction d'Amplification | Hiérarchie RF par date → RF global → linéaire → moyenne | Testée dans 8.4-8.8 mais pas isolément |

---

## 🎯 PLAN DE TEST PROPOSÉ

### Test 1 : Étape 7 - Analyser Relation Tendance → Amplification

**Objectif** : Valider que l'Étape 7 fusionne correctement les données et calcule les corrélations

**Script à créer** : `scripts/test_etape7_relation_tendance_amplification.py`

**Ce qui doit être testé** :
1. ✅ Fusion correcte de `trends_df` et `impacts_df`
2. ✅ Calcul de corrélation R² vs amplification_parfaite
3. ✅ Gestion des cas vides (DataFrames vides)
4. ✅ Structure du résultat retourné

**Données nécessaires** :
- Résultats de l'Étape 5 (tendances)
- Résultats de l'Étape 6 (impacts et amplifications)

**Date de test** : 2025-09-11 (cas de référence)

---

### Test 2 : Étape 8.3 - Prédiction d'Amplification

**Objectif** : Valider la hiérarchie de prédiction d'amplification

**Script à créer** : `scripts/test_etape8_3_prediction_amplification.py`

**Ce qui doit être testé** :
1. ✅ RF par date (placeholder actuellement, retourne moyenne)
2. ✅ RF global (skipped si module n'existe pas)
3. ✅ Modèle linéaire avec `predict_amplification_from_r2` (fonction validée)
4. ✅ Fallback vers moyenne historique
5. ✅ Hiérarchie respectée (RF date → RF global → linéaire → moyenne)

**Données nécessaires** :
- Impact base (Étape 8.1)
- Tendance détectée (Étape 8.2)
- Clusters identiques avec amplifications (Étape 6)

**Date de test** : 2025-09-11 (cas de référence)

---

## 📋 STRUCTURE DES SCRIPTS DE TEST

### Structure Générale

```python
"""
Test Étape X - Description
==========================
Test isolé de l'Étape X du pipeline.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.run_pipeline_complete import PipelineExecutor
import config

def test_etape_x():
    """Test de l'Étape X"""
    # 1. Initialiser PipelineExecutor
    # 2. Exécuter étapes prérequises
    # 3. Exécuter Étape X
    # 4. Vérifier résultats
    # 5. Afficher résultats

if __name__ == "__main__":
    test_etape_x()
```

---

## ✅ CRITÈRES DE SUCCÈS

### Test Étape 7
- [ ] Fusion des DataFrames réussie
- [ ] Corrélation calculée correctement (ou NaN si pas assez de données)
- [ ] Gestion des cas vides fonctionnelle
- [ ] Structure du résultat conforme à la documentation

### Test Étape 8.3
- [ ] Hiérarchie respectée (RF date → RF global → linéaire → moyenne)
- [ ] Modèle linéaire appelé correctement avec `predict_amplification_from_r2`
- [ ] Fallback vers moyenne si pas assez de données
- [ ] Amplification prédite dans une plage raisonnable (0.5x - 3.0x)

---

## 📝 PROCHAINES ÉTAPES

1. **Créer script test Étape 7** : `scripts/test_etape7_relation_tendance_amplification.py`
2. **Créer script test Étape 8.3** : `scripts/test_etape8_3_prediction_amplification.py`
3. **Exécuter les tests** et documenter les résultats
4. **Valider** que toutes les étapes fonctionnent correctement

---

## 🔗 RÉFÉRENCES

- Documentation Étape 7 : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md` (ligne 73)
- Documentation Étape 8.3 : `docs/PIPELINE_REFERENCE/PIPELINE_ARCHITECTURE_DETAILED.md`
- Code Étape 7 : `scripts/run_pipeline_complete.py` (ligne 923)
- Code Étape 8.3 : `scripts/run_pipeline_complete.py` (dans `etape8_appliquer_cluster_cible`)

