#!/bin/bash
# Script pour ajouter le code d'initialisation à toutes les pages

set -e

echo "🔧 Correction des imports dans les pages Streamlit..."

# Code à ajouter au début de chaque page
INIT_CODE='import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Télécharger la base de données si nécessaire (une seule fois)
try:
    from download_database import download_database
    download_database()
except Exception as e:
    pass  # Déjà téléchargée ou erreur gérée ailleurs

'

# Liste des pages à corriger
PAGES=(
    "fx_impact_app/streamlit_app/pages/0b_Impact-Planner.py"
    "fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py"
    "fx_impact_app/streamlit_app/pages/2_Backtest-Strategie.py"
    "fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py"
    "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
)

for page in "${PAGES[@]}"; do
    if [ -f "$page" ]; then
        # Vérifier si le code d'init est déjà présent
        if grep -q "download_database" "$page"; then
            echo "✅ $page déjà corrigé"
        else
            echo "🔧 Correction de $page..."
            # Créer une backup
            cp "$page" "${page}.backup_$(date +%Y%m%d_%H%M%S)"
            
            # Créer un fichier temporaire avec le nouveau contenu
            echo "$INIT_CODE" > /tmp/temp_page.py
            cat "$page" >> /tmp/temp_page.py
            mv /tmp/temp_page.py "$page"
            
            echo "✅ $page corrigé"
        fi
    else
        echo "⚠️  $page introuvable"
    fi
done

echo ""
echo "✅ Toutes les pages ont été corrigées !"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo "1. git add fx_impact_app/streamlit_app/pages/*.py"
echo "2. git commit -m 'Fix: Add path initialization to all pages'"
echo "3. git push origin main"
echo ""
echo "Streamlit Cloud va automatiquement redéployer l'app."
