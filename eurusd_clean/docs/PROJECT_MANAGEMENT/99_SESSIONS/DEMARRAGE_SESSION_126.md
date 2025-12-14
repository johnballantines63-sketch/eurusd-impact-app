# 📋 DÉMARRAGE SESSION 126 - Pipeline Master Automatisé

**Date :** 10 novembre 2025  
**Session :** 126  
**Objectif :** Créer pipeline master automatisé pour calibration amplification universelle

---

## 🎯 MESSAGE DÉMARRAGE (À COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 126.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_125_RAPPORT_FINAL.md
   → Section "FONCTION UNIVERSELLE VALIDÉE" : LIRE MOT PAR MOT
   → Point clé : UNE fonction amp(R²) pour TOUS types événements HIGH
   → Paramètres : a=0.040833, b=0.050220, c=-0.006553 (quadratique)
   → Si tu penses "fonction par famille" → TU AS MAL LU
   
2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_126_HANDOFF.md
   → Section "PLAN D'ACTION SESSION 126" : LIRE ÉTAPE PAR ÉTAPE
   → Étape 1 : Script master calibrate_universal_amplification.py (réutilisable)
   → Pipeline = 5 modules (find_matching → calculate_r2 → calibrate → validate → decide)
   → Si tu penses "créer nouveaux algo" → TU AS MAL LU

3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/VALIDATED_SCRIPTS/session125_amplification_universelle/README.md
   → Section "WORKFLOW COMPLET" : LIRE MOT PAR MOT
   → Scripts validés Session 125 à RÉUTILISER (pas recréer)
   → Window = 240 min (FIXE, validé)
   → Si tu penses "optimiser window" → TU AS MAL LU

📋 SURVOL AUTORISÉ (référence) :
────────────────────────────────────────────────────────────────
4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Juste comprendre état actuel projet

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Fonction universelle = [une fonction pour TOUS / fonction par famille] ?
- Validation Session 125 = [CPI+NFP +88% / seulement CPI] ?
- Scripts Session 125 = [réutiliser validés / recréer nouveaux] ?
- Window optimal = [à optimiser / 240 min fixe validé] ?
- Pipeline modules = [3 étapes / 5 modules] ?
- Objectif Session 126 = [intégrer Planificateur / pipeline master automatisé] ?
- Tests prévus = [seulement CPI/NFP / + Retail Sales + Fed] ?
- Critère succès = [amélioration >50% / pipeline exécutable 1 commande] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Vérifier scripts Session 125 disponibles :
   - /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session125/find_matching_clusters.py
   - /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session125/calculate_r2_trends.py
   - /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session125/calibrate_amplification_function.py
   - /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session125/cross_validate_nfp_final.py

2. Vérifier DB unifiée : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb

3. Proposer architecture script master calibrate_universal_amplification.py :
   - Input : event_type (string)
   - Modules : 5 étapes (find → calculate → calibrate → validate → decide)
   - Output : Fonction calibrée + métriques + décision
   - CLI avec argparse

4. Identifier event_keys pour :
   - Retail Sales (table events, country='US')
   - Fed Interest Rate Decision (table events, country='US')

5. Attendre validation architecture André

6. PUIS commencer implémentation (pas avant)

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS les sections critiques
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup
❌ Ne RECRÉÉ PAS scripts Session 125 (réutiliser !)
❌ Ne CHANGE PAS window 240 (validé optimal)
❌ Ne propose PAS "fonction par famille" (universelle validée)

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📊 RÉPONSES QUIZ ATTENDUES

**Réponses correctes :**
1. une fonction pour TOUS
2. CPI+NFP +88%
3. réutiliser validés
4. 240 min fixe validé
5. 5 modules
6. pipeline master automatisé
7. + Retail Sales + Fed
8. pipeline exécutable 1 commande

---

## 🎯 CONTEXTE SESSION 126

### **Acquis Session 125**
- ✅ Fonction amp(R²) = 0.040833 + 0.050220×R² - 0.006553×R²² (UNIVERSELLE)
- ✅ Validation croisée CPI→NFP : +88% amélioration vs baseline
- ✅ 4 scripts validés (find, calculate, calibrate, cross_validate)
- ✅ Window 240 min optimal (après tests 9 windows)
- ✅ Méthodologie scientifique : calibration + validation croisée

### **Mission Session 126**
**Objectif :** Pipeline master automatisé pour calibrer N'IMPORTE QUEL event_type

**Livrables :**
1. Script `calibrate_universal_amplification.py` (réutilise Session 125)
2. Tests Retail Sales + Fed Decisions (nouvelles familles)
3. Analyse comparative 4 familles (CPI, NFP, Retail, Fed)
4. Documentation complète usage pipeline
5. Scripts archivés dans VALIDATED_SCRIPTS

**Critère succès :**
- Pipeline exécutable : `python calibrate_universal_amplification.py --event_type="Retail Sales"`
- Amélioration >30% vs baseline pour nouvelles familles
- Documentation README + ARCHITECTURE

---

## 📁 FICHIERS CLÉS À CONNAÎTRE

### **Scripts Session 125 (À RÉUTILISER)**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session125/
├── find_matching_clusters.py          → Matching clusters identiques
├── calculate_r2_trends.py              → Calcul R² (window 240)
├── calibrate_amplification_function.py → Calibration fonction
└── cross_validate_nfp_final.py         → Validation croisée
```

### **Résultats Session 125**
```
scripts/session125/calibration_results/amplification_function_calibrated.json
scripts/session125/cross_validation/cross_validation_cpi_to_nfp_final.json
```

### **Documentation**
```
docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_125_RAPPORT_FINAL.md
docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_126_HANDOFF.md
docs/PROJECT_MANAGEMENT/VALIDATED_SCRIPTS/session125_amplification_universelle/README.md
```

---

## ⚙️ PARAMÈTRES VALIDÉS SESSION 125

**NE PAS MODIFIER (déjà optimisés) :**
```python
WINDOW = 240                # 4h (optimal après tests)
LOOKBACK_DAYS = 30          # Historique prix
MIN_AMPLITUDE_PIPS = 30     # Filtre inversions
CLUSTER_WINDOW_MINUTES = 10 # ±5 min pour matching
```

**Fonction calibrée (UNIVERSELLE) :**
```python
def calculate_amplification_from_r2(r2_trend):
    a, b, c = 0.040833, 0.050220, -0.006553
    r2 = max(0.0, min(1.0, r2_trend))
    return max(0.01, min(0.20, a + b * r2 + c * r2**2))
```

---

## 🚀 WORKFLOW SESSION 126

```
1. Quiz validation (MOT PAR MOT obligatoire)
   ↓
2. Vérification scripts Session 125 disponibles
   ↓
3. Proposition architecture script master
   ↓
4. Validation architecture par André
   ↓
5. Implémentation pipeline master
   ↓
6. Tests Retail Sales
   ↓
7. Tests Fed Decisions
   ↓
8. Analyse comparative 4 familles
   ↓
9. Documentation complète
   ↓
10. Archivage VALIDATED_SCRIPTS
```

---

## 💡 CONSEILS CLÉS

**RÉUTILISER (pas recréer) :**
- Scripts Session 125 sont VALIDÉS (+88% amélioration)
- Window 240 est OPTIMAL (testé vs 9 autres)
- Fonction amp(R²) est UNIVERSELLE (prouvé)

**NOUVEAU (à créer) :**
- Script master wrapper qui appelle scripts Session 125
- Tests sur Retail Sales (nouveau type événement)
- Tests sur Fed Decisions (nouveau type événement)
- Documentation usage pipeline

**ARCHITECTURE :**
```python
# calibrate_universal_amplification.py (NOUVEAU)
def calibrate_event_type_amplification(event_type: str):
    # MODULE 1 : Réutiliser find_matching_clusters.py
    clusters = find_matching_clusters(event_type)
    
    # MODULE 2 : Réutiliser calculate_r2_trends.py
    clusters_r2 = calculate_r2_trends(clusters)
    
    # MODULE 3 : Réutiliser calibrate_amplification_function.py
    function = calibrate_amplification(clusters_r2)
    
    # MODULE 4 : Validation
    metrics = validate_predictions(function, clusters_r2)
    
    # MODULE 5 : Décision
    decision = decide_integration(metrics)
    
    return {'function': function, 'metrics': metrics, 'decision': decision}
```

---

## ⚠️ PIÈGES À ÉVITER

1. ❌ **Recréer scripts Session 125**
   → Ils sont validés, juste les réutiliser !

2. ❌ **Changer window 240**
   → Déjà optimisé (tests 9 windows)

3. ❌ **Créer fonction par famille**
   → Universalité prouvée (+88% NFP)

4. ❌ **Commencer code avant quiz**
   → Lire attentivement D'ABORD

5. ❌ **Négliger documentation**
   → Pipeline doit être réutilisable facilement

---

**Auteur :** André Valentin avec Claude  
**Date :** 10 novembre 2025  
**Session :** 126  
**Budget :** ~120k / 190k tokens estimé
