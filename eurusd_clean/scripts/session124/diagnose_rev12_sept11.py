"""
Diagnostic Rev12 - 11 Septembre 2025
====================================

Investigation pourquoi Rev12 ne détecte pas le pattern attendu.
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime
import pytz

# Setup path
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
session120_dir = scripts_dir / 'session120'

if str(session120_dir) not in sys.path:
    sys.path.insert(0, str(session120_dir))

from double_wave_detector_rev12 import (
    detect_for_date_duckdb_rev12,
    load_ohlc_1m_duckdb
)


# Configuration
DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb')
TABLE = 'prices_bern'
TZ = 'Europe/Zurich'


def check_data_availability():
    """Vérifier données disponibles pour 11 septembre 2025"""
    
    print("\n" + "="*80)
    print("DIAGNOSTIC 1: DONNÉES DISPONIBLES")
    print("="*80)
    
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Vérifier table existe
    tables = conn.execute("SHOW TABLES").df()
    print(f"\n✅ Tables trouvées: {len(tables)}")
    print(f"   Table prices_bern présente: {TABLE in tables['name'].values}")
    
    # Vérifier données 11 septembre 2025
    date = datetime(2025, 9, 11)
    tz_obj = pytz.timezone(TZ)
    ts = tz_obj.localize(date)
    
    # Fenêtre trading (13:00-16:30)
    start_dt = ts.replace(hour=13, minute=0, second=0, microsecond=0)
    end_dt = ts.replace(hour=16, minute=30, second=0, microsecond=0)
    
    query = f"""
    SELECT 
        COUNT(*) as count,
        MIN(datetime) as first_bar,
        MAX(datetime) as last_bar
    FROM {TABLE}
    WHERE datetime >= ? AND datetime <= ?
    """
    
    result = conn.execute(query, [start_dt, end_dt]).fetchone()
    
    print(f"\n📊 Données 11 septembre 2025 (13:00-16:30 Bern):")
    print(f"   Nombre bars: {result[0]}")
    print(f"   Première bar: {result[1]}")
    print(f"   Dernière bar: {result[2]}")
    
    if result[0] == 0:
        print(f"\n❌ PROBLÈME: Aucune donnée prix pour cette date !")
        print(f"   Vérifier table prices_bern")
        return False
    
    # Vérifier données autour 14:30 (heure clé)
    key_time = ts.replace(hour=14, minute=30, second=0)
    window_start = key_time - pd.Timedelta(minutes=5)
    window_end = key_time + pd.Timedelta(minutes=90)
    
    query_window = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM {TABLE}
    WHERE datetime >= ? AND datetime <= ?
    ORDER BY datetime
    """
    
    df_window = conn.execute(query_window, [window_start, window_end]).df()
    
    print(f"\n📊 Données fenêtre critique (14:25-16:00):")
    print(f"   Bars: {len(df_window)}")
    
    if len(df_window) > 0:
        print(f"   Première: {df_window.iloc[0]['datetime']}")
        print(f"   Dernière: {df_window.iloc[-1]['datetime']}")
        
        # Calculer amplitude
        baseline = float(df_window.iloc[0]['close'])
        max_price = float(df_window['high'].max())
        min_price = float(df_window['low'].min())
        
        amp_high = (max_price - baseline) * 10000
        amp_low = (baseline - min_price) * 10000
        
        print(f"\n📈 Amplitude observée:")
        print(f"   Baseline (14:25): {baseline:.5f}")
        print(f"   Max: {max_price:.5f} (+{amp_high:.1f} pips)")
        print(f"   Min: {min_price:.5f} (-{amp_low:.1f} pips)")
        
        if amp_high > 30 or amp_low > 30:
            print(f"   ✅ Mouvement significatif détecté")
        else:
            print(f"   ⚠️  Mouvement faible (< 30 pips)")
    
    conn.close()
    return True


def test_rev12_with_debug():
    """Tester Rev12 avec mode debug activé"""
    
    print("\n" + "="*80)
    print("DIAGNOSTIC 2: TEST REV12 AVEC DEBUG")
    print("="*80)
    
    date = datetime(2025, 9, 11)
    
    print(f"\nTest détection 11 septembre 2025 avec debug=True...")
    print(f"DB: {DB_PATH}")
    print(f"Table: {TABLE}")
    print(f"TZ: {TZ}")
    print()
    
    try:
        result = detect_for_date_duckdb_rev12(
            db_path=DB_PATH,
            table=TABLE,
            date=date,
            tz=TZ,
            baseline_mode='close',
            minutes_after_hint=120,
            trading_window=True,
            debug=True  # Mode détaillé
        )
        
        print("\n" + "="*80)
        print("RÉSULTAT DÉTECTION")
        print("="*80)
        
        if result is None:
            print("❌ Aucun pattern détecté")
            print("\n🔍 CAUSES POSSIBLES:")
            print("   1. Données insuffisantes dans fenêtre temporelle")
            print("   2. Seuils détection trop stricts")
            print("   3. Pattern ne correspond pas aux critères Rev12")
            print("   4. Baseline incorrecte")
            return False
        else:
            print("✅ Pattern détecté !")
            print(f"\n   Wave1: {result['wave1_amp_pips']:.1f} pips")
            print(f"   Wave2: {result['wave2_amp_pips']:.1f} pips")
            print(f"   Confidence: {result['confidence']:.1f}%")
            return True
            
    except Exception as e:
        print(f"\n❌ ERREUR lors détection: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_timezone_config():
    """Vérifier configuration timezone"""
    
    print("\n" + "="*80)
    print("DIAGNOSTIC 3: TIMEZONE CONFIGURATION")
    print("="*80)
    
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Échantillon données
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime::DATE = '2025-09-11'
      AND datetime::TIME >= '14:25:00'
      AND datetime::TIME <= '14:35:00'
    ORDER BY datetime
    LIMIT 10
    """
    
    df = conn.execute(query).df()
    
    if len(df) > 0:
        print(f"\n📊 Échantillon données 11 sept (14:25-14:35):")
        print(df.to_string(index=False))
        
        print(f"\n🔍 Vérification timezone:")
        first_dt = df.iloc[0]['datetime']
        print(f"   Type: {type(first_dt)}")
        print(f"   Valeur: {first_dt}")
        
        # Vérifier si timezone-aware
        if isinstance(first_dt, pd.Timestamp):
            if first_dt.tz is not None:
                print(f"   ✅ Timezone-aware: {first_dt.tz}")
            else:
                print(f"   ⚠️  Timezone-naive (pas de tz)")
    else:
        print(f"\n❌ Aucune donnée trouvée pour cette fenêtre")
    
    conn.close()


def main():
    """Diagnostic complet"""
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLET - 11 SEPTEMBRE 2025")
    print("="*80)
    
    # Test 1: Données disponibles
    data_ok = check_data_availability()
    
    if not data_ok:
        print("\n❌ DIAGNOSTIC ARRÊTÉ - Pas de données")
        return
    
    # Test 2: Timezone
    check_timezone_config()
    
    # Test 3: Rev12 avec debug
    pattern_detected = test_rev12_with_debug()
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ DIAGNOSTIC")
    print("="*80)
    
    if pattern_detected:
        print("\n✅ Pattern détecté avec debug=True")
        print("   → Le test setup devrait fonctionner")
        print("   → Vérifier pourquoi test échoue")
    else:
        print("\n❌ Pattern NON détecté même avec debug")
        print("\n🔧 ACTIONS CORRECTIVES:")
        print("   1. Vérifier données 11 septembre dans DB")
        print("   2. Ajuster paramètres Rev12 (seuils, fenêtres)")
        print("   3. Vérifier timezone handling")
        print("   4. Tester autre date de référence")


if __name__ == '__main__':
    main()
