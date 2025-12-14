#!/usr/bin/env python3
"""Quick check pour 11 septembre 2025 dans le CSV"""

import pandas as pd

# Charger le CSV
csv_path = 'events_extreme_surprise_dukascopy_session25.csv'
df = pd.read_csv(csv_path)

print("=" * 70)
print("QUICK CHECK - 11 SEPTEMBRE 2025")
print("=" * 70)

# Convertir datetime avec UTC=True pour gérer les timezones mixtes
df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)

# Filtrer septembre 11
sept11 = df[df['ts_utc'].dt.date == pd.to_datetime('2025-09-11').date()]

print(f"\nTotal événements CSV: {len(df):,}")
print(f"Événements 11 septembre 2025: {len(sept11)}")

if len(sept11) > 0:
    print("\n" + "=" * 70)
    print("TOUS LES ÉVÉNEMENTS DU 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    # Trier par heure
    sept11_sorted = sept11.sort_values('ts_utc')
    
    for idx, row in sept11_sorted.iterrows():
        print(f"\n[{row['ts_utc']}]")
        print(f"  Événement: {row['event_title']}")
        print(f"  Pays: {row['country']}")
        print(f"  Surprise: {row['surprise_pct']:.1f}%")
        print(f"  Phase 1: {row['phase1_pips']:.2f} pips")
        print(f"  TTR: {row['ttr_minutes']} min")
        print(f"  Prix: {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        
    # Vérifier 12:30 UTC spécifiquement
    print("\n" + "=" * 70)
    print("RECHERCHE ÉVÉNEMENT À 12:30 UTC (= 14:30 Berne)")
    print("=" * 70)
    
    at_1230 = sept11_sorted[sept11_sorted['ts_utc'].dt.hour == 12]
    
    if len(at_1230) > 0:
        print(f"\n✅ Événements trouvés à 12h UTC: {len(at_1230)}")
        
        for idx, row in at_1230.iterrows():
            time_str = row['ts_utc'].strftime('%H:%M:%S')
            print(f"\n  📅 Heure: {time_str} UTC")
            print(f"  📰 {row['event_title']}")
            print(f"  🎯 Phase 1: {row['phase1_pips']:.2f} pips")
            print(f"  ⏱️  TTR: {row['ttr_minutes']} minutes")
            print(f"  💰 Prix: {row['start_price']:.5f} → {row['ttr_price']:.5f}")
            
            # VALIDATION vs référence MT5
            expected = 37.4
            actual = row['phase1_pips']
            error = abs(actual - expected)
            error_pct = (error / expected) * 100
            
            print(f"\n  ✅ VALIDATION:")
            print(f"     MT5 André (référence):  37.4 pips")
            print(f"     Dukascopy (calculé):    {actual:.2f} pips")
            print(f"     Écart:                  {error:.2f} pips ({error_pct:.1f}%)")
            
            if error <= 5:
                print(f"     Statut: ✅ EXCELLENT (< 5 pips)")
            elif error <= 10:
                print(f"     Statut: ⚠️  ACCEPTABLE (5-10 pips)")
            else:
                print(f"     Statut: ❌ PROBLÈME (> 10 pips)")
                
            # Vérifier aussi les prix
            expected_start = 1.16816
            expected_ttr = 1.17190
            
            diff_start = abs(row['start_price'] - expected_start) * 10000
            diff_ttr = abs(row['ttr_price'] - expected_ttr) * 10000
            
            print(f"\n  📍 VALIDATION PRIX:")
            print(f"     Prix départ attendu: 1.16816")
            print(f"     Prix départ trouvé:  {row['start_price']:.5f}")
            print(f"     Écart: {diff_start:.1f} pips")
            
            print(f"\n     Prix TTR attendu: 1.17190")
            print(f"     Prix TTR trouvé:  {row['ttr_price']:.5f}")
            print(f"     Écart: {diff_ttr:.1f} pips")
    else:
        print("\n❌ AUCUN ÉVÉNEMENT À 12:30 UTC")
        print("\nHeures disponibles le 11 septembre:")
        for h in sept11_sorted['ts_utc'].dt.hour.unique():
            print(f"  - {h}h UTC")
            
else:
    print("\n❌ AUCUN ÉVÉNEMENT TROUVÉ LE 11 SEPTEMBRE")
    
    # Vérifier quelles dates sont disponibles en septembre
    sept_2025 = df[(df['ts_utc'].dt.year == 2025) & (df['ts_utc'].dt.month == 9)]
    
    if len(sept_2025) > 0:
        dates = sept_2025['ts_utc'].dt.date.unique()
        print(f"\nDates disponibles en septembre 2025: {len(dates)} jours")
        print(f"Du {min(dates)} au {max(dates)}")
    else:
        print("\nAucune donnée pour septembre 2025")

print("\n" + "=" * 70)
print("FIN DE LA VÉRIFICATION")
print("=" * 70)
