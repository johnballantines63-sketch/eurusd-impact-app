# Session Validation Actuelle - Fichiers Actifs

**Date de création** : 2025-01-XX  
**Objectif** : Regrouper tous les fichiers actuellement utilisés pour la validation du pipeline

---

## 📁 STRUCTURE

```
SESSION_VALIDATION_ACTUELLE/
├── README.md                    # Ce fichier
├── INDEX_FICHIERS.md            # Index complet de tous les fichiers
├── scripts/                     # Scripts de test et validation
├── docs/                        # Documentation de la session
├── streamlit_app/               # Application Streamlit
├── outputs/                     # Résultats CSV et logs
├── src_core/                    # Modules core utilisés
└── references/                  # Références et backups
```

---

## 🎯 OBJECTIFS

1. **Clarté** : Regrouper tous les fichiers actifs dans un seul endroit
2. **Traçabilité** : Distinguer fichiers pré-11h37 vs post-11h37
3. **Validation** : Mesurer les impacts réels pour toutes les dates de test
4. **Documentation** : Documenter de façon exhaustive chaque étape

---

## 📋 FICHIERS CLÉS

### Scripts Principaux
- `scripts/run_pipeline_complete.py` - Pipeline complet (8 étapes)
- `scripts/validate_pipeline_multi_dates.py` - Validation multi-dates
- `scripts/test_restauration_cas_base.py` - Tests cas de base

### Documentation
- `docs/VALIDATION_SESSION_2025_01_XX/` - Documentation complète de la session
- `docs/PIPELINE_REFERENCE/` - Référence du pipeline

### Application
- `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py` - Planificateur actuel

### Modules Core
- `src/core/formulas_validated.py` - Formules validées
- `src/core/random_forest_amplification.py` - Random Forest
- `src/core/price_loader_finnhub.py` - Chargement prix Finnhub

---

## 🔍 DISTINCTION PRÉ/POST 11h37

**Pré-11h37** : Fichiers avant corrections majeures  
**Post-11h37** : Fichiers après corrections et optimisations

Voir `INDEX_FICHIERS.md` pour la liste complète avec timestamps.

---

## ✅ PROCHAINES ÉTAPES

1. Copier tous les fichiers actifs dans ce répertoire
2. Créer un script pour mesurer les impacts réels
3. Documenter chaque fichier et son rôle
4. Créer un index complet avec timestamps




