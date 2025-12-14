#!/usr/bin/env python3
"""
CALCUL PHASE 1 pour tous les événements event_impacts_v2
Session 28 - Calcul depuis prices_1m Dukascopy validé
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

def calculate_phase1_for_event(con, event_ts, event_id):
    """
    Calcule Phase 1 pour un événement
    
    Args:
        con: Connexion DuckDB
        event_ts: Timestamp événement (avec timezone)
        event_id: Pour logging
    
    Returns:
        dict avec phase1_pips, ttr_minutes, direction, start_price, ttr_price
        ou None si erreur
    """
    try:
        # Convertir en UTC pur pour requête
        if isinstance(event_ts, str):
            event_dt = pd.to_datetime(event_ts, utc=True)
        else:
            event_dt = event_ts
        
        # Fenêtre : event_time → event_time + 15 min
        start_time = event_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_dt = event_dt + timedelta(minutes=15)
        end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Requête prix (sans timezone dans la requête)
        query = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_1m
        WHERE datetime >= '{start_time}'::timestamp
        AND datetime < '{end_time}'::timestamp
        ORDER BY datetime
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
            # Mouvement UP
            phase1_pips = phase1_up
            direction = 'UP'
            ttr_price = max_high
            # TTR = index de la ligne où high est max
            ttr_idx = prices['high'].idxmax()
            ttr_minutes = ttr_idx + 1  # +1 car index commence à 0
        else:
            # Mouvement DOWN
            phase1_pips = phase1_down
            direction = 'DOWN'
            ttr_price = min_low
            # TTR = index de la ligne où low est min
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
    print("🔄 CALCUL PHASE 1 POUR TOUS LES ÉVÉNEMENTS")
    print("=" * 80)
    print("\nSession 28 - Calcul depuis prices_1m Dukascopy validé")
    print("Cas référence attendu : 11 sept 2025 → 33.7 pips ±5")
    print()
    
    con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
    
    # 1. Récupérer tous les événements
    print("📊 Récupération des événements...")
    
    events = con.execute("""
        SELECT 
            ts_utc,
            event_key,
            country,
            surprise_pct
        FROM event_impacts_v2
        ORDER BY ts_utc
    """).df()
    
    total = len(events)
    print(f"   ✅ {total:,} événements à traiter")
    
    # 2. Calculer Phase 1 pour chaque événement
    print("\n🔄 Calcul Phase 1...")
    print("   (Cela peut prendre 2-3 minutes)")
    print()
    
    success_count = 0
    error_count = 0
    
    # Pour afficher progression
    last_pct = 0
    
    for idx, event in events.iterrows():
        # Progression
        pct = int((idx + 1) / total * 100)
        if pct >= last_pct + 10:
            print(f"   {pct}% ... ({idx+1:,}/{total:,})")
            last_pct = pct
        
        # Calculer Phase 1
        result = calculate_phase1_for_event(con, event['ts_utc'], idx)
        
        if result is None:
            error_count += 1
            continue
        
        # UPDATE dans la base
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
            print(f"   ❌ Erreur UPDATE événement {idx}: {e}")
            error_count += 1
    
    print(f"\n   100% ... ({total:,}/{total:,})")
    print()
    print(f"✅ Terminé : {success_count:,} succès, {error_count:,} erreurs")
    print(f"   Taux succès : {100*success_count/total:.1f}%")
    
    # 3. VALIDATION CAS RÉFÉRENCE 11 SEPTEMBRE
    print("\n" + "=" * 80)
    print("📊 VALIDATION CAS RÉFÉRENCE : 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    sept11 = con.execute("""
        SELECT 
            ts_utc,
            event_key,
            country,
            surprise_pct,
            phase1_pips,
            ttr_minutes,
            direction,
            start_price
        FROM event_impacts_v2
        WHERE ts_utc::DATE = '2025-09-11'
        AND country = 'US'
        AND surprise_pct > 30
        ORDER BY surprise_pct DESC
    """).df()
    
    if len(sept11) == 0:
        print("❌ PROBLÈME : 11 septembre US non trouvé !")
        con.close()
        return
    
    # Afficher le cas référence
    ref = sept11.iloc[0]
    print(f"\n✅ Cas référence trouvé :")
    print(f"   Event : {ref['event_key']} ({ref['country']})")
    print(f"   Heure : {ref['ts_utc']}")
    print(f"   Surprise : {ref['surprise_pct']:.1f}%")
    print()
    print(f"   Phase 1 : {ref['phase1_pips']:.2f} pips")
    print(f"   TTR : {ref['ttr_minutes']} minutes")
    print(f"   Direction : {ref['direction']}")
    print(f"   Prix départ : {ref['start_price']:.5f}")
    print()
    
    # VALIDATION
    phase1 = ref['phase1_pips']
    expected = 33.7
    tolerance = 5.0
    
    if abs(phase1 - expected) <= tolerance:
        print(f"   ✅ VALIDATION OK : {phase1:.2f} pips (attendu {expected} ±{tolerance})")
        print(f"      Écart : {abs(phase1 - expected):.2f} pips")
    else:
        print(f"   ⚠️  ATTENTION : {phase1:.2f} pips (attendu {expected} ±{tolerance})")
        print(f"      Écart : {abs(phase1 - expected):.2f} pips")
        print(f"      Dépasse la tolérance de ±{tolerance} pips")
    
    # 4. Statistiques globales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES GLOBALES")
    print("=" * 80)
    
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(phase1_pips) as with_phase1,
            MIN(phase1_pips) as min_phase1,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY phase1_pips) as q25,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY phase1_pips) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY phase1_pips) as q75,
            MAX(phase1_pips) as max_phase1,
            AVG(phase1_pips) as avg_phase1
        FROM event_impacts_v2
    """).fetchone()
    
    print(f"\nTotal événements : {stats[0]:,}")
    print(f"Avec Phase 1 : {stats[1]:,} ({100*stats[1]/stats[0]:.1f}%)")
    print()
    print(f"Distribution Phase 1 :")
    print(f"  Min : {stats[2]:.2f} pips")
    print(f"  Q25 : {stats[3]:.2f} pips")
    print(f"  Médiane : {stats[4]:.2f} pips")
    print(f"  Q75 : {stats[5]:.2f} pips")
    print(f"  Max : {stats[6]:.2f} pips")
    print(f"  Moyenne : {stats[7]:.2f} pips")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("✅ CALCUL PHASE 1 TERMINÉ")
    print("=" * 80)
    print("\nProchaine étape : Créer formule V4 basée sur ces données empiriques")

if __name__ == "__main__":
    main()
