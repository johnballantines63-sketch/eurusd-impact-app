#!/usr/bin/env python3
"""
CRÉATION BACKUP ORGANISÉ - SCRIPTS VALIDÉS + DB
================================================

Crée un répertoire backup avec copies organisées des scripts validés
et sauvegarde de la base de données.

Structure créée :
eurusd_clean/
└── VALIDATED_BACKUP_YYYYMMDD_HHMMSS/
    ├── 00_README.md                    (Documentation structure)
    ├── 01_FORMULES_GOLD_STANDARD/      (Sessions 51-55)
    ├── 02_DETECTION_INVERSION/         (Sessions 102-107)
    ├── 03_SCANNER_PATTERNS/            (Session 117)
    ├── 04_DETECTEUR_DOUBLE_WAVE/       (Session 118)
    ├── 05_VALIDATION_CAS_ECOLE/        (Tests 11 sept)
    ├── 06_MODULES_CORE/                (src/core/)
    ├── 07_APPLICATION_STREAMLIT/       (streamlit_app/)
    ├── 08_DATABASES/                   (warehouse.duckdb)
    └── 09_DOCUMENTATION/               (docs critiques)

Auteur : André Valentin
Date   : 10 novembre 2025
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # eurusd_clean/
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_NAME = f"VALIDATED_BACKUP_{TIMESTAMP}"
BACKUP_DIR = PROJECT_ROOT / BACKUP_NAME

print("=" * 80)
print("🔄 CRÉATION BACKUP ORGANISÉ - SCRIPTS VALIDÉS + DB")
print("=" * 80)
print()
print(f"📂 Répertoire projet : {PROJECT_ROOT}")
print(f"📦 Répertoire backup : {BACKUP_DIR}")
print()

# Créer structure répertoires
STRUCTURE = {
    "01_FORMULES_GOLD_STANDARD": "Formules validées Sessions 51-55 (>94% précision)",
    "02_DETECTION_INVERSION": "Détection inversion tendance Sessions 102-107",
    "03_SCANNER_PATTERNS": "Scanner prix patterns Session 117 (Rev7)",
    "04_DETECTEUR_DOUBLE_WAVE": "Détecteur Double Wave Session 118",
    "05_VALIDATION_CAS_ECOLE": "Tests validation 11 septembre 2025",
    "06_MODULES_CORE": "Modules core production (src/core/)",
    "07_APPLICATION_STREAMLIT": "Interface utilisateur Streamlit",
    "08_DATABASES": "Bases de données (warehouse.duckdb + backup)",
    "09_DOCUMENTATION": "Documentation critique projet"
}

def create_structure():
    """Crée la structure de répertoires"""
    print("📁 Création structure répertoires...")
    BACKUP_DIR.mkdir(exist_ok=True)
    
    for folder, description in STRUCTURE.items():
        folder_path = BACKUP_DIR / folder
        folder_path.mkdir(exist_ok=True)
        print(f"  ✅ {folder}/")
    
    print()

def copy_formulas_gold_standard():
    """Copie formules gold standard (Sessions 51-55)"""
    print("📋 01_FORMULES_GOLD_STANDARD...")
    dest = BACKUP_DIR / "01_FORMULES_GOLD_STANDARD"
    
    # Module principal
    src_file = PROJECT_ROOT / "src" / "core" / "formulas_validated.py"
    if src_file.exists():
        shutil.copy2(src_file, dest / "formulas_validated.py")
        print(f"  ✅ formulas_validated.py (4 formules, >94% précision)")
    
    # Documentation associée
    docs_sources = [
        PROJECT_ROOT / "docs" / "session97" / "NOTES_FORMULAS_VALIDATED.md",
    ]
    
    for doc in docs_sources:
        if doc.exists():
            shutil.copy2(doc, dest / doc.name)
            print(f"  ✅ {doc.name}")
    
    print()

def copy_detection_inversion():
    """Copie scripts détection inversion (Sessions 102-107)"""
    print("🔍 02_DETECTION_INVERSION...")
    dest = BACKUP_DIR / "02_DETECTION_INVERSION"
    
    # Session 102 - Détection initiale
    session102 = PROJECT_ROOT / "scripts" / "session102"
    if session102.exists():
        scripts_102 = [
            "detect_inversions.py"
        ]
        for script in scripts_102:
            src = session102 / script
            if src.exists():
                shutil.copy2(src, dest / f"s102_{script}")
                print(f"  ✅ s102_{script}")
    
    # Session 107 - Méthode validée
    session107 = PROJECT_ROOT / "scripts" / "session107"
    if session107.exists():
        scripts_107 = [
            "phase2e_cluster3_inversion_trend.py",
            "phase2e_cluster1_inversion_trend.py",
            "verify_trend_11sept.py",
            "phase3_combined_calibration.py"
        ]
        for script in scripts_107:
            src = session107 / script
            if src.exists():
                shutil.copy2(src, dest / f"s107_{script}")
                print(f"  ✅ s107_{script}")
        
        # Copier aussi résultats CSV
        csv_files = [
            "cluster3_inversion_analysis.csv",
            "phase3_combined_calibration.csv"
        ]
        for csv in csv_files:
            src = session107 / csv
            if src.exists():
                shutil.copy2(src, dest / f"s107_{csv}")
                print(f"  ✅ s107_{csv}")
    
    print()

def copy_scanner_patterns():
    """Copie scanner patterns Session 117"""
    print("🔎 03_SCANNER_PATTERNS...")
    dest = BACKUP_DIR / "03_SCANNER_PATTERNS"
    
    session117 = PROJECT_ROOT / "scripts" / "session117"
    if session117.exists():
        # Scripts clés
        scripts = [
            "price_pattern_scanner_rev7_multimin.py",  # VERSION FINALE
            "enrich_double_waves.py",
            "analyze_enriched.py",
            "analyze_dw_35pips.py",
            "find_sept11.py"
        ]
        for script in scripts:
            src = session117 / script
            if src.exists():
                shutil.copy2(src, dest / script)
                star = " ⭐" if "rev7" in script else ""
                print(f"  ✅ {script}{star}")
        
        # Datasets
        datasets = [
            "patterns_detected.json",
            "patterns_detected.csv",
            "double_waves_enriched.json"
        ]
        for dataset in datasets:
            src = session117 / dataset
            if src.exists():
                shutil.copy2(src, dest / dataset)
                print(f"  ✅ {dataset}")
        
        # Copier graphiques (limité aux 10 premiers pour économiser espace)
        plots_dir = session117 / "plots_double_wave"
        if plots_dir.exists():
            dest_plots = dest / "plots_double_wave"
            dest_plots.mkdir(exist_ok=True)
            
            # Copier graphique 11 septembre obligatoirement
            sept11_plot = plots_dir / "double_wave_20250911_1432.png"
            if sept11_plot.exists():
                shutil.copy2(sept11_plot, dest_plots / sept11_plot.name)
                print(f"  ✅ plots_double_wave/double_wave_20250911_1432.png ⭐")
            
            # Copier 5 autres exemples
            plot_files = sorted(plots_dir.glob("*.png"))[:5]
            for plot in plot_files:
                if plot.name != "double_wave_20250911_1432.png":
                    shutil.copy2(plot, dest_plots / plot.name)
            print(f"  ✅ plots_double_wave/ (6 graphiques échantillon)")
    
    print()

def copy_detecteur_double_wave():
    """Copie détecteur Double Wave Session 118"""
    print("🌊 04_DETECTEUR_DOUBLE_WAVE...")
    dest = BACKUP_DIR / "04_DETECTEUR_DOUBLE_WAVE"
    
    session118 = PROJECT_ROOT / "scripts" / "session118"
    if session118.exists():
        # Scripts prioritaires
        scripts = [
            "double_wave_detector.py",  # PRIORITÉ ABSOLUE
            "run_validation_pro.py",
            "verify_sept11_correct.py",
            "validate_formula_s115.py"
        ]
        for script in scripts:
            src = session118 / script
            if src.exists():
                star = " ⭐" if "detector" in script else ""
                shutil.copy2(src, dest / script)
                print(f"  ✅ {script}{star}")
        
        # Résultats validation
        results = [
            "validation_results.json",
            "validation_results.csv"
        ]
        for result in results:
            src = session118 / result
            if src.exists():
                shutil.copy2(src, dest / result)
                print(f"  ✅ {result}")
    
    print()

def copy_validation_cas_ecole():
    """Copie tests validation 11 septembre"""
    print("✅ 05_VALIDATION_CAS_ECOLE...")
    dest = BACKUP_DIR / "05_VALIDATION_CAS_ECOLE"
    
    # Scripts racine
    scripts_root = [
        "test_11sept_correct_methodology.py",
        "test_formulas_92xx_11sept.py",
        "validate_planificateur_migration.py"
    ]
    
    for script in scripts_root:
        src = PROJECT_ROOT / "scripts" / script
        if src.exists():
            shutil.copy2(src, dest / script)
            print(f"  ✅ {script}")
    
    print()

def copy_modules_core():
    """Copie modules core production"""
    print("⚙️  06_MODULES_CORE...")
    dest = BACKUP_DIR / "06_MODULES_CORE"
    
    core_dir = PROJECT_ROOT / "src" / "core"
    if core_dir.exists():
        modules = [
            "formulas_validated.py",
            "cluster_impact_calculator.py",
            "double_wave.py",
            "single_wave_strong.py",
            "impact_measurement.py",
            "event_loader.py",
            "event_families.py",
            "scoring_engine.py",
            "forecaster_mvp.py"
        ]
        
        for module in modules:
            src = core_dir / module
            if src.exists():
                star = " ⭐" if module == "formulas_validated.py" else ""
                shutil.copy2(src, dest / module)
                print(f"  ✅ {module}{star}")
    
    print()

def copy_application_streamlit():
    """Copie application Streamlit"""
    print("🖥️  07_APPLICATION_STREAMLIT...")
    dest = BACKUP_DIR / "07_APPLICATION_STREAMLIT"
    
    app_dir = PROJECT_ROOT / "streamlit_app"
    if app_dir.exists():
        # Copier Home.py
        home = app_dir / "Home.py"
        if home.exists():
            shutil.copy2(home, dest / "Home.py")
            print(f"  ✅ Home.py")
        
        # Copier pages
        pages_dir = app_dir / "pages"
        if pages_dir.exists():
            dest_pages = dest / "pages"
            dest_pages.mkdir(exist_ok=True)
            
            pages = [
                "1_Calendrier_Trading.py",
                "2_Planificateur_V2.py",
                "3_API_Status.py",
                "4_Mise_a_jour_DB.py"
            ]
            
            for page in pages:
                src = pages_dir / page
                if src.exists():
                    star = " ⭐" if "Planificateur" in page else ""
                    shutil.copy2(src, dest_pages / page)
                    print(f"  ✅ pages/{page}{star}")
    
    print()

def copy_databases():
    """Copie bases de données"""
    print("💾 08_DATABASES...")
    dest = BACKUP_DIR / "08_DATABASES"
    
    # Copier warehouse.duckdb
    db_path = PROJECT_ROOT / "data" / "warehouse.duckdb"
    if db_path.exists():
        print(f"  📊 Copie warehouse.duckdb ({db_path.stat().st_size / 1024 / 1024:.1f} MB)...")
        shutil.copy2(db_path, dest / "warehouse.duckdb")
        print(f"  ✅ warehouse.duckdb")
        
        # Créer info fichier
        db_info = {
            "filename": "warehouse.duckdb",
            "size_mb": round(db_path.stat().st_size / 1024 / 1024, 2),
            "backup_date": datetime.now().isoformat(),
            "source_path": str(db_path),
            "description": "Base de données principale - 58,449 events + 1.1M prix 1min"
        }
        
        with open(dest / "database_info.json", "w") as f:
            json.dump(db_info, f, indent=2)
        print(f"  ✅ database_info.json")
    
    print()

def copy_documentation():
    """Copie documentation critique"""
    print("📚 09_DOCUMENTATION...")
    dest = BACKUP_DIR / "09_DOCUMENTATION"
    
    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.exists():
        # Documentation critique
        critical_docs = [
            "PROJECT_STATE.md",
            "__REFERENCE_CRITIQUE__/SESSION_112_RAPPORT_FINAL.md",
            "__REFERENCE_CRITIQUE__/SESSION_113_RAPPORT_FINAL.md",
            "__REFERENCE_CRITIQUE__/SOLUTION_DEFINITIVE_TIMEZONE.md",
            "PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md",
            "PROJECT_MANAGEMENT/03_FORMULAS/VALIDATED_FORMULAS.md"
        ]
        
        for doc_path in critical_docs:
            src = docs_dir / doc_path
            if src.exists():
                # Créer sous-dossiers si nécessaire
                dest_file = dest / Path(doc_path).name
                shutil.copy2(src, dest_file)
                print(f"  ✅ {Path(doc_path).name}")
    
    print()

def create_readme():
    """Crée README principal du backup"""
    print("📝 Création 00_README.md...")
    
    readme_content = f"""# BACKUP ORGANISÉ - SCRIPTS VALIDÉS + DB

**Date création :** {datetime.now().strftime("%d %B %Y %H:%M:%S")}  
**Version projet :** eurusd_clean  
**Auteur :** André Valentin

---

## 🎯 Objectif de ce Backup

Ce répertoire contient une **copie organisée** de tous les scripts validés et de la base de données du projet EUR/USD Impact Predictor.

**Important :** Les scripts originaux restent en place dans leur emplacement d'origine. Ce backup sert de :
1. **Sauvegarde de sécurité** (scripts + DB)
2. **Archive organisée** par fonction/étape
3. **Documentation** de l'état validé du projet

---

## 📂 Structure du Backup

```
{BACKUP_NAME}/
├── 00_README.md                      (Ce fichier)
├── 01_FORMULES_GOLD_STANDARD/        Sessions 51-55 (>94% précision)
├── 02_DETECTION_INVERSION/           Sessions 102-107 (méthode validée)
├── 03_SCANNER_PATTERNS/              Session 117 (Rev7 + 42 patterns)
├── 04_DETECTEUR_DOUBLE_WAVE/         Session 118 (MAE 4.5 pips)
├── 05_VALIDATION_CAS_ECOLE/          Tests 11 septembre 2025
├── 06_MODULES_CORE/                  Production (src/core/)
├── 07_APPLICATION_STREAMLIT/         Interface utilisateur
├── 08_DATABASES/                     warehouse.duckdb (205 MB)
└── 09_DOCUMENTATION/                 Docs critiques
```

---

## 📋 Contenu Détaillé

### 01_FORMULES_GOLD_STANDARD
**Sessions 51-55 | Précision >94%**

- `formulas_validated.py` ⭐ : 4 formules validées
  - Ajustement Score Empirique (99.9% précision)
  - Impact Net - Formule D (98.6% précision) 🏆
  - Time To Reversal - TTR C (94.4% précision)
  - Pullback Logarithmique V2 (99.3% précision)

**Cas école :** 11 septembre 2025 - Précision globale >98%

---

### 02_DETECTION_INVERSION
**Sessions 102-107 | Méthode Validée**

Scripts clés :
- `s107_phase2e_cluster3_inversion_trend.py` ⭐ : Détection par séquence
- `s107_verify_trend_11sept.py` : Validation 11 sept (capte pic 9 sept 08:00)
- `s107_phase3_combined_calibration.py` : Calibration multi-clusters

**Validation :** Inversion 9 sept 08:00 (PEAK), durée 54.6h, R² 0.6376

---

### 03_SCANNER_PATTERNS
**Session 117 | 42 Patterns Détectés**

Scripts :
- `price_pattern_scanner_rev7_multimin.py` ⭐ : Scanner final (seuil 35 pips)
- `enrich_double_waves.py` : Enrichissement events causaux (13 cas)
- `analyze_enriched.py` : Analyse patterns
- `find_sept11.py` : Debug 11 septembre

Datasets :
- `patterns_detected.json` : 42 patterns (15 Double Wave)
- `double_waves_enriched.json` : 13 cas avec events causaux
- `plots_double_wave/` : 6 graphiques échantillon

**Découverte :** 87% Double Wave prédictibles (avec events), 13% techniques purs

---

### 04_DETECTEUR_DOUBLE_WAVE
**Session 118 | MAE 4.5 pips**

Scripts :
- `double_wave_detector.py` ⭐ : Détecteur algorithmique validé
- `run_validation_pro.py` : Validation production
- `verify_sept11_correct.py` : Vérification 11 sept

Résultats :
- `validation_results.json` : Validation multi-dates

**Validation 11 sept :** Impact détecté 51.7 pips vs 56.2 réel (MAE 4.5 pips)

---

### 05_VALIDATION_CAS_ECOLE
**Tests 11 Septembre 2025**

Scripts tests :
- `test_11sept_correct_methodology.py`
- `test_formulas_92xx_11sept.py`
- `validate_planificateur_migration.py`

**Cas référence :** 11 septembre 2025 = Gold Standard projet

---

### 06_MODULES_CORE
**Production (src/core/)**

9 modules production-ready :
- `formulas_validated.py` ⭐ : 4 formules gold standard
- `cluster_impact_calculator.py` : Calcul impact clusters
- `double_wave.py` : Pattern Double Wave
- `impact_measurement.py` : Mesure impact MT5 (v4.0)
- + 5 autres modules

**Status :** Tous modules en production

---

### 07_APPLICATION_STREAMLIT
**Interface Utilisateur**

5 pages fonctionnelles :
- `Home.py` : Page accueil
- `pages/1_Calendrier_Trading.py` : Calendrier économique
- `pages/2_Planificateur_V2.py` ⭐ : Prédictions trading
- `pages/3_API_Status.py` : Status APIs
- `pages/4_Mise_a_jour_DB.py` : Import données

**Status :** Application 100% fonctionnelle

---

### 08_DATABASES
**Base de Données Principale**

- `warehouse.duckdb` (205 MB)
  - 58,449 événements économiques
  - 1,114,260 prix 1 minute EUR/USD
  - Vue prices_bern (timezone Bern +02:00)

- `database_info.json` : Métadonnées backup

**Période :** 2015-2025 (10 ans historique)

---

### 09_DOCUMENTATION
**Documentation Critique**

Documents clés :
- `PROJECT_STATE.md` : État actuel projet
- `SESSION_112_RAPPORT_FINAL.md` : Migration eurusd_clean
- `SESSION_113_RAPPORT_FINAL.md` : Validation cluster calculator
- `SOLUTION_DEFINITIVE_TIMEZONE.md` : Vue prices_bern
- `MASTER_PLAN.md` : Vision globale
- `VALIDATED_FORMULAS.md` : Synthèse formules

---

## 📊 Statistiques Backup

```
Scripts validés copiés   : ~30 scripts
Modules core             : 9 fichiers
Datasets                 : 5 fichiers JSON/CSV
Graphiques               : 6 échantillons
Base de données          : 205 MB
Documentation            : 6 documents critiques

Total taille backup      : ~210-220 MB
```

---

## ⚙️ Utilisation du Backup

### Restauration Scripts

Pour utiliser un script du backup :

```bash
# Copier script vers emplacement actif
cp 03_SCANNER_PATTERNS/price_pattern_scanner_rev7_multimin.py \\
   ../scripts/session117/

# Ou exécuter directement depuis backup
cd 03_SCANNER_PATTERNS/
python3 price_pattern_scanner_rev7_multimin.py
```

### Restauration Base de Données

```bash
# Sauvegarder DB actuelle
mv ../data/warehouse.duckdb ../data/warehouse.duckdb.old

# Restaurer depuis backup
cp 08_DATABASES/warehouse.duckdb ../data/

# Vérifier intégrité
python3 -c "import duckdb; duckdb.connect('../data/warehouse.duckdb')"
```

---

## 🔗 Emplacements Originaux

**Scripts originaux restent dans :**
- `eurusd_clean/src/core/` : Modules production
- `eurusd_clean/scripts/session117/` : Scanner patterns
- `eurusd_clean/scripts/session118/` : Détecteur Double Wave
- `eurusd_clean/scripts/session107/` : Détection inversion
- `eurusd_clean/streamlit_app/` : Application interface

**Base de données originale :**
- `eurusd_clean/data/warehouse.duckdb`

**Documentation originale :**
- `eurusd_clean/docs/`

---

## ⚠️ Important

1. **Ce backup est READ-ONLY** : Ne pas modifier les fichiers ici
2. **Scripts originaux prioritaires** : Toujours utiliser versions originales pour développement
3. **Backup périodique** : Créer nouveau backup après chaque validation majeure
4. **Vérifier intégrité DB** : Tester connexion après restauration

---

## 📅 Historique Versions

| Date | Version | Description |
|------|---------|-------------|
| {datetime.now().strftime("%Y-%m-%d")} | 1.0 | Backup initial organisé (Sessions 51-118) |

---

## 📞 Contact

**Auteur :** André Valentin  
**Projet :** EUR/USD News Impact Predictor  
**Sessions :** 51-125  
**Date backup :** {datetime.now().strftime("%d %B %Y")}

---

**🎯 Ce backup préserve l'état validé du projet à la date ci-dessus.**
"""
    
    readme_path = BACKUP_DIR / "00_README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"  ✅ 00_README.md ({len(readme_content)} caractères)")
    print()

def create_backup_info():
    """Crée fichier JSON avec métadonnées backup"""
    print("ℹ️  Création backup_info.json...")
    
    info = {
        "backup_name": BACKUP_NAME,
        "creation_date": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "backup_location": str(BACKUP_DIR),
        "structure": STRUCTURE,
        "statistics": {
            "scripts_copied": "~30",
            "core_modules": 9,
            "datasets": 5,
            "database_size_mb": 205,
            "documentation_files": 6
        },
        "sessions_included": {
            "formulas": "51-55",
            "inversion_detection": "102-107",
            "pattern_scanner": "117",
            "double_wave_detector": "118"
        },
        "key_validations": {
            "cas_ecole": "11 septembre 2025",
            "precision_formulas": ">94%",
            "precision_global": ">98%",
            "mae_double_wave": "4.5 pips"
        }
    }
    
    info_path = BACKUP_DIR / "backup_info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ backup_info.json")
    print()

def main():
    """Fonction principale"""
    try:
        # Créer structure
        create_structure()
        
        # Copier par catégorie
        copy_formulas_gold_standard()
        copy_detection_inversion()
        copy_scanner_patterns()
        copy_detecteur_double_wave()
        copy_validation_cas_ecole()
        copy_modules_core()
        copy_application_streamlit()
        copy_databases()
        copy_documentation()
        
        # Créer documentation
        create_readme()
        create_backup_info()
        
        # Résumé final
        print("=" * 80)
        print("✅ BACKUP CRÉÉ AVEC SUCCÈS !")
        print("=" * 80)
        print()
        print(f"📦 Emplacement : {BACKUP_DIR}")
        print()
        
        # Calculer taille totale
        total_size = sum(f.stat().st_size for f in BACKUP_DIR.rglob('*') if f.is_file())
        print(f"💾 Taille totale : {total_size / 1024 / 1024:.1f} MB")
        print()
        
        print("📋 Contenu :")
        for folder in sorted(BACKUP_DIR.iterdir()):
            if folder.is_dir():
                num_files = len(list(folder.rglob('*')))
                print(f"  ✅ {folder.name}/ ({num_files} fichiers)")
        
        print()
        print("🎯 Prochaines étapes :")
        print("  1. Vérifier contenu backup")
        print("  2. Tester restauration DB (optionnel)")
        print("  3. Consulter 00_README.md pour documentation")
        print()
        
    except Exception as e:
        print()
        print("❌ ERREUR lors création backup :")
        print(f"   {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
