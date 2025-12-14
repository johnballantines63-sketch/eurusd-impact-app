"""
Script pour appliquer automatiquement le patch d'optimisation
"""

import shutil

FILE_PATH = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_PATH = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements_BACKUP_v7.py"

def apply_patch():
    print("🚀 Application du patch v8.0\n")
    
    # 1. Backup
    print("1️⃣ Backup...")
    shutil.copy2(FILE_PATH, BACKUP_PATH)
    print(f"   ✅ {BACKUP_PATH}\n")
    
    # 2. Lire
    print("2️⃣ Lecture...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   ✅ {len(content)} caractères\n")
    
    # 3. Modifications
    print("3️⃣ Application patches...")
    
    # Trouver ligne avant def predict_impact
    import_section_end = content.find("def predict_impact(family")
    
    new_functions = """
@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db() -> dict:
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
        query = """
            SELECT DISTINCT family, latency_median, latency_p20, latency_p80,
                   ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
            FROM event_families WHERE latency_median IS NOT NULL
        """
        results = conn.execute(query).fetchall()
        conn.close()
        stats_dict = {}
        for row in results:
            stats_dict[row[0]] = {
                'latency_median': row[1], 'latency_p20': row[2], 'latency_p80': row[3],
                'ttr_median': row[4], 'ttr_p20': row[5], 'ttr_p80': row[6],
                'mfe_p80': row[7] if row[7] else 10.0, 'n_events': row[8]
            }
        return stats_dict
    except:
        return {}

def predict_impact_fast(family: str, surprise: float, precomputed_stats: dict, years_back: int = 3):
    if family in precomputed_stats:
        stats = precomputed_stats[family]
        mfe = stats['mfe_p80']
        impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
        impact = mfe * impact_factor
        return {
            'impact_median': round(impact, 1), 'impact_p20': round(impact * 0.6, 1),
            'impact_p80': round(impact * 1.3, 1), 'latency_median': round(stats['latency_median'], 1),
            'latency_p20': round(stats['latency_p20'], 1), 'latency_p80': round(stats['latency_p80'], 1),
            'ttr_median': round(stats['ttr_median'], 1), 'ttr_p20': round(stats['ttr_p20'], 1),
            'ttr_p80': round(stats['ttr_p80'], 1), 'retrace_median': round(impact * 0.5, 1),
            'retrace_p20': round(impact * 0.382, 1), 'retrace_p80': round(impact * 0.618, 1),
            'n_events': stats['n_events'], 'source': 'precomputed_db', 'surprise': round(surprise, 1)
        }
    else:
        result = predict_impact(family, surprise, years_back)
        if result:
            result['source'] = 'calculated_on_demand'
        return result

"""
    
    # Insérer nouvelles fonctions
    content = content[:import_section_end] + new_functions + content[import_section_end:]
    print("   ✅ Fonctions ajoutées")
    
    # Remplacer pré-chargement
    old_preload_start = content.find("if 'preloaded' not in st.session_state:")
    old_preload_end = content.find("st.session_state.preloaded = True", old_preload_start) + 37
    
    new_preload = """if 'preloaded' not in st.session_state:
    st.info("⚡ Chargement stats DB...")
    precomputed_stats = load_precomputed_stats_from_db()
    if precomputed_stats:
        st.session_state.precomputed_stats = precomputed_stats
        st.session_state.preloaded = True
        st.success(f"✅ {len(precomputed_stats)}/16 familles - Calculs ultra-rapides !", icon="⚡")
    else:
        st.warning("⚠️ Calculs classiques")
        st.session_state.precomputed_stats = {}
        st.session_state.preloaded = True"""
    
    content = content[:old_preload_start] + new_preload + content[old_preload_end:]
    print("   ✅ Pré-chargement modifié")
    
    # Modifier appel
    content = content.replace(
        "pred = predict_impact(event['family'], surprise)",
        "precomputed_stats = st.session_state.get('precomputed_stats', {})\n" +
        "                    pred = predict_impact_fast(event['family'], surprise, precomputed_stats)"
    )
    print("   ✅ Appels modifiés\n")
    
    # 4. Écrire
    print("4️⃣ Écriture...")
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✅ Fichier écrit\n")
    
    print("="*60)
    print("✅ PATCH APPLIQUÉ !")
    print("="*60)

if __name__ == "__main__":
    apply_patch()
