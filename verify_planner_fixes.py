#!/usr/bin/env python3
"""
Vérifie que les corrections du Planificateur ont été appliquées
À lancer APRÈS fix_planificateur_db_connections.py
"""

from pathlib import Path

PLANNER_FILE = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

def verify_fixes():
    """Vérifie les corrections appliquées"""
    
    print("🔍 VÉRIFICATION DES CORRECTIONS")
    print("=" * 60)
    
    if not PLANNER_FILE.exists():
        print(f"❌ Fichier introuvable: {PLANNER_FILE}")
        return False
    
    with open(PLANNER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    all_ok = True
    
    # === TEST 1: Connexions DB ===
    print("\n📡 Test 1: Connexions DB...")
    
    bad_connections = content.count('duckdb.connect(get_db_path())')
    good_connections = content.count('duckdb.connect(get_db_path(), read_only=True)')
    
    if bad_connections > 0:
        print(f"   ❌ {bad_connections} connexions SANS read_only=True")
        all_ok = False
    else:
        print(f"   ✅ 0 connexions sans read_only")
    
    print(f"   ℹ️  {good_connections} connexions avec read_only=True")
    
    # === TEST 2: Filtrage famille ===
    print("\n🔍 Test 2: Filtrage famille (ligne ~397)...")
    
    found_active_filter = False
    found_commented_filter = False
    
    for i, line in enumerate(lines, 1):
        # Chercher ligne active (non commentée)
        if "df = df[df['family'].notna()]" in line and not line.strip().startswith('#'):
            if 390 <= i <= 410:
                print(f"   ❌ Ligne {i}: Filtrage ACTIF (élimine événements sans famille)")
                found_active_filter = True
                all_ok = False
        
        # Chercher ligne commentée
        if "# df = df[df['family'].notna()]" in line:
            if 390 <= i <= 410:
                found_commented_filter = True
    
    if found_commented_filter and not found_active_filter:
        print("   ✅ Filtrage correctement désactivé (ligne commentée)")
    elif not found_active_filter and not found_commented_filter:
        print("   ⚠️  Ligne filtrage pas trouvée (peut-être supprimée)")
    
    # === TEST 3: Michigan visible ===
    print("\n🧪 Test 3: Vérification rapide Michigan...")
    
    try:
        import duckdb
        import sys
        sys.path.insert(0, 'fx_impact_app/src')
        from config import get_db_path
        
        conn = duckdb.connect(get_db_path(), read_only=True)
        
        result = conn.execute("""
            SELECT COUNT(*) as count
            FROM events
            WHERE DATE(ts_utc) = '2025-10-10'
              AND country = 'US'
              AND event_key LIKE '%michigan%'
        """).fetchone()
        
        conn.close()
        
        if result and result[0] > 0:
            print(f"   ✅ {result[0]} événement(s) Michigan trouvé(s) dans DB")
        else:
            print("   ⚠️  Aucun événement Michigan pour le 10 oct 2025")
            print("      → Peut être normal si pas encore scrapé")
    
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier DB: {e}")
    
    # === TEST 4: Structure générale ===
    print("\n📋 Test 4: Structure du fichier...")
    
    n_lines = len(lines)
    has_sequential = 'SEQUENTIAL_MODE_AVAILABLE' in content
    has_load_events = 'load_all_events_for_date' in content
    
    print(f"   • Lignes totales: {n_lines}")
    print(f"   • Mode séquentiel: {'✅ Présent' if has_sequential else '❌ Absent'}")
    print(f"   • Chargement complet: {'✅ Présent' if has_load_events else '❌ Absent'}")
    
    # === RÉSULTAT FINAL ===
    print("\n" + "=" * 60)
    
    if all_ok:
        print("✅ TOUTES LES CORRECTIONS APPLIQUÉES")
        print("\n🚀 Prochaines étapes:")
        print("   1. streamlit run fx_impact_app/streamlit_app/Home.py")
        print("   2. Aller dans 'Planificateur Multi-Événements'")
        print("   3. Sélectionner 10 octobre 2025")
        print("   4. Cliquer 'Charger Événements'")
        print("   5. Vérifier que Michigan Consumer Sentiment (16:00) apparaît")
        
        print("\n💡 Si Michigan n'apparaît pas:")
        print("   → python3 diagnose_michigan_event.py")
        
        return True
    else:
        print("❌ CERTAINES CORRECTIONS MANQUANTES")
        print("\n🔧 Actions suggérées:")
        print("   1. Relancer: python3 fix_planificateur_db_connections.py")
        print("   2. Vérifier backup si besoin de restaurer")
        print("   3. Relancer cette vérification")
        
        return False

if __name__ == '__main__':
    import sys
    success = verify_fixes()
    sys.exit(0 if success else 1)
