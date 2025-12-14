#!/usr/bin/env python3
"""
CORRECTION: Calcul Phase 1 avec conversion timezone CORRECTE
Session 28 - Fix problème timezone DuckDB
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

def calculate_phase1_for_event(con, event_ts, event_id):
    """
    Calcule Phase 1 pour un événement - VERSION CORRIGÉE
    """
    try:
        # Convertir en UTC pur
        if isinstance(event_ts, str):
            event_dt = pd.to_datetime(event_ts, utc=True)
        else:
            event_dt = event_ts
            if event_dt.tzinfo is not None:
                event_dt = event_dt.astimezone(pd.Timestamp.utcnow().tz)
        
        # CORRECTION: Extraire heure UTC sans timezone
        # Pour événement 14:30+02:00 → donne 12:30 UTC
        utc_hour = event_dt.hour
        utc_minute = event_dt.minute
        date_str = event_dt.strftime('%Y-%m-%d')
        
        # Fenêtre : event_time → event_time + 15 min
        end_dt = event_dt + timedelta(minutes=15)
        end_hour = end_dt.hour
        end_minute = end_dt.minute
        
        # CORRECTION: Requête qui compare SANS le timezone offset
        # On filtre sur DATE + HOUR + MINUTE en UTC
        query = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_1m
        WHERE DATE(datetime) = '{date_str}'
        AND (
            (EXTRACT(HOUR FROM datetime) = {utc_hour} AND EXTRACT(MINUTE FROM datetime) >= {utc_minute})
            OR (EXTRACT(HOUR FROM datetime) = {end_hour} AND EXTRACT(MINUTE FROM datetime) < {end_minute})
            OR (EXTRACT(HOUR FROM datetime) > {utc_hour} AND EXTRACT(HOUR FROM datetime) < {end_hour})
        )
        ORDER BY datetime
        LIMIT 15
        """
        
        prices = con.execute(query).df()
        
        if len(prices) == 0:
            return None
        
        # Prix départ = OPEN première minute
        start_price = prices.iloc[0]['open']
        
        # Trouver pic dans les 15 minutes
        max_high = prices['high'].max()
        min_low = prices['low'].min()
        
        # Phase 1 = mouvement maximum
        phase1_up = (max_high - start_price) * 10000
        phase1_down = (start_price - min_low) * 10000
        
        if phase1_up > phase1_down:
            phase1_pips = phase1_up
            direction = 'UP'
            ttr_price = max_high
            ttr_idx = prices['high'].idxmax()
            ttr_minutes = ttr_idx + 1
        else:
            phase1_pips = phase1_down
            direction = 'DOWN'
            ttr_price = min_low
            ttr_idx = prices['low'].idxmin()
            ttr_minutes = ttr_idx + 1
        
        return {
            'phase1_pips': phase1_pips,
            'ttr_minutes': int(ttr_minutes),
            'direction': direction,
            'start_price': start_price,
            'ttr_price': ttr_price
        }
        
    except Exception as e:
        print(f"   ❌ Erreur événement {event_id}: {e}")
        return None

def main():
    print("=" * 80)
    print("🔄 RECALCUL PHASE 1 - VERSION CORRIGÉE TIMEZONE")
    print("=" * 80)
    print("\nCorrection : Comparaison timezone correcte avec DuckDB")
    print("Cas référence attendu : 11 sept 2025 → 37.4 pips ±5")
    print()
    
    con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
    
    # Test sur 11 septembre D'ABORD
    print("🧪 TEST SUR 11 SEPTEMBRE D'ABORD")
    print("-" * 80)
    
    sept11_event = con.execute("""
        SELECT ts_utc, event_key, country, surprise_pct
        FROM event_impacts_v2
        WHERE ts_utc::DATE = '2025-09-11'
        AND country = 'US'
        AND event_key = 'inflation rate_mom'
    """).fetchone()
    
    if sept11_event:
        print(f"Événement : {sept11_event[1]} ({sept11_event[2]})")
        print(f"Timestamp : {sept11_event[0]}")
        print(f"Surprise : {sept11_event[3]:.1f}%")
        print()
        
        result = calculate_phase1_for_event(con, sept11_event[0], "11sept")
        
        if result:
            print(f"Phase 1 : {result['phase1_pips']:.2f} pips")
            print(f"TTR : {result['ttr_minutes']} minutes")
            print(f"Direction : {result['direction']}")
            print(f"Prix départ : {result['start_price']:.5f}")
            print()
            
            expected = 37.4
            tolerance = 5.0
            
            if abs(result['phase1_pips'] - expected) <= tolerance:
                print(f"✅ VALIDATION OK : {result['phase1_pips']:.2f} pips (attendu {expected} ±{tolerance})")
                print(f"   Écart : {abs(result['phase1_pips'] - expected):.2f} pips")
                print()
                print("✅ Script corrigé fonctionne ! Continuons avec tous les événements...")
            else:
                print(f"❌ VALIDATION ÉCHOUÉE : {result['phase1_pips']:.2f} pips (attendu {expected} ±{tolerance})")
                print(f"   Écart : {abs(result['phase1_pips'] - expected):.2f} pips")
                print()
                print("❌ STOP - Le script doit être corrigé davantage")
                con.close()
                return
        else:
            print("❌ Échec calcul 11 septembre")
            con.close()
            return
    
    # Si validation OK, continuer avec tous
    print("\n" + "=" * 80)
    print("📊 RECALCUL TOUS LES ÉVÉNEMENTS")
    print("=" * 80)
    
    events = con.execute("""
        SELECT ts_utc, event_key, country, surprise_pct
        FROM event_impacts_v2
        ORDER BY ts_utc
    """).df()
    
    total = len(events)
    print(f"\n✅ {total:,} événements à recalculer")
    print("   (Cela prendra 2-3 minutes)")
    print()
    
    success_count = 0
    error_count = 0
    last_pct = 0
    
    for idx, event in events.iterrows():
        pct = int((idx + 1) / total * 100)
        if pct >= last_pct + 10:
            print(f"   {pct}% ... ({idx+1:,}/{total:,})")
            last_pct = pct
        
        result = calculate_phase1_for_event(con, event['ts_utc'], idx)
        
        if result is None:
            error_count += 1
            continue
        
        try:
            update_query = f"""
            UPDATE event_impacts_v2
            SET 
                phase1_pips = {result['phase1_pips']},
                ttr_minutes = {result['ttr_minutes']},
                direction = '{result['direction']}',
                start_price = {result['start_price']},
                ttr_price = {result['ttr_price']}
            WHERE ts_utc = '{event['ts_utc']}'
            """
            con.execute(update_query)
            success_count += 1
            
        except Exception as e:
            error_count += 1
    
    print(f"\n   100% ... ({total:,}/{total:,})")
    print()
    print(f"✅ Terminé : {success_count:,} succès, {error_count:,} erreurs")
    print(f"   Taux succès : {100*success_count/total:.1f}%")
    
    # Statistiques
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES FINALES")
    print("=" * 80)
    
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(phase1_pips) as with_phase1,
            MIN(phase1_pips) as min_phase1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY phase1_pips) as median,
            MAX(phase1_pips) as max_phase1,
            AVG(phase1_pips) as avg_phase1
        FROM event_impacts_v2
    """).fetchone()
    
    print(f"\nTotal : {stats[0]:,}")
    print(f"Avec Phase 1 : {stats[1]:,} ({100*stats[1]/stats[0]:.1f}%)")
    print(f"\nDistribution :")
    print(f"  Min : {stats[2]:.2f} pips")
    print(f"  Médiane : {stats[3]:.2f} pips")
    print(f"  Max : {stats[4]:.2f} pips")
    print(f"  Moyenne : {stats[5]:.2f} pips")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("✅ CALCUL PHASE 1 TERMINÉ AVEC TIMEZONE CORRIGÉ")
    print("=" * 80)

if __name__ == "__main__":
    main()
