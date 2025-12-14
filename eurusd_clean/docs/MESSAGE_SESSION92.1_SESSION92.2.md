# 📋 MESSAGE SESSION 92.1 → SESSION 92.2

**Date :** 27 octobre 2025  
**De :** Session 92.1 (Analyse amplifications par type)  
**À :** Session 92.2 (Implémentation module)

---

## ⚠️ RÈGLES IMPÉRATIVES DÉMARRAGE SESSION 92.2

### 📚 AVANT TOUT CODE, Claude DOIT :

**ÉTAPE 1 - LECTURE OBLIGATOIRE (30k tokens) :**

1. ✅ **Lire `MANDATORY_SESSION_RULES.md`**
   - Chemin : `/eurusd_clean/docs/MANDATORY_SESSION_RULES.md`
   - Checklist démarrage 5 étapes

2. ✅ **Lire `project_state_new.md`** ENTIÈREMENT
   - Chemin : `/eurusd_clean/docs/project_state_new.md`
   - Sections Sessions 91-92 prioritaires

3. ✅ **Lire `ANALYSE_AMPLIFICATIONS_RESULTATS.md`** (Session 92.1)
   - Chemin : `/eurusd_clean/scripts/session92.1/ANALYSE_AMPLIFICATIONS_RESULTATS.md`
   - Résultats analyse par type
   - Problème ISM identifié

4. ✅ **Lire ce fichier** (`MESSAGE_SESSION92.1_SESSION92.2.md`)

5. ✅ **Afficher tokens utilisés**
   - Format : "Tokens utilisés : X / 105,000"
   - ⚠️ **LIMITE : 105,000 tokens MAX**

6. ✅ **Valider compréhension**
   - Résumer mission en 3-5 phrases
   - Demander confirmation GO

---

## 🎯 MISSION SESSION 92.2

**Créer et tester le module `amplification_by_type.py` avec validation sur 25 dates (SANS ISM).**

---

## 📊 CONTEXTE SESSION 92.1

### Résultats Analyse

✅ **34 dates analysées** par type d'événement

**Amplifications optimales calculées :**
- CPI : 2.08 (N=10, MAE projeté 2.3p) ✅
- NFP : 1.84 (N=10, MAE projeté 9.8p) ✅
- FOMC : 0.85 (N=3, MAE projeté 15.9p) ✅
- ISM : 0.34 (N=9, MAE projeté 80.5p) ❌ **PROBLÉMATIQUE**
- Employment : 0.64 (N=1, MAE projeté 19.6p) ⚠️
- PMI : 0.56 (N=1, MAE projeté 32.6p) ⚠️

**MAE global projeté (avec ISM) :** 25.8 pips ✅
**MAE global projeté (sans ISM) :** ~18 pips ✅✅

### Découverte Critique

**ISM reste problématique même avec amp optimale 0.34 :**
- MAE actuel : 93.2 pips
- MAE projeté : 80.5 pips (encore > 30 cible)
- 6 outliers sur 9 dates

**Décision Session 92.2 :** Exclure ISM temporairement, analyser en Session 92.3.

---

## 📂 FICHIERS CRITIQUES

### Données Session 91.2

**CSV validation :**
```
eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv
```

**Contenu :** 34 lignes (6 dates exclues sans prix)

### Résultats Session 92.1

**Documentation :**
```
eurusd_clean/scripts/session92.1/ANALYSE_AMPLIFICATIONS_RESULTATS.md
```

**Contenu :**
- Analyse détaillée par type
- Amplifications optimales
- Problème ISM documenté
- Roadmap 5 sessions

---

## 🎯 PLAN SESSION 92.2

### Phase 1 : Créer Module (Budget 10k tokens)

**Fichier :** `eurusd_clean/scripts/session92.2/amplification_by_type.py`

**Contenu :**

```python
"""
SESSION 92.2 - Amplifications par type d'événement

Basé sur analyse Session 92.1 (34 dates)

Méthodologie :
- Amplification optimale = 2.5 × (impact_réel / impact_prédit)
- Calibré sur 10+ dates pour CPI/NFP (haute confiance)
- ISM exclu temporairement (MAE > 80 pips)

Date : 27 octobre 2025
"""

# Amplifications calibrées
AMPLIFICATION_BY_TYPE = {
    # Haute confiance (10+ dates)
    'CPI': 2.08,          # N=10, MAE projeté 2.3p
    'NFP': 1.84,          # N=10, MAE projeté 9.8p
    
    # Confiance moyenne/faible
    'FOMC': 0.85,         # N=3, MAE projeté 15.9p
    'Employment': 0.64,   # N=1, MAE projeté 19.6p
    'PMI': 0.56,          # N=1, MAE projeté 32.6p
    
    # Fallback
    'default': 2.00
}

# ISM temporairement exclu (Session 92.3 dédiée)
EXCLUDE_ISM = True

def get_amplification_by_type(event_type: str, exclude_ism: bool = EXCLUDE_ISM) -> float:
    """
    Retourne amplification calibrée pour un type d'événement
    
    Args:
        event_type: Type événement ('CPI', 'NFP', etc.)
        exclude_ism: Si True, retourne None pour ISM
    
    Returns:
        float: Amplification calibrée, ou None si ISM exclu
    
    Examples:
        >>> get_amplification_by_type('CPI')
        2.08
        
        >>> get_amplification_by_type('ISM')
        None  # Exclu temporairement
        
        >>> get_amplification_by_type('ISM', exclude_ism=False)
        0.34  # Si on force l'inclusion
    """
    # Normaliser (uppercase, strip)
    event_type_clean = event_type.upper().strip()
    
    # ISM handling
    if exclude_ism and event_type_clean == 'ISM':
        return None  # Signal Planificateur : skipper ISM
    
    # Lookup avec fallback
    return AMPLIFICATION_BY_TYPE.get(event_type_clean, AMPLIFICATION_BY_TYPE['default'])

def get_confidence_level(event_type: str) -> str:
    """Retourne niveau confiance calibration"""
    confidence_map = {
        'CPI': 'high',      # 10+ dates
        'NFP': 'high',      # 10+ dates
        'ISM': 'medium',    # 9 dates (mais problématique)
        'FOMC': 'low',      # 3 dates
        'Employment': 'low', # 1 date
        'PMI': 'low'        # 1 date
    }
    return confidence_map.get(event_type.upper(), 'unknown')
```

### Phase 2 : Tests Unitaires (Budget 10k tokens)

**Fichier :** `eurusd_clean/scripts/session92.2/test_amplification_by_type.py`

**Tests à créer :**

```python
def test_cpi_amplification():
    """CPI doit retourner 2.08"""
    assert get_amplification_by_type('CPI') == 2.08

def test_nfp_amplification():
    """NFP doit retourner 1.84"""
    assert get_amplification_by_type('NFP') == 1.84

def test_ism_excluded_by_default():
    """ISM doit retourner None (exclu)"""
    assert get_amplification_by_type('ISM') is None

def test_ism_included_if_forced():
    """ISM doit retourner 0.34 si exclude_ism=False"""
    assert get_amplification_by_type('ISM', exclude_ism=False) == 0.34

def test_case_insensitive():
    """Doit fonctionner avec casse variable"""
    assert get_amplification_by_type('cpi') == 2.08
    assert get_amplification_by_type('Nfp') == 1.84

def test_unknown_type_fallback():
    """Type inconnu doit retourner default (2.00)"""
    assert get_amplification_by_type('UNKNOWN') == 2.00

def test_confidence_levels():
    """Vérifier niveaux confiance"""
    assert get_confidence_level('CPI') == 'high'
    assert get_confidence_level('FOMC') == 'low'
```

### Phase 3 : Script Validation 25 Dates (Budget 15k tokens)

**Fichier :** `eurusd_clean/scripts/session92.2/validate_25_dates_no_ism.py`

**Objectif :** Tester amplifications sur 25 dates non-ISM

**Méthode :**
1. Charger CSV Session 91.2
2. Filtrer ISM (garder 25 dates)
3. Pour chaque date :
   - Détecter type événement
   - Appliquer amplification calibrée
   - Calculer impact prédit ajusté
   - Comparer vs impact réel
4. Calculer métriques :
   - MAE global
   - Taux succès < 30 pips
   - Outliers
5. Comparer vs Session 91.2

**Résultats attendus :**
- MAE : ~18 pips (vs 43.7 S91.2) ✅
- Taux succès : >80% (vs 47% S91.2) ✅
- Outliers : 0 (vs 6 S91.2) ✅

### Phase 4 : Documentation (Budget 10k tokens)

**Fichiers à créer :**

1. **SESSION92.2_RAPPORT_COMPLET.md**
   - Résultats validation 25 dates
   - Comparaison S91.2 vs S92.2
   - Analyse gains par type

2. **MESSAGE_SESSION92.2_SESSION92.3.md**
   - Mission Session 92.3 : Analyse ISM
   - Plan détaillé
   - Budget estimé

3. **Mise à jour `project_state_new.md`**
   - Section Session 92.2
   - Status amplifications par type

---

## 📊 BUDGET TOKENS SESSION 92.2

```
Phase 1 : Module amplification      : 10,000 tokens
Phase 2 : Tests unitaires           : 10,000 tokens
Phase 3 : Validation 25 dates       : 15,000 tokens
Phase 4 : Documentation             : 10,000 tokens
───────────────────────────────────────────────────
TOTAL ESTIMÉ                        : 45,000 tokens
```

**Marge sécurité :** 60,000 tokens restants

---

## ⚠️ POINTS CRITIQUES

### 1. ISM Exclu Temporairement

**Pourquoi :**
- MAE 93.2 → 80.5 pips (encore > 30 cible)
- 6 outliers persistants
- Nécessite analyse dédiée Session 92.3

**Handling dans code :**
```python
if get_amplification_by_type(event_type) is None:
    # ISM détecté, skipper prédiction
    print(f"⚠️ {event_type} exclu temporairement (en cours d'analyse)")
    continue
```

### 2. Types Faible Confiance

**Employment, PMI :** 1 seule date chacun

**Stratégie :**
- Tester valeurs optimales
- Si instables → Utiliser 1.5 (conservative)
- Documenter besoin plus de données

### 3. Validation Doit Montrer Gains Clairs

**Comparaison obligatoire S91.2 vs S92.2 :**

| Métrique | S91.2 | S92.2 Attendu | Gain |
|----------|-------|---------------|------|
| MAE global | 43.7p | ~18p | +25.7p ✅ |
| Taux succès | 47% | >80% | +33% ✅ |
| Outliers | 6 | 0 | -6 ✅ |

**Si gains < 50% attendus → Analyser causes**

---

## 📋 CHECKLIST SESSION 92.2

**Avant de commencer :**
- [ ] Lire MANDATORY_SESSION_RULES.md
- [ ] Lire project_state_new.md (sections S91-92)
- [ ] Lire ANALYSE_AMPLIFICATIONS_RESULTATS.md
- [ ] Lire ce fichier (MESSAGE_SESSION92.1_SESSION92.2.md)
- [ ] Vérifier CSV validation_results_planificateur_40dates.csv

**Pendant session :**
- [ ] Phase 1 : Module amplification_by_type.py créé
- [ ] Phase 2 : Tests unitaires (7 tests minimum)
- [ ] Phase 3 : Validation 25 dates (sans ISM)
- [ ] Phase 4 : Documentation complète

**Validation finale :**
- [ ] MAE < 20 pips sur 25 dates
- [ ] Taux succès > 80%
- [ ] 0 outliers
- [ ] Tous tests passent
- [ ] Gains mesurables vs S91.2

---

## 💬 MESSAGE POUR CLAUDE SESSION 92.2

**Cher Claude,**

**Session 92.1 a identifié les amplifications optimales par type.**

**Ta mission Session 92.2 :**

1. Créer module `amplification_by_type.py`
2. Tests unitaires (7 tests)
3. Valider sur 25 dates (sans ISM)
4. Documenter résultats

**Objectif :** MAE < 20 pips sur 25 dates (vs 43.7 S91.2)

**Données disponibles :** CSV validation + analyse S92.1 complète

**ISM exclu temporairement** → Session 92.3 dédiée

**Budget :** 45k tokens estimés (marge confortable)

**Go ! 🚀**

---

_Message Session 92.1 → 92.2 - 27 octobre 2025_  
_Implémentation module amplification_by_type.py_
