#!/usr/bin/env python3
"""
Recalcul des 944 cas extrêmes avec données Dukascopy - Session 25
VERSION CORRIGÉE - Gestion colonne time_group
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import timedelta

def calculate_phase1_movement(con, event_datetime):
    """Calcule Phase 1 : mouvement jusqu'au TTR (5-15 minutes)"""
    end_time = event_datetime + timedelta(minutes=15)
    
    query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '{event_datetime}'
          AND datetime < '{end_time}'
        ORDER BY datetime
    """
    
    df = con.execute(query).df()
    
    if df.empty:
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

def main():
    print("=" * 80)
    print("🔄 RECALCUL 944 CAS EXTRÊMES - DONNÉES DUKASCOPY")
    print("=" * 80)
    
    project_dir = Path(__file__).parent
    db_path = project_dir / "fx_impact_app" / "data" / "warehouse.duckdb"
    extreme_cases_file = project_dir / "extreme_cases_surprise30_session23.csv"
    
    print(f"\n📂 Chargement: {extreme_cases_file.name}")
    df_cases = pd.read_csv(extreme_cases_file)
    print(f"   ✅ {len(df_cases)} cas chargés")
    
    print(f"\n💾 Connexion base de données...")
    con = duckdb.connect(str(db_path))
    count = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    print(f"   Lignes prices_1m: {count:,}")
    
    print(f"\n🔄 Recalcul des mouvements...")
    print("-" * 80)
    
    results = []
    errors = []
    
    for idx, row in df_cases.iterrows():
        try:
            event_dt = pd.to_datetime(row['time_group'])
            
            movement = calculate_phase1_movement(con, event_dt)
            
            if movement:
                results.append({
                    'event_datetime': event_dt,
                    'score': row['max_score'],
                    'surprise': row['max_surprise'],
                    'num_events': row['num_events'],
                    'phase1_pips_old': row['phase1_pips'],
                    'phase1_pips_new': movement['phase1_pips'],
                    'ttr_minutes': movement['ttr_minutes'],
                    'direction': movement['direction'],
                    'start_price': movement['start_price'],
                    'ttr_price': movement['ttr_price']
                })
            else:
                errors.append(f"{event_dt}: Pas de données")
        except Exception as e:
            errors.append(f"Ligne {idx}: {str(e)}")
        
        if (idx + 1) % 100 == 0:
            print(f"   Traité: {idx+1}/{len(df_cases)} ({(idx+1)/len(df_cases)*100:.1f}%)")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS")
    print("=" * 80)
    print(f"\nCas traités: {len(results)}/{len(df_cases)}")
    print(f"Erreurs: {len(errors)}")
    
    if errors and len(errors) <= 10:
        print(f"\n⚠️  Erreurs:")
        for err in errors:
            print(f"   - {err}")
    
    if results:
        df_results = pd.DataFrame(results)
        
        output_file = project_dir / "extreme_cases_recalculated_dukascopy_session25.csv"
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ Sauvegardé: {output_file.name}")
        
        print("\n" + "=" * 80)
        print("📊 COMPARAISON ANCIENNES vs NOUVELLES DONNÉES")
        print("=" * 80)
        
        old_avg = df_results['phase1_pips_old'].mean()
        new_avg = df_results['phase1_pips_new'].mean()
        
        print(f"\nPhase 1 moyenne:")
        print(f"   Anciennes (EODHD):     {old_avg:.2f} pips")
        print(f"   Nouvelles (Dukascopy): {new_avg:.2f} pips")
        print(f"   Ratio amélioration:    ×{new_avg/old_avg if old_avg > 0 else 0:.2f}")
        
        print(f"\nDistribution Dukascopy:")
        print(f"   Min:     {df_results['phase1_pips_new'].min():.2f} pips")
        print(f"   Q25:     {df_results['phase1_pips_new'].quantile(0.25):.2f} pips")
        print(f"   Médiane: {df_results['phase1_pips_new'].median():.2f} pips")
        print(f"   Q75:     {df_results['phase1_pips_new'].quantile(0.75):.2f} pips")
        print(f"   Max:     {df_results['phase1_pips_new'].max():.2f} pips")
        
        print(f"\nTTR (Time To Return):")
        print(f"   Moyen:   {df_results['ttr_minutes'].mean():.1f} minutes")
        print(f"   Médian:  {df_results['ttr_minutes'].median():.0f} minutes")
        
        direction_counts = df_results['direction'].value_counts()
        print(f"\nDirection:")
        for dir, count in direction_counts.items():
            print(f"   {dir}: {count} ({count/len(df_results)*100:.1f}%)")
        
        print("\n" + "=" * 80)
        print("🔥 TOP 10 PLUS GRANDS MOUVEMENTS")
        print("=" * 80)
        
        top10 = df_results.nlargest(10, 'phase1_pips_new')
        for i, (idx, row) in enumerate(top10.iterrows(), 1):
            print(f"\n{i}. {row['event_datetime']}")
            print(f"   Score: {row['score']:.1f} | Surprise: {row['surprise']:.1f}% | Events: {int(row['num_events'])}")
            print(f"   Phase 1: {row['phase1_pips_new']:.2f} pips ({row['direction']}) | TTR: {int(row['ttr_minutes'])} min")
            print(f"   Ancien:  {row['phase1_pips_old']:.2f} pips (×{row['phase1_pips_new']/row['phase1_pips_old'] if row['phase1_pips_old'] > 0 else 0:.1f})")
    
    print("\n" + "=" * 80)
    print("✅ TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    main()
