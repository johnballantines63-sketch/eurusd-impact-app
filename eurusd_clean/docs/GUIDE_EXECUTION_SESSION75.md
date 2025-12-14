# 🚀 GUIDE EXÉCUTION PIPELINE SESSION 75

## Objectif
Améliorer dataset Session 74 : 1 jour concentré → 50+ dates diversifiées

## Problème Session 74 Identifié
- **50 mouvements sur 1 SEUL jour** (1er août 2025)
- 80% mouvements sans événements
- R² = 0.541 (acceptable mais limité)
- Risque overfitting

## Solution Session 75
**Échantillonnage stratifié** : 1-2 mouvements par semaine (pas top 50 absolus)

---

## 📋 ÉTAPES D'EXÉCUTION

### Option A : Pipeline Complet (RECOMMANDÉ - 1 commande)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts
python3 pipeline_complete_session75.py
```

**Durée estimée :** 5-10 minutes  
**Outputs créés :**
- `movements_strong_session75_stratified.csv`
- `dataset_complete_session75.csv`
- `regression_results_session75.txt`

---

### Option B : Étape par Étape (Debug)

#### Étape 1 : Scanner Stratifié
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts
python3 scanner_movements_session75.py
```

**Vérifie :** Fichier `data/movements_strong_session75_stratified.csv` créé

#### Étape 2 : Dataset avec Événements
```bash
python3 create_dataset_session75.py
```

**Note :** Si ce fichier n'existe pas, utiliser `create_dataset_session73_FIXED.py` en modifiant la ligne d'input CSV

#### Étape 3 : Analyse ML
```bash
python3 analyze_correlations_session75.py
```

---

## ✅ VÉRIFICATION RÉSULTATS

### Critères Succès Session 75

| Métrique | V2.0 (S74) | V2.1 (S75) Objectif | Statut |
|----------|------------|---------------------|--------|
| Dataset | 10 mouvements | 50+ mouvements | ⏳ |
| Dates | 1 jour | 50+ jours | ⏳ |
| R² | 0.541 | >0.7 | ⏳ |
| MAE | 2.5 pips | <3 pips | ⏳ |
| Clusters | 3 | 4-5 | ⏳ |
| Couverture | 20% | 70-80% | ⏳ |

### Commandes Vérification

```bash
# Vérifier nombre lignes dataset
wc -l /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/dataset_complete_session75.csv

# Vérifier dates uniques
cut -d',' -f3 /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/dataset_complete_session75.csv | sort -u | wc -l

# Lire résultats régression
cat /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/regression_results_session75.txt
```

---

## 🎯 APRÈS EXÉCUTION

### Si R² >0.7 ✅
→ Créer `formulas_validated_v2.1.py`  
→ Progression 93% → 95%

### Si R² <0.7 ⚠️
→ Garder `formulas_validated_v2.0.py`  
→ Documenter limites dataset  
→ Envisager amélioration future

---

## 📞 EN CAS D'ERREUR

### Erreur "Module not found"
```bash
pip install pandas numpy scikit-learn duckdb
```

### Erreur "Permission denied"
```bash
chmod +x pipeline_complete_session75.py
```

### Erreur "Database locked"
```bash
# Fermer toutes connexions DuckDB
# Redémarrer terminal
```

---

## 📂 FICHIERS CRÉÉS SESSION 75

```
fx_impact_app/
├── scripts/
│   ├── scanner_movements_session75.py              ✅ Créé
│   ├── pipeline_complete_session75.py              ✅ Créé
│   ├── exec_pipeline_session75.py                  ✅ Créé
│   └── test_scanner_session75.py                   ✅ Créé
│
└── data/
    ├── movements_strong_session75_stratified.csv   ⏳ À créer
    ├── dataset_complete_session75.csv              ⏳ À créer
    └── regression_results_session75.txt            ⏳ À créer
```

---

*Guide créé Session 75 - 24 octobre 2025*
