#!/usr/bin/env python3
"""
Diagnostic TTR pour le 11 septembre 2025
Analyse les 2 phases détectées et compare avec la timeline attendue
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path

def fetch_minute_prices(db_path, start_time, duration_minutes=60):
    """Récupère les prix minute par minute"""
    conn = duckdb.connect(db_path, read_only=True)
    
    # Convertir en epoch
    if hasattr(start_time, 'tz') and start_time.tz is not None:
        start_time = start_time.tz_convert('UTC').tz_localize(None)
    
    start_epoch = int(start_time.timestamp())
    end_epoch = start_epoch + (duration_minutes * 60)
    
    query = f"""
    SELECT timestamp, close as price
    FROM prices_1m
    WHERE timestamp >= {start_epoch} AND timestamp <= {end_epoch}
    ORDER BY timestamp ASC
    """
    
    try:
        prices = conn.execute(query).fetchall()
        conn.close()
        
        if len(prices) > 0:
            times = [datetime.fromtimestamp(r[0]) for r in prices]
            values = [r[1] for r in prices]
            return pd.DataFrame({'time': times, 'price': values})
        return None
    except Exception as e:
        conn.close()
        print(f"❌ Erreur récupération prix: {e}")
        return None


def analyze_phase(prices_df, event_time, direction, retracement_threshold=0.30, phase_name="Phase"):
    """
    Analyse détaillée d'une phase
    """
    
    print(f"\n{'=' * 80}")
    print(f"🔍 ANALYSE {phase_name.upper()}")
    print(f"{'=' * 80}")
    
    if prices_df is None or len(prices_df) == 0:
        print("❌ Pas de données de prix")
        return None
    
    # Prix de référence
    ref_price = prices_df.iloc[0]['price']
    print(f"\n📊 Prix de référence (T0 = {event_time.strftime('%H:%M:%S')}) : {ref_price:.5f}")
    print(f"🎯 Direction attendue : {direction}")
    print(f"📐 Seuil de retracement : {retracement_threshold * 100:.0f}% du mouvement")
    
    # Trouver le peak
    if direction == 'DOWN':
        peak_idx = prices_df['price'].idxmin()
        peak_type = "MINIMUM"
    else:
        peak_idx = prices_df['price'].idxmax()
        peak_type = "MAXIMUM"
    
    peak_price = prices_df.loc[peak_idx, 'price']
    peak_time = prices_df.loc[peak_idx, 'time']
    movement_pips = abs((peak_price - ref_price) * 10000)
    
    peak_minutes = peak_idx
    
    print(f"\n🎯 PEAK DÉTECTÉ ({peak_type}) :")
    print(f"   Temps      : {peak_time.strftime('%H:%M:%S')} (T+{peak_minutes} min)")
    print(f"   Prix       : {peak_price:.5f}")
    print(f"   Mouvement  : {movement_pips:.1f} pips")
    
    # Tableau minute par minute
    print(f"\n📊 MOUVEMENT MINUTE PAR MINUTE :")
    print("-" * 80)
    print(f"{'Temps':<12} {'Prix':<12} {'Δ pips':<12} {'Note':<30}")
    print("-" * 80)
    
    for i in range(min(20, len(prices_df))):  # Afficher 20 premières minutes
        row = prices_df.iloc[i]
        delta = (row['price'] - ref_price) * 10000
        
        note = ""
        if i == 0:
            note = "← T0 (Référence)"
        elif i == peak_minutes:
            note = "← PEAK ATTEINT"
        elif abs(delta) >= 3 and i <= 10:
            note = "← Mouvement significatif"
        
        print(f"{row['time'].strftime('%H:%M:%S'):<12} {row['price']:.5f}    {delta:+8.1f}    {note}")
    
    # Chercher le retracement
    print(f"\n🔄 RECHERCHE DU RETRACEMENT :")
    print("-" * 80)
    print(f"{'Temps':<12} {'Prix':<12} {'Δ peak':<12} {'% retrace':<12} {'Status':<20}")
    print("-" * 80)
    
    retracement_found = False
    ttr_minutes = None
    
    if peak_idx < len(prices_df) - 1:
        after_peak = prices_df.iloc[peak_idx + 1:]
        
        for i, row in after_peak.iterrows():
            current_price = row['price']
            
            if direction == 'DOWN':
                retracement_pips = (current_price - peak_price) * 10000
            else:
                retracement_pips = (peak_price - current_price) * 10000
            
            retracement_pct = (retracement_pips / movement_pips * 100) if movement_pips > 0 else 0
            
            status = ""
            if retracement_pips > movement_pips * retracement_threshold:
                status = "✅ RETRACEMENT DÉTECTÉ"
                retracement_found = True
                ttr_minutes = i
            elif retracement_pips > 0:
                status = f"⚠️ En cours ({retracement_pct:.1f}%)"
            
            # Afficher seulement après le peak et jusqu'au retracement
            if i >= peak_idx:
                print(f"{row['time'].strftime('%H:%M:%S'):<12} {row['price']:.5f}    {retracement_pips:+8.1f}    {retracement_pct:+8.1f}%    {status}")
            
            if retracement_found:
                break
            
            # Limiter affichage
            if i - peak_idx > 15:
                print("...")
                break
    
    # Résultat
    print("\n" + "=" * 80)
    print("📊 RÉSULTAT :")
    print("=" * 80)
    
    if retracement_found:
        print(f"✅ TTR détecté : {ttr_minutes} minutes")
        print(f"   Peak à        : T+{peak_minutes} min")
        print(f"   Retracement à : T+{ttr_minutes} min")
    else:
        print(f"❌ Pas de retracement > {retracement_threshold * 100:.0f}%")
        print(f"   Peak à        : T+{peak_minutes} min")
        print(f"   Mouvement     : {movement_pips:.1f} pips")
        print(f"   💡 Le mouvement est peut-être trop faible pour détecter un retracement significatif")
    
    return {
        'peak_minutes': peak_minutes,
        'ttr_minutes': ttr_minutes,
        'movement_pips': movement_pips,
        'retracement_found': retracement_found,
        'peak_price': peak_price
    }


def check_data_availability(db_path, date_str='2025-09-11'):
    """Vérifie la disponibilité des données"""
    conn = duckdb.connect(db_path, read_only=True)
    
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION DISPONIBILITÉ DES DONNÉES")
    print("=" * 80)
    
    # Vérifier événements
    query_events = f"""
    SELECT event_key, ts_utc, country, importance_n
    FROM events
    WHERE DATE(ts_utc) = '{date_str}'
      AND country IN ('US', 'DE', 'EU')
    ORDER BY ts_utc
    """
    
    events = conn.execute(query_events).fetchdf()
    
    print(f"\n📋 Événements trouvés le {date_str} :")
    print("-" * 80)
    for _, evt in events.iterrows():
        print(f"⏰ {evt['ts_utc'].strftime('%H:%M')} - {evt['event_key']} ({evt['country']}) - Importance: {evt['importance_n']}")
    
    # Vérifier prix autour de 14:30
    test_time = datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S")
    test_epoch = int(test_time.timestamp())
    
    query_prices = f"""
    SELECT COUNT(*) as count, MIN(timestamp) as first, MAX(timestamp) as last
    FROM prices_1m
    WHERE timestamp >= {test_epoch} AND timestamp <= {test_epoch + 3600}
    """
    
    prices_info = conn.execute(query_prices).fetchone()
    
    print(f"\n💹 Prix disponibles autour de 14:30 :")
    print("-" * 80)
    if prices_info[0] > 0:
        first_time = datetime.fromtimestamp(prices_info[1])
        last_time = datetime.fromtimestamp(prices_info[2])
        print(f"✅ {prices_info[0]} minutes de données")
        print(f"   De {first_time.strftime('%H:%M')} à {last_time.strftime('%H:%M')}")
    else:
        print("❌ Aucune donnée de prix trouvée")
    
    conn.close()
    
    return len(events), prices_info[0]


def main():
    print("=" * 80)
    print("🧪 DIAGNOSTIC TTR - 11 septembre 2025")
    print("=" * 80)
    
    db_path = get_db_path()
    
    # 1. Vérifier disponibilité des données
    n_events, n_prices = check_data_availability(db_path, '2025-09-11')
    
    if n_events == 0:
        print("\n❌ Aucun événement trouvé pour cette date")
        return
    
    if n_prices == 0:
        print("\n❌ Aucun prix trouvé - TTR observé impossible à calculer")
        return
    
    print("\n" + "=" * 80)
    print("📊 ANALYSE DES PHASES DÉTECTÉES")
    print("=" * 80)
    
    # 2. Analyser Phase 1 : Jobless + CPI (14:30)
    print("\n" + "🔬" * 40)
    print("PHASE 1 : Jobless Claims + CPI (14:30)")
    print("🔬" * 40)
    
    phase1_time = datetime(2025, 9, 11, 14, 30, 0)
    phase1_prices = fetch_minute_prices(db_path, phase1_time, duration_minutes=20)
    
    if phase1_prices is not None:
        phase1_result = analyze_phase(
            phase1_prices, 
            phase1_time, 
            direction='DOWN',
            retracement_threshold=0.30,
            phase_name="Phase 1"
        )
        
        if phase1_result:
            print(f"\n💡 CONCLUSION PHASE 1 :")
            if phase1_result['retracement_found']:
                print(f"   ✅ TTR réel : {phase1_result['ttr_minutes']} min")
                print(f"   ⚠️ Système affiche : 39 min (ERREUR !)")
                print(f"   📉 Écart : {39 - phase1_result['ttr_minutes']} min")
            else:
                print(f"   ❌ Pas de retracement détecté")
                print(f"   💡 Mouvement trop faible : {phase1_result['movement_pips']:.1f} pips")
    
    # 3. Analyser Phase 2 : Current Account (14:45)
    print("\n" + "🔬" * 40)
    print("PHASE 2 : Current Account DE (14:45)")
    print("🔬" * 40)
    
    phase2_time = datetime(2025, 9, 11, 14, 45, 0)
    phase2_prices = fetch_minute_prices(db_path, phase2_time, duration_minutes=20)
    
    if phase2_prices is not None:
        phase2_result = analyze_phase(
            phase2_prices,
            phase2_time,
            direction='UP',
            retracement_threshold=0.30,
            phase_name="Phase 2"
        )
        
        if phase2_result:
            print(f"\n💡 CONCLUSION PHASE 2 :")
            if phase2_result['retracement_found']:
                print(f"   ✅ TTR réel : {phase2_result['ttr_minutes']} min")
                print(f"   ⚠️ Système affiche : 50 min (ERREUR !)")
                print(f"   📉 Écart : {50 - phase2_result['ttr_minutes']} min")
            else:
                print(f"   ❌ Pas de retracement détecté")
                print(f"   💡 Mouvement trop faible : {phase2_result['movement_pips']:.1f} pips")
    
    # 4. Analyse globale
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC GLOBAL")
    print("=" * 80)
    
    print("\n📋 Ce que la timeline attendait :")
    print("   14:30 → Jobless + CPI (DOWN)")
    print("   14:35 → Retracement (TTR₁ = 5 min) ✅")
    print("   14:45 → Current Account (UP)")
    print("   14:50 → Retracement (TTR₂ = 5 min) ✅")
    
    print("\n❌ Ce que le système calcule :")
    print("   Phase 1 : TTR = 39 min (au lieu de ~5 min)")
    print("   Phase 2 : TTR = 50 min (au lieu de ~5 min)")
    
    print("\n🔍 HYPOTHÈSES SUR LE PROBLÈME :")
    print("   1️⃣ Le mouvement réel est trop faible (< 5-10 pips)")
    print("      → Le seuil de 30% n'est pas atteint")
    print("   2️⃣ Bug dans calculate_real_ttr_for_phase()")
    print("      → Mauvaise fenêtre de prix récupérée")
    print("   3️⃣ Problème de timezone")
    print("      → Décalage entre event_time et prix réels")
    
    print("\n💡 PROCHAINE ÉTAPE :")
    print("   → Tester avec seuils plus bas (15%, 20%)")
    print("   → Vérifier le code de calculate_real_ttr_for_phase()")
    print("   → Comparer avec le cas 2024/09/11 qui fonctionne")
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    main()
