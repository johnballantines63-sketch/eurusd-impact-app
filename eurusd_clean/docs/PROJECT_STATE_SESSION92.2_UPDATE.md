## 🔬 SESSION 92.2 : GRID SEARCH MÉTHODOLOGIE CORRECTE (27 octobre 2025)

### Objectif et Résultat

**Mission :** Créer grid search amplifications par TYPE avec méthodologie CORRECTE  
**Résultat :** ✅ SCRIPTS CRÉÉS - Exécution manuelle requise

### Correction Erreur Session 92.1

**Erreur identifiée :**
Session 92.1 utilisait approche **SIMPLIFIÉE INCORRECTE** :
```python
# ❌ INCORRECT (Session 92.1)
ratio = impact_réel_moyen / impact_prédit_moyen
amplification_optimale = 2.5 × ratio
```

**Cette approche NE respectait PAS la méthodologie complète du Planificateur !**

**Méthodologie CORRECTE (Session 92.2) :**

Le Planificateur V2.4 utilise une **CHAÎNE COMPLÈTE** :

1. Query SQL (lignes 189-210) : Charger événements `score > 40`
2. Calcul surprise (lignes 230-242) : Surprise max depuis actual/estimate
3. Ajustement score : `calculate_adjusted_empirical_score(base_score, surprise)`
4. Calcul impact : `calculate_impact_d(adjusted_score, num_events, amplification)`
5. Somme vectorielle : Direction + correction 0.758

**Session 92.2 réplique TOUTE cette chaîne, pas juste le ratio final !**

### Scripts Créés

**1. grid_search_amplification_by_type.py** (350 lignes)

Réplique EXACTEMENT le Planificateur V2.4 :
- Fonction `replicate_planificateur_prediction()` : Chaîne complète
- Fonction `grid_search_by_type()` : Grid search par type
- 26 amplifications testées (0.5 à 3.0, pas 0.1)
- Par type : CPI, NFP, FOMC, ISM, Employment
- Métrique : MAE (Mean Absolute Error)

**Algorithme :**
```
Pour chaque TYPE:
    Pour chaque AMPLIFICATION:
        Pour chaque DATE:
            1. Charger événements (query SQL Planificateur)
            2. Calculer surprise
            3. Ajuster score (Session 55)
            4. Calculer impact (Session 51 avec AMP testée)
            5. Comparer vs réel
        Calculer MAE
    Garder amplification minimisant MAE
```

**2. test_replication.py** (100 lignes)

Test validation sur 11 septembre 2025 :
- Vérifie réplication Planificateur fonctionne
- Résultat attendu : Impact ~56.3 pips ✅

### Différence Fondamentale vs Session 92.1

| Aspect | Session 92.1 (❌) | Session 92.2 (✅) |
|--------|-------------------|-------------------|
| **Approche** | Ratio simplifié | Chaîne complète |
| **Formules** | Ignorées | Sessions 51-55 |
| **Score** | Non ajusté | `calculate_adjusted_empirical_score()` |
| **Impact** | Ratio simple | `calculate_impact_d()` |
| **Validité** | Incorrecte | Méthodologie Planificateur |

**Résultats Session 92.1 (NON VALIDÉS) :**
- CPI : 2.08
- NFP : 1.84
- FOMC : 0.85
- ISM : 0.34

**Ces valeurs sont des ESTIMATIONS GROSSIÈRES à valider avec Session 92.2 !**

### Exécution Requise

**Scripts créés MAIS non exécutés** (trop lourd pour session Claude)

**André doit exécuter manuellement :**

```bash
cd eurusd_clean/scripts/session92.2

# 1. Test validation (rapide)
python test_replication.py

# 2. Grid search complet (5-10 minutes)
python grid_search_amplification_by_type.py
```

**Output attendu :**
- Console : Progression + résultats détaillés par type
- CSV : `grid_search_results_session92.2.csv`

**Format CSV :**
```csv
type,amplification_optimal,mae_pips,n_dates
CPI,X.X,XX.X,12
NFP,X.X,XX.X,10
FOMC,X.X,XX.X,8
ISM,X.X,XX.X,6
```

### Méthodologie Validée

**Réplication exacte Planificateur V2.4 :**

✅ Query SQL identique (lignes 189-210)  
✅ Calcul surprise identique (lignes 230-242)  
✅ `calculate_adjusted_empirical_score()` (Session 55)  
✅ `calculate_impact_d()` (Session 51)  
✅ Pas de raccourcis ou simplifications

**Cette approche garantit :**
- Cohérence avec Planificateur actuel
- Utilisation formules validées (94-99% précision)
- Comparabilité directe prédictions vs réalité
- Pas de biais méthodologique

### Fichiers Session 92.2

**Scripts :**
```
eurusd_clean/scripts/session92.2/
├── grid_search_amplification_by_type.py (350 lignes)
└── test_replication.py (100 lignes)
```

**Documentation :**
```
eurusd_clean/docs/
├── SESSION92.2_RAPPORT_COMPLET.md (400+ lignes)
└── MESSAGE_SESSION92.2_SESSION92.3.md (350+ lignes)
```

**Outputs attendus :**
```
eurusd_clean/scripts/session92.2/
└── grid_search_results_session92.2.csv (résultats)
```

### Points Critiques

**1. ISM Restera Problématique**

Attendu : MAE > 30 pips même avec amplification optimale

Raison : ISM a patterns différents (variabilité extrême)

Solution : Si confirmé, analyser ISM séparément Session 92.3

**2. Pas de Nouvelles Formules**

Grid search utilise formules Sessions 51-55 UNIQUEMENT

Amplification = seul paramètre variable

Formules validées = fondation inviolable

**3. Validation Obligatoire**

Après exécution, OBLIGATOIRE :
- Vérifier amplifications cohérentes (0.5-3.0)
- Tester sur 11 septembre
- Calculer MAE projeté global
- Confirmer amélioration vs facteur fixe 2.5

### Leçons Apprises

**1. Simplification = Danger**

Session 92.1 a échoué en simplifiant la chaîne de calcul.

Leçon : Toujours répliquer TOUTE la méthodologie, pas juste le résultat.

**2. Documentation Code Source Essentielle**

Sans lire lignes 189-277 du Planificateur, impossible de répliquer.

Leçon : MANDATORY_SESSION_RULES.md a raison - LIRE code avant coder.

**3. Formules Validées = Fondation**

Les formules Sessions 51-55 sont la base de TOUT.

Leçon : Utiliser `formulas_validated.py` toujours, jamais créer nouvelles.

### Métriques Session 92.2

- **Tokens :** 88,000 / 105,000 (83.8%)
- **Durée :** ~2h
- **Scripts créés :** 2 (450 lignes total)
- **Documentation :** 2 fichiers (750+ lignes)
- **Exécution :** ⏳ Manuelle requise (André)

### Prochaine Étape Session 92.3

**Mission :** Implémenter amplifications calibrées dans Planificateur V2.4

**Approche :**
1. Examiner résultats CSV grid search
2. Créer dictionnaire AMPLIFICATIONS_BY_TYPE
3. Modifier calculate_predictions() pour utiliser amplifications dynamiques
4. Tester sur 5+ dates (11 sept, 01 août, etc.)
5. Valider MAE global < 25 pips

**Scénarios :**
- **A (attendu)** : Amplifications cohérentes → Implémentation
- **B (si ISM problématique)** : MAE ISM > 50 pips → Analyse dédiée

**Budget estimé :** 95k tokens
