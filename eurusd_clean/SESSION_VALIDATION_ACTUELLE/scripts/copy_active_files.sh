#!/bin/bash
# Script pour copier tous les fichiers actifs dans SESSION_VALIDATION_ACTUELLE

PROJECT_ROOT="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean"
SESSION_DIR="$PROJECT_ROOT/SESSION_VALIDATION_ACTUELLE"

echo "================================================================================"
echo "COPIE DES FICHIERS ACTIFS"
echo "================================================================================"
echo

# Créer les répertoires
mkdir -p "$SESSION_DIR/scripts"
mkdir -p "$SESSION_DIR/docs"
mkdir -p "$SESSION_DIR/streamlit_app"
mkdir -p "$SESSION_DIR/outputs"
mkdir -p "$SESSION_DIR/src_core"
mkdir -p "$SESSION_DIR/references"

# Scripts principaux
echo "📝 Copie des scripts..."
cp "$PROJECT_ROOT/scripts/run_pipeline_complete.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/validate_pipeline_multi_dates.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_restauration_cas_base.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_pipeline_cas_base_validation.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_2025_08_01_detailed.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_2025_05_29_detailed.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/investigate_de_events_2025_09_11.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_timing_2025_09_11_simple.py" "$SESSION_DIR/scripts/" 2>/dev/null
cp "$PROJECT_ROOT/scripts/test_validation_multi_dates.py" "$SESSION_DIR/scripts/" 2>/dev/null

# Documentation
echo "📚 Copie de la documentation..."
cp -r "$PROJECT_ROOT/docs/VALIDATION_SESSION_2025_01_XX" "$SESSION_DIR/docs/" 2>/dev/null
cp -r "$PROJECT_ROOT/docs/PIPELINE_REFERENCE" "$SESSION_DIR/docs/" 2>/dev/null
cp "$PROJECT_ROOT/docs/METHODOLOGIE_TRAVAIL.md" "$SESSION_DIR/docs/" 2>/dev/null
cp "$PROJECT_ROOT/docs/INDEX_DOCUMENTATION_CENTRAL.md" "$SESSION_DIR/docs/" 2>/dev/null

# Streamlit App
echo "🎨 Copie de l'application Streamlit..."
cp "$PROJECT_ROOT/streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py" "$SESSION_DIR/streamlit_app/" 2>/dev/null
cp "$PROJECT_ROOT/streamlit_app/Home.py" "$SESSION_DIR/streamlit_app/" 2>/dev/null

# Outputs
echo "📊 Copie des outputs..."
cp "$PROJECT_ROOT/outputs/validation_finale_pipeline.csv" "$SESSION_DIR/outputs/" 2>/dev/null
cp "$PROJECT_ROOT/outputs/validation_pipeline_multi_dates.csv" "$SESSION_DIR/outputs/" 2>/dev/null
cp "$PROJECT_ROOT/outputs/timing_precision_comparison.csv" "$SESSION_DIR/outputs/" 2>/dev/null

# Modules Core
echo "🔧 Copie des modules core..."
cp "$PROJECT_ROOT/src/core/formulas_validated.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/random_forest_amplification.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/price_loader_finnhub.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/trend_detection_pre_event_s107.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/event_loader.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/r2_amplification_correlation.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/double_wave.py" "$SESSION_DIR/src_core/" 2>/dev/null
cp "$PROJECT_ROOT/src/core/single_wave_strong.py" "$SESSION_DIR/src_core/" 2>/dev/null

# Références
echo "📖 Copie des références..."
cp -r "$PROJECT_ROOT/pipeline_backup/20251203_114640" "$SESSION_DIR/references/" 2>/dev/null

echo
echo "✅ Copie terminée !"
echo "📁 Fichiers copiés dans : $SESSION_DIR"




