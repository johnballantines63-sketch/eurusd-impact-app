# 📋 DÉMARRAGE SESSION 121

**Date :** 07 novembre 2025  
**Session précédente :** 120  
**Session actuelle :** 121  
**Objectif :** Valider détecteurs V2 sur cas réels (ÉTAPE 2) + système validation global (ÉTAPE 3)

---

## 🎯 MESSAGE DÉMARRAGE (À COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 121.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "Pattern Detectors" : LIRE MOT PAR MOT
   → Point clé : Détecteurs V2 Session 120 utilisent approche mathématique ATR-based (pas paramètres fixes)
   → Point clé : Rev12 validé MAE 4.5 pips (convergence Session 118)
   → Si tu comprends "détecteurs V1 OK" ou "paramètres fixes suffisants" → TU AS MAL LU
   → Section "État actuel" : LIRE les accomplissements Session 120
   
2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/SESSION_120_RAPPORT_PARTIEL.md
   → Section "Plan Session 121" : LIRE MOT PAR MOT
   → Point clé : ÉTAPE 2 (Single Wave) AVANT ÉTAPE 3 (Système global)
   → Point clé : Détecteurs V2 utilisent seuils adaptatifs ATR (pas 10 pips fixes)
   → Si tu proposes ÉTAPE 3 avant ÉTAPE 2 → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_121_HANDOFF.md
   → Section "ÉTAPE 2 : Validation Single Wave V2" : LIRE LIGNE PAR LIGNE
   → Sous-étapes : 2.1 Scanner DB → 2.2 Valider → 2.3 Ajuster
   → Objectif : MAE < 10 pips sur 5+ cas (3 Fort + 2 Intermediate)
   → Si tu proposes tester V1 au lieu de V2 → TU AS MAL LU
   
4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/README_REFACTORING_V2.md
   → Section "Solutions V2" : LIRE ATTENTIVEMENT
   → Comprendre seuils adaptatifs ATR-based
   → Comprendre garde temporelle MIN_BARS=3
   → Comprendre validation stricte (timestamps, ratios, ATR)

📋 SURVOL AUTORISÉ (contexte général) :
────────────────────────────────────────────────────────────────
5. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/README_SESSION_120_FINAL.md
   → Accomplissements Session 120
   → Rev12 validé (MAE 4.5 pips)
   → Refactoring V2 complet

═══════════════════════════════════════════════════════════════════

📁 STRUCTURE PROJET (CHEMINS CRITIQUES) :
────────────────────────────────────────────────────────────────
DÉTECTEURS V2 (Session 120 - À UTILISER) :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/base_pattern_detector_v2.py
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/single_wave_detectors_v2.py
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/zigzag_detector_v2.py
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/double_wave_detector_rev12.py

DÉTECTEURS V1 (Session 119 - OBSOLÈTES, NE PAS UTILISER) :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session119/pattern_detectors.py

BASE DE DONNÉES :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb
  Tables : events, prices_bern

RÉPERTOIRE SESSION 121 (À CRÉER FICHIERS) :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/
  (créer : find_single_wave_cases_v2.py, validate_single_wave_v2.py, etc.)

FONCTIONS UTILITAIRES (rev10 - RÉUTILISER) :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session119/double_wave_detector_rev10.py
  Fonctions : load_ohlc_1m_duckdb, atr1m, to_pips, is_local_peak, is_local_trough

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Détecteurs à utiliser Session 121 = [V1 Session 119 / V2 Session 120] ?
- Approche détecteurs V2 = [paramètres fixes 10 pips / ATR-based adaptatifs] ?
- Rev12 MAE validé = [4.5 pips / 10 pips / 22 pips] ?
- Convergence Rev12 vs Session 118 = [51.7 pips identique / différent] ?
- Ordre étapes Session 121 = [ÉTAPE 2 puis 3 / ÉTAPE 3 puis 2] ?
- ÉTAPE 2 objectif = [Valider Single Wave V2 / Système global / Rev12] ?
- Nombre cas minimum Single Wave = [3 / 5 / 10] cas ?
- Composition cas = [3 Fort + 2 Intermediate / 5 Fort / tous Fort] ?
- Objectif MAE Single Wave = [< 5 pips / < 10 pips / < 20 pips] ?
- Garde temporelle V2 = [absente / MIN_BARS=3 obligatoire] ?
- Validation stricte V2 = [basique / triple validation timestamps+ratios+ATR] ?
- Si MAE > 10 pips persiste = [accepter / analyser + ajuster / ignorer] ?
- Chemin détecteurs V2 = [scripts/session119/ / scripts/session120/] ?
- Chemin DB = [data/warehouse.duckdb / data/prices.db] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Créer répertoire scripts/session121/ si inexistant
2. Créer find_single_wave_cases_v2.py (scanner DB 2024-2025)
   - Importer depuis session120/base_pattern_detector_v2.py
   - Importer load_ohlc_1m_duckdb depuis session119/double_wave_detector_rev10.py
3. Critères scan : 1 pic dominant, impact 20-80 pips, pullback < 20%
4. Identifier 3+ cas Single Fort (> 40 pips)
5. Identifier 2+ cas Single Intermediate (20-40 pips)
6. Proposer architecture validation (validate_single_wave_v2.py)
7. Attendre validation André
8. PUIS implémenter validation (appliquer détecteurs V2)
9. Calculer MAE par cas
10. Si MAE moyen < 10 pips → ÉTAPE 2 OK → passer ÉTAPE 3
11. Sinon → analyser causes + ajuster V2

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne commence PAS ÉTAPE 3 avant ÉTAPE 2 validée
❌ Ne teste PAS détecteurs V1 (obsolètes, focus V2)
❌ Ne propose PAS paramètres fixes 10 pips (V2 = ATR adaptatif)
❌ N'accepte PAS MAE > 10 pips sans analyser cause
❌ Ne survole PAS sections critiques (lecture mot par mot)
❌ Ne propose RIEN avant quiz validé
❌ Ne crée PAS validate_all_patterns avant validate_single_wave
❌ N'utilise PAS scripts/session119/pattern_detectors.py (V1 obsolète)
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 RÉPONSES ATTENDUES QUIZ

**Réponses correctes :**
- Détecteurs = **V2 Session 120**
- Approche V2 = **ATR-based adaptatifs**
- Rev12 MAE = **4.5 pips**
- Convergence = **51.7 pips identique**
- Ordre étapes = **ÉTAPE 2 puis 3**
- ÉTAPE 2 objectif = **Valider Single Wave V2**
- Nombre cas minimum = **5** cas
- Composition cas = **3 Fort + 2 Intermediate**
- Objectif MAE = **< 10 pips**
- Garde temporelle = **MIN_BARS=3 obligatoire**
- Validation stricte = **triple validation timestamps+ratios+ATR**
- Si MAE > 10 pips = **analyser + ajuster**
- Chemin détecteurs V2 = **scripts/session120/**
- Chemin DB = **data/warehouse.duckdb**

**Notes critiques :**
- **V2 SEULEMENT** : V1 déprécié (scripts/session119/pattern_detectors.py obsolète)
- **ATR-based** : Pas de paramètres fixes 10 pips
- **Rev12 validé** : MAE 4.5 pips (convergence S118 prouve robustesse)
- **ÉTAPE 2 AVANT 3** : Valider Single Wave avant système global
- **Chemins complets** : Toujours utiliser chemins absolus

---

## 📁 STRUCTURE PROJET DÉTAILLÉE

### **Répertoires Session 120 (LECTURE)**
```
scripts/session120/
├── double_wave_detector_rev12.py              ← Rev12 validé (MAE 4.5)
├── base_pattern_detector_v2.py                ← Base ATR-adaptatif (RÉUTILISER)
├── single_wave_detectors_v2.py                ← Fort + Intermediate V2 (UTILISER)
├── zigzag_detector_v2.py                      ← ZigZag V2 (UTILISER)
├── test_detectors_v2_validation.py            ← Test V1 vs V2
├── SESSION_120_RAPPORT_PARTIEL.md             ← Plan Session 121 (LIRE)
├── README_REFACTORING_V2.md                   ← Comparaison V1 vs V2 (LIRE)
└── README_SESSION_120_FINAL.md                ← Récapitulatif

Chemin complet : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120/
```

### **Répertoires Session 119 (RÉFÉRENCE seulement)**
```
scripts/session119/
├── pattern_detectors.py                       ← V1 OBSOLÈTE (ne pas utiliser)
└── double_wave_detector_rev10.py              ← Fonctions utilitaires (réutiliser)
    Fonctions utiles :
    - load_ohlc_1m_duckdb(db_path, table, tz, start, end)
    - atr1m(df)
    - to_pips(price_diff)
    - is_local_peak(series, i, width)
    - is_local_trough(series, i, width)

Chemin complet : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session119/
```

### **Répertoire Session 121 (À CRÉER)**
```
scripts/session121/                            ← CRÉER ce répertoire
├── find_single_wave_cases_v2.py               ← À CRÉER (scanner DB)
├── validate_single_wave_v2.py                 ← À CRÉER (validation 5+ cas)
├── validate_all_patterns_v2.py                ← À CRÉER (système global)
├── SINGLE_WAVE_VALIDATION_REPORT.md           ← À CRÉER (rapport)
└── VALIDATION_REPORT_S121.md                  ← À CRÉER (rapport global)

Chemin complet : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/
```

### **Base de Données**
```
data/warehouse.duckdb                          ← DB principale (205MB)

Tables importantes :
- events : Événements économiques (58,449 rows)
  Colonnes : datetime (Bern time), importance, event_name, actual, forecast
- prices_bern : Prix OHLC 1-min (timezone Bern)
  Colonnes : datetime, open, high, low, close

Chemin complet : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb
```

### **Documentation Projet**
```
docs/PROJECT_MANAGEMENT/
├── 01_VISION/
│   └── MASTER_PLAN.md                         ← Vision globale (LIRE section Pattern Detectors)
└── 99_SESSIONS/
    ├── SESSION_121_HANDOFF.md                 ← Plan détaillé Session 121 (LIRE)
    └── DEMARRAGE_SESSION_121.md               ← Ce fichier

Chemin complet : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/
```

---

## 🎯 OBJECTIFS SESSION 121

### **Objectif Principal**
Valider détecteurs Single Wave V2 + système validation global sur 10+ cas

### **Critères Succès**
- [ ] 5+ cas Single Wave identifiés (3 Fort + 2 Intermediate)
- [ ] MAE Single Wave < 10 pips (moyen sur 5+ cas)
- [ ] Système validation global opérationnel
- [ ] 10+ cas testés (mix patterns)
- [ ] Statistiques globales (MAE, RMSE, R²)
- [ ] Graphiques (scatter plot, distribution erreurs)
- [ ] Documentation complète (rapport + handoff S122)

### **Livrables Attendus**
1. `find_single_wave_cases_v2.py` (scanner DB)
2. `validate_single_wave_v2.py` (validation 5+ cas)
3. `validate_all_patterns_v2.py` (système global 10+ cas)
4. `SINGLE_WAVE_VALIDATION_REPORT.md` (rapport Single Wave)
5. `VALIDATION_REPORT_S121.md` (rapport global)
6. Graphiques PNG (scatter plot, distribution, etc.)
7. `SESSION_121_RAPPORT_FINAL.md`
8. `SESSION_122_HANDOFF.md`

---

## ⚠️ PIÈGES À ÉVITER

### **Erreur #1 : Utiliser V1 au lieu de V2**
**Piège :** Importer depuis scripts/session119/pattern_detectors.py  
**Solution :** Importer depuis scripts/session120/single_wave_detectors_v2.py

**Raison :** V1 paramètres fixes inadaptés (10 pips)

### **Erreur #2 : Commencer ÉTAPE 3 avant ÉTAPE 2**
**Piège :** Vouloir créer système global sans valider Single Wave  
**Solution :** ÉTAPE 2 (Single Wave) PUIS ÉTAPE 3 (Global)

**Raison :** Valider détecteurs simples avant système complet

### **Erreur #3 : Oublier lecture MASTER_PLAN**
**Piège :** Commencer sans lire section Pattern Detectors  
**Solution :** Lire MASTER_PLAN.md AVANT tout (1er fichier liste)

**Raison :** Comprendre état actuel projet (Rev12, V2)

### **Erreur #4 : Accepter MAE > 10 pips sans analyser**
**Piège :** Ignorer MAE élevé et continuer  
**Solution :** Analyser cause + ajuster V2 si nécessaire

**Raison :** MAE élevé peut révéler problème V2

### **Erreur #5 : Scanner période trop courte**
**Piège :** Scanner seulement 2025 (pas assez cas)  
**Solution :** Scanner 2024-2025 minimum (étendre 2023 si besoin)

**Raison :** 5+ cas Single Wave peuvent être rares

---

## 💡 CODE RÉUTILISABLE

### **Imports à utiliser**
```python
# Détecteurs V2 (Session 120)
from pathlib import Path
import sys

session120_dir = Path(__file__).parent.parent / 'session120'
sys.path.insert(0, str(session120_dir))

from single_wave_detectors_v2 import (
    SingleWaveFortDetectorV2,
    SingleWaveIntermediateDetectorV2
)
from base_pattern_detector_v2 import prepare_dataframe

# Fonctions utilitaires (rev10)
session119_dir = Path(__file__).parent.parent / 'session119'
sys.path.insert(0, str(session119_dir))

from double_wave_detector_rev10 import (
    load_ohlc_1m_duckdb,
    to_pips
)
```

### **Structure Scanner DB**
```python
def scan_single_wave_cases(db_path, start_date, end_date):
    """
    Scanner DB pour mouvements 1 pic
    
    ALGORITHME:
    1. Charger events HIGH importance période
    2. Pour chaque date:
       - Charger OHLC 1-min
       - Calculer baseline
       - Détecter extrema post-event (utiliser find_local_extrema_adaptive V2)
       - Compter peaks significatifs (> seuil ATR)
       - Si 1 pic dominant → Single Wave candidat
       - Calculer impact approximatif
    3. Filtrer Fort (> 40 pips) vs Intermediate (20-40 pips)
    4. Sauvegarder JSON
    
    Returns:
        List[Dict] cas identifiés
    """
```

### **Structure Validation**
```python
def validate_single_wave_v2(cases, db_path):
    """
    Valide détecteurs V2 sur cas réels
    
    ALGORITHME:
    1. Pour chaque cas:
       - Charger OHLC
       - Calculer baseline
       - Appliquer SingleWaveFortV2 ou IntermediateV2
       - Récupérer impact MT5 (référence)
       - Calculer MAE
    2. Statistiques:
       - MAE par cas
       - MAE moyen
       - Success rate
       - Best/worst case
    
    Returns:
        Dict stats + résultats
    """
```

---

## 🎯 VALIDATION FIN SESSION 121

### **Checklist Succès**
- [ ] 5+ cas Single Wave identifiés
- [ ] MAE Single Wave < 10 pips (moyen)
- [ ] Système validation global opérationnel
- [ ] 10+ cas testés (mix patterns)
- [ ] R² > 0.90 (tous patterns)
- [ ] Graphiques créés (scatter plot, distribution)
- [ ] Documentation complète (2 rapports + handoff S122)

### **Métriques Attendues**
- Single Wave MAE : < 10 pips (moyen)
- Validation globale R² : > 0.90
- Success rate détection : > 80%

---

**Auteur :** André Valentin avec Claude  
**Date :** 07 novembre 2025  
**Version :** 1.1 (ajout MASTER_PLAN + structure projet)  
**Session :** 120 → 121
