"""
SESSION 18 - VÉRIFICATION RÉALITÉ DB
Objectif : Vérifier CE QUI EST VRAIMENT dans la DB pour le 11 septembre
Auteur : Claude
Date : 19 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

db_path = Path('fx_impact_app/data/warehouse.duckdb')
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("🔍 VÉRIFICATION RÉALITÉ DB - 11 SEPTEMBRE 2025")
print("=" * 80)

# Requête exhaustive pour le 11 septembre
query = """
SELECT 
    event_key,
    event_title,
    ts_utc,
    actual,
    estimate,
    previous,
    CASE 
        WHEN estimate IS NOT NULL AND estimate != 0 
        THEN ROUND(ABS((actual - estimate) / estimate) * 100, 2)
        ELSE NULL 
    END as surprise_pct
FROM events
WHERE strftime(ts_utc, '%Y-%m-%d') = '2025-09-11'
    AND country = 'US'
    AND (event_key LIKE '%inflation%' OR event_title LIKE '%Inflation%')
ORDER BY ts_utc, actual DESC
"""

df = conn.execute(query).df()

print(f"\n📊 TOUS LES ÉVÉNEMENTS INFLATION DU 11 SEPTEMBRE :")
print(f"   Nombre total : {len(df)}")
print()
print(df.to_string(index=False))

# Vérifier s'il y a des doublons au même timestamp
if len(df) > 0:
    duplicates = df.groupby('ts_utc').size()
    if (duplicates > 1).any():
        print("\n✅ CONFIRMATION : Il y a bien PLUSIEURS événements à la même heure !")
        for ts, count in duplicates[duplicates > 1].items():
            print(f"   {ts} : {count} événements")
            subset = df[df['ts_utc'] == ts]
            print(subset[['event_key', 'event_title', 'actual', 'estimate', 'surprise_pct']].to_string(index=False))
            print()
    else:
        print("\n⚠️ UN SEUL événement par timestamp")

# Compter les variantes
monthly_like = df[df['actual'] < 1.0]
annual_like = df[df['actual'] >= 1.0]

print(f"\n📊 ANALYSE DES VARIANTES :")
print(f"   Valeurs < 1.0 (probablement monthly) : {len(monthly_like)}")
if len(monthly_like) > 0:
    print(monthly_like[['event_title', 'actual', 'estimate', 'surprise_pct']].to_string(index=False))

print(f"\n   Valeurs >= 1.0 (probablement annual) : {len(annual_like)}")
if len(annual_like) > 0:
    print(annual_like[['event_title', 'actual', 'estimate', 'surprise_pct']].to_string(index=False))

# Vérifier comment le Planificateur les voit
print("\n" + "=" * 80)
print("🔍 SIMULATION : Comment V2 les traite")
print("=" * 80)

if len(df) > 0:
    # Grouper par timestamp (comme le fait le code)
    for ts in df['ts_utc'].unique():
        events_at_ts = df[df['ts_utc'] == ts]
        
        print(f"\n📅 Timestamp : {ts}")
        print(f"   Nombre d'événements : {len(events_at_ts)}")
        
        # Méthode MAX (comme V2)
        if 'surprise_pct' in events_at_ts.columns:
            max_surprise = events_at_ts['surprise_pct'].max()
            event_with_max = events_at_ts[events_at_ts['surprise_pct'] == max_surprise].iloc[0]
            
            print(f"\n   🎯 MÉTHODE MAX (V2 actuelle) :")
            print(f"      Surprise MAX : {max_surprise}%")
            print(f"      Événement utilisé : {event_with_max['event_title']}")
            print(f"      Actual : {event_with_max['actual']}")
            print(f"      Estimate : {event_with_max['estimate']}")
            
            # Est-ce le bon ?
            if max_surprise == 0 and len(events_at_ts) > 1:
                print(f"\n      ⚠️ PROBLÈME : Surprise = 0% mais il y a {len(events_at_ts)} événements !")
                print(f"      Autres événements à ce timestamp :")
                others = events_at_ts[events_at_ts['surprise_pct'] != max_surprise]
                print(others[['event_title', 'surprise_pct']].to_string(index=False))
            elif max_surprise > 20:
                print(f"\n      ✅ BON : Surprise élevée détectée")

conn.close()

print("\n" + "=" * 80)
print("📊 CONCLUSION")
print("=" * 80)
print("""
Si tu vois LES DEUX événements dans le Planificateur :
→ La DB contient bien les deux ✅
→ Le problème est dans COMMENT on les utilise dans le calcul V2

Si tu vois UN SEUL événement :
→ Un seul est dans la DB
→ Problème d'import EODHD

Copie-colle les résultats ci-dessus pour qu'on comprenne !
""")

print("\n✅ Vérification terminée !")
print("=" * 80)
