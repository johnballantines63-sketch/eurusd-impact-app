# 🎯 PLAN D'AMÉLIORATION PLANIFICATEUR V3 - OUTIL TRADING

**Date :** 16 novembre 2025  
**Session :** Post-Session 142  
**Objectif :** Transformer Planificateur V3 en outil d'aide au trading complet

---

## 🎯 OBJECTIF RÉEL DU PLANIFICATEUR

**Le Planificateur est un outil d'aide au trading**, permettant de :

1. **Identifier dates futures** avec impact minimum choisi
2. **Choisir date future** dans calendrier et déterminer impact potentiel
3. **Afficher événements** comme calendrier myfxbook
4. **Renseigner valeurs actual** ou tester à l'avance
5. **Déclencher prédiction** avec score de confiance
6. **Confirmer événements** par checkbox
7. **Afficher métriques trading** :
   - Probabilité (80%)
   - Latence (5 minutes)
   - Pic prédit (120 pips)
   - Pattern détecté
   - TTR (Time To Reversal)

---

## 📊 ÉTAT ACTUEL DES FONCTIONNALITÉS

### **✅ FONCTIONNALITÉS EXISTANTES**

| Fonctionnalité | Calendrier | V2 | V3 | Statut |
|----------------|------------|----|----|--------|
| **Affichage événements futurs** | ✅ | ❌ | ❌ | ✅ |
| **Prédiction impact** | ❌ | ✅ | ✅ | ✅ |
| **Détection pattern** | ❌ | ⚠️ | ✅ | ✅ |
| **Ensemble Methods** | ❌ | ❌ | ✅ | ✅ |
| **TTR calculé** | ⚠️ | ✅ | ⚠️ | ⚠️ |
| **Latence calculée** | ⚠️ | ✅ | ⚠️ | ⚠️ |
| **Probabilité mouvement** | ⚠️ | ❌ | ❌ | ⚠️ |

### **❌ FONCTIONNALITÉS MANQUANTES**

| Fonctionnalité | Priorité | Effort |
|----------------|----------|--------|
| **Checkbox événements** | ⭐⭐⭐⭐⭐ | 2h |
| **Saisie actual pour test** | ⭐⭐⭐⭐⭐ | 2h |
| **Score de confiance** | ⭐⭐⭐⭐ | 1h |
| **Recherche dates impact min** | ⭐⭐⭐⭐ | 2h |
| **Affichage métriques trading** | ⭐⭐⭐⭐⭐ | 2h |
| **Intégration calendrier → V3** | ⭐⭐⭐⭐⭐ | 3h |

---

## 🚀 PLAN D'AMÉLIORATION

### **PHASE 1 : INTÉGRATION CALENDRIER + CHECKBOX** ⭐⭐⭐⭐⭐

**Objectif :** Permettre sélection date depuis calendrier avec checkbox événements

**Fonctionnalités :**
1. Bouton "Sélectionner depuis Calendrier" dans V3
2. Afficher événements futurs avec checkbox
3. Permettre sélection multiple événements
4. Afficher cluster détecté

**Fichiers à modifier :**
- `streamlit_app/pages/3_Planificateur_V3.py`
- Créer : `src/core/trading_utils.py`

**Durée :** 3-4h

---

### **PHASE 2 : SAISIE ACTUAL + TEST PRÉDICTION** ⭐⭐⭐⭐⭐

**Objectif :** Permettre saisie actual et tester prédiction avant annonce

**Fonctionnalités :**
1. Champs actual/estimate éditable pour chaque événement
2. Bouton "Tester Prédiction" avec actual simulés
3. Comparer différents scénarios (actual optimiste/pessimiste)
4. Afficher prédiction avec actual simulés

**Fichiers à modifier :**
- `streamlit_app/pages/3_Planificateur_V3.py`
- Créer : `src/core/prediction_tester.py`

**Durée :** 2-3h

---

### **PHASE 3 : SCORE DE CONFIANCE** ⭐⭐⭐⭐

**Objectif :** Afficher confiance prédiction

**Fonctionnalités :**
1. Calculer score confiance :
   - Nombre cas historiques similaires (40%)
   - Similarité cluster Jaccard (30%)
   - Qualité données actual/estimate (30%)
2. Afficher dans interface avec couleur (vert > 80%, orange 50-80%, rouge < 50%)
3. Afficher détails (n_historical, similarité, qualité)

**Fichiers à modifier :**
- `src/core/ensemble_prediction.py`
- `streamlit_app/pages/3_Planificateur_V3.py`

**Durée :** 1-2h

---

### **PHASE 4 : MÉTRIQUES TRADING COMPLÈTES** ⭐⭐⭐⭐⭐

**Objectif :** Afficher toutes métriques trading nécessaires

**Fonctionnalités :**
1. **Probabilité mouvement** :
   - Calculer p_up, p_down depuis historique
   - Afficher avec barre de progression
2. **Latence** :
   - Calculer depuis formule validée
   - Afficher en minutes
3. **Pic prédit** :
   - Impact prédit (déjà calculé)
   - Afficher avec direction (UP/DOWN)
4. **TTR** :
   - Calculer depuis formule validée (calculate_ttr_c)
   - Afficher en minutes
5. **Pattern détecté** :
   - Déjà affiché
   - Améliorer affichage avec icônes

**Fichiers à modifier :**
- `streamlit_app/pages/3_Planificateur_V3.py`
- `src/core/formulas_validated.py` (déjà disponible)

**Durée :** 2-3h

---

### **PHASE 5 : RECHERCHE DATES AVEC IMPACT MINIMUM** ⭐⭐⭐⭐

**Objectif :** Trouver dates futures intéressantes pour trading

**Fonctionnalités :**
1. Fonction `find_dates_with_min_impact()` :
   - Scanner période future (1-30 jours)
   - Filtrer par impact minimum
   - Filtrer par pattern, score, nombre événements
2. Afficher liste dates triée par impact
3. Permettre sélection date depuis liste

**Fichiers à créer :**
- `src/core/date_scanner.py`

**Durée :** 2-3h

---

### **PHASE 6 : DASHBOARD TRADING** ⭐⭐⭐⭐⭐

**Objectif :** Interface complète d'aide au trading

**Fonctionnalités :**
1. **Section 1 : Sélection Date**
   - Calendrier ou recherche impact minimum
2. **Section 2 : Événements**
   - Affichage style calendrier myfxbook
   - Checkbox pour sélection
   - Saisie actual/estimate
3. **Section 3 : Prédiction**
   - Impact prédit
   - Probabilité
   - Latence
   - TTR
   - Pic prédit
   - Score confiance
4. **Section 4 : Recommandation Trading**
   - Fenêtre d'entrée suggérée
   - Point de sortie suggéré
   - Stop loss suggéré

**Fichiers à modifier :**
- `streamlit_app/pages/3_Planificateur_V3.py`

**Durée :** 3-4h

---

## 📋 FONCTIONS À CRÉER

### **1. `find_dates_with_min_impact()`**

```python
def find_dates_with_min_impact(
    min_impact_pips: float,
    date_from: datetime,
    date_to: datetime,
    countries: List[str] = ['US'],
    min_confidence: float = 0.5
) -> pd.DataFrame:
    """
    Trouve dates futures avec impact prédit >= min_impact_pips.
    
    Returns:
        DataFrame avec colonnes :
        - date
        - pattern_type
        - impact_predicted
        - confidence
        - num_events
        - total_score
        - cluster_composition
    """
```

---

### **2. `display_events_calendar()`**

```python
def display_events_calendar(
    df_events: pd.DataFrame,
    editable: bool = True,
    show_checkbox: bool = True
) -> Dict:
    """
    Affiche événements avec :
    - Checkbox pour sélection
    - Champs actual/estimate éditable
    - Affichage style calendrier myfxbook
    
    Returns:
        Dict avec :
        - selected_events: Liste événements sélectionnés
        - actual_values: Dict {event_key: actual_value}
    """
```

---

### **3. `calculate_confidence_score()`**

```python
def calculate_confidence_score(
    n_historical: int,
    jaccard_similarity: float,
    data_quality: float
) -> float:
    """
    Calcule score de confiance (0-100%).
    
    Formule :
    confidence = (
        0.4 * min(n_historical / 20, 1.0) +
        0.3 * jaccard_similarity +
        0.3 * data_quality
    ) * 100
    """
```

---

### **4. `calculate_trading_metrics()`**

```python
def calculate_trading_metrics(
    pattern_type: str,
    total_score: float,
    historical_movements: pd.DataFrame
) -> Dict:
    """
    Calcule métriques trading complètes.
    
    Returns:
        Dict avec :
        - probability_up: Probabilité mouvement haussier
        - probability_down: Probabilité mouvement baissier
        - latency_minutes: Latence prédite
        - ttr_minutes: TTR prédit
        - peak_pips: Pic prédit
        - confidence: Score confiance
    """
```

---

### **5. `test_prediction_scenario()`**

```python
def test_prediction_scenario(
    df_events: pd.DataFrame,
    actual_values: Dict[str, float],
    pattern_type: str,
    total_score: float
) -> Dict:
    """
    Teste prédiction avec actual simulés.
    
    Args:
        df_events: Événements avec estimate
        actual_values: Dict {event_key: actual_value}
        pattern_type: Type de pattern
        total_score: Score total
    
    Returns:
        Prédiction avec actual simulés
    """
```

---

## 🎯 PRIORITÉS D'IMPLÉMENTATION

### **PRIORITÉ HAUTE** ⭐⭐⭐⭐⭐

1. **Phase 1 : Intégration Calendrier + Checkbox** (3-4h)
2. **Phase 4 : Métriques Trading Complètes** (2-3h)
3. **Phase 6 : Dashboard Trading** (3-4h)

**Total :** 8-11h

---

### **PRIORITÉ MOYENNE** ⭐⭐⭐⭐

4. **Phase 2 : Saisie Actual + Test** (2-3h)
5. **Phase 5 : Recherche Dates Impact Min** (2-3h)

**Total :** 4-6h

---

### **PRIORITÉ BASSE** ⭐⭐⭐

6. **Phase 3 : Score de Confiance** (1-2h)

**Total :** 1-2h

---

## 📊 ARCHITECTURE PROPOSÉE

```
Planificateur V3.0 Trading
├── Section 1 : Sélection Date
│   ├── Calendrier (intégré depuis 1_Calendrier_Trading.py)
│   └── Recherche impact minimum
│
├── Section 2 : Événements
│   ├── Affichage style calendrier myfxbook
│   ├── Checkbox pour sélection
│   └── Saisie actual/estimate
│
├── Section 3 : Prédiction
│   ├── Ensemble Methods (déjà intégré)
│   ├── Score de confiance
│   └── Métriques trading
│
└── Section 4 : Recommandation Trading
    ├── Fenêtre d'entrée
    ├── Point de sortie
    └── Stop loss
```

---

## 🚀 PLAN D'ACTION IMMÉDIAT

### **ÉTAPE 1 : Améliorer Chargement Événements** (30 min)

**Problème actuel :** Beaucoup de dates sans événements trouvés

**Solution :**
- Améliorer matching event_keys (normalisation, fuzzy matching)
- Charger par timestamp au lieu de event_keys si nécessaire

---

### **ÉTAPE 2 : Ajouter Support DOUBLE_WAVE** (1h)

**Problème actuel :** V3 limité à SINGLE_WAVE

**Solution :**
- Intégrer DOUBLE_WAVE dans predict_pattern_based_ensemble
- Ou utiliser module existant avec validation

---

### **ÉTAPE 3 : Intégrer Calendrier + Checkbox** (3-4h)

**Solution :**
- Ajouter bouton "Sélectionner depuis Calendrier"
- Créer composant `display_events_calendar()`
- Ajouter checkbox pour chaque événement

---

### **ÉTAPE 4 : Ajouter Métriques Trading** (2-3h)

**Solution :**
- Calculer probabilité (p_up, p_down)
- Afficher latence, TTR, pic prédit
- Créer dashboard trading

---

## 💡 RECOMMANDATION

### **Commencer par Phase 1 + Phase 4** ⭐⭐⭐⭐⭐

**Justification :**
1. ✅ Intégration calendrier essentielle (sélection date future)
2. ✅ Checkbox événements essentiel (confirmation cluster)
3. ✅ Métriques trading essentielles (aide décision)

**Durée totale :** 5-7h

**Gain :** Planificateur utilisable comme outil trading complet

---

**Auteur :** André Valentin avec Claude  
**Date :** 16 novembre 2025  
**Statut :** ✅ PLAN DÉFINI - PRÊT POUR IMPLÉMENTATION

