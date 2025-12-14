# Pipeline Actif - Fichiers Principaux

**Date création** : 2025-12-03  
**Objectif** : Regrouper tous les fichiers utilisés par le pipeline pour faciliter la gestion, les backups et l'utilisation

---

## 📁 STRUCTURE

```
pipeline_active/
├── README.md (ce fichier)
├── scripts/
│   └── run_pipeline_complete.py (script principal)
├── core/
│   ├── event_loader.py
│   ├── formulas_validated.py
│   ├── trend_detection_pre_event_s107.py
│   ├── price_loader_finnhub.py
│   ├── random_forest_amplification.py
│   ├── r2_amplification_correlation.py
│   ├── finnhub_patterns.py
│   ├── double_wave.py
│   └── single_wave_strong.py
└── session120/
    └── double_wave_detector_rev12.py
```

---

## 🔗 LIENS SYMBOLIQUES

Les fichiers dans `pipeline_active/` sont des liens symboliques vers les fichiers réels dans le projet.

**Avantages** :
- ✅ Un seul endroit pour voir tous les fichiers du pipeline
- ✅ Facilite les backups (copier `pipeline_active/`)
- ✅ Facilite la gestion de versions
- ✅ Évite la duplication de code

---

## 📋 FICHIERS UTILISÉS PAR LE PIPELINE

### Script Principal
- `scripts/run_pipeline_complete.py` : Pipeline complet en 8 étapes

### Modules Core
- `src/core/event_loader.py` : Chargement événements
- `src/core/formulas_validated.py` : Formules validées (Formule D, etc.)
- `src/core/trend_detection_pre_event_s107.py` : Détection tendances
- `src/core/price_loader_finnhub.py` : Mesure impact réel
- `src/core/random_forest_amplification.py` : Random Forest pour amplification
- `src/core/r2_amplification_correlation.py` : Modèle linéaire R²
- `src/core/finnhub_patterns.py` : Patterns Finnhub
- `src/core/double_wave.py` : Détection Double Wave
- `src/core/single_wave_strong.py` : Détection Single Wave

### Modules Session
- `scripts/session120/double_wave_detector_rev12.py` : Détecteur pattern réel

---

## 🔄 UTILISATION

### Créer les liens symboliques
```bash
cd pipeline_active
ln -s ../scripts/run_pipeline_complete.py scripts/
ln -s ../src/core/*.py core/
ln -s ../scripts/session120/double_wave_detector_rev12.py session120/
```

### Backup complet
```bash
cp -r pipeline_active pipeline_backup/YYYYMMDD_HHMMSS
```

### Restaurer depuis backup
```bash
cp pipeline_backup/YYYYMMDD_HHMMSS/* pipeline_active/
```

---

_Date création : Organisation fichiers pipeline_  
_Status : ✅ Structure créée_




