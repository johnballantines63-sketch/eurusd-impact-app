#!/bin/bash
# Script de lancement CORRIGÉ - Session 68
# Lancement depuis le bon répertoire

echo "🎯 PLANIFICATEUR V2.4 - LANCEMENT CORRIGÉ"
echo "=========================================="
echo ""

# Se placer dans le bon répertoire (fx_impact_app)
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

echo "📁 Répertoire actuel : $(pwd)"
echo ""
echo "🔍 Vérification structure..."

if [ -d "src" ]; then
    echo "  ✅ src/ trouvé"
else
    echo "  ❌ src/ NOT FOUND"
    exit 1
fi

if [ -f "src/formulas_validated.py" ]; then
    echo "  ✅ formulas_validated.py trouvé"
else
    echo "  ❌ formulas_validated.py NOT FOUND"
    exit 1
fi

if [ -f "src/single_wave_strong.py" ]; then
    echo "  ✅ single_wave_strong.py trouvé"
else
    echo "  ❌ single_wave_strong.py NOT FOUND"
    exit 1
fi

if [ -f "src/double_wave.py" ]; then
    echo "  ✅ double_wave.py trouvé"
else
    echo "  ❌ double_wave.py NOT FOUND"
    exit 1
fi

echo ""
echo "🚀 Lancement Streamlit depuis fx_impact_app/..."
echo ""

# Lancer Streamlit avec le bon path
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
