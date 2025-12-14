#!/bin/bash
set -e

echo "🔧 Script de mise à jour du Calendrier Trading"
echo "=============================================="

# Chemin du fichier
FILE="streamlit_app/pages/1_Calendrier-Trading.py"
BACKUP="streamlit_app/pages/1_Calendrier-Trading.py.backup.$(date +%Y%m%d_%H%M%S)"

# Vérifier que le fichier existe
if [ ! -f "$FILE" ]; then
    echo "❌ Fichier introuvable : $FILE"
    echo "💡 Lancez ce script depuis : eurusd_news_impact_calculator/fx_impact_app/"
    exit 1
fi

echo "✅ Fichier trouvé : $FILE"

# Créer backup
cp "$FILE" "$BACKUP"
echo "💾 Backup créé : $BACKUP"

# Créer le fichier Python de remplacement
cat > /tmp/new_main.py << 'PYTHON_CODE'
def main():
    st.title("📅 Calendrier Trading - Événements à Surveiller")
    st.caption("🚀 Version optimisée avec cache intelligent + Timeline + Alertes")
    
    # ========================================================================
    # SIDEBAR - Configuration (TOUT EN PREMIER)
    # ========================================================================
    
    st.sidebar.header("⚙️ Configuration")
    
    # 1. Toggle classification
    st.sidebar.subheader("📊 Classification")
    classification_mode = st.sidebar.radio(
        "Source d'importance",
        ["📅 Calendrier (a priori)", "📊 Empirique (historique)"],
        index=0,
        help=(
            "📅 **Calendrier** : Importance théorique selon économistes\n\n"
            "📊 **Empirique** : Impact réel observé sur EUR/USD (nécessite famille mappée)"
        )
    )
    
    st.sidebar.divider()
    
    # 2. Mode sélection date
    st.sidebar.subheader("📅 Période")
    mode_date = st.sidebar.radio(
        "Mode de sélection",
        ["Date unique", "Période"],
        index=0
    )
    
    # 3. Dates selon mode
    if mode_date == "Date unique":
        selected_date = st.sidebar.date_input(
            "Date",
            datetime.now().date()
        )
        date_from = datetime.combine(selected_date, datetime.min.time())
        date_to = datetime.combine(selected_date, datetime.max.time())
    else:
        period_preset = st.sidebar.selectbox(
            "Période rapide",
            ["Personnalisé", "Aujourd'hui", "7 derniers jours", "30 derniers jours", "Ce mois", "Mois dernier"],
            index=1
        )
        
        today = datetime.now().date()
        
        if period_preset == "Aujourd'hui":
            default_start = today
            default_end = today
        elif period_preset == "7 derniers jours":
            default_start = today - timedelta(days=7)
            default_end = today
        elif period_preset == "30 derniers jours":
            default_start = today - timedelta(days=30)
            default_end = today
        elif period_preset == "Ce mois":
            default_start = today.replace(day=1)
            default_end = today
        elif period_preset == "Mois dernier":
            first_of_month = today.replace(day=1)
            default_end = first_of_month - timedelta(days=1)
            default_start = default_end.replace(day=1)
        else:
            default_start = today - timedelta(days=7)
            default_end = today
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("De", default_start)
        with col2:
            end_date = st.date_input("À", default_end)
        
        date_from = datetime.combine(start_date, datetime.min.time())
        date_to = datetime.combine(end_date, datetime.max.time())
    
    st.sidebar.divider()
    
    # 4. Toggles fonctionnalités
    show_timeline = st.sidebar.checkbox("📈 Afficher Timeline", value=True)
    show_alerts = st.sidebar.checkbox("🔔 Activer Alertes", value=True)
    show_heatmap = st.sidebar.checkbox("🕐 Afficher Heatmap", value=False)
    
    # ========================================================================
    # CHARGEMENT DES DONNÉES
    # ========================================================================
    
    with st.spinner("⏳ Chargement événements..."):
        df_all = load_all_events_cached(
            start_date=date_from.strftime('%Y-%m-%d'),
            end_date=date_to.strftime('%Y-%m-%d')
        )
    
    if df_all.empty:
        st.warning("⚠️ Aucun événement trouvé pour cette période")
        return
    
    # ========================================================================
    # APPLICATION DE LA CLASSIFICATION CHOISIE
    # ========================================================================
    
    use_empirical = classification_mode == "📊 Empirique (historique)"
    
    if use_empirical:
        df_all['impact'] = df_all['impact_empirical']
        unknown_count = len(df_all[df_all['impact'] == 'Unknown'])
        if unknown_count > 0:
            st.warning(f"⚠️ {unknown_count} événements sans score empirique")
    else:
        df_all['impact'] = df_all['impact_calendar']
    
    # Message info
    if use_empirical:
        st.info("📊 **Classification Empirique** : Impact réel basé sur historique", icon="📊")
    else:
        st.info("📅 **Classification Calendrier** : Importance théorique (a priori)", icon="📅")
PYTHON_CODE

# Script Python pour faire le remplacement
cat > /tmp/replace_main.py << 'PYTHON_SCRIPT'
import sys

# Lire l'ancien fichier
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()

# Lire la nouvelle fonction
with open('/tmp/new_main.py', 'r', encoding='utf-8') as f:
    new_main = f.read()

# Trouver le début et la fin de main()
lines = content.split('\n')
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if line.strip() == 'def main():':
        start_idx = i
    elif start_idx is not None and line.strip().startswith('def ') and 'main' not in line:
        end_idx = i
        break
    elif start_idx is not None and line.strip() == 'if __name__ == "__main__":':
        end_idx = i
        break

if start_idx is None:
    print("❌ Fonction main() non trouvée", file=sys.stderr)
    sys.exit(1)

if end_idx is None:
    end_idx = len(lines)

# Reconstruire
before = '\n'.join(lines[:start_idx])
after = '\n'.join(lines[end_idx:])
new_content = before + '\n\n' + new_main + '\n\n' + after

# Écrire
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Fonction main() remplacée (lignes {start_idx+1} à {end_idx})")
PYTHON_SCRIPT

# Exécuter le remplacement
python3 /tmp/replace_main.py "$FILE"

echo ""
echo "📋 Résumé :"
echo "   - Backup : $(basename $BACKUP)"
echo "   - Fonction main() mise à jour"
echo "   - Toggle classification ajouté"
echo "   - Mode Date unique/Période ajouté"
echo ""
echo "🚀 Prochaines étapes :"
echo "   1. Testez : streamlit run streamlit_app/Home.py"
echo "   2. Vérifiez le toggle Classification dans la sidebar"
echo "   3. Si problème, restaurez : cp $BACKUP $FILE"
echo ""
echo "✅ Mise à jour terminée avec succès !"

# Cleanup
rm -f /tmp/new_main.py /tmp/replace_main.py
