#!/bin/bash
# Script de rollback - Restaure le backup automatiquement

echo "🔄 ROLLBACK - Restauration du fichier original"
echo "=============================================="

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

# Trouver le backup le plus récent
BACKUP=$(ls -t fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.backup_*.py 2>/dev/null | head -1)

if [ -z "$BACKUP" ]; then
    echo "❌ Aucun backup trouvé !"
    exit 1
fi

echo "📂 Backup trouvé : $(basename $BACKUP)"

# Restaurer
cp "$BACKUP" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py

echo "✅ Fichier restauré !"
echo ""
echo "🧪 Test syntaxe..."

# Tester la syntaxe
python3 -m py_compile fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe OK - Fichier restauré avec succès"
    echo ""
    echo "💡 Le backup est conservé : $(basename $BACKUP)"
else
    echo "⚠️ Problème de syntaxe persistant"
fi
