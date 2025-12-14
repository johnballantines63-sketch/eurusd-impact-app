# Flowchart Validation LOO-CV DoubleWave

**Session 132**  
**Date : 13 novembre 2025**

---

## 📊 Diagramme Mermaid

Copie-colle ce code dans **https://mermaid.live** pour visualiser :

```mermaid
flowchart TD
    Start([Début: Validation LOO-CV DoubleWave]) --> LoadClusters[Charger 6 clusters Overlap identiques<br/>depuis find_clusters.py]
    
    LoadClusters --> VerifyPatterns{Étape 6 CRITIQUE:<br/>Vérifier patterns<br/>vraiment identiques?}
    
    VerifyPatterns -->|Non: Patterns différents| SubdivideGroups[Subdiviser en sous-groupes<br/>par type de pattern]
    SubdivideGroups --> LoadClusters
    
    VerifyPatterns -->|Oui: Tous identiques| InitLoop[Initialiser:<br/>i = 1<br/>results = liste vide]
    
    InitLoop --> LoopCheck{i <= 6 ?}
    
    LoopCheck -->|Non| CalcGlobalMAE[Calculer MAE Global:<br/>moyenne des 6 MAE_itération]
    
    LoopCheck -->|Oui| SelectEtalon[ITÉRATION i:<br/>Sélectionner Cas i comme étalon]
    
    SelectEtalon --> MeasureEtalon[Mesurer Cas Étalon i:<br/>1. impact_réel_i prices_bern<br/>2. R²_i tendance 30j avant<br/>3. amp_idéal_i = impact / score × racine n]
    
    MeasureEtalon --> InitInnerLoop[Initialiser boucle interne:<br/>j = 1<br/>errors_i = liste vide]
    
    InitInnerLoop --> InnerLoopCheck{j <= 6 ?}
    
    InnerLoopCheck -->|Non| CalcIterMAE[Calculer MAE_itération_i:<br/>moyenne errors_i]
    CalcIterMAE --> StoreResult[Stocker:<br/>results ajouter MAE_i]
    StoreResult --> IncrementI[i = i + 1]
    IncrementI --> LoopCheck
    
    InnerLoopCheck -->|Oui| CheckSameCase{j == i ?<br/>Même cas?}
    
    CheckSameCase -->|Oui: Sauter| IncrementJ[j = j + 1]
    IncrementJ --> InnerLoopCheck
    
    CheckSameCase -->|Non: Prédire| CalcR2J[Calculer R²_j:<br/>Tendance cas j]
    
    CalcR2J --> PredictAmp[Prédire amp_j:<br/>Tester plusieurs formules:<br/>Ratio: amp_i × R²_i / R²_j<br/>Linéaire: amp_i + k × delta R²<br/>Quadratique: a + b×R² + c×R²²]
    
    PredictAmp --> PredictImpact[Prédire impact_j:<br/>score_j × amp_pred_j × racine n_j]
    
    PredictImpact --> MeasureReal[Mesurer impact_réel_j:<br/>depuis prices_bern]
    
    MeasureReal --> CalcError[Calculer erreur_j:<br/>valeur absolue impact_pred_j - impact_réel_j]
    
    CalcError --> StoreError[Stocker:<br/>errors_i ajouter erreur_j]
    StoreError --> IncrementJ
    
    CalcGlobalMAE --> DetectOutliers[Identifier outliers:<br/>Si MAE_i > 2× moyenne<br/>alors Cas i = outlier potentiel]
    
    DetectOutliers --> CompareBaseline[Comparer avec baselines:<br/>Amp fixe 0.1201<br/>Fonction universelle Session 125<br/>Baseline amp=2.5]
    
    CompareBaseline --> Decision{MAE Global<br/>< 10 pips ?}
    
    Decision -->|Oui: EXCELLENT| ValidateMethod[✅ Méthode validée:<br/>Corrélation R² → amp fonctionne<br/>pour DoubleWave Overlap]
    
    Decision -->|Non: À améliorer| AnalyzeFailure[Analyser échec:<br/>Outliers détectés?<br/>Formule corrélation inadéquate?<br/>Patterns pas vraiment identiques?]
    
    ValidateMethod --> Documentation[Documenter résultats:<br/>MAE par itération<br/>Outliers identifiés<br/>Meilleure formule corrélation<br/>Recommandations intégration]
    
    AnalyzeFailure --> Documentation
    
    Documentation --> End([Fin: Rapport validation complet])
    
    style Start fill:#90EE90
    style End fill:#90EE90
    style VerifyPatterns fill:#FFD700
    style Decision fill:#FFD700
    style ValidateMethod fill:#87CEEB
    style AnalyzeFailure fill:#FFA07A
```

---

## 📝 Description du Workflow

### **Étape Critique : Vérification Patterns**
Avant toute calibration, vérifier que les 6 clusters produisent vraiment le même pattern (Single Wave Fort, Double Wave, etc.)

### **Boucle Principale (LOO-CV)**
Pour chaque cas i de 1 à 6 :
1. Sélectionner cas i comme étalon
2. Mesurer impact réel, R², amp idéal pour étalon
3. Pour chaque autre cas j ≠ i :
   - Calculer R²_j
   - Prédire amp_j via corrélation avec étalon
   - Comparer prédiction vs réalité
4. Calculer MAE pour cette itération

### **Résultat Final**
- MAE global = moyenne des 6 itérations
- Détection automatique outliers
- Comparaison avec baselines
- Décision EXCELLENT / À AMÉLIORER

---

## 🎯 Objectif

Valider scientifiquement si la corrélation R² → amplification permet de prédire les cas futurs pour pattern DoubleWave Overlap.

**Critère succès :** MAE global < 10 pips
