# PLAN CORRECTION BUG TIMEZONE - SESSION 129

**Date :** 12 novembre 2025  
**Auteur :** André Valentin avec Claude  
**Statut :** ⏳ EN ATTENTE VALIDATION

---

## 🎯 OBJECTIF

Corriger le bug timezone dans 3 scripts de validation qui ajoutaient +2h à `ts_utc` alors qu'il est déjà en Bern time, causant un décalage de 2h dans tous les calculs.

**Impact :** Validation croisée CPI→NFP invalide (+98.6% faux), tests réels 1.8 invalides.

---

## 📋 SCRIPTS À CORRIGER

### **1. validate_cross_cpi_to_nfp.py**

**Lignes buguées :** 163-164, 273-274

**Fonction affectée :** `calculate_simple_r2_before_event()`

**Correction :**
```python
# ❌ AVANT (BUGUÉ)
def calculate_simple_r2_before_event(cluster_time, lookback_hours=168):
    # Convertir en Bern time
    cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
    start_bern = cluster_bern - pd.Timedelta(hours=lookback_hours)

# ✅ APRÈS (CORRIGÉ)
from utils_timezone import ensure_bern_time, get_price_window

def calculate_simple_r2_before_event(cluster_time, lookback_hours=168):
    # cluster_time vient de ts_utc qui est DÉJÀ en Bern time
    start_str, cluster_str, _ = get_price_window(
        cluster_time, 
        lookback_hours=lookback_hours,
        lookahead_hours=0
    )
```

**Lignes exactes à modifier :**
- Ligne 163-164 : Calcul R² avant événement
- Ligne 273-274 : Mesure impact réel

---

### **2. test_real_01_aout_2025.py**

**Lignes buguées :** ~130, ~150, ~246

**Corrections :**
```python
# ❌ AVANT (BUGUÉ)
cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
start_bern = cluster_bern - pd.Timedelta(hours=lookback_hours)

# ✅ APRÈS (CORRIGÉ)
from utils_timezone import ensure_bern_time, get_price_window

# Pour calcul R² (7j avant événement)
start_str, cluster_str, _ = get_price_window(
    cluster_time,
    lookback_hours=168,
    lookahead_hours=0
)

# Pour mesure impact (baseline + 1h après)
start_str, cluster_str, end_str = get_price_window(
    cluster_time,
    lookback_hours=0,  # Baseline = juste avant
    lookahead_hours=1
)
```

---

### **3. validate_split_train_test.py**

**Statut :** ✅ PAS de bug direct (utilise CSV Session 125)

**Action :** Vérifier que données source correctes (probablement OK)

---

## 🔧 MÉTHODE DE CORRECTION

### **Étape 1 : Import utils_timezone**

Ajouter en haut de chaque script :
```python
import sys
from pathlib import Path

# Import utilitaire timezone
UTILS_DIR = Path(__file__).parent
sys.path.insert(0, str(UTILS_DIR))
from utils_timezone import ensure_bern_time, get_price_window, format_for_prices_bern_query
```

### **Étape 2 : Remplacer conversions manuelles**

**Pattern à chercher :**
```python
cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
```

**Remplacer par :**
```python
cluster_bern = ensure_bern_time(cluster_time)  # Pas de +2h !
```

### **Étape 3 : Utiliser get_price_window()**

**Au lieu de :**
```python
cluster_bern = pd.to_datetime(cluster_time) + pd.Timedelta(hours=2)
start_bern = cluster_bern - pd.Timedelta(hours=lookback_hours)
start_str = start_bern.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
cluster_str = cluster_bern.strftime('%Y-%m-%d %H:%M:%S') + '+02:00'
```

**Utiliser :**
```python
start_str, cluster_str, _ = get_price_window(
    cluster_time,
    lookback_hours=168,
    lookahead_hours=0
)
```

### **Étape 4 : Validation**

Tester sur 11 septembre 2025 :
```python
# Événement connu
cluster_time = '2025-09-11 14:30:00+02:00'

# Doit retourner EXACTEMENT :
# event_str = '2025-09-11 14:30:00+02:00'
# PAS : '2025-09-11 16:30:00+02:00' (bugué)

start, event, end = get_price_window(cluster_time)
assert event == '2025-09-11 14:30:00+02:00', "Bug timezone persist!"
```

---

## 📊 TESTS DE VALIDATION

### **Test 1 : validate_cross_cpi_to_nfp.py**

**Attendu :**
- Clusters NFP : ~35 (2023-2025)
- Amélioration : probablement < 98.6% (résultat Session 128 faux)
- Amélioration réaliste : 30-60% (comme Session 125)

**Critère succès :**
- ✅ EXCELLENT : ≥ 50%
- ✅ GOOD : ≥ 30%
- ⚠️ MODERATE : ≥ 10%
- ❌ FAILED : < 10%

### **Test 2 : test_real_01_aout_2025.py**

**Attendu (selon image MT5) :**
- Impact réel : 173.7 pips HAUT (NFP spike)
- Baseline : ~1.0925 (close 14:29)
- Peak : ~1.1099 (max 1h après)

**Calcul correct :**
- Baseline prise à 14:29 (PAS 16:29)
- Impact mesuré 14:30-15:30 (PAS 16:30-17:30)

**Critère succès :**
- ✅ BON : Erreur < 20 pips
- ⚠️ MODÉRÉ : Erreur < 30 pips
- ❌ FAIBLE : Erreur > 30 pips

### **Test 3 : 11 septembre 2025**

**Référence validée :**
- Cluster : 14:30 Bern time
- Impact attendu : ~56 pips
- Baseline : close(14:29)

**Validation rapide :**
```python
# Test unitaire
def test_11_sept():
    cluster_time = '2025-09-11 14:30:00+02:00'
    start, event, end = get_price_window(cluster_time, lookback_hours=0, lookahead_hours=1)
    
    assert event == '2025-09-11 14:30:00+02:00', "Bug timezone!"
    assert end == '2025-09-11 15:30:00+02:00', "Bug lookahead!"
    
    print("✅ 11 septembre : Timestamps corrects")
```

---

## 🚦 ORDRE D'EXÉCUTION

### **Phase 1 : Correction (1h)**

1. ✅ Créer `utils_timezone.py` (FAIT)
2. ⏳ Corriger `validate_cross_cpi_to_nfp.py`
3. ⏳ Corriger `test_real_01_aout_2025.py`
4. ⏳ Vérifier `validate_split_train_test.py`

### **Phase 2 : Tests Unitaires (30min)**

1. ⏳ Test 11 septembre (timestamps corrects)
2. ⏳ Test fenêtres prix (baseline/impact corrects)
3. ⏳ Test consistency DB (ts_utc en +02:00)

### **Phase 3 : Re-validation (1h)**

1. ⏳ Lancer `validate_cross_cpi_to_nfp.py` corrigé
2. ⏳ Analyser vraie amélioration CPI→NFP
3. ⏳ Lancer `test_real_01_aout_2025.py` corrigé
4. ⏳ Vérifier erreur réelle vs 173.7 pips

### **Phase 4 : Décision (30min)**

1. ⏳ Comparer résultats avant/après correction
2. ⏳ Décision honnête : EXCELLENT/GOOD/MODERATE/FAILED
3. ⏳ Documentation complète
4. ⏳ Rapport Session 129

---

## 📝 CHECKLIST FINALE

### **Corrections**
- [ ] utils_timezone.py créé
- [ ] validate_cross_cpi_to_nfp.py corrigé (2 occurrences)
- [ ] test_real_01_aout_2025.py corrigé (3 occurrences)
- [ ] validate_split_train_test.py vérifié

### **Tests**
- [ ] Test 11 sept : timestamps corrects
- [ ] Test 1.8 : baseline correcte (14:29 pas 16:29)
- [ ] Test 1.8 : impact mesuré correct (173.7 pips)
- [ ] Validation croisée : résultats cohérents

### **Documentation**
- [ ] PLAN_CORRECTION.md (ce fichier)
- [ ] RAPPORT_CORRECTION_COMPLETE.md
- [ ] SESSION_129_RAPPORT_FINAL.md
- [ ] SESSION_130_HANDOFF.md

---

## ⚠️ POINTS CRITIQUES

### **1. NE JAMAIS faire confiance aux résultats sans vérifier**

Session 128 : +98.6% sonnait trop beau → était faux

### **2. TOUJOURS tester sur cas référence d'abord**

11 septembre DOIT valider avant tester 35 NFP

### **3. Accepter si résultats < attendus**

Session 125 : +88% CPI→NFP (à vérifier)  
Session 129 attendu : 30-60% (réaliste)

### **4. Documenter limitations honnêtement**

Pas survendre résultats → Crédibilité scientifique

---

## 🎯 CRITÈRES SUCCÈS SESSION 129

### **Minimum (OBLIGATOIRE)**
- ✅ Bug timezone corrigé (fonction utils_timezone)
- ✅ Validation croisée refaite avec vrais résultats
- ✅ Tests 1.8 + 11.9 avec calculs corrects
- ✅ Décision honnête (pas survente)

### **Optimal (SOUHAITABLE)**
- ✅ Amélioration validation > 30% (GOOD)
- ✅ Erreur tests réels < 20 pips
- ✅ Documentation complète avec limitations
- ✅ Fonction utilisable production (monitoring)

---

## 💡 LEÇONS POUR FUTURES SESSIONS

### **Éviter**
- ❌ Faire confiance aux résultats sans vérifier cas référence
- ❌ Ajouter Timedelta sans vérifier timezone existante
- ❌ Valider avec calculs complexes sans tests simples
- ❌ Survendre résultats (+98% trop beau!)

### **Prioriser**
- ✅ Créer utilitaires centralisés (ensure_bern_time)
- ✅ Tester sur cas référence AVANT généraliser
- ✅ Comparer avec résultats validés (Session 115/118)
- ✅ Accepter performance < attendue si honnête

---

**Auteur :** André Valentin avec Claude  
**Date :** 12 novembre 2025  
**Session :** 129  
**Statut :** ⏳ EN ATTENTE VALIDATION ANDRÉ
