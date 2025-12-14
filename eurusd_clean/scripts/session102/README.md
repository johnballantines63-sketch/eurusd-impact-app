# 📊 Session 102 - Chargement Données Réelles

## 🎯 Objectif

Charger les **VRAIES données événements** depuis `warehouse.duckdb` pour résoudre le problème identifié en Session 101.5 : toutes les analyses utilisaient des valeurs hardcodées (base_score=44.31, surprise=33.33%, num_events=11) qui empêchaient de trouver des corrélations.

## 🔧 Scripts

### 1. load_real_event_data.py

**Mission :** Pour chaque date dans `real_impacts_TIMEZONE_FIX_FINAL.csv`, charger depuis la DB :
- `base_score_real` : Moyenne empirical_score des événements HIGH IMPACT
- `surprise_real` : Max |actual - estimate| / |estimate| × 100
- `num_events_real` : Nombre événements HIGH IMPACT

**Critères HIGH IMPACT :**
- Country = 'US'
- empirical_score > 40
- empirical_score IS NOT NULL

**Output :** `real_event_data.csv`

**Colonnes output :**
```
date,base_score_real,surprise_real,num_events_real,impact_real
2025-09-11,44.31,33.33,9,57.1
...
```

### 2. analyze_with_real_data.py

**Mission :** Utiliser les données réelles pour :
1. Calculer prédictions avec Formule V2.4
2. Trouver amplification parfaite (scipy optimize)
3. Tester corrélations variables vs amp_parfaite
4. Décider formule finale

**Output :** `analysis_real_data_complete.csv`

## 🚀 Exécution

```bash
# Étape 1 : Charger données réelles
chmod +x run_load_data.sh
./run_load_data.sh

# Étape 2 : Analyser avec vraies données
chmod +x run_analyze.sh
./run_analyze.sh
```

## ⚠️ Points d'Attention

### Timezone
- Événements dans DB : Bern time (+02:00)
- Query par DATE seule (pas d'heure) : `DATE(e.ts_utc) = ?`
- Pas besoin de conversion timezone car on filtre par date

### Surprise Calculation
Fallback prioritaire :
1. estimate (priorité)
2. forecast (si estimate NULL)
3. previous (si forecast NULL)

### Événements Multiples
Si plusieurs événements simultanés (ex: CPI core + CPI yoy) :
- **Score** : Moyenne de tous les scores
- **Surprise** : Maximum de toutes les surprises
- **Num events** : Compte TOUS les événements

## 📊 Validation

**AVANT (Session 101.5 - données hardcodées) :**
```
base_score = 44.31 pour TOUTES dates
surprise = 33.33% pour TOUTES dates
num_events = 11 pour TOUTES dates
→ Variance nulle → Corrélations impossibles
```

**APRÈS (Session 102 - données réelles) :**
```
base_score varie : 40 à 80+
surprise varie : 0% à 100%+
num_events varie : 1 à 15+
→ Variance non-nulle → Corrélations possibles !
```

## 📈 Métriques Attendues

**Si tout fonctionne :**
- ✅ 32 dates avec données réelles chargées
- ✅ Variance non-nulle pour base_score, surprise, num_events
- ✅ Au moins 1 corrélation > 0.3
- ✅ MAE avec vraies données < 31.44 pips (baseline hardcodée)

## 🔗 Fichiers Requis

**Input :**
- `../session99/real_impacts_TIMEZONE_FIX_FINAL.csv` (32 dates)
- `../../warehouse.duckdb` (base événements)

**Output :**
- `real_event_data.csv` (données réelles chargées)
- `analysis_real_data_complete.csv` (analyse complète)

## 🎯 Prochaine Session

Si corrélations fortes (> 0.5) → **Créer formule multi-variables**
Si corrélations faibles (< 0.3) → **Rester baseline amp=2.5**
