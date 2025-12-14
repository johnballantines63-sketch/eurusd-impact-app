#!/usr/bin/env python3
"""
Ajoute 2 améliorations du Planificateur au Calendrier :
1. Mode Date précise / Période
2. Pré-chargement DB au démarrage (cache)
"""

from pathlib import Path
from datetime import datetime

def add_improvements():
    file_path = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé : {file_path}")
        return False
    
    # Backup
    backup_path = file_path.parent / "backups" / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
    backup_path.parent.mkdir(exist_ok=True)
    
    lines = file_path.read_text(encoding='utf-8').split('\n')
    backup_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Backup créé : {backup_path}")
    
    corrections = []
    
    # ═══════════════════════════════════════════════════════════
    # AMÉLIORATION 1 : Ajouter pré-chargement DB (après imports)
    # ═══════════════════════════════════════════════════════════
    
    print("\n🔧 Amélioration 1 : Ajouter pré-chargement DB...")
    
    # Trouver où insérer (après @st.cache_resource)
    insert_cache_at = None
    for i, line in enumerate(lines):
        if '@st.cache_resource' in line and 'init_engines' in lines[i+1]:
            insert_cache_at = i + 4  # Après la fonction init_engines
            break
    
    if insert_cache_at:
        cache_code = [
            '',
            '# ═══════════════════════════════════════════════════════════',
            '# PRÉ-CHARGEMENT DB (comme Planificateur) - Réponse instantanée',
            '# ═══════════════════════════════════════════════════════════',
            '',
            '@st.cache_data(ttl=3600)',
            'def load_precomputed_stats_from_db():',
            '    """Charge stats pré-calculées depuis DB (CACHE pour vitesse)"""',
            '    try:',
            '        conn = duckdb.connect(get_db_path())',
            '        schema = conn.execute("DESCRIBE event_families").fetchall()',
            '        cols = [col[0] for col in schema]',
            '        ',
            '        if \'latency_median\' not in cols:',
            '            conn.close()',
            '            return {}',
            '        ',
            '        query = """',
            '            SELECT DISTINCT family, latency_median, latency_p20, latency_p80,',
            '                   ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency',
            '            FROM event_families WHERE latency_median IS NOT NULL',
            '        """',
            '        results = conn.execute(query).fetchall()',
            '        conn.close()',
            '        ',
            '        stats_dict = {}',
            '        for row in results:',
            '            stats_dict[row[0]] = {',
            '                \'latency_median\': row[1], \'latency_p20\': row[2], \'latency_p80\': row[3],',
            '                \'ttr_median\': row[4], \'ttr_p20\': row[5], \'ttr_p80\': row[6],',
            '                \'mfe_p80\': row[7] if row[7] else 10.0, \'n_events\': row[8]',
            '            }',
            '        return stats_dict',
            '    except:',
            '        return {}',
            '',
            '# Pré-charger au démarrage (UNE SEULE FOIS)',
            'if \'preloaded\' not in st.session_state:',
            '    with st.spinner("⚡ Chargement stats DB..."):',
            '        precomputed_stats = load_precomputed_stats_from_db()',
            '        if precomputed_stats:',
            '            st.session_state.precomputed_stats = precomputed_stats',
            '            st.session_state.preloaded = True',
            '            st.success(f"✅ {len(precomputed_stats)} familles en cache - Réponse instantanée !", icon="⚡")',
            '        else:',
            '            st.session_state.precomputed_stats = {}',
            '            st.session_state.preloaded = True',
            ''
        ]
        
        # Insérer le code
        for j, code_line in enumerate(cache_code):
            lines.insert(insert_cache_at + j, code_line)
        
        corrections.append(f"✅ Pré-chargement DB ajouté (ligne {insert_cache_at})")
        print(f"   ✅ Code inséré ligne {insert_cache_at}")
    
    # ═══════════════════════════════════════════════════════════
    # AMÉLIORATION 2 : Ajouter mode Date précise / Période
    # ═══════════════════════════════════════════════════════════
    
    print("\n🔧 Amélioration 2 : Ajouter mode Date précise / Période...")
    
    # Trouver la section Période dans sidebar
    insert_date_mode_at = None
    for i, line in enumerate(lines):
        if 'st.sidebar.subheader("📅 Période' in line:
            insert_date_mode_at = i + 1
            break
    
    if insert_date_mode_at:
        date_mode_code = [
            '',
            'mode_date = st.sidebar.radio(',
            '    "Mode de sélection",',
            '    ["Date précise", "Période"],',
            '    index=0,',
            '    key=\'date_mode\'',
            ')',
            '',
            'if mode_date == "Date précise":',
            '    selected_date = st.sidebar.date_input(',
            '        "Date",',
            '        datetime.now().date() + timedelta(days=1),',
            '        key=\'single_date\'',
            '    )',
            '    date_from = datetime.combine(selected_date, datetime.min.time())',
            '    date_to = datetime.combine(selected_date, datetime.max.time())',
            'else:',
            '    # Mode Période (code existant ci-dessous)'
        ]
        
        # Insérer le code
        for j, code_line in enumerate(date_mode_code):
            lines.insert(insert_date_mode_at + j, code_line)
        
        # Indenter le code existant de période
        # Trouver les lignes à indenter (lookforward_days, date_from, date_to)
        for k in range(insert_date_mode_at + len(date_mode_code), insert_date_mode_at + len(date_mode_code) + 20):
            if k < len(lines):
                if 'lookforward_days' in lines[k] or 'date_from =' in lines[k] or 'date_to =' in lines[k]:
                    # Ajouter 4 espaces d'indentation
                    if not lines[k].startswith('    '):
                        lines[k] = '    ' + lines[k]
        
        corrections.append(f"✅ Mode Date précise ajouté (ligne {insert_date_mode_at})")
        print(f"   ✅ Radio button inséré ligne {insert_date_mode_at}")
    
    # ═══════════════════════════════════════════════════════════
    # ÉCRITURE
    # ═══════════════════════════════════════════════════════════
    
    if corrections:
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        
        print("\n" + "="*70)
        print("✅ AMÉLIORATIONS AJOUTÉES")
        print("="*70)
        
        for correction in corrections:
            print(f"   {correction}")
        
        print(f"\n📄 Fichier : {file_path}")
        print(f"💾 Backup : {backup_path}")
        
        print("\n" + "="*70)
        print("📊 AMÉLIORATIONS")
        print("="*70)
        
        print("\n1️⃣  Mode Date précise / Période :")
        print("   - Radio button dans sidebar")
        print("   - Date précise : Choisir UN jour spécifique")
        print("   - Période : Plage de dates (existant)")
        
        print("\n2️⃣  Pré-chargement DB :")
        print("   - Stats chargées UNE FOIS au démarrage")
        print("   - Réponses INSTANTANÉES (pas de requête à chaque fois)")
        print("   - Message : '✅ X familles en cache'")
        
        print("\n🎯 Résultat attendu :")
        print("   ⚡ Chargement initial : ~2-3 secondes")
        print("   ⚡ Analyses suivantes : INSTANTANÉES !")
        print("   📅 Choix date précise disponible")
        
        print("\n🚀 Relancez : streamlit run fx_impact_app/streamlit_app/Home.py")
        
        return True
    else:
        print("\n⚠️  Aucune amélioration ajoutée")
        return False

if __name__ == "__main__":
    print("🔧 AJOUT DES AMÉLIORATIONS DU PLANIFICATEUR")
    print("="*70)
    
    if not add_improvements():
        print("\n❌ Échec - Modifications manuelles nécessaires")
        
        print("\n📋 À ajouter manuellement :")
        
        print("\n1️⃣  Après init_engines() :")
        print("   - Copier la fonction load_precomputed_stats_from_db() du Planificateur")
        print("   - Ajouter le bloc if 'preloaded' not in st.session_state")
        
        print("\n2️⃣  Dans sidebar, après '📅 Période' :")
        print("   - Ajouter radio button mode_date")
        print("   - Ajouter if/else pour Date précise vs Période")
