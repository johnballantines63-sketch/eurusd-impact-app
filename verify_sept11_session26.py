#!/usr/bin/env python3
"""
Vérification cas référence 11 septembre 2025
Session 26 - Validation des données Dukascopy
"""

import pandas as pd
from datetime import datetime

# Charger le CSV
df = pd.read_csv('events_extreme_surprise_dukascopy_session25.csv')

print("=" * 80)
print("VÉRIFICATION CAS RÉFÉRENCE 11 SEPTEMBRE 2025")
print("=" * 80)
print(f"\nTotal événements dans le CSV: {len(df):,}\n")

# Convertir la colonne ts_utc en datetime
df['ts_utc'] = pd.to_datetime(df['ts_utc'])

# Filtrer sur le 11 septembre 2025
sept11 = df[df['ts_utc'].dt.date == pd.to_datetime('2025-09-11').date()].copy()

print(f"Événements trouvés le 11 septembre 2025: {len(sept11)}")

if len(sept11) == 0:
    print("\n⚠️  AUCUN ÉVÉNEMENT TROUVÉ POUR LE 11 SEPTEMBRE 2025")
    print("\nVérifions les dates disponibles en septembre 2025:")
    
    sept2025 = df[(df['ts_utc'].dt.year == 2025) & (df['ts_utc'].dt.month == 9)]
    dates_sept = sept2025['ts_utc'].dt.date.unique()
    print(f"Dates en septembre 2025: {sorted(dates_sept)}")
    
else:
    print("\n" + "=" * 80)
    print("ÉVÉNEMENTS DU 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Trier par heure
    sept11 = sept11.sort_values('ts_utc')
    
    # Afficher tous les événements
    for idx, row in sept11.iterrows():
        print(f"\n[{row['ts_utc']}]")
        print(f"  Événement: {row['event_title']}")
        print(f"  Country: {row['country']}")
        print(f"  Surprise: {row['surprise_pct']:.1f}%")
        print(f"  Phase 1: {row['phase1_pips']:.2f} pips")
        print(f"  TTR: {row['ttr_minutes']} minutes")
        print(f"  Direction: {row['direction']}")
        print(f"  Prix départ: {row['start_price']:.5f}")
        print(f"  Prix TTR: {row['ttr_price']:.5f}")
    
    # Chercher spécifiquement l'heure 12:30 UTC (14:30 Berne)
    print("\n" + "=" * 80)
    print("RECHERCHE DE L'ÉVÉNEMENT À 12:30 UTC (14:30 Berne)")
    print("=" * 80)
    
    event_1230 = sept11[sept11['ts_utc'].dt.hour == 12]
    event_1230_min30 = sept11[(sept11['ts_utc'].dt.hour == 12) & (sept11['ts_utc'].dt.minute == 30)]
    
    print(f"\nÉvénements à 12h UTC: {len(event_1230)}")
    print(f"Événements à 12:30 UTC: {len(event_1230_min30)}")
    
    if len(event_1230_min30) > 0:
        print("\n🔍 DÉTAIL ÉVÉNEMENTS 12:30 UTC (= 14:30 Berne):")
        for idx, row in event_1230_min30.iterrows():
            print(f"\n  - {row['event_title']}")
            print(f"    Surprise: {row['surprise_pct']:.1f}%")
            print(f"    Phase 1: {row['phase1_pips']:.2f} pips")
            print(f"    TTR: {row['ttr_minutes']} min")
            print(f"    Prix: {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        
        # Validation vs référence
        print("\n" + "=" * 80)
        print("VALIDATION VS RÉFÉRENCE")
        print("=" * 80)
        
        # Prendre le premier événement (ou celui avec le plus grand phase1)
        main_event = event_1230_min30.loc[event_1230_min30['phase1_pips'].idxmax()]
        
        expected_phase1 = 37.4  # Valeur MT5 André
        actual_phase1 = main_event['phase1_pips']
        error_pips = abs(actual_phase1 - expected_phase1)
        error_pct = (error_pips / expected_phase1) * 100
        
        print(f"\n📊 Phase 1:")
        print(f"  Attendu (MT5):  {expected_phase1:.2f} pips")
        print(f"  Trouvé (Duka):  {actual_phase1:.2f} pips")
        print(f"  Écart:          {error_pips:.2f} pips ({error_pct:.1f}%)")
        
        if error_pips <= 5:
            print(f"  ✅ EXCELLENT (< 5 pips)")
        elif error_pips <= 10:
            print(f"  ⚠️  ACCEPTABLE (5-10 pips)")
        else:
            print(f"  ❌ ÉCART TROP IMPORTANT (> 10 pips)")
        
        print(f"\n📍 Prix:")
        print(f"  Attendu départ: 1.16816")
        print(f"  Trouvé départ:  {main_event['start_price']:.5f}")
        print(f"  Attendu TTR:    1.17190")
        print(f"  Trouvé TTR:     {main_event['ttr_price']:.5f}")
        
        expected_start = 1.16816
        actual_start = main_event['start_price']
        diff_start_pips = abs(actual_start - expected_start) * 10000
        
        expected_ttr = 1.17190
        actual_ttr = main_event['ttr_price']
        diff_ttr_pips = abs(actual_ttr - expected_ttr) * 10000
        
        print(f"\n  Écart prix départ: {diff_start_pips:.1f} pips")
        print(f"  Écart prix TTR:    {diff_ttr_pips:.1f} pips")

print("\n" + "=" * 80)
print("FIN DE LA VÉRIFICATION")
print("=" * 80)
