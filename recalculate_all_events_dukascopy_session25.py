#!/usr/bin/env python3
"""
Recalcul COMPLET avec Dukascopy - Session 25
Utilise la table 'events' pour avoir TOUS les événements historiques
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import timedelta

def calculate_phase1_movement(con, event_datetime):
    """Calcule Phase 1 depuis datetime exact"""
    end_time = event_datetime + timedelta(minutes=15)
    
    query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '{event_datetime}'
          AND datetime < '{end_time}'
        ORDER BY datetime
    """
    
    df = con.execute(query).df()
    
    if df.empty or len(df) < 2:
        return None
    
    start_price = df.iloc[0]['open']
    
    max_move = 0
    ttr_minutes = 0
    ttr_price = start_price
    direction = "FLAT"
    
    for i in range(len(df)):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']
        
        move_up = (high - start_price) * 10000
        move_down = (start_price - low) * 10000
        
        if move_up > max_move:
            max_move = move_up
            ttr_minutes = i + 1
            ttr_price = high
            direction = "UP"
        
        if move_down > max_move:
            max_move = move_down
            ttr_minutes = i + 1
            ttr_price = low
            direction = "DOWN"
    
    return {
        'phase1_pips': max_move,
        'ttr_minutes': ttr_minutes,
        'ttr_price': ttr_price,
        'start_price': start_price,
        'direction': direction
    }

def calculate_surprise(actual, forecast, previous):
    """Calcule surprise %"""
    if pd.isna(forecast) or forecast == 0:
        if pd.isna(previous) or previous == 0:
            return 0
        ref = previous
    else:
        ref = forecast
    
    if ref == 0:
        return 0
    
    return abs((actual - ref) / ref * 100)

def main():
    print("=" * 80)
    print("🔄 RECALCUL COMPLET - TABLE EVENTS + DUKASCOPY")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # Stats tables
    print("\n📊 Statistiques:")
    events_count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    prices_count = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    
    print(f"   Events disponibles: {events_count:,}")
    print(f"   Prix M1 disponibles: {prices_count:,}")
    
    # Charger événements avec surprise calculable
    print("\n📂 Chargement événements...")
    
    query = """
        SELECT 
            ts_utc,
            event_key,
            event_title,
            country,
            actual,
            forecast,
            previous,
            estimate,
            importance_n
        FROM events
        WHERE actual IS NOT NULL
          AND (forecast IS NOT NULL OR previous IS NOT NULL)
        ORDER BY ts_utc
    """
    
    df_events = con.execute(query).df()
    print(f"   ✅ {len(df_events):,} événements chargés")
    
    # Calculer surprises
    print("\n🔢 Calcul surprises...")
    df_events['surprise_pct'] = df_events.apply(
        lambda row: calculate_surprise(row['actual'], row['forecast'], row['previous']),
        axis=1
    )
    
    # Filtrer surprise > 30%
    df_extreme = df_events[df_events['surprise_pct'] > 30].copy()
    print(f"   ✅ {len(df_extreme):,} événements avec surprise > 30%")
    
    # Période couverture prix
    price_range = con.execute("""
        SELECT MIN(datetime) as min_dt, MAX(datetime) as max_dt
        FROM prices_1m
    """).df().iloc[0]
    
    print(f"\n📅 Période prix Dukascopy:")
    print(f"   {price_range['min_dt']} → {price_range['max_dt']}")
    
    # Filtrer événements dans période prix
    df_extreme['ts_utc'] = pd.to_datetime(df_extreme['ts_utc'])
    min_price = pd.to_datetime(price_range['min_dt'])
    max_price = pd.to_datetime(price_range['max_dt'])
    
    df_extreme = df_extreme[
        (df_extreme['ts_utc'] >= min_price) & 
        (df_extreme['ts_utc'] <= max_price)
    ].copy()
    
    print(f"   ✅ {len(df_extreme):,} événements dans période prix")
    
    # Recalculer Phase 1
    print(f"\n🔄 Recalcul Phase 1 avec Dukascopy...")
    print(f"   (Ceci peut prendre quelques minutes)")
    print("-" * 80)
    
    results = []
    errors = []
    
    for idx, row in df_extreme.iterrows():
        try:
            movement = calculate_phase1_movement(con, row['ts_utc'])
            
            if movement:
                results.append({
                    'ts_utc': row['ts_utc'],
                    'event_key': row['event_key'],
                    'event_title': row['event_title'],
                    'country': row['country'],
                    'actual': row['actual'],
                    'forecast': row['forecast'],
                    'previous': row['previous'],
                    'surprise_pct': row['surprise_pct'],
                    'importance': row['importance_n'],
                    'phase1_pips': movement['phase1_pips'],
                    'ttr_minutes': movement['ttr_minutes'],
                    'direction': movement['direction'],
                    'start_price': movement['start_price'],
                    'ttr_price': movement['ttr_price']
                })
            else:
                errors.append(f"{row['ts_utc']}: Pas de données prix")
        except Exception as e:
            errors.append(f"{row['ts_utc']}: {str(e)}")
        
        if (idx + 1) % 100 == 0 or (idx + 1) == len(df_extreme):
            print(f"   Traité: {idx+1}/{len(df_extreme)} ({(idx+1)/len(df_extreme)*100:.1f}%)")
    
    con.close()
    
    # Résultats
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS")
    print("=" * 80)
    
    print(f"\nCas traités: {len(results)}/{len(df_extreme)}")
    print(f"Erreurs: {len(errors)}")
    
    if errors and len(errors) <= 20:
        print(f"\n⚠️  Erreurs ({len(errors)}):")
        for err in errors[:20]:
            print(f"   - {err}")
    
    if results:
        df_results = pd.DataFrame(results)
        
        # Sauvegarder
        output_file = Path(__file__).parent / "events_extreme_surprise_dukascopy_session25.csv"
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ Sauvegardé: {output_file.name}")
        print(f"   Lignes: {len(df_results):,}")
        
        # Statistiques
        print("\n" + "=" * 80)
        print("📊 STATISTIQUES DUKASCOPY")
        print("=" * 80)
        
        print(f"\nPhase 1:")
        print(f"   Moyenne:  {df_results['phase1_pips'].mean():.2f} pips")
        print(f"   Médiane:  {df_results['phase1_pips'].median():.2f} pips")
        print(f"   Min:      {df_results['phase1_pips'].min():.2f} pips")
        print(f"   Max:      {df_results['phase1_pips'].max():.2f} pips")
        print(f"   Q25:      {df_results['phase1_pips'].quantile(0.25):.2f} pips")
        print(f"   Q75:      {df_results['phase1_pips'].quantile(0.75):.2f} pips")
        
        print(f"\nTTR:")
        print(f"   Moyen:    {df_results['ttr_minutes'].mean():.1f} minutes")
        print(f"   Médian:   {df_results['ttr_minutes'].median():.0f} minutes")
        
        print(f"\nSurprise:")
        print(f"   Moyenne:  {df_results['surprise_pct'].mean():.1f}%")
        print(f"   Médiane:  {df_results['surprise_pct'].median():.1f}%")
        print(f"   Max:      {df_results['surprise_pct'].max():.1f}%")
        
        direction_counts = df_results['direction'].value_counts()
        print(f"\nDirection:")
        for dir, count in direction_counts.items():
            print(f"   {dir}: {count} ({count/len(df_results)*100:.1f}%)")
        
        # Top 10
        print("\n" + "=" * 80)
        print("🔥 TOP 10 PLUS GRANDS MOUVEMENTS")
        print("=" * 80)
        
        top10 = df_results.nlargest(10, 'phase1_pips')
        for i, (idx, row) in enumerate(top10.iterrows(), 1):
            print(f"\n{i}. {row['ts_utc']}")
            print(f"   Event: {row['event_title']} ({row['country']})")
            print(f"   Surprise: {row['surprise_pct']:.1f}% | Importance: {row['importance']}")
            print(f"   Phase 1: {row['phase1_pips']:.2f} pips ({row['direction']}) | TTR: {int(row['ttr_minutes'])} min")
    
    print("\n" + "=" * 80)
    print("✅ TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    main()
