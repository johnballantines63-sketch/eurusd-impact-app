# 📊 DIAGRAMMES UML - EUR/USD News Impact Calculator

**Version :** 1.0  
**Date :** 16 novembre 2025  
**Architecture :** Clean Architecture (Core / Services / UI)

---

## 📑 TABLE DES MATIÈRES

1. [Diagramme de Classes](#1-diagramme-de-classes)
2. [Diagramme de Séquence](#2-diagramme-de-séquence)
3. [Diagramme d'Activité](#3-diagramme-dactivité)
4. [Diagramme de Cas d'Utilisation](#4-diagramme-de-cas-dutilisation)

---

## 1. DIAGRAMME DE CLASSES

### Vue d'Ensemble Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI LAYER                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PlanificateurV3                                    │   │
│  │  - date: datetime                                   │   │
│  │  - timezone: str                                    │   │
│  │  - min_pips: float                                  │   │
│  │  + validate_input()                                 │   │
│  │  + load_events()                                    │   │
│  │  + load_prices()                                    │   │
│  │  + detect_pattern()                                 │   │
│  │  + predict_impact()                                 │   │
│  │  + display_results()                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ utilise
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICES LAYER                           │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  DataService     │  │  PredictionService│               │
│  │  - db_path: str  │  │  - data_service  │               │
│  │  + get_events()  │  │  + predict()     │               │
│  │  + get_prices()  │  │  + validate()    │               │
│  │  + get_scores()  │  └──────────────────┘           │
│  └──────────────────┘                                      │
│  ┌──────────────────┐                                      │
│  │  ScoringService  │                                      │
│  │  - weights: dict │                                      │
│  │  + calculate()   │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ utilise
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORE LAYER                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │  FormulasValidated       │  │  ClusterImpactCalculator │ │
│  │  + calculate_impact_d()  │  │  + calculate_cluster()  │ │
│  │  + calculate_ttr_c()     │  │  + calculate_ttr()      │ │
│  │  + calculate_pullback()   │  │  + calculate_overlap() │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │  DoubleWavePrediction    │  │  PatternDetector          │ │
│  │  + predict_overlap()     │  │  + detect_double_wave()  │ │
│  │  + check_criteria()      │  │  + detect_single_wave()  │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ utilise
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  warehouse.duckdb                                   │   │
│  │  - events (58,449)                                  │   │
│  │  - event_families (2,467)                           │   │
│  │  - prices_bern (1.1M)                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Classes Principales

#### **1. PlanificateurV3**

```python
class PlanificateurV3:
    """
    Planificateur V3.0 - Pipeline LOO-CV Intégré
    """
    def __init__(self, db_path: str, timezone: str = "Europe/Zurich"):
        self.db_path = db_path
        self.timezone = timezone
        self.data_service = DataService(db_path)
        self.pattern_detector = PatternDetector()
        self.double_wave_predictor = DoubleWavePrediction()
    
    def validate_input(self, date_str: str, min_pips: float) -> Dict:
        """Valide entrées utilisateur"""
        pass
    
    def load_events(self, date: datetime) -> pd.DataFrame:
        """Charge événements HIGH pour date donnée"""
        pass
    
    def load_prices(self, date: datetime) -> pd.DataFrame:
        """Charge prix 1-minute pour date donnée"""
        pass
    
    def detect_pattern(self, df_prices: pd.DataFrame, df_events: pd.DataFrame) -> Dict:
        """Détecte pattern (Double Wave / Single Wave / Inconnu)"""
        pass
    
    def predict_impact(self, pattern_type: str, df_events: pd.DataFrame) -> Dict:
        """Prédit impact selon pattern détecté"""
        pass
    
    def display_results(self, prediction: Dict) -> None:
        """Affiche résultats formatés"""
        pass
```

#### **2. DataService**

```python
class DataService:
    """
    Interface unique accès warehouse.duckdb
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_events(self, date: datetime, importance: int = 3) -> pd.DataFrame:
        """Récupère événements pour date donnée"""
        pass
    
    def get_prices(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Récupère prix 1-minute pour période"""
        pass
    
    def get_event_families(self) -> pd.DataFrame:
        """Récupère statistiques event_families"""
        pass
    
    def get_scores(self, event_key: str, country: str) -> float:
        """Récupère score empirique pour événement"""
        pass
```

#### **3. ClusterImpactCalculator**

```python
class ClusterImpactCalculator:
    """
    Calcul impact par cluster d'événements
    """
    def calculate_cluster_impact(self, events: List[Event], amp: float) -> Dict:
        """Calcule impact cluster isolé"""
        pass
    
    def calculate_cluster_ttr(self, impact: float, latency: float) -> float:
        """Calcule Time To Reversal"""
        pass
    
    def calculate_double_wave_overlapping(
        self, 
        wave1_result: Dict,
        wave2_result: Dict,
        pullback: Dict,
        timing_delta: float
    ) -> Dict:
        """Calcule impact total Double Wave + Overlapping"""
        pass
```

#### **4. FormulasValidated**

```python
class FormulasValidated:
    """
    Formules mathématiques validées (Sessions 51-55)
    """
    @staticmethod
    def calculate_impact_d(score: float, num_events: int, amp: float) -> float:
        """Formule D - Impact Multi-Événements (98.6% précision)"""
        pass
    
    @staticmethod
    def calculate_adjusted_empirical_score(base_score: float, surprise_pct: float) -> float:
        """Ajustement score selon surprise (99.9% précision)"""
        pass
    
    @staticmethod
    def calculate_ttr_c(latency: float, surprise_pct: float) -> float:
        """Formule TTR C (94.4% précision)"""
        pass
    
    @staticmethod
    def calculate_pullback_v2(impact: float, minutes: float) -> float:
        """Formule Pullback V2 (99.3% précision)"""
        pass
```

---

## 2. DIAGRAMME DE SÉQUENCE

### Séquence : Prédiction Impact (Planificateur V3.0)

```
Utilisateur    PlanificateurV3    DataService    PatternDetector    DoubleWavePrediction    ClusterImpactCalculator
     │                │                 │                │                  │                        │
     │───date_str───>│                 │                │                  │                        │
     │                │                 │                │                  │                        │
     │                │───validate()────>│                │                  │                        │
     │                │<──valid─────────│                │                  │                        │
     │                │                 │                │                  │                        │
     │                │───get_events()─>│                │                  │                        │
     │                │<──df_events─────│                │                  │                        │
     │                │                 │                │                  │                        │
     │                │───get_prices()─>│                │                  │                        │
     │                │<──df_prices─────│                │                  │                        │
     │                │                 │                │                  │                        │
     │                │───detect()──────┼────────────────>│                  │                        │
     │                │                 │                │                  │                        │
     │                │                 │                │───detect_dw()───>│                        │
     │                │                 │                │<──pattern───────│                        │
     │                │<──pattern───────┼────────────────│                  │                        │
     │                │                 │                │                  │                        │
     │                │───predict()─────┼────────────────┼──────────────────>│                        │
     │                │                 │                │                  │                        │
     │                │                 │                │                  │───calculate_overlap()──>│
     │                │                 │                │                  │<──impact───────────────│
     │                │                 │                │                  │                        │
     │                │<──prediction────┼────────────────┼──────────────────│                        │
     │                │                 │                │                  │                        │
     │<──results──────│                 │                │                  │                        │
     │                │                 │                │                  │                        │
```

### Séquence : Pipeline LOO-CV (Session 139)

```
PlanificateurV3    DataService    PatternClassifier    LOO_CV_Engine    FormulasValidated
     │                 │                  │                  │                  │
     │───events───────>│                  │                  │                  │
     │                 │                  │                  │                  │
     │                 │───classify()─────┼──────────────────>│                  │
     │                 │                  │                  │                  │
     │                 │                  │                  │───group()───────>│
     │                 │                  │                  │<──groups────────│
     │                 │                  │                  │                  │
     │                 │                  │                  │───loo_cv()──────┼──────────────────>│
     │                 │                  │                  │                  │                  │
     │                 │                  │                  │<──mae────────────┼──────────────────│
     │                 │                  │                  │                  │                  │
     │<──prediction────┼──────────────────┼──────────────────│                  │                  │
     │                 │                  │                  │                  │                  │
```

---

## 3. DIAGRAMME D'ACTIVITÉ

### Activité : Workflow Planificateur V3.0

```
                    [DÉBUT]
                       │
                       ▼
            ┌──────────────────────┐
            │  Valider Entrée      │
            │  (date, timezone)    │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Charger Events      │
            │  (HIGH importance)  │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Charger Prix        │
            │  (1-minute Bern)     │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Enrichir Scores     │
            │  (empirical scores)  │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Détecter Pattern    │
            │  (Double/Single)     │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Pattern Type ?      │
            └──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ DOUBLE_WAVE │ │ SINGLE_WAVE │ │   INCONNU   │
└─────────────┘ └─────────────┘ └─────────────┘
        │              │              │
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ predict_dw()│ │ predict_sw()│ │   Message   │
└─────────────┘ └─────────────┘ └─────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Afficher Résultats  │
            │  (impact, pattern)  │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Export CSV (opt)    │
            └──────────────────────┘
                       │
                       ▼
                    [FIN]
```

### Activité : Pipeline LOO-CV (Session 139)

```
                    [DÉBUT]
                       │
                       ▼
            ┌──────────────────────┐
            │  Scanner Mouvements  │
            │  (≥40 pips, 2023-25) │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Enrichir Événements │
            │  (scores empiriques) │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Classifier Patterns │
            │  (6 patterns)        │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Grouper Patterns    │
            │  (pattern + score)   │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  LOO-CV Validation  │
            │  (396 prédictions)   │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Calculer MAE        │
            │  (par groupe)        │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Classifier Qualité  │
            │  (EXCELLENT/...)     │
            └──────────────────────┘
                       │
                       ▼
                    [FIN]
```

---

## 4. DIAGRAMME DE CAS D'UTILISATION

### Acteurs

- **Trader** : Utilisateur principal (utilise Planificateur V3.0)
- **Système** : Automatisation (Pipeline LOO-CV, Détection patterns)

### Cas d'Utilisation

```
                    ┌─────────────┐
                    │   Trader    │
                    └─────────────┘
                           │
                           │ utilise
                           ▼
        ┌──────────────────────────────────────┐
        │     Planificateur V3.0              │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Prédire Impact Événement   │   │
        │  └──────────────────────────────┘   │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Visualiser Timeline        │   │
        │  └──────────────────────────────┘   │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Exporter Résultats CSV     │   │
        │  └──────────────────────────────┘   │
        └──────────────────────────────────────┘
                           │
                           │ utilise
                           ▼
        ┌──────────────────────────────────────┐
        │         Système Automatique          │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Détecter Pattern            │   │
        │  └──────────────────────────────┘   │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Calculer Impact (LOO-CV)   │   │
        │  └──────────────────────────────┘   │
        │                                      │
        │  ┌──────────────────────────────┐   │
        │  │  Valider Prédiction          │   │
        │  └──────────────────────────────┘   │
        └──────────────────────────────────────┘
```

### Détails Cas d'Utilisation

#### **UC1 : Prédire Impact Événement**

**Acteur :** Trader  
**Préconditions :** Date valide, événements HIGH présents  
**Flux principal :**
1. Trader saisit date
2. Système charge événements HIGH
3. Système détecte pattern
4. Système calcule impact prédit
5. Système affiche résultats

**Flux alternatif :**
- Aucun événement HIGH → Message informatif
- Pattern inconnu → Suggestion ajuster paramètres

**Postconditions :** Prédiction affichée avec métriques

---

#### **UC2 : Visualiser Timeline**

**Acteur :** Trader  
**Préconditions :** Prédiction calculée  
**Flux principal :**
1. Trader demande visualisation
2. Système génère graphique Plotly
3. Système affiche timeline (TTR, pullback, pics)

**Postconditions :** Graphique interactif affiché

---

#### **UC3 : Exporter Résultats CSV**

**Acteur :** Trader  
**Préconditions :** Prédiction calculée  
**Flux principal :**
1. Trader clique "Export CSV"
2. Système génère fichier CSV
3. Système propose téléchargement

**Postconditions :** Fichier CSV téléchargé

---

## 📊 LÉGENDE SYMBOLES UML

### Diagramme de Classes
- **Classe** : Rectangle avec 3 sections (nom, attributs, méthodes)
- **Association** : Flèche simple (──→)
- **Dépendance** : Flèche pointillée (┄┄→)
- **Héritage** : Flèche triangle (──▷)
- **Composition** : Losange plein (◆──)
- **Agrégation** : Losange vide (◇──)

### Diagramme de Séquence
- **Acteur** : Rectangle avec nom
- **Lifeline** : Ligne verticale pointillée
- **Message** : Flèche horizontale (──→)
- **Activation** : Rectangle sur lifeline
- **Retour** : Flèche pointillée (┄┄→)

### Diagramme d'Activité
- **Début** : Cercle noir (●)
- **Fin** : Cercle noir avec bordure (◉)
- **Activité** : Rectangle arrondi
- **Décision** : Losange (◇)
- **Fork/Join** : Barre horizontale (━)

---

## 🔗 RÉFÉRENCES

- **Architecture complète :** `MASTER_PLAN.md`
- **Modules détaillés :** `MODULES_STATUS.md`
- **Flowchart Planificateur :** `flowchart_planificateur.md`

---

**Document créé :** 16 novembre 2025  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0  
**Statut :** Diagrammes UML complets

