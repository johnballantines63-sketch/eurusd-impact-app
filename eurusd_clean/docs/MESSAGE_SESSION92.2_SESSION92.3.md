# 📋 MESSAGE SESSION 92.2 → SESSION 92.3

**Date :** 27 octobre 2025  
**De :** Session 92.2 (Scripts grid search créés)  
**À :** Session 92.3 (Implémentation amplifications calibrées)

---

## 📊 STATUT SESSION 92.2

### ✅ Réalisations

**Scripts créés avec méthodologie CORRECTE :**

1. **`grid_search_amplification_by_type.py`** (350 lignes)
   - Réplication EXACTE Planificateur V2.4
   - Grid search 26 amplifications × 40 dates
   - Par type : CPI, NFP, FOMC, ISM, Employment

2. **`test_replication.py`** (100 lignes)
   - Test validation 11 septembre
   - Vérifie réplication fonctionne

**Documentation complète :**
- SESSION92.2_RAPPORT_COMPLET.md (400+ lignes)
- Méthodologie expliquée en détail
- Comparaison vs Session 92.1 incorrecte

**Correction erreur Session 92.1 :**
- ❌ Session 92.1 : Formule simplifiée (ratio)
- ✅ Session 92.2 : Chaîne complète Planificateur

### ⏳ Exécution Requise

**Scripts créés MAIS non exécutés** (trop lourd pour session)

**André doit exécuter manuellement :**
```bash
cd eurusd_clean/scripts/session92.2
python test_replication.py              # Validation rapide
python grid_search_amplification_by_type.py  # Grid search complet (5-10 min)
```

---

## 🎯 MISSION SESSION 92.3

### OBJECTIF PRINCIPAL

**Implémenter amplifications calibrées dans Planificateur V2.4**

**Approche :**
1. Examiner résultats grid search Session 92.2
2. Valider cohérence amplifications trouvées
3. Modifier Planificateur pour utiliser amplifications par TYPE
4. Tester sur 11 septembre + autres dates
5. Valider MAE global < 25 pips

### SCÉNARIOS POSSIBLES

**Scénario A : Grid Search Réussi (attendu)**

Résultats cohérents, amplifications optimales trouvées

→ **SESSION 92.3 : Implémentation Planificateur**

**Scénario B : ISM Problématique**

ISM a MAE > 50 pips même avec amplification optimale

→ **SESSION 92.3 : Analyse ISM dédiée**

---

## 📋 CHECKLIST DÉMARRAGE SESSION 92.3

### Avant Tout Code

- [ ] Lire `MANDATORY_SESSION_RULES.md`
- [ ] Lire `project_state_new.md` (sections S51-55, S91-92)
- [ ] Lire `SESSION92.2_RAPPORT_COMPLET.md` (ce qui a été fait)
- [ ] Lire ce fichier (MESSAGE transition)
- [ ] **CRITIQUE : Examiner CSV résultats grid search**
- [ ] Afficher tokens utilisés
- [ ] Résumer compréhension mission
- [ ] Demander confirmation GO

### Fichiers Critiques à Lire

**Résultats Session 92.2 :**
```
eurusd_clean/scripts/session92.2/grid_search_results_session92.2.csv
```

**Planificateur actuel :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_[...].py
```

**Formules validées :**
```
fx_impact_app/src/formulas_validated.py
```

---

## 🔬 PLAN SESSION 92.3 (Scénario A)

### Phase 1 : Analyse Résultats (Budget 15k tokens)

**1. Charger CSV résultats**
```python
df_results = pd.read_csv('grid_search_results_session92.2.csv')
```

**2. Examiner amplifications trouvées**
- Valeurs entre 0.5 et 3.0 ? ✅
- Cohérence inter-types ?
- Comparaison vs Session 92.1 (±20% acceptable)

**3. Décision validation**
- Si cohérent → Continuer implémentation
- Si incohérent → Analyser causes

### Phase 2 : Modification Planificateur (Budget 40k tokens)

**Fichier à modifier :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py
```

**Backup OBLIGATOIRE avant modification :**
```
5_Planificateur_V2_[...].py.backup_session92.3_avant_amplification_type
```

**Modifications à effectuer :**

**1. Dictionnaire amplifications (après ligne 45)**
```python
# SESSION 92.3 : Amplifications calibrées par type
AMPLIFICATIONS_BY_TYPE = {
    'CPI': X.X,      # Depuis grid search
    'NFP': X.X,
    'FOMC': X.X,
    'ISM': X.X,
    'Employment': X.X,
    'DEFAULT': 2.5   # Fallback types inconnus
}
```

**2. Fonction get_amplification_for_type()**
```python
def get_amplification_for_type(events_df: pd.DataFrame) -> float:
    """
    Retourne amplification optimale selon type événement dominant
    
    Args:
        events_df: DataFrame événements
    
    Returns:
        float: Amplification calibrée ou 2.5 si type inconnu
    """
    if events_df.empty:
        return 2.5
    
    # Identifier type dominant (majorité événements)
    # Stratégie 1 : Famille la plus fréquente
    families = events_df['family'].value_counts()
    dominant_family = families.index[0] if len(families) > 0 else None
    
    # Mapper famille → type
    # CPI, NFP, etc.
    type_mapping = {
        'CPI': 'CPI',
        'NFP': 'NFP',
        'FOMC': 'FOMC',
        'ISM': 'ISM',
        'Jobless': 'Employment',
        # ...
    }
    
    event_type = type_mapping.get(dominant_family, 'DEFAULT')
    amplification = AMPLIFICATIONS_BY_TYPE.get(event_type, 2.5)
    
    return amplification
```

**3. Modifier calculate_predictions() (ligne ~246)**
```python
# AVANT (Session 72) :
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=2.5  # ← Facteur fixe
)

# APRÈS (Session 92.3) :
amplification = get_amplification_for_type(cpi_events)  # ← Dynamique !
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=amplification
)
```

**4. Affichage UI (badge)**
```python
st.info(f"📊 Type détecté : {event_type} | Amplification : {amplification:.1f}x")
```

### Phase 3 : Tests Validation (Budget 25k tokens)

**Tests obligatoires :**

**1. Test 11 septembre 2025** (CPI)
- Amplification utilisée = amplification CPI trouvée
- Impact prédit ~55-60 pips (vs 56.2 réel)
- MAE < 10 pips ✅

**2. Test 01 août 2025** (NFP)
- Amplification utilisée = amplification NFP trouvée
- Impact prédit ~170-180 pips (vs 173.8 réel)
- Amélioration vs Session 92.1

**3. Test 17 septembre ou 10 décembre**
- Type FOMC ou autre
- Vérifier amplification correcte appliquée
- MAE cohérent

**4. Calcul MAE global**
- Retester TOUTES les 40 dates CSV
- Comparer vs Session 91.2 (MAE 39.5 pips)
- Objectif : MAE < 30 pips ✅

### Phase 4 : Documentation (Budget 15k tokens)

**Fichiers à créer :**

1. **SESSION92.3_RAPPORT_COMPLET.md**
   - Amplifications trouvées
   - Modifications Planificateur
   - Tests validation
   - Comparaison vs Sessions 91-92

2. **MESSAGE_SESSION92.3_SESSION93.md**
   - Système production-ready
   - MAE final obtenu
   - Limitations connues (ISM si >50 pips)

3. **Mise à jour `project_state_new.md`**
   - Section Session 92.3
   - Amplifications validées
   - Performance finale

---

## 🔬 PLAN SESSION 92.3 (Scénario B - ISM Problématique)

**Si ISM a MAE > 50 pips après grid search :**

### Mission Alternative

**Analyser pourquoi ISM est différent**

**1. Analyse patterns ISM** (20k tokens)
- Charger TOUTES dates ISM depuis DB
- Comparer vs CPI/NFP/FOMC
- Identifier différences structurelles

**2. Hypothèses à tester** (30k tokens)
- ISM a timing différent (TTR plus long ?)
- ISM a amplification non-linéaire ?
- ISM nécessite formule séparée ?

**3. Tests validation** (20k tokens)
- Si formule ISM créée, valider sur dates test
- Calculer MAE ISM spécifique
- Objectif : MAE < 40 pips

**4. Documentation** (25k tokens)
- Patterns ISM documentés
- Formule ISM si créée
- Limitations ISM si non résolu

---

## ⚠️ POINTS CRITIQUES SESSION 92.3

### 1. Mapper Famille → Type

**Défi :** CSV a colonne `type` mais Planificateur utilise `family`

**Solution :**
```python
# Créer dictionnaire mapping
FAMILY_TO_TYPE = {
    'CPI': 'CPI',
    'Core CPI': 'CPI',
    'CPI_YoY': 'CPI',
    'NFP': 'NFP',
    'Nonfarm Payrolls': 'NFP',
    'FOMC': 'FOMC',
    'ISM': 'ISM',
    'Jobless Claims': 'Employment',
    # ...
}
```

**Alternative :**
- Détection automatique via patterns dans `event_title`
- Plus robuste mais plus complexe

### 2. Type Mixte

**Problème :** Cluster avec CPI + NFP + Jobless (types différents)

**Solutions possibles :**
- **Option A :** Type majoritaire (>50% événements)
- **Option B :** Moyenne pondérée amplifications
- **Option C :** Amplification max (approche conservatrice)

**Recommandation :** Option A (type majoritaire)

### 3. Version Planificateur

**Attention :** Plusieurs versions Planificateur existent

**Utiliser :**
```
5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py
```

**C'est la version Session 72 corrigée (importance_n fixé)**

### 4. Tests Exhaustifs

**Ne PAS se contenter de 11 septembre !**

**Minimum 5 dates :**
- 11.09 (CPI)
- 01.08 (NFP)
- 17.09 ou 05.09 (FOMC/autre)
- 1 date ISM
- 1 date Employment

**Idéal : Retester toutes 40 dates CSV Session 90**

---

## 📊 MÉTRIQUES CIBLES SESSION 92.3

### Performance Attendue

**MAE par type (après calibration) :**
- CPI : < 15 pips ✅✅
- NFP : < 20 pips ✅✅
- FOMC : < 25 pips ✅
- ISM : < 40 pips ⚠️ (acceptable si >30)
- Employment : < 20 pips ✅

**MAE global :**
- Session 91.2 (coefficient 0.55) : 39.5 pips
- **Session 92.3 (amplifications calibrées) : < 25 pips** ✅✅✅

**Amélioration attendue : +37%**

### Critères Succès

**✅ Amplifications cohérentes**
- Entre 0.5 et 3.0
- Variation logique inter-types
- Pas de valeurs aberrantes

**✅ MAE < 30 pips**
- Sur ensemble test 40 dates
- Amélioration vs Session 91.2
- ≥80% dates MAE < 20 pips

**✅ Implémentation stable**
- Planificateur fonctionne avec amplifications dynamiques
- UI affiche type + amplification
- Tests passent ✅

**✅ Documentation complète**
- Amplifications documentées
- Méthodologie expliquée
- Limitations connues (ISM ?)

---

## 🔄 BUDGET TOKENS SESSION 92.3

**Scénario A (Implémentation) :**
```
Phase 1 : Analyse résultats        : 15,000 tokens
Phase 2 : Modification Planificateur: 40,000 tokens
Phase 3 : Tests validation         : 25,000 tokens
Phase 4 : Documentation            : 15,000 tokens
─────────────────────────────────────────────────
TOTAL ESTIMÉ                       : 95,000 tokens
```

**Scénario B (Analyse ISM) :**
```
Analyse patterns ISM               : 20,000 tokens
Tests hypothèses                   : 30,000 tokens
Validation formule ISM             : 20,000 tokens
Documentation                      : 25,000 tokens
─────────────────────────────────────────────────
TOTAL ESTIMÉ                       : 95,000 tokens
```

**Budget serré mais réaliste dans les deux cas.**

---

## 📚 RÉFÉRENCES IMPORTANTES

### Formules Sessions 51-55

**Module :** `fx_impact_app/src/formulas_validated.py`

**Utilisées :**
- `calculate_adjusted_empirical_score()` (99.9% précision)
- `calculate_impact_d()` (98.6% précision)

**À continuer d'utiliser !** Pas de nouvelles formules !

### Planificateur V2.4

**Fichier actuel (Session 72) :**
```
5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py
```

**Lignes critiques :**
- 189-210 : Query SQL
- 230-242 : Calcul surprise
- 244-277 : calculate_predictions()

**À modifier ligne ~246 :** Amplification dynamique

### Données Validation

**CSV Session 90 :**
```
eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv
```

**40 dates testées avec amplification 2.5 fixe**

**CSV Session 92.2 :**
```
eurusd_clean/scripts/session92.2/grid_search_results_session92.2.csv
```

**Amplifications optimales par type (à examiner Session 92.3)**

---

## 💬 MESSAGE POUR CLAUDE SESSION 92.3

**Cher Claude,**

**Session 92.2 a créé les scripts grid search avec méthodologie CORRECTE.**

**Ta mission Session 92.3 dépend des résultats grid search :**

**SI amplifications cohérentes trouvées :**
1. Examiner CSV résultats
2. Créer dictionnaire AMPLIFICATIONS_BY_TYPE
3. Modifier Planificateur fonction calculate_predictions()
4. Tester sur 5+ dates
5. Valider MAE < 25 pips ✅

**SI ISM problématique (MAE > 50) :**
1. Analyser patterns ISM
2. Identifier différences structurelles
3. Tester formule ISM séparée
4. Documenter limitations

**MÉTHODOLOGIE OBLIGATOIRE :**
- Utiliser formules Sessions 51-55 (JAMAIS créer nouvelles)
- Backup avant modification Planificateur
- Tests exhaustifs (5+ dates minimum)
- Documentation complète

**Budget : ~95k tokens**

**Résultat attendu : Planificateur avec amplifications calibrées, MAE < 25 pips**

**Go avec rigueur ! 🚀**

---

_Message Session 92.2 → 92.3 - 27 octobre 2025_  
_Implémentation amplifications calibrées par type_
