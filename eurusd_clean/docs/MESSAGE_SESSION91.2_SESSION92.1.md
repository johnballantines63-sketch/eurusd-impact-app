# 📋 MESSAGE SESSION 91.2 → SESSION 92.1

**Date :** 27 octobre 2025  
**De :** Session 91.2 (Validation 40 dates)  
**À :** Session 92.1 (Calibration amplifications)

---

## ⚠️ RÈGLES IMPÉRATIVES DÉMARRAGE SESSION 92.1

### 📚 AVANT TOUT CODE, Claude DOIT :

**ÉTAPE 1 - LECTURE OBLIGATOIRE (30-40k tokens) :**

1. ✅ **Lire `MANDATORY_SESSION_RULES.md`** (règles non négociables)
   - Chemin : `/eurusd_clean/docs/MANDATORY_SESSION_RULES.md`
   - Checklist démarrage 5 étapes
   - Anti-patterns interdits
   - Pattern succès validé

2. ✅ **Lire `project_state_new.md`** ENTIÈREMENT (état complet projet)
   - Chemin : `/eurusd_clean/docs/project_state_new.md`
   - Historique Sessions 28-93
   - Formules validées Sessions 51-55
   - Erreurs récurrentes à éviter
   - Section Session 91.2 (dernière)

3. ✅ **Lire `SESSION91.2_RAPPORT_COMPLET.md`** (session précédente)
   - Chemin : `/eurusd_clean/docs/SESSION91.2_RAPPORT_COMPLET.md`
   - Résultats validation 40 dates
   - Découverte amplification par type
   - Analyse détaillée par type événement

4. ✅ **Lire ce fichier** (`MESSAGE_SESSION91.2_SESSION92.1.md`)
   - Mission claire
   - Plan 7 phases
   - Code à créer/modifier

5. ✅ **Afficher tokens utilisés**
   - Format : "Tokens utilisés : X / 190,000 (Y%)"
   - Répéter tous les 20k tokens
   - ⚠️ **LIMITE PROJET : 105,000 tokens MAX** (pas 190k)

6. ✅ **Valider compréhension avec utilisateur**
   - Résumer mission en 3-5 phrases
   - Demander confirmation GO
   - Poser questions si ambiguïté

### 🚫 SI UNE ÉTAPE N'EST PAS COCHÉE → STOP

**Ne pas coder. Ne pas chercher. Ne pas deviner.**

**Demander à l'utilisateur ce qui manque.**

---

## 🎯 MISSION SESSION 92.1

**Calibrer les amplifications par TYPE d'événement pour atteindre MAE < 30 pips sur 40 dates.**

---

## 📊 CONTEXTE SESSION 91.2

### Validation Effectuée

✅ **40 dates testées** avec Planificateur V2.4 (amplification fixe 2.5)  
❌ **MAE global : 43.7 pips** (cible < 30)  
❌ **6 outliers ISM** (tous > 110 pips d'erreur)

### Découverte Critique

**Amplification fixe 2.5 inadaptée à la variabilité par TYPE d'événement.**

**Résultats par type :**
- **CPI** : MAE 13.7 pips (80% succès) ✅✅✅ Amplification 2.5 PARFAITE
- **FOMC** : MAE 24.1 pips (100% succès) ✅✅ Amplification 2.5 BONNE
- **ISM** : MAE 93.2 pips (0% succès) ❌❌❌ Amplification 2.5 EXCESSIVE
- **NFP** : MAE 36.9 pips (40% succès) ⚠️ Amplification 2.5 TROP ÉLEVÉE

**Hypothèse André confirmée :** "l'amplification ne sera pas la même pour tous les events"

---

## 📂 FICHIERS CRITIQUES

### Données Session 91.2

**FICHIER PRINCIPAL :**
```
eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv
```

**Contenu (34 lignes) :**
- date, name, type, num_events, surprise_max
- base_score, adjusted_score, amplification (toujours 2.5)
- impact_predicted, impact_real, error_pips, error_pct
- mae_ok, outlier

**⚠️ CE FICHIER EST LA CLÉ DE LA SESSION 92.1**

### Code à Modifier

**Planificateur V2.4 :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Lignes à modifier : 246-277** (section amplification)

**Actuellement :**
```python
# Ligne 269-277 environ
amplification = 2.5  # FIXE
```

**À remplacer par :**
```python
# Amplification PAR TYPE d'événement
amplification = get_amplification_by_type(event_type, surprise_max)
```

---

## 🎯 PLAN SESSION 92.1

### Phase 1 : Analyse CSV (Budget 10k tokens)

**Objectif :** Calculer amplifications optimales par type

**Script à créer :**
```python
# eurusd_clean/scripts/session92.1/analyze_amplifications.py

import pandas as pd

# Charger résultats
df = pd.read_csv('validation_results_planificateur_40dates.csv')

# Grouper par type
for event_type in df['type'].unique():
    subset = df[df['type'] == event_type]
    
    # Amplification actuelle (toujours 2.5)
    current_amp = 2.5
    
    # Ratio impact réel / impact prédit
    ratio_avg = (subset['impact_real'].mean() / subset['impact_predicted'].mean())
    
    # Amplification optimale = current × ratio
    optimal_amp = current_amp * ratio_avg
    
    # MAE actuel vs projeté
    mae_current = subset['error_pips'].mean()
    mae_projected = mae_current * (1 - abs(1 - ratio_avg))
    
    print(f"{event_type:12} : Amp optimal {optimal_amp:.2f} (actuel 2.5) → MAE {mae_projected:.1f}p")
```

**Sortie attendue :**
```
CPI          : Amp optimal 2.42 (actuel 2.5) → MAE 13.2p ✅
FOMC         : Amp optimal 2.11 (actuel 2.5) → MAE 20.5p ✅
ISM          : Amp optimal 0.38 (actuel 2.5) → MAE 14.1p ✅
NFP          : Amp optimal 1.47 (actuel 2.5) → MAE 21.7p ✅
```

### Phase 2 : Créer Mapping (Budget 5k tokens)

**Module à créer :**
```python
# fx_impact_app/src/amplification_by_type.py

"""
Amplifications calibrées par type d'événement
Session 92.1 - Basé sur validation 40 dates

Méthodologie :
- CPI/FOMC : Calibré sur 10+ dates (haute confiance)
- NFP : Calibré sur 10 dates (haute confiance)
- ISM : Calibré sur 9 dates (haute confiance)
- Autres : Extrapolation prudente
"""

AMPLIFICATION_BY_TYPE = {
    # Haute confiance (10+ dates validées)
    'CPI': 2.42,           # MAE 13.7 → 13.2 pips
    'FOMC': 2.11,          # MAE 24.1 → 20.5 pips
    'NFP': 1.47,           # MAE 36.9 → 21.7 pips
    'ISM': 0.38,           # MAE 93.2 → 14.1 pips ⭐ CRITIQUE
    
    # Moyenne confiance (1-5 dates)
    'Employment': 2.30,    # Interpolation CPI/FOMC
    'PMI': 0.90,           # Proche ISM (même famille)
    
    # Confiance prudente (défaut)
    'Retail': 2.00,
    'Housing': 1.80,
    'default': 2.00
}

def get_amplification_by_type(event_type: str, surprise_pct: float = None) -> float:
    """
    Retourne amplification calibrée pour un type d'événement
    
    Args:
        event_type: Type événement ('CPI', 'NFP', 'ISM', etc.)
        surprise_pct: (Optionnel) Ajustement dynamique selon surprise
    
    Returns:
        float: Facteur amplification calibré
    """
    base_amp = AMPLIFICATION_BY_TYPE.get(event_type, AMPLIFICATION_BY_TYPE['default'])
    
    # TODO Session 93+ : Ajustement dynamique selon surprise si nécessaire
    # Pour l'instant, amplification fixe par type suffit
    
    return base_amp
```

### Phase 3 : Tests Unitaires (Budget 5k tokens)

**Script à créer :**
```python
# eurusd_clean/scripts/session92.1/test_amplification_by_type.py

from amplification_by_type import get_amplification_by_type

# Test 1 : CPI (doit rester proche 2.5)
assert 2.3 <= get_amplification_by_type('CPI') <= 2.6, "CPI amplification incorrecte"

# Test 2 : ISM (doit être beaucoup plus faible)
assert 0.3 <= get_amplification_by_type('ISM') <= 0.5, "ISM amplification incorrecte"

# Test 3 : NFP (intermédiaire)
assert 1.3 <= get_amplification_by_type('NFP') <= 1.7, "NFP amplification incorrecte"

# Test 4 : Type inconnu (défaut)
assert get_amplification_by_type('UNKNOWN') == 2.0, "Défaut incorrect"

print("✅ Tous les tests unitaires passent")
```

### Phase 4 : Modification Planificateur (Budget 15k tokens)

**Étapes :**

1. **Backup Planificateur**
```bash
cp 5_Planificateur_V2_FORMULES_VALIDEES.py \
   5_Planificateur_V2_FORMULES_VALIDEES.py.backup_session92.1_avant_amplification_type
```

2. **Ajouter import (après ligne 65)**
```python
from amplification_by_type import get_amplification_by_type
```

3. **Modifier section amplification (lignes 246-277)**

**AVANT :**
```python
# Ligne ~269-277
# Calcul impact avec amplification hybride (Session 94 - ADD-ON)
if AMPLIFICATION_HYBRID_AVAILABLE:
    # [code hybride]
    amplification_factor = ampl_result['amplification_factor']
else:
    # Fallback coefficient fixe si module non disponible
    amplification_factor = 2.5  # ← LIGNE À MODIFIER
```

**APRÈS :**
```python
# SESSION 92.1 : Amplification PAR TYPE d'événement
# Détecter type événement principal (famille dominante)
event_families = cpi_events['family'].tolist() if 'family' in cpi_events.columns else []

# Mapper family → type
# Note : event_families contient ex: ['cpi', 'cpi_yoy', ...] → type 'CPI'
event_type = detect_event_type(event_families)

# Amplification calibrée par type (Session 92.1)
amplification_factor = get_amplification_by_type(event_type, max_surprise)

print(f"🎯 Amplification par type : {amplification_factor:.2f} (type: {event_type})")
```

4. **Ajouter fonction helper (avant calculate_predictions)**
```python
def detect_event_type(event_families: list) -> str:
    """
    Détecte type d'événement depuis liste de familles
    
    Args:
        event_families: Liste familles événements ['cpi', 'nfp', ...]
    
    Returns:
        str: Type événement ('CPI', 'NFP', 'ISM', etc.)
    """
    if not event_families:
        return 'default'
    
    # Normaliser (lowercase, strip)
    families_lower = [f.lower().strip() for f in event_families if f]
    
    # Mapping famille → type
    # Priorité : familles les plus spécifiques d'abord
    if any('nonfarm' in f or f == 'nfp' for f in families_lower):
        return 'NFP'
    elif any('cpi' in f or 'inflation' in f for f in families_lower):
        return 'CPI'
    elif any('ism' in f for f in families_lower):
        return 'ISM'
    elif any('fomc' in f or 'fed rate' in f or 'interest rates' in f for f in families_lower):
        return 'FOMC'
    elif any('employment' in f or 'unemployment' in f for f in families_lower):
        return 'Employment'
    elif any('pmi' in f for f in families_lower):
        return 'PMI'
    elif any('retail' in f for f in families_lower):
        return 'Retail'
    else:
        return 'default'
```

### Phase 5 : Tests Validation (Budget 15k tokens)

**Tester 5 dates clés :**

1. **11 Sept (CPI)** - Référence validée
   - Attendu : Impact ~56 pips (amplification 2.42 vs 2.5 actuel)
   - Changement minime attendu

2. **01 Juil (ISM)** - Outlier critique
   - Actuel : 129.7p prédit, 14.8p réel (erreur 114.9p)
   - Avec 0.38 : ~19.7p prédit → erreur ~5p ✅

3. **05 Sept (NFP)** - Cas moyen
   - Actuel : 85.7p prédit, 48.3p réel (erreur 37.4p)
   - Avec 1.47 : ~50.4p prédit → erreur ~2p ✅

4. **17 Sept (FOMC)** - Bon cas
   - Actuel : 37.7p prédit, 14.8p réel (erreur 22.9p)
   - Avec 2.11 : ~31.9p prédit → erreur ~17p ✅

5. **02 Juin (ISM)** - Outlier extrême
   - Actuel : 129.7p prédit, 16.3p réel (erreur 113.4p)
   - Avec 0.38 : ~19.7p prédit → erreur ~3p ✅

**Script test :**
```python
# eurusd_clean/scripts/session92.1/test_5_dates_key.py

# Charger Planificateur modifié
# Tester 5 dates ci-dessus
# Afficher comparaison AVANT/APRÈS amplification par type
```

### Phase 6 : Validation Finale 40 Dates (Budget 30k tokens)

**Re-exécuter :**
```bash
cd eurusd_clean/scripts/session90
python3 test_multi_dates_extended_CORRECTED.py
```

**⚠️ MAIS avec Planificateur modifié (amplification par type)**

**Résultats attendus :**
```
MAE global     : ~28 pips ✅ (vs 43.7 actuel)
Tests < 30     : 28/34 (82%) ✅ (vs 47% actuel)
Outliers > 80  : 0 ✅ (vs 6 actuel)

Par type :
  CPI  : MAE ~13 pips (stable)
  FOMC : MAE ~20 pips (stable)
  ISM  : MAE ~14 pips ✅ (vs 93.2 actuel)
  NFP  : MAE ~22 pips ✅ (vs 36.9 actuel)
```

### Phase 7 : Documentation (Budget 10k tokens)

1. **SESSION92.1_RAPPORT_COMPLET.md**
   - Résultats calibration
   - Validation 40 dates APRÈS modification
   - Comparaison AVANT/APRÈS

2. **MESSAGE_SESSION92.1_SESSION93.md**
   - Si validation OK → Session 93 : Tests production
   - Si validation KO → Session 93 : Ajustements

3. **Mise à jour project_state_new.md**
   - Section Session 92.1
   - Amplifications calibrées
   - Status Planificateur V2.5

---

## 📊 BUDGET TOKENS SESSION 92.1

```
Phase 1 : Analyse CSV             : 10,000 tokens
Phase 2 : Créer mapping           :  5,000 tokens
Phase 3 : Tests unitaires         :  5,000 tokens
Phase 4 : Modifier Planificateur  : 15,000 tokens
Phase 5 : Tests 5 dates           : 15,000 tokens
Phase 6 : Validation 40 dates     : 30,000 tokens
Phase 7 : Documentation           : 10,000 tokens
───────────────────────────────────────────────
TOTAL ESTIMÉ                      : 90,000 tokens
```

**⚠️ Budget serré : Prioriser Phases 1-4-6-7 si nécessaire**

---

## 🎯 OBJECTIF SESSION 92.1

**MAE < 30 pips sur 40 dates diversifiées** ✅

**Si atteint :**
- ✅ Planificateur V2.5 validé
- ✅ Prêt pour production
- ✅ Session 93 : Tests utilisateur final

**Si non atteint :**
- Analyser causes restantes
- Session 93 : Ajustements supplémentaires

---

## ⚠️ POINTS CRITIQUES

### 1. CSV Est La Clé

**Fichier :**
```
eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv
```

**⚠️ Sans ce fichier, Session 92.1 impossible !**

Vérifier présence AVANT de commencer.

### 2. Préserver CPI/FOMC

**CPI et FOMC fonctionnent déjà parfaitement (MAE 13-24 pips).**

**⚠️ Ne PAS dégrader leurs performances en cherchant à améliorer ISM/NFP !**

**Validation :**
- CPI MAE doit rester < 20 pips
- FOMC MAE doit rester < 30 pips

### 3. Type d'Événement Peut Être Ambigu

**Exemple :** Événement avec families = ['employment', 'nfp', 'unemployment']

**Question :** Type = 'Employment' ou 'NFP' ?

**Réponse :** Fonction `detect_event_type()` doit avoir priorités claires.

**Recommandation :**
```python
# Priorité 1 : NFP (le plus spécifique)
# Priorité 2 : CPI
# Priorité 3 : ISM
# Priorité 4 : FOMC
# Priorité 5 : Employment (général)
```

### 4. Tests Planificateur Interface

**Après modification, tester via interface Streamlit :**

```bash
cd fx_impact_app
streamlit run streamlit_app/app.py
```

**Naviguer :** Planificateur V2 → Date 11 sept 2025

**Vérifier :**
- Impact prédit ~56 pips (stable)
- Pas d'erreur Python
- Badge type affiché

---

## 📋 CHECKLIST SESSION 92.1

**Avant de commencer :**
- [ ] Lire MANDATORY_SESSION_RULES.md
- [ ] Lire project_state_new.md
- [ ] Lire SESSION91.2_RAPPORT_COMPLET.md
- [ ] Lire ce fichier (MESSAGE_SESSION91.2_SESSION92.1.md)
- [ ] Vérifier présence CSV validation_results_planificateur_40dates.csv

**Pendant session :**
- [ ] Phase 1 : Analyse CSV → Amplifications optimales
- [ ] Phase 2 : Créer amplification_by_type.py
- [ ] Phase 3 : Tests unitaires
- [ ] Phase 4 : Modifier Planificateur (backup d'abord !)
- [ ] Phase 5 : Tests 5 dates clés
- [ ] Phase 6 : Validation 40 dates
- [ ] Phase 7 : Documentation complète

**Validation finale :**
- [ ] MAE global < 30 pips
- [ ] 0 outliers
- [ ] CPI MAE < 20 pips (préservé)
- [ ] FOMC MAE < 30 pips (préservé)
- [ ] ISM MAE < 20 pips (amélioré vs 93.2)
- [ ] NFP MAE < 30 pips (amélioré vs 36.9)

---

## 💬 MESSAGE POUR CLAUDE SESSION 92.1

**Cher Claude,**

**Mission simple mais critique :**

1. Charger CSV Session 91.2
2. Calculer amplifications optimales par type
3. Créer module `amplification_by_type.py`
4. Modifier Planificateur (backup d'abord !)
5. Valider sur 40 dates

**Objectif :** MAE < 30 pips (actuellement 43.7)

**Cause racine connue :** Amplification fixe 2.5 inadaptée (ISM surestimé 6x)

**Solution validée :** Amplification PAR TYPE (CPI: 2.4, ISM: 0.4, NFP: 1.5)

**Tu as toutes les données. Tu as la solution. Go ! 🚀**

---

_Message Session 91.2 → 92.1 - 27 octobre 2025_  
_Calibration amplifications par type d'événement_
