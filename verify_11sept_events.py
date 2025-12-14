"""
Script rapide pour vérifier les événements insérés
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from create_validation_table import get_validation_events_for_date


def verify():
    """Vérifie les événements du 11 septembre"""
    
    print("=" * 70)
    print("🔍 VÉRIFICATION ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    df = get_validation_events_for_date('2025-09-11')
    
    if df.empty:
        print("❌ Aucun événement trouvé")
        return
    
    print(f"\n✅ {len(df)} événement(s) trouvé(s)")
    
    # Grouper par heure
    df['hour'] = df['event_time'].astype(str).str[:5]
    
    for hour in df['hour'].unique():
        hour_events = df[df['hour'] == hour]
        print(f"\n⏰ {hour} UTC ({len(hour_events)} événements)")
        print("─" * 70)
        
        for _, row in hour_events.iterrows():
            surprise_str = f"{row['surprise']:+.2f}" if pd.notna(row['surprise']) else "N/A"
            dir_str = "⬆️ UP" if row['direction'] > 0 else "⬇️ DOWN"
            
            print(f"   • {row['event_key']} ({row['country']})")
            print(f"     Actual: {row['actual']}, Forecast: {row['forecast']}, Surprise: {surprise_str}")
            print(f"     → {row['predicted_pips']:.1f} pips {dir_str}, Score: {row['empirical_score']:.0f}")
    
    # Résumé global
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ GLOBAL")
    print("=" * 70)
    print(f"   Total événements    : {len(df)}")
    print(f"   Événements 12:30 UTC : {len(df[df['hour'] == '12:30'])}")
    print(f"   Événements 12:45 UTC : {len(df[df['hour'] == '12:45'])}")
    print(f"   Impact total prédit  : {df['predicted_pips'].sum():.1f} pips (somme brute)")
    print(f"   UP (direction +1)    : {len(df[df['direction'] > 0])}")
    print(f"   DOWN (direction -1)  : {len(df[df['direction'] < 0])}")
    
    # Calcul somme vectorielle
    print("\n" + "=" * 70)
    print("📊 SOMME VECTORIELLE (12:30 UTC)")
    print("=" * 70)
    
    events_1230 = df[df['hour'] == '12:30']
    
    for _, row in events_1230.iterrows():
        contribution = row['predicted_pips'] * row['direction']
        dir_str = "⬆️" if row['direction'] > 0 else "⬇️"
        print(f"   {row['predicted_pips']:.1f} × {row['direction']:+d} = {contribution:+.1f} pips {dir_str} ({row['event_key']})")
    
    total_vectoriel = sum(events_1230['predicted_pips'] * events_1230['direction'])
    print(f"   {'─' * 66}")
    print(f"   TOTAL VECTORIEL : {total_vectoriel:+.1f} pips")
    print(f"   Direction finale : {'⬆️ UP' if total_vectoriel >= 0 else '⬇️ DOWN'}")
    
    print("\n💡 Mouvement réel observé (MT5) : +56.2 pips")
    print(f"   Écart : {56.2 - abs(total_vectoriel):.1f} pips")


if __name__ == "__main__":
    verify()
