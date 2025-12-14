#!/usr/bin/env python3
"""
🔧 Remplacement simple - get_future_events()
Remplace la fonction par celle qui marche dans le Planificateur

Usage:
    python replace_get_future_events.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def backup_file(filepath: Path):
    backup_dir = filepath.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.stem}_{timestamp}.backup"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup: {backup_path.name}")

def main():
    print("="*70)
    print("🔧 REMPLACEMENT get_future_events()")
    print("="*70)
    print()
    
    filepath = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not filepath.exists():
        print("❌ Fichier introuvable")
        return
    
    backup_file(filepath)
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Trouver la fonction
    func_start = None
    func_end = None
    
    for i, line in enumerate(lines):
        if 'def get_future_events' in line:
            func_start = i
            print(f"✅ Fonction trouvée ligne {i + 1}")
            break
    
    if not func_start:
        print("❌ Fonction non trouvée")
        return
    
    # Trouver la fin (return df ou prochaine def)
    for i in range(func_start + 1, len(lines)):
        if (lines[i].startswith('def ') and i > func_start) or \
           ('return df' in lines[i] or 'return events' in lines[i]):
            func_end = i + 1 if 'return' in lines[i] else i
            break
    
    print(f"✅ Fonction s'étend jusqu'à ligne {func_end + 1}")
    
    # NOUVELLE FONCTION (copiée du Planificateur)
    new_function = '''def get_future_events(date_from, date_to, countries):
    """Récupère les événements futurs (copié du Planificateur qui marche)"""
    # Expansion : EU → tous pays eurozone
    expanded_countries = []
    eurozone_countries = ['EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR']
    
    for country in countries:
        if country == 'EU':
            expanded_countries.extend(eurozone_countries)
        else:
            expanded_countries.append(country)
    
    # Dédupliquer
    expanded_countries = list(set(expanded_countries))
    
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    country_filter = "', '".join(expanded_countries)
    
    query = f"""
    SELECT 
        e.ts_utc, e.event_key, e.country, e.importance_n,
        e.actual, e.forecast, e.previous,
        ef.empirical_score, ef.empirical_impact, ef.impact_level,
        ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
      AND e.ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
      AND e.country IN ('{country_filter}')
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    if len(df) > 0:
        # Mapper les colonnes pour compatibilité
        df['impact_calendar'] = df['importance_n'].map({1:'High', 2:'Medium', 3:'Low'})
        df['impact_empirical'] = df['empirical_impact'].fillna('Unknown')
        
        # Identifier familles si besoin
        df['family'] = df['event_key'].apply(identify_family)
    
    return df

'''
    
    # Remplacer
    del lines[func_start:func_end]
    lines.insert(func_start, new_function)
    
    print("✅ Fonction remplacée")
    
    # Ajouter identify_family si manquante
    if 'def identify_family' not in content:
        identify_family_func = '''
def identify_family(event_key):
    """Identifie la famille d'un événement"""
    for family_name, pattern in FAMILY_PATTERNS.items():
        clean_pattern = pattern.replace('(?i)', '')
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            return family_name
    return None

'''
        lines.insert(func_start + 1, identify_family_func)
        print("✅ identify_family ajoutée")
    
    # Ajouter imports si manquants
    content_new = '\n'.join(lines)
    
    if 'import duckdb' not in content_new:
        content_new = 'import duckdb\n' + content_new
        print("✅ import duckdb ajouté")
    
    if 'from event_families import FAMILY_PATTERNS' not in content_new:
        # Trouver où insérer (après les imports)
        lines_new = content_new.split('\n')
        for i, line in enumerate(lines_new):
            if 'from config import get_db_path' in line:
                lines_new.insert(i + 1, 'from event_families import FAMILY_PATTERNS')
                content_new = '\n'.join(lines_new)
                print("✅ import FAMILY_PATTERNS ajouté")
                break
    
    # Sauvegarder
    filepath.write_text(content_new, encoding='utf-8')
    
    print("\n" + "="*70)
    print("🎉 SUCCÈS ! Fonction remplacée")
    print("="*70)
    print("\n📝 Modifications:")
    print("   - get_future_events() → version du Planificateur")
    print("   - JOIN avec event_families")
    print("   - Mapping impact_calendar/empirical")
    print("   - read_only=True")
    print("\n🧪 Test:")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")

if __name__ == "__main__":
    main()
