# SESSION 114 - TEST & INTÉGRATION

**Tokens:** ~75,000 / 190,000 (39%)  
**Date:** 06 novembre 2025

---

## 🎯 OBJECTIF

Valider que la logique overlapping prédit **56.2 pips** avant d'intégrer dans le Planificateur.

---

## 🧪 ÉTAPE 1: TEST COMPLET (OBLIGATOIRE)

### **Lancer le test :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Rendre exécutable
chmod +x scripts/session114/run_test.sh

# Lancer
./scripts/session114/run_test.sh
```

### **Résultats attendus :**

```
✅ 10 événements chargés
🔧 1 événement(s) sans estimate exclu(s)
✅ 2 cluster(s) détecté(s)

📊 Cluster 1 (14:30): 37.4 pips
📊 Cluster 2 (14:45): ~19 pips

Pattern: overlapping
Pullback: ~27 pips

IMPACT TOTAL: 56.2 pips ✅

VALIDATION MT5:
✅ Cluster 1: MAE < 1 pip
✅ Pullback: MAE < 3 pips
✅ TOTAL: MAE < 1 pip

🎉 SUCCÈS: OK pour intégration Planificateur
```

---

## ✅ ÉTAPE 2: INTÉGRATION (SI TEST OK)

**SEULEMENT si test réussi**, intégrer dans Planificateur :

```bash
python scripts/session114/integrate_cluster_calculator.py
```

Puis relancer Streamlit et tester.

---

## ❌ SI TEST ÉCHOUE

**NE PAS intégrer dans Planificateur !**

Actions :
1. Analyser les écarts dans le test
2. Ajuster formules overlapping dans `cluster_impact_calculator.py`
3. Relancer test jusqu'à succès
4. ALORS intégrer

---

## 📊 CRITÈRES DE SUCCÈS

- [ ] Cluster 1 : MAE < 5 pips (vs 37.3 réel)
- [ ] Pullback : MAE < 5 pips (vs 26.8 réel)
- [ ] TOTAL : MAE < 10 pips (vs 56.2 réel)
- [ ] Pattern overlapping détecté
- [ ] 2 clusters identifiés (9+1 events)

Si TOUS validés → OK intégration ✅  
Sinon → Ajuster formules ⚠️

---

## 📁 FICHIERS SESSION 114

```
scripts/session114/
├── test_overlapping_complete_11sept.py  # Test complet ⭐
├── run_test.sh                          # Launcher
├── integrate_cluster_calculator.py      # Intégration (après test)
├── SPECIFICATIONS.md                    # Specs détaillées
└── README.md                            # Ce fichier
```

---

## 🔧 DÉPANNAGE

### **Erreur "module not found"**
```bash
# Vérifier qu'on est dans eurusd_clean/
pwd

# Activer venv
source .venv/bin/activate
```

### **Erreur DB**
```bash
# Vérifier que warehouse.duckdb existe
ls -lh app/data/warehouse.duckdb
```

### **Test échoue**
```bash
# Lire la sortie complète
./scripts/session114/run_test.sh > test_output.txt 2>&1
cat test_output.txt
```

---

## 📋 WORKFLOW COMPLET

1. **TEST** : `./scripts/session114/run_test.sh`
   - Valide logique complète
   - Vérifie 56.2 pips

2. **SI OK** : Intégrer Planificateur
   - Backup auto créé
   - Modifications appliquées

3. **VÉRIFIER** : Relancer Streamlit
   - Tester 11 septembre
   - Comparer avec résultats test

4. **SI KO** : Restaurer backup
   - Analyser différences
   - Ajuster et retester

---

**Prochaine action :** Lancer `run_test.sh` ! 🚀

---

**Session:** 114  
**Auteur:** André Valentin avec Claude
