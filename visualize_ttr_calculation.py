#!/usr/bin/env python3
"""
Script de diagnostic pour visualiser le calcul du TTR réel
Montre minute par minute ce qui se passe après l'événement
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
    
    prices = conn.execute(query).fetchall()
    conn.close()
    
    if len(prices) > 0:
        times = [datetime.fromtimestamp(r[0]) for r in prices]
        values = [r[1] for r in prices]
        return pd.DataFrame({'time': times, 'price': values})
    return None


def analyze_ttr_calculation(prices_df, event_time, direction='DOWN', retracement_threshold=0.30):
    """
    Analyse détaillée du calcul TTR
    Reproduit la logique de calculate_real_ttr_for_phase()
    """
    
    print("\n" + "=" * 80)
    print("🔍 ANALYSE DÉTAILLÉE DU CALCUL TTR")
    print("=" * 80)
    
    if prices_df is None or len(prices_df) == 0:
        print("❌ Pas de données de prix")
        return
    
    # Prix de référence
    ref_price = prices_df.iloc[0]['price']
    print(f"\n📊 Prix de référence (T0 = {event_time.strftime('%H:%M:%S')}) : {ref_price:.5f}")
    print(f"🎯 Direction attendue : {direction}")
    print(f"📐 Seuil de retracement : {retracement_threshold * 100:.0f}% du mouvement")
    
    # Trouver le peak
    if direction == 'DOWN':
        peak_idx = prices_df['price'].idxmin()
        peak_type = "MINIMUM (prix le plus bas)"
    else:
        peak_idx = prices_df['price'].idxmax()
        peak_type = "MAXIMUM (prix le plus haut)"
    
    peak_price = prices_df.loc[peak_idx, 'price']
    peak_time = prices_df.loc[peak_idx, 'time']
    movement_pips = abs((peak_price - ref_price) * 10000)
    
    peak_minutes = peak_idx
    
    print(f"\n🎯 PEAK DÉTECTÉ ({peak_type}) :")
    print(f"   Temps      : {peak_time.strftime('%H:%M:%S')} (T+{peak_minutes} min)")
    print(f"   Prix       : {peak_price:.5f}")
    print(f"   Mouvement  : {movement_pips:.1f} pips")
    
    # Tableau minute par minute jusqu'au peak
    print(f"\n📊 MOUVEMENT VERS LE PEAK (minute par minute) :")
    print("-" * 80)
    print(f"{'Temps':<12} {'Prix':<12} {'Δ pips':<12} {'Δ cumul':<12} {'Note':<20}")
    print("-" * 80)
    
    for i in range(min(peak_minutes + 1, len(prices_df))):
        row = prices_df.iloc[i]
        delta = (row['price'] - ref_price) * 10000
        
        note = ""
        if i == 0:
            note = "← T0 (Référence)"
        elif i == peak_minutes:
            note = "← PEAK"
        elif abs(delta) >= 5 and i <= 5:
            note = "← Mouvement significatif"
        
        print(f"{row['time'].strftime('%H:%M:%S'):<12} {row['price']:.5f}    {delta:+8.1f}    {delta:+8.1f}    {note}")
    
    # Chercher le retracement après le peak
    print(f"\n🔄 RECHERCHE DU RETRACEMENT (après le peak) :")
    print("-" * 80)
    print(f"{'Temps':<12} {'Prix':<12} {'Δ peak':<12} {'% retrace':<12} {'Status':<20}")
    print("-" * 80)
    
    retracement_found = False
    ttr_minutes = None
    
    if peak_idx < len(prices_df) - 1:
        after_peak = prices_df.iloc[peak_idx + 1:]
        
        for i, row in after_peak.iterrows():
            current_price = row['price']
            
            # Calculer retracement par rapport au peak
            if direction == 'DOWN':
                retracement_pips = (current_price - peak_price) * 10000  # Remontée
            else:
                retracement_pips = (peak_price - current_price) * 10000  # Descente
            
            retracement_pct = (retracement_pips / movement_pips * 100) if movement_pips > 0 else 0
            
            status = ""
            if retracement_pips > movement_pips * retracement_threshold:
                status = "✅ RETRACEMENT DÉTECTÉ"
                retracement_found = True
                ttr_minutes = i
            elif retracement_pips > 0:
                status = f"⚠️  En cours ({retracement_pct:.0f}%)"
            
            print(f"{row['time'].strftime('%H:%M:%S'):<12} {row['price']:.5f}    {retracement_pips:+8.1f}    {retracement_pct:+8.1f}%    {status}")
            
            if retracement_found:
                break
    
    # Résultat final
    print("\n" + "=" * 80)
    print("📊 RÉSULTAT FINAL :")
    print("=" * 80)
    
    if retracement_found:
        print(f"✅ TTR détecté : {ttr_minutes} minutes")
        print(f"   Peak à        : T+{peak_minutes} min")
        print(f"   Retracement à : T+{ttr_minutes} min")
        print(f"   Durée totale  : {ttr_minutes} min")
    else:
        ttr_minutes = len(prices_df)
        print(f"⚠️  Pas de retracement significatif détecté dans les {len(prices_df)} minutes")
        print(f"   Peak à        : T+{peak_minutes} min")
        print(f"   TTR par défaut: {ttr_minutes} min (fin de fenêtre)")
    
    print("\n💡 INTERPRÉTATION :")
    if peak_minutes <= 6 and ttr_minutes > 15:
        print("   Le peak arrive rapidement (≤6 min) mais le marché met plus de temps")
        print("   à retracer significativement. C'est normal si le mouvement persiste.")
    elif ttr_minutes <= 10:
        print("   TTR court détecté - Mouvement rapide avec retournement rapide.")
    else:
        print("   TTR moyen/long - Le mouvement persiste avant un retracement clair.")
    
    return {
        'peak_minutes': peak_minutes,
        'ttr_minutes': ttr_minutes,
        'movement_pips': movement_pips,
        'retracement_found': retracement_found
    }


def main():
    print("=" * 80)
    print("🧪 DIAGNOSTIC TTR - Événement CPI du 11/09/2024 14:30")
    print("=" * 80)
    
    # Paramètres
    event_time = datetime(2024, 9, 11, 14, 30, 0)
    direction = 'DOWN'
    
    # Récupérer les prix
    print("\n📥 Récupération des prix depuis la base de données...")
    db_path = get_db_path()
    prices_df = fetch_minute_prices(db_path, event_time, duration_minutes=60)
    
    if prices_df is None:
        print("❌ Impossible de récupérer les prix")
        return
    
    print(f"✅ {len(prices_df)} minutes de données récupérées")
    print(f"   Période : {prices_df['time'].min().strftime('%H:%M')} → {prices_df['time'].max().strftime('%H:%M')}")
    
    # Test avec différents seuils
    for threshold in [0.30, 0.20, 0.15]:
        print("\n" + "🔬" * 40)
        print(f"TEST avec seuil de retracement : {threshold * 100:.0f}%")
        print("🔬" * 40)
        
        result = analyze_ttr_calculation(prices_df, event_time, direction, threshold)
        
        print(f"\n📊 Résumé pour seuil {threshold * 100:.0f}% :")
        print(f"   TTR calculé : {result['ttr_minutes']} min")
        print(f"   Peak à      : {result['peak_minutes']} min")
        print(f"   Mouvement   : {result['movement_pips']:.1f} pips")
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 80)
    print("\n💡 Pour comparer avec votre graphique :")
    print("   1. Vérifiez à quelle minute le prix atteint son plus bas")
    print("   2. Vérifiez quand le prix remonte de façon significative")
    print("   3. Comparez avec les résultats ci-dessus")


if __name__ == "__main__":
    main()
