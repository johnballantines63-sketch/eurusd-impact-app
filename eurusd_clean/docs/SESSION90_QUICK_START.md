# 🚀 SESSION 90 - GUIDE RAPIDE EXÉCUTION

**Objectif :** Valider coefficient 0.55 sur 10-15 dates

**Temps estimé :** 30-40 minutes

---

## ⚡ OPTION A : AUTOMATIQUE (RECOMMANDÉ)

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90
chmod +x run_validation_complete.sh
./run_validation_complete.sh
```

Le script guidera à travers les 3 étapes.

---

## 🔧 OPTION B : MANUEL (ÉTAPE PAR ÉTAPE)

### Étape 1 : Diagnostic 05.09 (5 min)

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90
python3 diagnose_0509_detailed.py
```

**Observer :**
- Nombre événements
- Surprise max
- Coverage estimate/forecast/previous
- Hypothèses cause outlier

---

### Étape 2 : Liste Dates (2 min)

```bash
python3 list_available_dates.py
```

**Actions :**
1. Lire output console (top 20 dates)
2. Ouvrir `dates_disponibles_session90.csv`
3. Noter 10-15 dates diversifiées :
   - 3-4 NFP
   - 3-4 CPI
   - 2-3 Jobless Claims
   - 1-2 Retail Sales

---

### Étape 3 : Configuration (5 min)

Éditer `test_multi_dates_extended.py` ligne 31 :

```python
TEST_DATES = [
    # Session 89 (garder)
    {'date': '2025-08-01', 'time': '12:30:00', 'name': '01 Août (NFP 500%)', 'type': 'NFP'},
    {'date': '2025-09-17', 'time': '12:30:00', 'name': '17 Sept (Standard)', 'type': 'CPI'},
    {'date': '2025-09-05', 'time': '12:30:00', 'name': '05 Sept (NFP)', 'type': 'NFP'},
    
    # AJOUTER ICI 7-12 dates du CSV
    {'date': '2025-XX-XX', 'time': '12:30:00', 'name': 'Description', 'type': 'NFP/CPI/Jobless/Retail'},
    # ...
]
```

---

### Étape 4 : Validation (10-20 min)

```bash
python3 test_multi_dates_extended.py
```

**Répondre "y" si < 10 dates** (pour test rapide)

**Observer sortie console :**
- Tableau résultats
- MAE global
- Tests < 30 pips
- Outliers

---

## 📊 INTERPRÉTER RÉSULTATS

### ✅ SUCCÈS : MAE < 30 pips, 0 outliers, N ≥ 10

```
✅✅✅ VALIDATION RÉUSSIE !
   MAE < 30 pips : ✅ (25.2)
   0 outliers    : ✅ (0)
   N ≥ 10        : ✅ (12)

🎯 COEFFICIENT 0.55 VALIDÉ POUR PRODUCTION
```

**Action :** Intégration production Session 91

---

### ⚠️ PARTIEL : MAE 30-35 pips OU 1-2 outliers

```
⚠️ VALIDATION PARTIELLE
   MAE < 30 pips : ❌ (32.1)
   0 outliers    : ✅ (0)
   N ≥ 10        : ✅ (11)
```

**Action :** Ajustements mineurs Session 91 puis intégration

---

### ❌ ÉCHEC : MAE > 35 pips OU 3+ outliers

```
⚠️ VALIDATION PARTIELLE
   MAE < 30 pips : ❌ (42.3)
   0 outliers    : ❌ (3)
   N ≥ 10        : ✅ (10)
```

**Action :** Analyse approfondie Session 91, corrections

---

## 🎯 DÉCISIONS RAPIDES

| MAE Global | Outliers | N dates | Décision |
|------------|----------|---------|----------|
| < 30 pips | 0 | ≥ 10 | ✅ **Intégrer S91** |
| 30-35 pips | 0-1 | ≥ 10 | ⚠️ **Ajuster S91** |
| > 35 pips | 2+ | ≥ 10 | ❌ **Analyser S91** |
| Tout | Tout | < 10 | ⚠️ **Ajouter dates** |

---

## 📝 FICHIERS GÉNÉRÉS

Après exécution complète :

```
scripts/session90/
├── dates_disponibles_session90.csv    ← Liste dates HIGH
└── validation_results_session90.csv   ← Résultats détaillés
```

---

## 🔑 COMMANDES UTILES

```bash
# Réexécuter validation après ajout dates
python3 test_multi_dates_extended.py

# Voir résultats détaillés
cat validation_results_session90.csv

# Relire dates disponibles
cat dates_disponibles_session90.csv | head -20

# Compter dates dans CSV
wc -l dates_disponibles_session90.csv
```

---

## ⚠️ TROUBLESHOOTING

**Erreur "ModuleNotFoundError: surprise_utils"**
→ Vérifier que Session 89 existe : `ls ../session89/surprise_utils.py`

**Erreur "No such file: warehouse.duckdb"**
→ Vérifier DB : `ls ~/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb`

**Erreur "Aucun événement trouvé"**
→ Vérifier date format : YYYY-MM-DD (ex: 2025-08-01)

**Script bloqué "Continuer avec 3 dates ? (y/n)"**
→ Taper 'y' puis Entrée (ou 'n' pour annuler et ajouter dates)

---

## 💡 CONSEILS

1. **Toujours commencer par Option A (automatique)** - guidage complet

2. **Sélection dates diversifiées** - ne pas prendre 10 NFP uniquement

3. **Vérifier CSV avant configurer** - éviter typos dans dates

4. **Lire output console en entier** - statistiques par type utiles

5. **Sauvegarder résultats** - CSV pour référence future

---

**Temps total : 30-40 min**  
**Prêt ? → Exécuter Option A** ⚡

---

_Guide rapide Session 90 - Validation étendue_  
_26 octobre 2025_
