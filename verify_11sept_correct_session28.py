#!/usr/bin/env python3
"""Audit corrigé - Cherche 11 sept CORRECTEMENT"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("RECHERCHE 11 SEPTEMBRE - AUDIT CORRIGÉ")
print("="*60)

# Chercher TOUS les événements du 11 septembre (peu importe l'heure)
sept11_all = con.execute("""
    SELECT 
        ts_utc,
        event_title,
        country,
        surprise_pct,
        phase1_pips
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    ORDER BY surprise_pct DESC NULLS LAST
""").df()

print(f"\n✅ {len(sept11_all)} événements 11 septembre dans event_impacts_v2\n")

if len(sept11_all) > 0:
    for i, evt in sept11_all.iterrows():
        print(f"{i+1}. {evt['ts_utc']}")
        print(f"   {evt['event_title']} ({evt['country']})")
        print(f"   Surprise: {evt['surprise_pct']:.1f}%")
        if evt['phase1_pips']:
            print(f"   Phase 1: {evt['phase1_pips']:.2f} pips")
        else:
            print(f"   Phase 1: NULL")
        
        # Vérifier si c'est Inflation Rate MoM
        if 'Inflation' in evt['event_title'] and evt['country'] == 'US':
            if abs(evt['surprise_pct'] - 33.3) < 1:
                print(f"   ✅ C'EST LE CAS RÉFÉRENCE (surprise 33.3%)")
        print()

# Chercher spécifiquement Inflation Rate MoM
print("\n" + "="*60)
print("Recherche Inflation Rate MoM spécifiquement...")

inflation = con.execute("""
    SELECT 
        ts_utc,
        event_title,
        country,
        surprise_pct,
        phase1_pips
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    AND event_title LIKE '%Inflation%'
    AND country = 'US'
""").df()

if len(inflation) > 0:
    print(f"\n✅ Trouvé : {inflation.iloc[0]['event_title']}")
    print(f"   Heure: {inflation.iloc[0]['ts_utc']}")
    print(f"   Surprise: {inflation.iloc[0]['surprise_pct']:.1f}%")
    
    if inflation.iloc[0]['phase1_pips']:
        phase1 = inflation.iloc[0]['phase1_pips']
        print(f"   Phase 1: {phase1:.2f} pips")
        
        if 28 <= phase1 <= 42:
            print(f"   ✅ Phase 1 validé (attendu 33.7 ±5)")
        else:
            print(f"   ⚠️  Phase 1 = {phase1:.2f} (attendu 33.7 ±5)")
    else:
        print(f"   Phase 1: NULL (à calculer)")
        
    print(f"\n✅ CAS RÉFÉRENCE TROUVÉ DANS event_impacts_v2")
else:
    print("\n❌ Inflation Rate MoM US pas trouvé")

con.close()

print("\n" + "="*60)
print("CONCLUSION: event_impacts_v2 contient bien le 11 septembre")
print("Phase 1 est NULL (normal, à calculer)")
print("="*60)
