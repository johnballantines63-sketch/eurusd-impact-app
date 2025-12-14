#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION : Pourquoi surprise = 266.7% au lieu de 500% ?
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_surprise():
    """Investigation sur le calcul de la surprise"""
    
    date_str = '2025-08-01'
    anchor_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION SURPRISE - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(DB_PATH)
    
    # Charger tous les événements du 1er août avec JOIN event_families
    query = """
    SELECT 
        e.event_key,
        e.event_title,
        e.country,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = DATE '2025-08-01'
      AND e.country = 'US'
      AND (ef.empirical_score IS NULL OR ef.empirical_score > 40)
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query).df()
    
    print(f"📊 Événements trouvés : {len(df_events)}")
    print()
    
    # Calculer surprise pour chaque événement
    surprises = []
    
    for _, event in df_events.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        forecast = event.get('forecast')
        previous = event.get('previous')
        
        # Utiliser estimate en priorité, sinon forecast, sinon previous
        reference = estimate if pd.notna(estimate) and estimate != 0 else (
            forecast if pd.notna(forecast) and forecast != 0 else (
                previous if pd.notna(previous) and previous != 0 else None
            )
        )
        
        surprise_pct = 0.0
        if actual is not None and reference is not None and reference != 0:
            surprise_pct = abs(actual - reference) / abs(reference) * 100
        
        surprises.append({
            'event_key': event.get('event_key', 'N/A'),
            'event_title': event.get('event_title', 'N/A')[:50],
            'actual': actual,
            'estimate': estimate,
            'forecast': forecast,
            'previous': previous,
            'reference': reference,
            'surprise_pct': surprise_pct
        })
    
    # Trier par surprise décroissante
    surprises_sorted = sorted(surprises, key=lambda x: x['surprise_pct'], reverse=True)
    
    print("=" * 80)
    print("  SURPRISES CALCULÉES (triées par valeur décroissante)")
    print("=" * 80)
    print()
    
    print(f"{'Event':<40} {'Actual':<12} {'Estimate':<12} {'Surprise':<10}")
    print("-" * 80)
    
    for i, s in enumerate(surprises_sorted[:10]):  # Top 10
        event_name = s['event_title'][:38] if len(s['event_title']) > 38 else s['event_title']
        actual_str = f"{s['actual']:.2f}" if s['actual'] is not None else "N/A"
        estimate_str = f"{s['estimate']:.2f}" if s['estimate'] is not None else "N/A"
        surprise_str = f"{s['surprise_pct']:.1f}%"
        
        print(f"{event_name:<40} {actual_str:<12} {estimate_str:<12} {surprise_str:<10}")
        
        if i == 0:
            print(f"   → TOP SURPRISE : {s['surprise_pct']:.1f}%")
    
    print()
    
    # Surprise maximale
    max_surprise = max([s['surprise_pct'] for s in surprises])
    print(f"📊 Surprise maximale trouvée : {max_surprise:.1f}%")
    print()
    
    # Vérifier Construction Spending (était à 500% dans Session 88)
    construction_events = [s for s in surprises if 'construction' in s['event_title'].lower() or 'spending' in s['event_title'].lower()]
    
    if construction_events:
        print("=" * 80)
        print("  ÉVÉNEMENTS CONSTRUCTION SPENDING")
        print("=" * 80)
        print()
        
        for s in construction_events:
            print(f"   {s['event_title']}")
            print(f"   Actual : {s['actual']}")
            print(f"   Estimate : {s['estimate']}")
            print(f"   Forecast : {s['forecast']}")
            print(f"   Previous : {s['previous']}")
            print(f"   Reference utilisée : {s['reference']}")
            print(f"   Surprise : {s['surprise_pct']:.1f}%")
            print()
    
    # Chercher événement avec surprise ~500%
    events_500 = [s for s in surprises if s['surprise_pct'] > 400]
    
    if events_500:
        print("=" * 80)
        print("  ÉVÉNEMENTS AVEC SURPRISE > 400%")
        print("=" * 80)
        print()
        
        for s in events_500:
            print(f"   {s['event_title']}")
            print(f"   Surprise : {s['surprise_pct']:.1f}%")
            print(f"   Actual : {s['actual']}")
            print(f"   Estimate : {s['estimate']}")
            print()
    
    conn.close()
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    investiguer_surprise()

