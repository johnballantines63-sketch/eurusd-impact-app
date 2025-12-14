# Changelog - EUR/USD Impact Calculator Clean

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Prévu
- PredictionService (Session 31)
- ScoringService (Session 31-32)
- Interface UI Streamlit refactorisée
- Tests d'intégration complets

---

## [0.3.0] - 2025-10-22 - Session 30

### Ajouté
- **app/config.py** : Configuration centralisée complète (500 lignes)
  - Classe Config avec paramètres métier
  - Gestion variables d'environnement (.env)
  - Validation configuration au démarrage
  - Fonctions rétro-compatibles avec legacy
  
- **app/services/data_service.py** : Interface unique DB (650 lignes)
  - 9 méthodes d'accès données
  - Context manager pour connexions
  - get_events() avec filtres multiples
  - get_event_families() avec statistiques
  - get_prices() pour prix EUR/USD
  - get_db_stats() pour diagnostics
  
- **tests/test_services/test_data_service.py** : Tests complets (450 lignes)
  - 30+ tests unitaires et intégration
  - Tests edge cases critiques
  - Validation avec DB réelle
  
- **scripts/test_data_service.py** : Script validation rapide
- **docs/SESSION_30_SUMMARY.md** : Documentation complète Session 30
- **MESSAGE_SESSION_31.md** : Instructions Session suivante

### Changé
- Structure services/ créée avec __init__.py
- Tests organisés par module (test_services/)

### Corrigé
- Respect erreur #2 : Surprise avec fallback estimate/previous
- Respect erreur #3 : Jointure event_families avec country
- Import circulaire services/__init__.py

### Statistiques
- Code produit : 1,900 lignes
- Tests/Code ratio : 65%
- Modules migrés : 3/11 (27%)
- Progression : 30% → 50%

---

## [0.2.0] - 2025-10-22 - Session 29

### Ajouté
- **scripts/migration/analyze_current_usage.py** : Analyse AST imports (520 lignes)
  - Scan complet fx_impact_app/ (148 fichiers)
  - Détection dépendances entre modules
  - Génération MIGRATION_REPORT.md
  
- **app/core/calculations.py** : Logique calculs pure (450 lignes)
  - Migration depuis forecaster_mvp.py
  - 6 fonctions principales refactorisées
  - calculate_family_stats()
  - calculate_single_event_impact()
  - calculate_latency()
  - calculate_ttr()
  - predict_impact_v9_clean()
  - calculate_multiple_families()
  
- **app/core/models.py** : Data models événements (520 lignes)
  - Migration depuis event_families.py
  - Data class EventFamily
  - 28 familles d'événements avec patterns
  - Fonctions utilitaires
  
- **tests/test_core/test_calculations.py** : Tests calculations (350 lignes)
  - Tests latence, TTR, prédiction
  - Cas nominaux + edge cases
  
- **tests/test_core/test_models.py** : Tests models (280 lignes)
  - Tests EventFamily, getters
  - Validation données

### Changé
- Séparation logique métier / accès DB
- Documentation inline enrichie (docstrings avec exemples)
- Type hints ajoutés partout

### Amélioré
- Code legacy classe → Fonctions pures
- Tests unitaires complets créés
- Organisation claire par module

### Statistiques
- Code migré : ~800 lignes → ~970 lignes (clean + tests)
- Modules testés : 2/11 (18%)
- Progression : 10% → 30%

---

## [0.1.0] - 2025-10-22 - Session 28

### Ajouté
- Structure complète eurusd_clean/
- **PROJECT_STATE.md** : Fichier maître unique (source de vérité)
- **STRUCTURE.md** : Arborescence détaillée
- **README.md** : Guide démarrage
- Répertoires app/, tests/, scripts/, docs/

### Décisions Architecturales
- Migration vers structure clean (vs correction incrémentale)
- Séparation core / services / UI
- Tests automatisés obligatoires
- Documentation centralisée

### Analysé
- Lecture complète 27 sessions précédentes
- Identification 9 erreurs récurrentes critiques
- Analyse 400+ fichiers legacy
- Création plan migration détaillé

### Documenté
- Section 3 PROJECT_STATE.md : Erreurs à ne jamais répéter
- Checklist avant requête SQL
- Standards qualité code

### Statistiques
- Temps analyse : 3 heures
- Documents créés : 4
- Scripts diagnostic : 3
- Progression : 0% → 10%

---

## [0.0.1] - 2025-10-21 - Sessions 1-27 (Legacy)

### Contexte
Développement initial application EUR/USD Impact Calculator.
400+ fichiers Python à la racine, organisation chaotique.

### Problèmes Identifiés
- Code spaghetti (Planificateur 2,200 lignes)
- Multiples versions coexistant (v85-v87)
- 9 erreurs répétées faute de continuité
- Dette technique importante
- Documentation fragmentée

### Décision
Migration complète vers structure clean professionnelle.

---

## Types de changements

- **Ajouté** : pour les nouvelles fonctionnalités
- **Changé** : pour les modifications de fonctionnalités existantes
- **Déprécié** : pour les fonctionnalités qui seront bientôt supprimées
- **Supprimé** : pour les fonctionnalités supprimées
- **Corrigé** : pour les corrections de bugs
- **Sécurité** : en cas de vulnérabilités

---

## Versioning

Format : MAJEUR.MINEUR.CORRECTIF

- **MAJEUR** : Changements incompatibles de l'API
- **MINEUR** : Ajout de fonctionnalités rétro-compatibles
- **CORRECTIF** : Corrections de bugs rétro-compatibles

---

**Maintenu par :** Sessions de développement avec Claude
**Dernière mise à jour :** Session 30 (22 octobre 2025)
