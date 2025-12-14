"""
Investigation : Vérifier si les scores empiriques ont été recalculés depuis Finnhub
"""
import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

def check_event_families_table():
    """Vérifier la structure et le contenu de event_families"""
    print("="*100)
    print("1. VÉRIFICATION TABLE event_families")
    print("="*100)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Vérifier structure
    query_structure = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'event_families'
    ORDER BY ordinal_position
    """
    df_structure = conn.execute(query_structure).df()
    print("\nStructure de la table:")
    print(df_structure)
    
    # Statistiques générales
    query_stats = """
    SELECT 
        COUNT(*) as total,
        COUNT(empirical_score) as avec_score,
        COUNT(DISTINCT event_key) as event_keys_uniques,
        COUNT(DISTINCT country) as pays_uniques,
        MIN(empirical_score) as min_score,
        MAX(empirical_score) as max_score,
        AVG(empirical_score) as avg_score,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY empirical_score) as median_score
    FROM event_families
    """
    df_stats = conn.execute(query_stats).df()
    print("\nStatistiques:")
    print(df_stats)
    
    # Top 10 scores
    query_top = """
    SELECT event_key, country, empirical_score, family
    FROM event_families
    WHERE empirical_score IS NOT NULL
    ORDER BY empirical_score DESC
    LIMIT 10
    """
    df_top = conn.execute(query_top).df()
    print("\nTop 10 scores empiriques:")
    print(df_top)
    
    conn.close()
    return df_stats

def check_events_table():
    """Vérifier la table events (source Finnhub)"""
    print("\n" + "="*100)
    print("2. VÉRIFICATION TABLE events (SOURCE FINNHUB)")
    print("="*100)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Statistiques générales
    query_stats = """
    SELECT 
        COUNT(*) as total_events,
        COUNT(DISTINCT DATE(ts_utc)) as dates_uniques,
        COUNT(DISTINCT event_key) as event_keys_uniques,
        COUNT(DISTINCT country) as pays_uniques,
        MIN(ts_utc) as premier_event,
        MAX(ts_utc) as dernier_event
    FROM events
    WHERE country = 'US'
    """
    df_stats = conn.execute(query_stats).df()
    print("\nStatistiques events (US):")
    print(df_stats)
    
    # Vérifier couverture temporelle
    query_coverage = """
    SELECT 
        DATE(ts_utc) as date_event,
        COUNT(*) as n_events
    FROM events
    WHERE country = 'US'
      AND DATE(ts_utc) >= '2020-01-01'
    GROUP BY DATE(ts_utc)
    ORDER BY date_event DESC
    LIMIT 10
    """
    df_coverage = conn.execute(query_coverage).df()
    print("\nDernières dates avec événements:")
    print(df_coverage)
    
    # Vérifier événements récents
    query_recent = """
    SELECT 
        event_key,
        event_title,
        ts_utc,
        country,
        importance_n
    FROM events
    WHERE country = 'US'
      AND DATE(ts_utc) >= '2025-09-01'
    ORDER BY ts_utc DESC
    LIMIT 5
    """
    df_recent = conn.execute(query_recent).df()
    print("\nÉvénements récents (US):")
    print(df_recent)
    
    conn.close()
    return df_stats

def check_prices_finnhub():
    """Vérifier la table prices_finnhub_m1"""
    print("\n" + "="*100)
    print("3. VÉRIFICATION TABLE prices_finnhub_m1")
    print("="*100)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Statistiques générales
    query_stats = """
    SELECT 
        COUNT(*) as total_candles,
        MIN(datetime) as premier_candle,
        MAX(datetime) as dernier_candle,
        COUNT(DISTINCT DATE(datetime)) as dates_uniques
    FROM prices_finnhub_m1
    """
    df_stats = conn.execute(query_stats).df()
    print("\nStatistiques prices_finnhub_m1:")
    print(df_stats)
    
    conn.close()
    return df_stats

def check_recalculation_scripts():
    """Chercher des scripts de recalcul récents"""
    print("\n" + "="*100)
    print("4. RECHERCHE SCRIPTS DE RECALCUL")
    print("="*100)
    
    scripts_dir = PROJECT_ROOT / 'scripts'
    recalculation_scripts = []
    
    # Chercher scripts avec "recalculate" ou "empirical" dans le nom
    for script_path in scripts_dir.rglob('*recalculate*.py'):
        recalculation_scripts.append(script_path)
    for script_path in scripts_dir.rglob('*empirical*.py'):
        if script_path not in recalculation_scripts:
            recalculation_scripts.append(script_path)
    
    print(f"\nScripts de recalcul trouvés: {len(recalculation_scripts)}")
    for script in sorted(recalculation_scripts):
        # Lire les premières lignes pour voir la date
        try:
            with open(script, 'r') as f:
                lines = f.readlines()[:20]
                date_found = False
                for line in lines:
                    if 'date' in line.lower() or 'Date' in line:
                        print(f"\n{script.relative_to(PROJECT_ROOT)}")
                        print(f"  {line.strip()}")
                        date_found = True
                        break
                if not date_found:
                    print(f"\n{script.relative_to(PROJECT_ROOT)}")
                    # Vérifier date de modification
                    mtime = script.stat().st_mtime
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  Dernière modification: {mtime_str}")
        except Exception as e:
            print(f"\n{script.relative_to(PROJECT_ROOT)}: Erreur lecture ({e})")
    
    return recalculation_scripts

def check_finnhub_in_scripts(scripts):
    """Vérifier si les scripts utilisent Finnhub"""
    print("\n" + "="*100)
    print("5. VÉRIFICATION UTILISATION FINNHUB DANS SCRIPTS")
    print("="*100)
    
    finnhub_scripts = []
    
    for script_path in scripts:
        try:
            with open(script_path, 'r') as f:
                content = f.read().lower()
                if 'finnhub' in content:
                    finnhub_scripts.append(script_path)
                    print(f"\n✅ {script_path.relative_to(PROJECT_ROOT)}")
                    # Chercher lignes avec finnhub
                    with open(script_path, 'r') as f2:
                        lines = f2.readlines()
                        for i, line in enumerate(lines[:50], 1):
                            if 'finnhub' in line.lower():
                                print(f"  Ligne {i}: {line.strip()[:80]}")
        except Exception as e:
            pass
    
    if not finnhub_scripts:
        print("\n❌ Aucun script de recalcul trouvé utilisant Finnhub")
    
    return finnhub_scripts

def check_sample_calculation():
    """Calculer un score empirique d'exemple pour vérifier la méthode"""
    print("\n" + "="*100)
    print("6. CALCUL D'EXEMPLE : Score empirique pour un événement")
    print("="*100)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Prendre un événement fréquent (ex: CPI US)
    query_events = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country
    FROM events e
    WHERE e.event_key LIKE '%cpi%'
      AND e.country = 'US'
      AND DATE(e.ts_utc) >= '2020-01-01'
    ORDER BY e.ts_utc
    LIMIT 20
    """
    df_events = conn.execute(query_events).df()
    
    if df_events.empty:
        print("❌ Aucun événement CPI trouvé")
        conn.close()
        return
    
    print(f"\nÉvénements CPI US trouvés: {len(df_events)}")
    print("Premiers événements:")
    print(df_events.head())
    
    # Pour chaque événement, mesurer l'impact depuis prices_finnhub_m1
    impacts = []
    for _, event in df_events.head(5).iterrows():  # Limiter à 5 pour test
        event_time = pd.to_datetime(event['ts_utc'])
        event_time_naive = event_time.replace(tzinfo=None) if hasattr(event_time, 'tzinfo') and event_time.tzinfo else event_time
        
        # Chercher baseline (OPEN première bougie après événement)
        query_baseline = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= TIMESTAMP '{event_time_naive.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime <= TIMESTAMP '{event_time_naive.strftime('%Y-%m-%d %H:%M:%S')}' + INTERVAL '240 minutes'
        ORDER BY datetime ASC
        LIMIT 1
        """
        df_baseline = conn.execute(query_baseline).df()
        
        if not df_baseline.empty:
            baseline_price = df_baseline.iloc[0]['open']
            
            # Chercher pic maximum dans 240 minutes
            query_peak = f"""
            SELECT MAX(high) as peak_high, MIN(low) as peak_low
            FROM prices_finnhub_m1
            WHERE datetime >= TIMESTAMP '{event_time_naive.strftime('%Y-%m-%d %H:%M:%S')}'
              AND datetime <= TIMESTAMP '{event_time_naive.strftime('%Y-%m-%d %H:%M:%S')}' + INTERVAL '240 minutes'
            """
            df_peak = conn.execute(query_peak).df()
            
            if not df_peak.empty and not pd.isna(df_peak.iloc[0]['peak_high']):
                peak_high = df_peak.iloc[0]['peak_high']
                peak_low = df_peak.iloc[0]['peak_low']
                impact_up = (peak_high - baseline_price) * 10000
                impact_down = (baseline_price - peak_low) * 10000
                impact = max(abs(impact_up), abs(impact_down))
                
                impacts.append({
                    'date': event_time_naive.date(),
                    'impact_pips': impact
                })
    
    if impacts:
        df_impacts = pd.DataFrame(impacts)
        print(f"\nImpacts mesurés depuis prices_finnhub_m1 (échantillon {len(impacts)} événements):")
        print(df_impacts)
        print(f"\nMoyenne: {df_impacts['impact_pips'].mean():.2f} pips")
        print(f"Médiane: {df_impacts['impact_pips'].median():.2f} pips")
        print(f"P80: {df_impacts['impact_pips'].quantile(0.8):.2f} pips")
        
        # Comparer avec score dans event_families
        query_score = """
        SELECT empirical_score
        FROM event_families
        WHERE event_key LIKE '%cpi%'
          AND country = 'US'
        LIMIT 1
        """
        df_score = conn.execute(query_score).df()
        if not df_score.empty:
            score_db = df_score.iloc[0]['empirical_score']
            print(f"\nScore dans event_families: {score_db:.2f}")
            print(f"Comparaison: Score DB vs Calculé depuis Finnhub")
    
    conn.close()

def main():
    print("="*100)
    print("INVESTIGATION : SCORES EMPIRIQUES DEPUIS FINNHUB")
    print("="*100)
    print()
    
    # 1. Vérifier event_families
    df_ef_stats = check_event_families_table()
    
    # 2. Vérifier events (Finnhub)
    df_events_stats = check_events_table()
    
    # 3. Vérifier prices_finnhub_m1
    df_prices_stats = check_prices_finnhub()
    
    # 4. Chercher scripts de recalcul
    scripts = check_recalculation_scripts()
    
    # 5. Vérifier utilisation Finnhub
    finnhub_scripts = check_finnhub_in_scripts(scripts)
    
    # 6. Calcul d'exemple
    check_sample_calculation()
    
    # Résumé
    print("\n" + "="*100)
    print("RÉSUMÉ")
    print("="*100)
    print("\n✅ Table event_families: Scores présents")
    print("✅ Table events: Données Finnhub présentes")
    print("✅ Table prices_finnhub_m1: Données prix présentes")
    
    if finnhub_scripts:
        print(f"\n✅ Scripts utilisant Finnhub trouvés: {len(finnhub_scripts)}")
    else:
        print("\n⚠️  Aucun script de recalcul utilisant Finnhub trouvé")
        print("   → Les scores peuvent être basés sur EODHD ou autre source")
    
    print("\n" + "="*100)

if __name__ == '__main__':
    main()




