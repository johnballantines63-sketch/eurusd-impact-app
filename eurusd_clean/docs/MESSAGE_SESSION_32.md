# 🚀 MESSAGE SESSION 32 - Démarrage

**Date :** Session 32  
**Session précédente :** Session 31 - PredictionService créé  
**Tokens disponibles :** 190,000  
**Objectif :** Créer ScoringService + migrer scoring_engine.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 RÈGLE CRITIQUE - ORGANISATION FICHIERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**LIRE OBLIGATOIREMENT :** docs/REGLES_ORGANISATION_FICHIERS.md

**Règle absolue :**
✅ Fichiers permanents (PROJECT_STATE.md, README.md, etc.) → Racine
✅ Fichiers de session (MESSAGE_, SESSION_, FIN_) → docs/
❌ JAMAIS de fichiers de session à la racine

**En cas de doute : mettre dans docs/ !**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ INSTRUCTIONS DÉMARRAGE (5 MINUTES MAX)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📖 Lecture Obligatoire

**1. Lire PROJECT_STATE.md (10 min)**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
cat PROJECT_STATE.md
```

**Sections CRITIQUES à lire :**
- ✅ Section 1 : État Actuel (OBLIGATOIRE)
- ✅ Section 2 : Architecture Système (RÉFÉRENCE)
- ✅ Section 3 : Décisions Critiques (NE PAS OUBLIER)
- ✅ Section 7 : Sessions 29-31 Résumés (NOUVEAU)

**2. Consulter Résumé Session 31**
```bash
cat docs/SESSION_31_SUMMARY.md
```

**3. Vérifier Tokens Session 31**
Tokens utilisés Session 31 : 75,000 / 190,000 (39%)
→ Excellente gestion, beaucoup de marge !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RÉSUMÉ SESSION 31
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Ce qui a été fait ✅

### Analyse sequence_v87.py
✅ **Lecture complète** (750 lignes)
✅ Compréhension somme vectorielle
✅ Identification fonctions à migrer
✅ Documentation algorithme

### PredictionService Créé
✅ **app/services/prediction_service.py** (630 lignes)
✅ 3 méthodes principales :
   - predict_single_event()
   - predict_multi_events() avec somme vectorielle
   - predict_time_window()
✅ Fonctions utilitaires migrées :
   - get_event_direction()
   - calculate_surprise_percentage()
   - calculate_amplification_factor()
✅ Facteur correction 0.758 appliqué
✅ Respect erreurs récurrentes (#2, #3, #5)

### Tests Complets
✅ **tests/test_services/test_prediction_service.py** (550 lignes)
✅ 30+ tests unitaires + intégration
✅ Tests somme vectorielle validée
✅ Tests facteur 0.758
✅ Tests prévention erreurs récurrentes
✅ Script validation (test_prediction_service.py)

## Statistiques

**Progression migration :** 50% → 65% ✅  
**Modules migrés :** 4/11 (36%)  
**Services créés :** 2/3 (67%)  
**Code produit Session 31 :** ~1,540 lignes  
**Ratio tests/code :** 87%  
**Temps écoulé :** 3 heures  
**Tokens utilisés :** 75,000 / 190,000 (39%)

## Architecture Actuelle

```
eurusd_clean/
├── app/
│   ├── config.py              ✅ Session 30
│   ├── core/
│   │   ├── calculations.py    ✅ Session 29
│   │   └── models.py          ✅ Session 29
│   └── services/
│       ├── data_service.py    ✅ Session 30
│       └── prediction_service.py  ✅ Session 31
└── tests/
    ├── test_config.py         ✅ Session 30
    ├── test_core/             ✅ Session 29
    └── test_services/         ✅ Sessions 30-31
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 OBJECTIF SESSION 32
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Mission Principale

**Créer ScoringService + migrer scoring_engine.py**

## Tâches Détaillées

### 1. Lire scoring_engine.py (30 min)

**Source :** `fx_impact_app/src/scoring_engine.py`

**Objectif :** Comprendre logique score composite

**Points critiques :**
- Fonction principale : calculate_composite_score()
- Pondérations des critères (30% avg_pips, 25% consistency, ...)
- Échelle tradability (A+, A, B, C, D, E)
- Normalisation valeurs
- Critères : avg_movement, consistency, success_rate, latency, ttr

### 2. Créer ScoringService (2h)

**Destination :** `eurusd_clean/app/services/scoring_service.py`

**Objectif :** Service calcul scores familles d'événements

**Architecture :**
```python
class ScoringService:
    """Service calcul scores composite 0-100"""
    
    def __init__(self, data_service: DataService):
        """Injection DataService"""
        self.data = data_service
    
    def calculate_composite_score(
        self,
        avg_movement_pips: float,
        consistency_rate: float,
        success_rate: float,
        latency_minutes: float,
        ttr_minutes: float
    ) -> Dict[str, Any]:
        """
        Calcule score composite 0-100.
        
        Pondérations :
        - Avg movement : 30%
        - Consistency : 25%
        - Success rate : 20%
        - Latency : 15%
        - TTR : 10%
        
        Returns:
            - composite_score: 0-100
            - tradability: A+, A, B, C, D, E
            - subscores: {movement: X, consistency: Y, ...}
        """
    
    def calculate_family_score(
        self,
        family: str,
        country: str = 'US'
    ) -> Dict[str, Any]:
        """
        Calcule score pour famille d'événement.
        
        Utilise :
        - data_service.get_event_families() pour stats
        - calculate_composite_score() pour calcul
        """
    
    def rank_families(
        self,
        countries: List[str] = None,
        min_score: float = 0
    ) -> pd.DataFrame:
        """
        Classe toutes les familles par score.
        
        Returns DataFrame avec :
        - family, country, score, tradability
        """
    
    def get_tradability_label(
        self,
        score: float
    ) -> str:
        """
        Convertit score en label tradability.
        
        A+ : 90-100
        A  : 80-89
        B  : 70-79
        C  : 60-69
        D  : 50-59
        E  : 0-49
        """
```

**Fonctionnalités clés :**
- Injection DataService (pas de connexion directe DB)
- Pondérations configurables (depuis config.py)
- Normalisation valeurs
- Documentation complète

### 3. Tests ScoringService (1.5h)

**Destination :** `eurusd_clean/tests/test_services/test_scoring_service.py`

**Tests à créer :**
- test_init_with_data_service()
- test_calculate_composite_score()
- test_calculate_family_score()
- test_rank_families()
- test_get_tradability_label()
- test_score_bounds()
- test_ponderation_weights()
- test_integration_with_data_service()

**Cas edge à tester :**
- Famille sans stats
- Valeurs extrêmes (très haut/bas)
- Pondérations = 100%
- Score = 0, 50, 100

### 4. Script Validation (OPTIONNEL si temps)

**Si temps restant :**
- Créer scripts/test_scoring_service.py
- Validation 5-7 étapes
- Affichage scores familles principales

## Critères de Succès

- [ ] scoring_engine.py lu et compris
- [ ] ScoringService créé avec 4 méthodes principales
- [ ] Tests ScoringService passent
- [ ] Intégration avec DataService fonctionne
- [ ] Pondérations validées (100% au total)
- [ ] Documentation complète
- [ ] Tokens < 115k

## Temps Estimé

⏱️ **Total :** 4-5 heures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ POINTS D'ATTENTION CRITIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚨 Erreurs à NE JAMAIS Répéter

### Rappels Section 3 PROJECT_STATE.md

1. **Pas d'accès direct DB dans ScoringService**
   ```python
   # ❌ FAUX
   class ScoringService:
       def score(self):
           conn = duckdb.connect('warehouse.duckdb')
   
   # ✅ CORRECT
   class ScoringService:
       def __init__(self, data_service: DataService):
           self.data = data_service
   ```

2. **Utiliser event_families avec jointure country**
   ```sql
   -- ✅ CORRECT - Respecter erreur #3
   SELECT * FROM event_families ef
   WHERE ef.country = ?
   ```

3. **Normaliser valeurs avant calcul score**
   ```python
   # ✅ CORRECT - Normaliser [0, 1]
   normalized = (value - min_val) / (max_val - min_val)
   ```

4. **Vérifier pondérations = 100%**
   ```python
   # ✅ CORRECT - Validation
   weights = [0.30, 0.25, 0.20, 0.15, 0.10]
   assert sum(weights) == 1.0
   ```

**→ Lire toute la Section 3 pour les 9 erreurs complètes**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 GESTION TOKENS SESSION 32
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Instructions pour Claude

**À chaque étape importante :**

1. **Indiquer tokens utilisés**
   ```
   📊 Tokens : X / 190,000 (Y%)
   ```

2. **Fréquence :** Tous les 20-30k tokens

3. **Alerte à 115k tokens :**
   ```
   ⚠️ ALERTE TOKENS : 115k atteints
   
   Actions immédiates :
   1. 🛑 STOP développement
   2. 📝 Sauvegarder progression
   3. 🔄 Mettre à jour PROJECT_STATE.md
   4. ✉️ Créer MESSAGE_SESSION_33.md
   5. 🏁 Terminer proprement
   ```

4. **Format mise à jour PROJECT_STATE.md**
   ```markdown
   ## Session 32 (Date)
   
   ### Réalisations
   ✅ [Accomplissement 1]
   ✅ [Accomplissement 2]
   
   ### En Cours
   🚧 [Tâche non terminée] - X% complété
   
   ### Problèmes
   ⚠️ [Problème rencontré] - Solution : [...]
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 WORKFLOW SESSION 32
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Ordre d'Exécution Recommandé

### Phase 1 : Préparation (15 min)
1. Lire PROJECT_STATE.md (Sections 1-3 + Session 31)
2. Consulter SESSION_31_SUMMARY.md
3. Vérifier environnement Python
4. Tester DataService + PredictionService fonctionnent

### Phase 2 : Analyse scoring_engine (30 min)
1. Lire scoring_engine.py
2. Comprendre calcul score composite
3. Identifier fonctions à migrer
4. Noter dépendances

### Phase 3 : Création ScoringService (2h)
1. Créer app/services/scoring_service.py
2. Implémenter calculate_composite_score()
3. Implémenter calculate_family_score()
4. Implémenter rank_families()
5. Implémenter get_tradability_label()
6. Documentation complète

### Phase 4 : Tests ScoringService (1.5h)
1. Créer tests/test_services/test_scoring_service.py
2. Tests unitaires (méthodes isolées)
3. Tests intégration (avec DataService)
4. Tests edge cases

### Phase 5 : Documentation (30 min)
1. Mettre à jour PROJECT_STATE.md
2. Créer SESSION_32_SUMMARY.md
3. Mettre à jour CHANGELOG.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CHECKLIST SESSION 32
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Avant de Commencer
- [ ] PROJECT_STATE.md lu (Sections 1-3 + Session 31)
- [ ] SESSION_31_SUMMARY.md consulté
- [ ] DataService + PredictionService testés et fonctionnels

## Pendant la Session
- [ ] scoring_engine.py analysé
- [ ] ScoringService créé (4 méthodes)
- [ ] Tests ScoringService créés
- [ ] Tests passent
- [ ] Pondérations = 100%
- [ ] Scores dans plage [0, 100]
- [ ] Tokens surveillés (<115k)

## Avant de Terminer
- [ ] PROJECT_STATE.md mis à jour
- [ ] SESSION_32_SUMMARY.md créé
- [ ] CHANGELOG.md mis à jour
- [ ] Tests validation passent
- [ ] MESSAGE_SESSION_33.md créé (si nécessaire)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 RÉFÉRENCES RAPIDES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Fichiers Importants

| Fichier | Description | Chemin |
|---------|-------------|--------|
| PROJECT_STATE.md | Fichier maître | eurusd_clean/ |
| SESSION_31_SUMMARY.md | Résumé Session 31 | eurusd_clean/docs/ |
| scoring_engine.py | À analyser | fx_impact_app/src/ |
| data_service.py | Service DB | eurusd_clean/app/services/ |
| prediction_service.py | Service prédiction | eurusd_clean/app/services/ |
| config.py | Config centralisé | eurusd_clean/app/ |

## Commandes Utiles

```bash
# Tester DataService
cd eurusd_clean
python3 scripts/test_data_service.py

# Tester PredictionService
python3 scripts/test_prediction_service.py

# Lancer tests
pytest tests/test_services/ -v

# Activer venv
source venv/bin/activate

# Analyser scoring_engine
cat fx_impact_app/src/scoring_engine.py | head -100
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RAPPEL OBJECTIF FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Projet :** Application professionnelle EUR/USD Impact Calculator

**Statut actuel :** Migration structure clean 65% complétée

**Objectif Session 32 :** Avancer à 75% (ScoringService + tests)

**Objectif final :** Structure clean 100% opérationnelle

**Architecture cible :**
```
eurusd_clean/
├── app/
│   ├── config.py              ✅
│   ├── core/                  ✅
│   └── services/
│       ├── data_service.py    ✅
│       ├── prediction_service.py  ✅
│       └── scoring_service.py     ⏳ Session 32
└── tests/                     ✅ + Session 32
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🚀 Prêt à démarrer Session 32 !**

**Première action :** Lire PROJECT_STATE.md Section 1 + SESSION_31_SUMMARY.md

**Tokens Session 31 :** 75,000 / 190,000 (39% - Excellent)
**Tokens disponibles Session 32 :** 190,000

**Let's build the ScoringService! 🎯**
