#!/bin/bash
# Script pour créer tous les fichiers de diagnostic automatiquement
# Usage: bash 0_setup_all_scripts.sh

echo "🔧 CRÉATION SCRIPTS DE DIAGNOSTIC"
echo "========================================"
echo ""

cd ~/Projects/eurusd_news_impact_calculator

# Script 1: Test API EODHD
cat > 1_test_eodhd_api.py << 'ENDFILE1'
#!/usr/bin/env python3
import os, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_eodhd_api():
    api_key = os.getenv('EODHD_API_KEY')
    if not api_key:
        print("❌ EODHD_API_KEY non trouvée")
        return False
    
    print(f"✓ Clé trouvée: {api_key[:10]}...")
    
    test_dates = [
        ('2025-09-05', '2025-09-05'),
        ('2025-10-04', '2025-10-04'),
    ]
    
    for date_from, date_to in test_dates:
        print(f"\n📅 Test: {date_from}")
        print("-" * 60)
        
        r = requests.get('https://eodhd.com/api/economic-events', params={
            'from': date_from, 'to': date_to,
            'api_token': api_key, 'countries': 'US', 'fmt': 'json'
        }, timeout=10)
        
        if r.status_code != 200:
            print(f"❌ Erreur: {r.status_code}")
            continue
        
        data = r.json()
        if not data:
            print("⚠️  Aucun événement")
            continue
        
        print(f"✓ {len(data)} événements")
        
        has_forecast = sum(1 for e in data if e.get('forecast') is not None)
        has_previous = sum(1 for e in data if e.get('previous') is not None)
        
        print(f"  Forecast: {has_forecast} ({has_forecast/len(data)*100:.1f}%)")
        print(f"  Previous: {has_previous} ({has_previous/len(data)*100:.1f}%)")
    
    return True

if __name__ == '__main__':
    print("🔍 TEST API EODHD\n")
    test_eodhd_api()
ENDFILE1

echo "✓ 1_test_eodhd_api.py créé"

# Script 2: Nettoyage base
cat > 2_clean_database.py << 'ENDFILE2'
#!/usr/bin/env python3
import duckdb, shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path("fx_impact_app/data/warehouse.duckdb")

def backup_database():
    if not DB_PATH.exists():
        print(f"❌ Base non trouvée: {DB_PATH}")
        return False
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.parent / f"warehouse_backup_{timestamp}.duckdb"
    shutil.copy2(DB_PATH, backup)
    print(f"✓ Sauvegarde: {backup}")
    return True

def audit_before():
    conn = duckdb.connect(str(DB_PATH))
    print("\n📊 AUDIT AVANT NETTOYAGE")
    print("=" * 60)
    
    result = conn.execute("""
        SELECT COUNT(*) as total,
               COUNT(*) - COUNT(DISTINCT (ts_utc, event_key, country)) as dups
        FROM events
    """).fetchone()
    
    print(f"Total: {result[0]:,}")
    print(f"Doublons: {result[1]:,} ({result[1]/result[0]*100:.1f}%)")
    
    conn.close()
    return result[0], result[1]

def clean_duplicates():
    conn = duckdb.connect(str(DB_PATH))
    print("\n🧹 NETTOYAGE...")
    
    before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    
    conn.execute("""
        CREATE TABLE events_clean AS
        SELECT DISTINCT ON (ts_utc, event_key, country) *
        FROM events
        ORDER BY ts_utc, event_key, country,
                 CASE WHEN actual IS NOT NULL THEN 0 ELSE 1 END
    """)
    
    after = conn.execute("SELECT COUNT(*) FROM events_clean").fetchone()[0]
    
    conn.execute("DROP TABLE events")
    conn.execute("ALTER TABLE events_clean RENAME TO events")
    
    conn.close()
    
    deleted = before - after
    print(f"✓ Supprimés: {deleted:,} doublons")
    return deleted

def main():
    print("🔧 NETTOYAGE BASE DE DONNÉES\n")
    
    if not backup_database():
        return
    
    total, dupes = audit_before()
    
    if dupes == 0:
        print("\n✅ Aucun doublon")
        return
    
    response = input(f"\n⚠️  Supprimer {dupes:,} doublons? (oui/non): ")
    
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Annulé")
        return
    
    deleted = clean_duplicates()
    
    print("\n✅ TERMINÉ")
    print(f"Doublons supprimés: {deleted:,}")

if __name__ == '__main__':
    main()
ENDFILE2

echo "✓ 2_clean_database.py créé"

# Script 3: Quick Fix Surprise
cat > 3_quick_fix.py << 'ENDFILE3'
#!/usr/bin/env python3
import shutil
from pathlib import Path

SURPRISE = Path("fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py")

def fix_surprise():
    if not SURPRISE.exists():
        print(f"❌ Non trouvé: {SURPRISE}")
        return
    
    # Backup
    shutil.copy2(SURPRISE, str(SURPRISE) + ".backup")
    
    with open(SURPRISE, 'r') as f:
        content = f.read()
    
    # Remplacements clés
    content = content.replace('forecast IS NOT NULL', 'previous IS NOT NULL')
    content = content.replace('Consensus (Forecast)', 'Référence (Previous)')
    content = content.replace('surprise = actual - forecast', 'surprise = actual - previous')
    
    with open(SURPRISE, 'w') as f:
        f.write(content)
    
    print("✅ Analyseur-Surprise corrigé (utilise previous)")
    print("   Backup: 3_Analyseur-Surprise.py.backup")

if __name__ == '__main__':
    print("🔧 CORRECTION ANALYSEUR SURPRISE\n")
    fix_surprise()
ENDFILE3

echo "✓ 3_quick_fix.py créé"

# Script 4: Test rapide
cat > 4_test_all.sh << 'ENDFILE4'
#!/bin/bash
echo "🧪 TEST COMPLET"
echo "==============="

echo -e "\n1️⃣  Test API..."
python 1_test_eodhd_api.py | head -30

echo -e "\n\n2️⃣  Audit base..."
python -c "
import duckdb
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
r = conn.execute('SELECT COUNT(*), COUNT(*) - COUNT(DISTINCT (ts_utc, event_key, country)) FROM events').fetchone()
print(f'Total: {r[0]:,}')
print(f'Doublons: {r[1]:,}')
conn.close()
"

echo -e "\n✅ Tests terminés"
ENDFILE4

chmod +x 4_test_all.sh

echo "✓ 4_test_all.sh créé"

echo ""
echo "========================================"
echo "✅ TOUS LES SCRIPTS CRÉÉS"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo ""
echo "1. Test rapide:"
echo "   bash 4_test_all.sh"
echo ""
echo "2. Nettoyage complet:"
echo "   python 2_clean_database.py"
echo ""
echo "3. Corriger Analyseur Surprise:"
echo "   python 3_quick_fix.py"
echo ""
