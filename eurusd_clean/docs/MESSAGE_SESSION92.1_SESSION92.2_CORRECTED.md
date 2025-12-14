# 📋 MESSAGE SESSION 92.1 → SESSION 92.2 (CORRIGÉ)

**Date :** 27 octobre 2025  
**De :** Session 92.1 (Analyse amplifications - ERREUR MÉTHODOLOGIQUE DÉTECTÉE)  
**À :** Session 92.2 (Calibration CORRECTE avec réplication Planificateur)

---

## 🚨 CORRECTION CRITIQUE SESSION 92.1

### ⚠️ ERREUR MÉTHODOLOGIQUE IDENTIFIÉE

**Session 92.1 a utilisé une approche SIMPLIFIÉE incorrecte :**
```python
# ❌ INCORRECT (Session 92.1)
ratio = impact_réel_moyen / impact_prédit_moyen
amplification_optimale = 2.5 × ratio
```

**Cette approche NE RESPECTE PAS la méthodologie du Planificateur !**

### ✅ MÉTHODOLOGIE CORRECTE (Obligatoire Session 92.2)

**Le Planificateur V2.4 utilise une CHAÎNE COMPLÈTE :**

1. **Ajustement score** : `calculate_adjusted_empirical_score(base_score, surprise_max)`
2. **Calcul impact** : `calculate_impact_d(adjusted_score, num_events, amplification)`
3. **Somme vectorielle** : Direction événements + correction 0.758
4. **Amplification** : Facteur multiplicatif (actuellement fixe 2.5)

**Session 92.2 DOIT répliquer TOUTE cette chaîne, pas juste le ratio final !**

---

## ⚠️ RÈGLES IMPÉRATIVES DÉMARRAGE SESSION 92.2

### 📚 AVANT TOUT CODE, Claude DOIT :

**ÉTAPE 1 - LECTURE OBLIGATOIRE (40k tokens) :**

1. ✅ **Lire `MANDATORY_SESSION_RULES.md`**
   - Chemin : `/eurusd_clean/docs/MANDATORY_SESSION_RULES.md`
   - **SECTION CRITIQUE** : "Règle Critique Validation - Erreur Récurrente (Sessions 74-84)"
   - **Cette règle INTERDIT de créer nouvelles formules sans valider existantes !**

2. ✅ **Lire `project_state_new.md`** ENTIÈREMENT
   - Chemin : `/eurusd_clean/docs/project_state_new.md`
   - **Section Sessions 51-55** : Formules validées (94-99% précision)
   - **Section Session 91.2** : Validation 40 dates
   - **Section Session 92.1** : Erreur méthodologique corrigée

3. ✅ **Lire `formulas_validated.py`** COMPLET
   - Chemin : `/fx_impact_app/src/formulas_validated.py`
   - Comprendre les 4 formules validées
   - Voir comment elles sont utilisées

4. ✅ **Lire Planificateur V2.4** (lignes critiques)
   - Chemin : `/fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py`
   - **Lignes 189-210** : Query SQL événements
   - **Lignes 230-242** : Calcul surprise
   - **Lignes 244-277** : Amplification et calculate_predictions()
   - **COMPRENDRE la logique complète AVANT de coder**

5. ✅ **Lire ce fichier** (`MESSAGE_SESSION92.1_SESSION92.2_CORRECTED.md`)

6. ✅ **Afficher tokens utilisés**
   - Format : "Tokens utilisés : X / 105,000"
   - ⚠️ **LIMITE : 105,000 tokens MAX**

7. ✅ **Valider compréhension**
   - Résumer méthodologie CORRECTE
   - Demander confirmation GO

---

## 🎯 MISSION SESSION 92.2 (CORRIGÉE)

**Calibrer les amplifications par TYPE en RÉPLIQUANT exactement la méthodologie du Planificateur V2.4.**

**⚠️ PAS de formules simplifiées ! RÉPLICATION EXACTE uniquement !**

---

## 📊 CE QUE SESSION 92.1 A FAIT (INCOMPLET)

### Analyse Simplifiée

**Méthode utilisée (INCORRECTE) :**
```python
# Pour chaque type :
impact_pred_mean = moyenne des impacts prédits
impact_real_mean = moyenne des impacts réels
ratio = impact_real_mean / impact_pred_mean
amp_optimal = 2.5 × ratio
```

**Résultats obtenus (NON VALIDÉS) :**
- CPI : 2.08
- NFP : 1.84
- FOMC : 0.85
- ISM : 0.34

**⚠️ CES VALEURS SONT DES ESTIMATIONS GROSSIÈRES, PAS DES CALIBRATIONS VALIDÉES !**

### Ce qui manquait

1. ❌ Pas d'utilisation de `calculate_adjusted_empirical_score()`
2. ❌ Pas d'utilisation de `calculate_impact_d()`
3. ❌ Pas de somme vectorielle
4. ❌ Pas de test de différentes amplifications
5. ❌ Pas de validation avec méthodologie complète

### Leçon Session 92.1

**Les résultats Session 92.1 sont indicatifs UNIQUEMENT.**

**Session 92.2 doit RECOMMENCER avec méthodologie correcte !**

---

## 🎯 PLAN SESSION 92.2 (CORRIGÉ)

### Phase 1 : Script Validation Répliquant Planificateur (Budget 30k tokens)

**Fichier :** `eurusd_clean/scripts/session92.2/grid_search_amplification.py`

**Objectif :** Tester TOUTES les amplifications possibles par TYPE avec méthodologie EXACTE du Planificateur

**Méthodologie OBLIGATOIRE :**

```python
"""
Grid Search Amplification par Type - Session 92.2

Réplique EXACTEMENT le Planificateur V2.4 (lignes 189-277)
"""

import sys
from pathlib import Path

# Importer formules validées (Sessions 51-55)
sys.path.append(str(Path(__file__).parent.parent.parent / "fx_impact_app" / "src"))
from formulas_validated import (
    calculate_adjusted_empirical_score,  # Session 55
    calculate_impact_d                    # Session 51
)

def replicate_planificateur_prediction(events_df, amplification_factor):
    """
    RÉPLIQUE EXACTE du Planificateur V2.4 (lignes 189-277)
    
    Args:
        events_df: DataFrame événements (query SQL identique ligne 189-210)
        amplification_factor: Facteur à tester (ex: 2.5, 2.0, 1.5, etc.)
    
    Returns:
        float: Impact prédit (pips)
    """
    # 1. Calcul surprise (LIGNE 230-242 Planificateur)
    surprises = []
    for _, event in events_df.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
        else:
            surprise_pct = 0
        
        surprises.append(surprise_pct)
    
    max_surprise = max(surprises) if surprises else 0
    
    # 2. Score ajusté (LIGNE 244 Planificateur)
    base_score_avg = events_df['empirical_score'].mean()
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # 3. Nombre événements
    num_events = len(events_df)
    
    # 4. Impact avec amplification (LIGNE 246-277 Planificateur)
    impact_predicted = calculate_impact_d(
        adjusted_score, 
        num_events, 
        amplification_factor  # ← Variable à optimiser
    )
    
    return impact_predicted

def grid_search_by_type(csv_path):
    """
    Grid search amplification optimale PAR TYPE
    
    Teste amplifications de 0.5 à 3.0 par pas de 0.1
    Trouve celle qui minimise MAE par type
    """
    import pandas as pd
    
    # Charger CSV validation Session 91.2
    df = pd.read_csv(csv_path)
    
    # Range amplifications à tester
    amplifications = [round(x * 0.1, 1) for x in range(5, 31)]  # 0.5 à 3.0
    
    results = {}
    
    for event_type in df['type'].unique():
        subset = df[df['type'] == event_type]
        
        best_amp = None
        best_mae = float('inf')
        
        for amp in amplifications:
            errors = []
            
            for _, row in subset.iterrows():
                # Recalculer impact prédit avec cette amplification
                # NOTE: Ici on doit RE-CALCULER, pas utiliser impact_predicted CSV !
                impact_predicted_new = replicate_planificateur_prediction(
                    # TODO: Charger événements de cette date depuis DB
                    events_for_date,
                    amp
                )
                
                impact_real = row['impact_real']
                error = abs(impact_predicted_new - impact_real)
                errors.append(error)
            
            mae = sum(errors) / len(errors)
            
            if mae < best_mae:
                best_mae = mae
                best_amp = amp
        
        results[event_type] = {
            'amplification': best_amp,
            'mae': best_mae,
            'n_dates': len(subset)
        }
    
    return results
```

**⚠️ CE SCRIPT EST LA BASE MINIMALE - À DÉVELOPPER !**

### Phase 2 : Implémentation Complète (Budget 40k tokens)

**Sous-phases :**

1. **Connexion DB et chargement événements** (10k tokens)
   - Répliquer query SQL lignes 189-210 Planificateur
   - Pour CHAQUE date du CSV, charger ses événements depuis DB
   - Stocker dans structure reproductible

2. **Grid search par type** (20k tokens)
   - Pour chaque type (CPI, NFP, FOMC, ISM, etc.)
   - Tester amplifications 0.5 → 3.0 (pas 0.1) = 26 valeurs
   - Calculer MAE avec méthodologie complète
   - Trouver amplification minimisant MAE

3. **Validation résultats** (10k tokens)
   - Comparer amplifications trouvées vs Session 92.1
   - Vérifier cohérence
   - Documenter écarts

### Phase 3 : Documentation (Budget 20k tokens)

**Fichiers à créer :**

1. **SESSION92.2_RAPPORT_COMPLET.md**
   - Correction erreur Session 92.1
   - Méthodologie correcte appliquée
   - Résultats grid search
   - Amplifications validées

2. **MESSAGE_SESSION92.2_SESSION92.3.md**
   - Amplifications validées à utiliser
   - Plan implémentation Planificateur
   - Tests validation

3. **Mise à jour `project_state_new.md`**
   - Section Session 92.2
   - Correction Session 92.1

---

## 📊 BUDGET TOKENS SESSION 92.2

```
Phase 1 : Script grid search             : 30,000 tokens
Phase 2 : Implémentation complète        : 40,000 tokens
Phase 3 : Documentation                  : 20,000 tokens
─────────────────────────────────────────────────────────
TOTAL ESTIMÉ                             : 90,000 tokens
```

**Budget serré mais réaliste.**

---

## 📂 FICHIERS CRITIQUES

### Données

**CSV validation Session 91.2 :**
```
eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv
```

**Database :**
```
fx_impact_app/data/warehouse.duckdb
```

### Code à comprendre

**Formules validées (Sessions 51-55) :**
```
fx_impact_app/src/formulas_validated.py
```

**Planificateur V2.4 :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Lignes critiques Planificateur :**
- 189-210 : Query SQL événements
- 230-242 : Calcul surprise
- 244-277 : Amplification + calculate_predictions()

---

## ⚠️ POINTS CRITIQUES

### 1. RÉPLIQUER, NE PAS SIMPLIFIER

**❌ INTERDIT :**
```python
ratio = impact_real / impact_predicted
amp_optimal = 2.5 * ratio
```

**✅ OBLIGATOIRE :**
```python
adjusted_score = calculate_adjusted_empirical_score(base_score, surprise)
impact_predicted = calculate_impact_d(adjusted_score, num_events, amplification)
```

### 2. Utiliser Formules Sessions 51-55

**Module obligatoire :**
```python
from formulas_validated import (
    calculate_adjusted_empirical_score,  # Session 55
    calculate_impact_d                    # Session 51
)
```

**Ces formules ont 94-99% précision - NE PAS les remplacer !**

### 3. Query SQL Identique

**COPIER EXACTEMENT du Planificateur (lignes 189-210) :**
```python
query = """
SELECT 
    e.event_key, e.event_title as label, e.ts_utc,
    e.actual, e.estimate, ef.family, ef.empirical_score, ef.latency_median
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""
```

### 4. ISM Reste Problématique

**Même avec méthodologie correcte, ISM peut rester > 30 pips MAE.**

**Si c'est le cas :**
- Documenter résultat
- Reporter Session 92.3 (analyse ISM dédiée)
- Pas d'inquiétude - c'est attendu

---

## 📋 CHECKLIST SESSION 92.2

**Avant de commencer :**
- [ ] Lire MANDATORY_SESSION_RULES.md (section validation)
- [ ] Lire project_state_new.md (sections S51-55, S91.2, S92.1)
- [ ] Lire formulas_validated.py COMPLET
- [ ] Lire Planificateur lignes 189-277
- [ ] Comprendre chaîne calcul complète
- [ ] Lire ce fichier (MESSAGE corrigé)

**Pendant session :**
- [ ] Script grid_search_amplification.py créé
- [ ] Réplication exacte Planificateur validée
- [ ] Grid search exécuté par type
- [ ] Amplifications optimales trouvées
- [ ] Comparaison vs Session 92.1
- [ ] Documentation complète

**Validation finale :**
- [ ] Formules Sessions 51-55 utilisées ✅
- [ ] Query SQL identique Planificateur ✅
- [ ] Méthodologie complète respectée ✅
- [ ] Résultats cohérents avec Session 92.1 (à ±20%)
- [ ] MAE projeté < 30 pips

---

## 💬 MESSAGE POUR CLAUDE SESSION 92.2

**Cher Claude,**

**Session 92.1 a commis une erreur méthodologique :**

❌ Calcul simplifié (ratio impacts) au lieu de réplication Planificateur

**Ta mission Session 92.2 :**

1. **LIRE** formulas_validated.py et Planificateur (lignes 189-277)
2. **RÉPLIQUER** exactement la méthodologie
3. **TESTER** différentes amplifications par type (grid search)
4. **TROUVER** amplification minimisant MAE par type
5. **DOCUMENTER** résultats validés

**Méthodologie obligatoire :**
- `calculate_adjusted_empirical_score()` (Session 55)
- `calculate_impact_d()` (Session 51)
- Query SQL identique
- Somme vectorielle si multi-événements

**PAS de simplifications ! RÉPLICATION EXACTE uniquement !**

**Les valeurs Session 92.1 (2.08, 1.84, etc.) sont indicatives - à VALIDER avec méthodologie correcte.**

**Budget : 90k tokens**

**Go avec méthodologie rigoureuse ! 🚀**

---

_Message Session 92.1 → 92.2 (CORRIGÉ) - 27 octobre 2025_  
_Calibration amplifications par type - MÉTHODOLOGIE CORRECTE_
