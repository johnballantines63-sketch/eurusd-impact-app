# 🚀 QUICK START - SESSION 73

**Pour utilisateur pressé qui veut juste exécuter la pipeline**

---

## ⚡ EN 3 COMMANDES

```bash
# 1. Aller dans le répertoire
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

# 2. Tester l'environnement (10 secondes)
python3 scripts/test_environment_session73.py

# 3. Exécuter la pipeline (5-10 minutes)
python3 scripts/run_pipeline_session73.py
```

C'est tout ! ✅

---

## 📊 CE QUI VA SE PASSER

### Étape 1 : Scanner (30 sec - 1 min)
```
🔍 Scanning prices_1m database...
   Finding movements > 100 pips in last 22 months
   
✅ 50 strong movements detected
   Top movement: 193 pips on 2025-08-01
   Output: data/movements_strong_session73.csv
```

### Étape 2 : Dataset (2-3 min)
```
📊 Crossing movements with events...
   For each movement: finding events within ±10 min
   Calculating cluster metrics (scores, surprises, concordance)
   
✅ Dataset created: 50 movements × 15 features
   Movements with events: 35 (70%)
   Output: data/dataset_complete_session73.csv
```

### Étape 3 : ML Analysis (1 min)
```
🤖 Running ML analysis...
   - Correlations (pandas)
   - Linear regression (sklearn)
   - K-Means clustering (4 clusters)
   
✅ Results:
   Regression: R²=0.7, MAE=18 pips
   Clusters: 4 movement types identified
   Outputs: 
   - regression_results_session73.txt
   - clustering_results_session73.txt
   - dataset_clustered_session73.csv
```

---

## 📁 FICHIERS GÉNÉRÉS

Tous dans `/fx_impact_app/data/` :

1. **movements_strong_session73.csv** - Top 50 mouvements forts
2. **dataset_complete_session73.csv** - Dataset complet avec features
3. **regression_results_session73.txt** - Coefficients formule Impact V2.0
4. **clustering_results_session73.txt** - Caractéristiques clusters
5. **dataset_clustered_session73.csv** - Dataset avec cluster IDs

---

## 🔍 EXAMINER RÉSULTATS

```bash
# Formule Impact V2.0
cat data/regression_results_session73.txt

# Types de mouvements identifiés
cat data/clustering_results_session73.txt

# Dataset complet (Excel/Pandas)
open data/dataset_complete_session73.csv
```

---

## ⚠️ SI ERREUR

**Erreur : "warehouse.duckdb not found"**
```bash
# Vérifier emplacement DB
ls -lh data/warehouse.duckdb

# Si absent, chercher dans fx_impact_app/
find . -name "warehouse.duckdb" -type f
```

**Erreur : "Module 'sklearn' not found"**
```bash
# Installer scikit-learn
pip install scikit-learn

# Ou avec le requirements.txt du projet
pip install -r requirements.txt
```

**Erreur : "movements_strong_session73.csv not found" (Étape 2)**
```bash
# Étape 1 n'a pas fonctionné, exécuter manuellement
python3 scripts/scanner_movements_session73.py
```

---

## 💡 CONSEILS

### Première Exécution
1. Laisser tourner sans interruption (5-10 min total)
2. Ne pas fermer terminal pendant exécution
3. Vérifier espace disque (besoin ~50 MB pour CSV outputs)

### Ajuster Paramètres
Si tu veux changer les paramètres (avancé) :

**Scanner** (`scanner_movements_session73.py`) :
- `min_impact_pips = 100.0` → Seuil minimum (défaut 100 pips)
- `limit = 50` → Nombre mouvements (défaut 50)
- `start_date = "2024-01-01"` → Date début analyse

**Dataset** (`create_dataset_session73.py`) :
- `time_window_minutes = 10` → Fenêtre recherche événements (±10 min)

**ML** (`analyze_correlations_session73.py`) :
- `n_clusters = 4` → Nombre clusters K-Means (défaut 4)

---

## 🎯 PROCHAINES ÉTAPES

Après exécution réussie :

1. **Examiner résultats ML** (txt files)
2. **Créer formulas_validated_v2.py** (Session 74)
3. **Intégrer au Planificateur V2.5** (Session 74)
4. **Valider sur nouveaux cas** (Session 75)

---

## 📞 AIDE

Si problème :
1. Relire `SESSION73_README.md` (documentation complète)
2. Exécuter `test_environment_session73.py` pour diagnostiquer
3. Vérifier logs d'erreur dans terminal

---

*Quick Start - Session 73*  
*Temps total : 5-10 minutes*  
*Niveau : Débutant OK*
