# 📋 LISTE FONCTIONS PLANIFICATEUR V3.0 - ORDRE D'EXÉCUTION

**Date :** 16 novembre 2025  
**Version :** 3.0 (Session 134) + Optimisations Session 142  
**Objectif :** Documenter toutes les fonctions et leur ordre d'utilisation avant intégration

---

## 🎯 VUE D'ENSEMBLE

Le Planificateur V3.0 suit un pipeline en **11 étapes** selon le flowchart Session 133. Chaque étape correspond à une ou plusieurs fonctions spécifiques.

**Architecture :**
```
INPUT (Date + Timezone + Seuil)
    ↓
[11 ÉTAPES SÉQUENTIELLES]
    ↓
OUTPUT (Prédiction + Métriques + Export)
```

---

## 📊 ORDRE D'EXÉCUTION DES FONCTIONS

### **ÉTAPE 1 : VALIDATION ENTRÉE**

#### **1.1. `parse_flexible_date(date_str: str) -> datetime`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 94-109)
- **Rôle :** Parse date avec formats multiples (YYYY-MM-DD, DD.MM.YYYY, etc.)
- **Ordre :** 1er appel
- **Retour :** `datetime` object

#### **1.2. `validate_input(date_str, timezone_str, min_pips) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 112-141)
- **Rôle :** Valide entrées utilisateur (date, timezone, min_pips)
- **Ordre :** 2ème appel (après parse_flexible_date)
- **Retour :** `{'valid': bool, 'date': datetime, 'timezone': pytz.timezone, 'min_pips': float, 'error_message': str}`

---

### **ÉTAPE 2 : CHARGER ÉVÉNEMENTS**

#### **2.1. `load_events_for_date(date, db_path, timezone_str) -> pd.DataFrame`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 148-168)
- **Rôle :** Charge événements HIGH (importance_n=3) pour date donnée depuis DB
- **Ordre :** 3ème appel (après validation)
- **Requête DB :** `SELECT * FROM events WHERE DATE(ts_utc AT TIME ZONE 'timezone') = ? AND importance_n = 3`
- **Retour :** DataFrame avec colonnes : `ts_utc`, `country`, `event_title`, `event_key`, `actual`, `estimate`, `forecast`, `previous`, `ts_bern`

---

### **ÉTAPE 3 : CHARGER PRIX**

#### **3.1. `load_prices_for_date(date, db_path, timezone_str) -> pd.DataFrame`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 175-193)
- **Rôle :** Charge prix 1-minute pour date donnée depuis DB
- **Ordre :** 4ème appel (après chargement events)
- **Requête DB :** `SELECT datetime, open, high, low, close FROM prices_bern WHERE DATE(datetime) = ?`
- **Retour :** DataFrame avec index `datetime` (timezone Bern) et colonnes : `open`, `high`, `low`, `close`

---

### **ÉTAPE 4 : ENRICHIR ÉVÉNEMENTS AVEC SCORES**

#### **4.1. `enrich_events_with_scores(df_events, db_path) -> pd.DataFrame`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 200-229)
- **Rôle :** Enrichit événements avec scores empiriques et surprises
- **Ordre :** 5ème appel (après chargement prix)
- **Actions :**
  - Cherche score dans `event_families` (table DB)
  - Calcule surprise : `(actual - estimate) / estimate * 100`
  - Calcule score ajusté : `score * (1 + surprise / 100)`
- **Retour :** DataFrame enrichi avec colonnes : `score`, `surprise`, `score_adjusted`

---

### **ÉTAPE 5 : DÉTECTER PATTERN**

#### **5.1. `detect_pattern_type(df_events, df_prices, min_pips, timezone) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 236-284)
- **Rôle :** Détecte type de pattern (classification simplifiée)
- **Ordre :** 6ème appel (après enrichissement)
- **Logique :**
  1. Calcule baseline (close t-1 avant premier event)
  2. Scanner prix 6h après événement
  3. Calculer impact : `max(|close - baseline|) * 10000` (pips)
  4. Classification :
     - Si `impact < min_pips` → `INCONNU`
     - Si `total_score >= 150` ET `num_scored >= 5` → `DOUBLE_WAVE`
     - Si `impact > 40` → `SINGLE_WAVE_FORT`
     - Si `impact >= 20` → `SINGLE_WAVE_STANDARD`
     - Sinon → `INCONNU`
- **Retour :** `{'pattern_type': str, 'detection_confidence': float, 'metrics': dict, 'error': str (optionnel)}`

---

### **ÉTAPE 6 : AIGUILLAGE PRÉDICTION**

#### **6.1. `route_prediction(pattern_type, df_events, df_prices, db_path) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 291-300)
- **Rôle :** Aiguille vers le bon module de prédiction selon pattern
- **Ordre :** 7ème appel (après détection pattern)
- **Routing :**
  - Si `pattern_type == "DOUBLE_WAVE"` → Appelle `predict_double_wave()` (ÉTAPE 7)
  - Si `pattern_type in ["SINGLE_WAVE_STANDARD", "SINGLE_WAVE_FORT"]` → Appelle `predict_single_wave()` (ÉTAPE 8)
  - Si `pattern_type == "INCONNU"` → Appelle `handle_unknown_pattern()` (ÉTAPE 9)
- **Retour :** Dict résultat prédiction (selon module appelé)

---

### **ÉTAPE 7 : PRÉDICTION DOUBLE WAVE**

#### **7.1. `predict_double_wave(df_events) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 307-335)
- **Rôle :** Prédiction pattern Double Wave (wrapper)
- **Ordre :** 8ème appel (si pattern DOUBLE_WAVE)
- **Actions :**
  1. Convertit DataFrame → liste de dicts
  2. Appelle module externe `predict_doublewave_overlap()`

#### **7.2. `predict_doublewave_overlap(events, pattern_type, debug) -> Dict`**
- **Fichier :** `src/core/doublewave_prediction.py` (lignes 375-466+)
- **Rôle :** Prédiction Double Wave avec critères inclusion/exclusion
- **Ordre :** 9ème appel (appelé par predict_double_wave)
- **Actions :**
  1. Valide entrée
  2. Calcule score total
  3. Classifie pattern (overlap_standard, overlap_superposition, cascade)
  4. Vérifie critères inclusion/exclusion
  5. Si inclus : applique amplification fixe (0.1201 ou 0.0128)
  6. Calcule prédiction
- **Retour :** `{'prediction': float, 'amplification': float, 'status': str, 'reason': str, 'pattern_type': str, ...}`

**Fonctions internes utilisées :**
- `PatternClassifier.classify_pattern()` (doublewave_prediction.py)
- `InclusionCriteria.should_predict()` (doublewave_prediction.py)
- `calculate_combined_surprise()` (doublewave_prediction.py)

---

### **ÉTAPE 8 : PRÉDICTION SINGLE WAVE**

#### **8.1. `predict_single_wave(df_events, df_prices, pattern_type, db_path) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 342-398)
- **Rôle :** Prédiction Single Wave avec fonction universelle fallback
- **Ordre :** 10ème appel (si pattern SINGLE_WAVE_STANDARD ou SINGLE_WAVE_FORT)
- **Actions :**
  1. Identifie type événement principal
  2. Calcule R² tendance (60 min avant event)
  3. Applique fonction universelle `amp(R²)`
  4. Calcule prédiction : `score_adjusted_total * amp`

#### **8.2. `identify_main_event_type(df_events) -> str`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 401-418)
- **Rôle :** Identifie type événement principal (CPI, NFP, Fed, etc.)
- **Ordre :** 11ème appel (appelé par predict_single_wave)
- **Logique :** Cherche event avec score max, normalise nom

#### **8.3. `calculate_amplification_from_r2_universal(r2_trend) -> float`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 421-426)
- **Rôle :** Fonction universelle fallback (Sessions 125-126)
- **Ordre :** 12ème appel (appelé par predict_single_wave)
- **Formule :** `amp = max(0.01, min(0.20, 0.040833 + 0.050220*r2 - 0.006553*r2²))`

**⚠️ OPTIMISATION SESSION 142 À INTÉGRER :**
- **Nouvelle fonction :** `predict_single_wave_with_loocv()` (à créer)
- **Rôle :** Utilise approche pattern-based LOO-CV (Session 139-142)
- **Logique :**
  1. Identifier pattern + score_range (ex: SINGLE_WAVE_FORT_UP 200-300)
  2. Si groupe existe dans données historiques :
     - Si pattern == DOUBLE_WAVE_UP ET score_range == 300-400 :
       - Utiliser **MÉDIANE** (optimisation Session 142)
     - Sinon :
       - Utiliser **MOYENNE** (baseline)
  3. Si groupe n'existe pas :
     - Fallback fonction universelle `amp(R²)`

**Fonctions à ajouter :**
- `get_pattern_group_prediction(pattern_type, score_range, use_median=False) -> float`
- `assign_score_range(total_score) -> str`

---

### **ÉTAPE 9 : GESTION PATTERN INCONNU**

#### **9.1. `handle_unknown_pattern(df_events) -> Dict`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 433-443)
- **Rôle :** Gestion pattern non reconnu
- **Ordre :** 13ème appel (si pattern INCONNU)
- **Retour :** `{'prediction_pips': None, 'status': 'excluded', 'reason': str, 'suggestion': str}`

---

### **ÉTAPE 10 : AFFICHAGE RÉSULTATS**

#### **10.1. `display_results(target_date, min_pips, timezone_str, pattern_result, prediction_result, df_events) -> None`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 450-539)
- **Rôle :** Affiche résultats complets dans interface Streamlit
- **Ordre :** 14ème appel (après prédiction)
- **Affichage :**
  - Paramètres détection
  - Pattern détecté + confiance
  - Impact prédit + amplification
  - Méthodologie utilisée
  - Métriques pattern
  - Liste événements analysés
  - Warnings (si présents)

---

### **ÉTAPE 11 : EXPORT CSV**

#### **11.1. `export_results_csv(target_date, pattern_result, prediction_result, df_events) -> str`**
- **Fichier :** `streamlit_app/pages/3_Planificateur_V3.py` (lignes 546-571)
- **Rôle :** Génère CSV téléchargeable avec résultats
- **Ordre :** 15ème appel (après affichage)
- **Retour :** String CSV (format téléchargeable)

---

## 🔧 FONCTIONS UTILITAIRES (APPELÉES EN INTERNE)

### **Formules Validées (Sessions 51-55)**

#### **`calculate_adjusted_empirical_score(base_empirical_score, surprise_pct) -> float`**
- **Fichier :** `src/core/formulas_validated.py` (lignes 144-225)
- **Rôle :** Ajuste score empirique selon surprise
- **Utilisée par :** `calculate_cluster_impact()` (cluster_impact_calculator.py)
- **Formule :** Facteur 1.0-1.9 selon surprise (5%, 15%, 30%)

#### **`calculate_impact_d(empirical_score, num_events, amplification, correction_factor) -> float`**
- **Fichier :** `src/core/formulas_validated.py` (lignes 232-307)
- **Rôle :** Calcule impact net (Formule D - 98.6% précision)
- **Utilisée par :** `calculate_cluster_impact()` (cluster_impact_calculator.py)
- **Formule :** `Impact = |(-10.47 + 0.477×score)| × amplification × 0.758` (multi-événements)

#### **`calculate_ttr_c(latency_minutes, surprise_pct) -> float`**
- **Fichier :** `src/core/formulas_validated.py` (lignes 314-382)
- **Rôle :** Calcule Time To Reversal (Formule C - 94.4% précision)
- **Utilisée par :** `calculate_cluster_ttr()` (cluster_impact_calculator.py)
- **Formule :** `TTR = latency × multiplier` (2.0-3.0 selon surprise)

#### **`calculate_pullback_v2(phase1_impact, minutes_since_peak, minutes_to_next_phase) -> float`**
- **Fichier :** `src/core/formulas_validated.py` (lignes 389-479)
- **Rôle :** Calcule pullback entre phases (Formule Pullback V2 - 99.3% précision)
- **Formule :** `pullback = phase1_impact × min(0.30×ln(minutes+1), 0.75)`

### **Cluster Impact Calculator (Session 111)**

#### **`calculate_cluster_impact(cluster_events, amplification) -> Dict`**
- **Fichier :** `src/core/cluster_impact_calculator.py` (lignes 49-230)
- **Rôle :** Calcule impact d'un cluster d'événements isolé
- **Utilisée par :** Modules multi-clusters (si nécessaire)
- **Méthodologie :**
  1. Score base moyen
  2. Surprise nette (somme vectorielle)
  3. Score ajusté (Session 55)
  4. Impact formule D (Session 51)

#### **`calculate_cluster_ttr(cluster_impact, cluster_latency_median) -> float`**
- **Fichier :** `src/core/cluster_impact_calculator.py` (lignes 237-310)
- **Rôle :** Calcule TTR adaptatif pour cluster
- **Utilisée par :** Modules multi-clusters (si nécessaire)

---

## 🆕 FONCTIONS À AJOUTER (OPTIMISATIONS SESSION 142)

### **1. `get_pattern_group_prediction(pattern_type, score_range, use_median=False) -> float`**
- **Fichier :** `src/core/pattern_based_predictor.py` (à créer)
- **Rôle :** Prédiction basée sur groupe pattern+score_range (approche LOO-CV Session 139)
- **Ordre :** Appelée par `predict_single_wave()` si groupe existe
- **Logique :**
  1. Charger données historiques (step3_movements_with_patterns_v2.csv)
  2. Filtrer groupe : `pattern_type` + `score_range`
  3. Si `use_median=True` ET groupe == DOUBLE_WAVE_UP 300-400 :
     - Prédiction = médiane impacts historiques
  4. Sinon :
     - Prédiction = moyenne impacts historiques
  5. Retourner prédiction

### **2. `assign_score_range(total_score) -> str`**
- **Fichier :** `src/core/pattern_based_predictor.py` (à créer)
- **Rôle :** Assigne score à une range (0-100, 100-200, 200-300, etc.)
- **Ordre :** Appelée par `get_pattern_group_prediction()`
- **Logique :**
  ```python
  if score < 100: return "0-100"
  elif score < 200: return "100-200"
  elif score < 300: return "200-300"
  elif score < 400: return "300-400"
  elif score < 500: return "400-500"
  else: return "500+"
  ```

### **3. `detect_pattern_direction(df_prices, baseline, first_event_time) -> str`**
- **Fichier :** `src/core/pattern_based_predictor.py` (à créer)
- **Rôle :** Détecte direction pattern (UP vs DOWN)
- **Ordre :** Appelée par `predict_single_wave()` pour compléter pattern_type
- **Logique :**
  1. Scanner prix après événement
  2. Trouver pic max (haut ou bas)
  3. Si pic haut > pic bas → "UP"
  4. Sinon → "DOWN"
  5. Retourner : `pattern_type + "_" + direction` (ex: "SINGLE_WAVE_FORT_UP")

---

## 📊 RÉSUMÉ ORDRE D'EXÉCUTION COMPLET

```
1.  parse_flexible_date()                    [ÉTAPE 1]
2.  validate_input()                         [ÉTAPE 1]
3.  load_events_for_date()                   [ÉTAPE 2]
4.  load_prices_for_date()                   [ÉTAPE 3]
5.  enrich_events_with_scores()              [ÉTAPE 4]
6.  detect_pattern_type()                    [ÉTAPE 5]
7.  route_prediction()                       [ÉTAPE 6]
    ├─→ predict_double_wave()               [ÉTAPE 7]
    │   └─→ predict_doublewave_overlap()    [ÉTAPE 7]
    │       ├─→ PatternClassifier.classify_pattern()
    │       ├─→ InclusionCriteria.should_predict()
    │       └─→ calculate_combined_surprise()
    │
    ├─→ predict_single_wave()               [ÉTAPE 8]
    │   ├─→ identify_main_event_type()
    │   ├─→ detect_pattern_direction()      [NOUVEAU S142]
    │   ├─→ assign_score_range()            [NOUVEAU S142]
    │   ├─→ get_pattern_group_prediction()  [NOUVEAU S142]
    │   │   └─→ (Utilise médiane si DOUBLE_WAVE_UP 300-400)
    │   └─→ calculate_amplification_from_r2_universal() [FALLBACK]
    │
    └─→ handle_unknown_pattern()           [ÉTAPE 9]
8.  display_results()                        [ÉTAPE 10]
9.  export_results_csv()                    [ÉTAPE 11]
```

---

## ⚠️ POINTS D'ATTENTION INTÉGRATION SESSION 142

### **1. Optimisation Médiane DOUBLE_WAVE_UP 300-400**
- **Où :** Dans `get_pattern_group_prediction()`
- **Condition :** `if pattern_type == "DOUBLE_WAVE_UP" and score_range == "300-400":`
- **Action :** Utiliser médiane au lieu de moyenne
- **Gain :** MAE 29.79 → 23.76 pips (-6.03 pips)

### **2. Détection Direction Pattern**
- **Nécessaire :** Pour utiliser groupes pattern-based (SINGLE_WAVE_FORT_UP vs DOWN)
- **Où :** Dans `predict_single_wave()` avant `get_pattern_group_prediction()`
- **Action :** Compléter `pattern_type` avec direction (ex: "SINGLE_WAVE_FORT_UP")

### **3. Fallback Fonction Universelle**
- **Quand :** Si groupe pattern+score_range n'existe pas dans données historiques
- **Où :** Dans `predict_single_wave()` après tentative `get_pattern_group_prediction()`
- **Action :** Utiliser `calculate_amplification_from_r2_universal()` (existant)

### **4. Gestion SINGLE_WAVE_FORT_UP 200-300**
- **Note :** Optimisé Session 141 avec médiane (MAE 23.69 → 19.36 pips)
- **Action :** Vérifier que médiane utilisée pour ce groupe aussi

---

## 🎯 VALIDATION AVANT INTÉGRATION

### **Checklist Fonctions**
- [ ] Toutes fonctions ÉTAPES 1-11 présentes
- [ ] Fonctions optimisations Session 142 ajoutées
- [ ] Ordre d'exécution respecté
- [ ] Gestion erreurs complète
- [ ] Fallback fonction universelle fonctionnel

### **Checklist Optimisations**
- [ ] Médiane DOUBLE_WAVE_UP 300-400 intégrée
- [ ] Médiane SINGLE_WAVE_FORT_UP 200-300 intégrée (Session 141)
- [ ] Détection direction pattern fonctionnelle
- [ ] Assignation score_range correcte

### **Checklist Tests**
- [ ] Test date avec DOUBLE_WAVE (2025-09-11)
- [ ] Test date avec SINGLE_WAVE (2024-12-18)
- [ ] Test date avec pattern inconnu
- [ ] Test fallback fonction universelle

---

**Auteur :** André Valentin avec Claude  
**Date :** 16 novembre 2025  
**Statut :** ✅ DOCUMENTATION COMPLÈTE - Prêt validation avant intégration

