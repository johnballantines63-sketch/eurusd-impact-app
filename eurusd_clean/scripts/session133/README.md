# 📊 SESSION 133 - INTÉGRATION DOUBLEWAVE DANS PLANIFICATEUR

**Date :** 13 novembre 2025  
**Durée estimée :** 4 heures  
**Statut :** 🟡 EN COURS

---

## 🎯 OBJECTIF

Intégrer le module DoubleWave validé (Session 132) dans le Planificateur avec aiguillage intelligent par pattern détecté.

---

## 📋 PLAN SESSION

### **PHASE 1 : Flowchart (✅ COMPLÉTÉ)**

**Objectif :** Créer flowchart complet AVANT toute intégration code

**Livrables :**
- ✅ `flowchart_planificateur.md` (11 étapes détaillées)

**Durée :** 30 minutes

---

### **PHASE 2 : Implémentation (⏳ EN COURS)**

**Objectif :** Coder Planificateur V3.0 selon flowchart

**Actions :**
1. ⏳ Créer `planificateur_v3.py`
2. ⏳ Implémenter 11 étapes flowchart
3. ⏳ Intégrer modules existants :
   - `src/core/doublewave_prediction.py`
   - `scripts/session120/double_wave_detector_rev12.py`
   - Fonction universelle amp(R²)
4. ⏳ Tests unitaires

**Livrables :**
- ⏳ `planificateur_v3.py` (~1,000 lignes)
- ⏳ Tests validation

**Durée estimée :** 2 heures

---

### **PHASE 3 : Tests Multi-Dates (⏳ PRÉVU)**

**Objectif :** Valider sur 3+ cas représentatifs

**Cas tests :**
1. **2025-09-11** : Double Wave (Overlap superposition ECB+US)
2. **2024-12-18** : Single Wave (Fed Decision)
3. **2024-09-12** : Double Wave (Overlap standard US)

**Critères validation :**
- ✅ Pattern détecté correctement
- ✅ Prédiction calculée
- ✅ Affichage clair
- ✅ Pas d'erreur timezone
- ✅ Warnings appropriés

**Livrables :**
- ⏳ `test_planificateur.py`
- ⏳ Résultats 3 dates

**Durée estimée :** 1 heure

---

### **PHASE 4 : Interface Streamlit (⏳ PRÉVU)**

**Objectif :** Interface utilisateur graphique

**Actions :**
1. ⏳ Adapter `app.py` pour utiliser Planificateur V3.0
2. ⏳ Affichage pattern détecté
3. ⏳ Graphiques interactifs
4. ⏳ Export résultats

**Livrables :**
- ⏳ Interface Streamlit fonctionnelle
- ⏳ Documentation utilisateur

**Durée estimée :** 30 minutes

---

## 📁 FICHIERS CRÉÉS

```
scripts/session133/
├── README.md                          # Ce fichier
├── flowchart_planificateur.md        # ✅ Flowchart 11 étapes
├── planificateur_v3.py               # ⏳ Implémentation
├── test_planificateur.py             # ⏳ Tests 3 dates
└── integration_notes.md              # ⏳ Notes intégration
```

---

## 🔑 POINTS CRITIQUES

### **1. Flowchart AVANT Code**
✅ Flowchart créé et complet (11 étapes)  
⏳ Attendre validation André avant implémenter

### **2. Modules Existants à Utiliser**
- ✅ `src/core/doublewave_prediction.py` (Session 132)
- ✅ `scripts/session120/double_wave_detector_rev12.py` (MAE 4.5 pips)
- ✅ Fonction universelle amp(R²) (Session 125-126)

### **3. Critères Session 131 à Respecter**
- ✅ Overlap standard : amp 0.1201
- ✅ Overlap superposition : amp 0.0128
- ✅ Cascade : EXCLURE systématiquement
- ✅ Score 150-350, 5-10 events, pays majeurs

### **4. MAE Session 132 à Considérer**
- ✅ Single_Wave_Standard : 9.99 pips (EXCELLENT)
- ⚠️ Double_Wave : 957.97 pips (À AMÉLIORER)
- ❌ Single_Wave_Fort : 39k pips (À AMÉLIORER)
→ Afficher warnings appropriés

### **5. Timezone CRITIQUE**
- ✅ Toujours `tz='Europe/Zurich'` pour prix
- ✅ Convertir events UTC → Bern
- ✅ Baseline = close(t-1) avant premier event

---

## 📊 CRITÈRES SUCCÈS SESSION 133

### **Minimum (2h) :**
- [x] Flowchart créé et complet
- [ ] Planificateur V3.0 implémenté
- [ ] 1 date testée avec succès

### **Optimal (4h) :**
- [x] Flowchart créé et validé
- [ ] Planificateur V3.0 implémenté et testé
- [ ] 3+ dates testées (différents patterns)
- [ ] Interface Streamlit adaptée
- [ ] Documentation utilisateur

---

## 🎓 LEÇONS SESSION 132 À APPLIQUER

### **1. Flowchart ESSENTIEL**
✅ Créé AVANT code (évite 50% erreurs)

### **2. Vérification Patterns CRITIQUE**
→ Utiliser détecteur validé (Rev12)

### **3. Ne Pas Mélanger Amplifications**
- Double Wave : amp fixes (0.1201 ou 0.0128)
- Single Wave : amp(R²) dynamique
- NE JAMAIS mélanger !

### **4. Timezone Précis**
- Baseline correcte = critique
- 5 pips erreur → 20+ pips finale

---

## 📈 MÉTRIQUES ATTENDUES

### **Performance**
- Temps exécution : < 5 sec/date
- Pas d'erreur timezone
- Prédictions cohérentes

### **Précision**
- Single_Wave_Standard : MAE ~10 pips (validé S132)
- Double_Wave : MAE à valider sur nouveaux cas
- Warnings affichés pour Single_Wave_Fort

### **UX**
- Affichage clair pattern détecté
- Justification méthodologie
- Messages erreur explicites

---

## 🚀 PROCHAINES ACTIONS

### **Immédiat**
1. ✅ Flowchart créé → Attendre validation André
2. ⏳ Implémenter planificateur_v3.py
3. ⏳ Tester sur 2025-09-11 (cas référence)

### **Après Tests**
1. ⏳ Adapter interface Streamlit
2. ⏳ Documentation utilisateur
3. ⏳ Session 134 : Nouveaux cas nov-déc 2025

---

## 💡 NOTES DÉVELOPPEMENT

### **Architecture Planificateur V3.0**
```python
class PlanificateurV3:
    """
    Planificateur intégrant détection pattern + prédiction adaptée
    
    Workflow:
    1. Charger events + prix
    2. Enrichir avec scores
    3. Détecter pattern (Double/Single)
    4. Aiguiller vers bon module
    5. Afficher résultats
    """
    
    def __init__(self, db_path, timezone="Europe/Zurich"):
        self.db_path = db_path
        self.timezone = timezone
        self.detector = DoubleWaveDetectorRev12()
    
    def predict_for_date(self, date_str):
        # Implémenter flowchart 11 étapes
        pass
```

### **Modules à Importer**
```python
# Détection pattern
from scripts.session120.double_wave_detector_rev12 import DoubleWaveDetectorRev12

# Prédiction Double Wave
from src.core.doublewave_prediction import predict_doublewave_overlap

# Scores empiriques
from scripts.session127.utils_mapping_variants import get_empirical_score_with_variants

# Amplification universelle (Single Wave)
from src.core.formulas_validated import calculate_amplification_from_r2
```

---

## ⚠️ PIÈGES À ÉVITER

1. ❌ **Coder sans flowchart validé**
   → ✅ Flowchart créé, attendre validation

2. ❌ **Utiliser pattern Single_Wave_Fort sans warning**
   → ✅ Afficher MAE 39k pips (Session 132)

3. ❌ **Oublier timezone**
   → ✅ Toujours Europe/Zurich + conversions

4. ❌ **Mélanger amplifications**
   → ✅ Double Wave = fixes, Single Wave = amp(R²)

5. ❌ **Baseline incorrecte**
   → ✅ close(t-1), PAS low(t0)

---

## 📚 RÉFÉRENCES

### **Flowchart**
→ `scripts/session133/flowchart_planificateur.md`

### **Module DoubleWave**
→ `src/core/doublewave_prediction.py` (Session 132)

### **Détecteur Rev12**
→ `scripts/session120/double_wave_detector_rev12.py` (MAE 4.5 pips)

### **Critères Inclusion/Exclusion**
→ `docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_132_HANDOFF.md`

### **Fonction Universelle**
→ `01_VISION/PIPELINE_AUTOMATISE_REUTILISABLE.md`

---

**Auteur :** André Valentin avec Claude  
**Session :** 133  
**Date :** 13 novembre 2025  
**Statut :** 🟡 PHASE 1 COMPLÉTÉE - PHASE 2 À DÉMARRER
