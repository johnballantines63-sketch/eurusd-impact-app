#!/usr/bin/env python3
"""
Calcul mouvements réels pour CAS EXTRÊMES (surprise >30%) - Session 23
=======================================================================
Focus sur les événements avec surprises extrêmes, pas juste scores élevés
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import timedelta

print("="*80)
print("🔬 CALCUL MOUVEMENTS RÉELS - CAS EXTRÊMES (SURPRISE >30%)")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ═══════════════════════════════════════════════════════════════
# PARAMÈTRES
# ═══════════════════════════════════════════════════════════════

PHASE1_MINUTES = 15
PULLBACK_MINUTES = 15
SURPRISE_THRESHOLD = 30.0  # Focus sur surprises >30%

print(f"\n⚙️  PARAMÈTRES :")
print(f"   Phase 1        : {PHASE1_MINUTES} minutes")
print(f"   Pullback       : {PULLBACK_MINUTES} minutes")
print(f"   Seuil surprise : >{SURPRISE_THRESHOLD}%")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : TROUVER TOUS LES GROUPES AVEC SURPRISE >30%
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 1 : IDENTIFICATION GROUPES AVEC SURPRISE >30%")
print("="*80)

# D'abord, calculer les surprises pour tous les événements
print("\n⏳ Calcul des surprises pour tous les événements US...")

query_surprises = """
WITH event_surprises AS (
    SELECT 
        DATE_TRUNC('minute', e.ts_utc) as time_group,
        e.event_key,
        e.actual,
        e.estimate,
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate * 100)
            ELSE 0
        END as surprise_pct
    FROM events e
    WHERE e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
      AND e.country = 'US'
),
group_max_surprise AS (
    SELECT 
        time_group,
        MAX(surprise_pct) as max_surprise_pct,
        COUNT(*) as num_events_with_data
    FROM event_surprises
    GROUP BY time_group
    HAVING MAX(surprise_pct) > 30.0
)
SELECT 
    egi.time_group,
    egi.num_events,
    egi.max_empirical_score,
    egi.event_keys,
    gms.max_surprise_pct,
    gms.num_events_with_data
FROM event_group_impacts egi
INNER JOIN group_max_surprise gms 
    ON egi.time_group = gms.time_group
WHERE egi.max_empirical_score IS NOT NULL
ORDER BY gms.max_surprise_pct DESC
"""

groups_df = conn.execute(query_surprises).df()

print(f"   ✅ {len(groups_df)} groupes avec surprise >30% trouvés")

if len(groups_df) > 0:
    print(f"\n   Distribution surprises :")
    print(f"      Min      : {groups_df['max_surprise_pct'].min():.1f}%")
    print(f"      Moyenne  : {groups_df['max_surprise_pct'].mean():.1f}%")
    print(f"      Médiane  : {groups_df['max_surprise_pct'].median():.1f}%")
    print(f"      Max      : {groups_df['max_surprise_pct'].max():.1f}%")
    
    print(f"\n   Distribution scores :")
    print(f"      Min      : {groups_df['max_empirical_score'].min():.2f}")
    print(f"      Moyenne  : {groups_df['max_empirical_score'].mean():.2f}")
    print(f"      Médiane  : {groups_df['max_empirical_score'].median():.2f}")
    print(f"      Max      : {groups_df['max_empirical_score'].max():.2f}")
    
    # Vérifier si 11 septembre est dedans
    sept11_check = groups_df[groups_df['time_group'].astype(str).str.contains('2025-09-11 14:30')]
    if len(sept11_check) > 0:
        print(f"\n   ✅ 11 SEPTEMBRE 2025 14:30 TROUVÉ !")
        print(f"      Surprise : {sept11_check.iloc[0]['max_surprise_pct']:.1f}%")
        print(f"      Score    : {sept11_check.iloc[0]['max_empirical_score']:.2f}")
    else:
        print(f"\n   ⚠️  11 septembre 2025 14:30 NON trouvé")
else:
    print(f"\n   ❌ Aucun groupe avec surprise >30% trouvé !")
    conn.close()
    exit(1)

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : CALCULER MOUVEMENTS RÉELS POUR CES GROUPES
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 2 : CALCUL MOUVEMENTS RÉELS")
print("="*80)

print(f"\n⏳ Calcul en cours pour {len(groups_df)} groupes...\n")

results = []
errors = 0

for idx, group in groups_df.iterrows():
    time_group = group['time_group']
    
    try:
        # Convertir en datetime
        if isinstance(time_group, str):
            event_time = pd.to_datetime(time_group)
        else:
            event_time = time_group
        
        # Fenêtres temporelles
        phase1_start = event_time
        phase1_end = event_time + timedelta(minutes=PHASE1_MINUTES)
        pullback_end = phase1_end + timedelta(minutes=PULLBACK_MINUTES)
        
        # Prix Phase 1
        query_phase1 = """
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime >= ? AND datetime <= ?
        ORDER BY datetime
        """
        
        prices_phase1 = conn.execute(query_phase1, [
            event_time.strftime('%Y-%m-%d %H:%M:%S'),
            phase1_end.strftime('%Y-%m-%d %H:%M:%S')
        ]).df()
        
        if len(prices_phase1) < 2:
            errors += 1
            continue
        
        # Calculer Phase 1
        start_price = prices_phase1['close'].iloc[0]
        max_price = prices_phase1['close'].max()
        min_price = prices_phase1['close'].min()
        
        movement_up = (max_price - start_price) * 10000
        movement_down = (start_price - min_price) * 10000
        
        if abs(movement_up) > abs(movement_down):
            phase1_pips = movement_up
            phase1_direction = 1
            extreme_price = max_price
        else:
            phase1_pips = -movement_down
            phase1_direction = -1
            extreme_price = min_price
        
        # Prix Pullback
        query_pullback = """
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime > ? AND datetime <= ?
        ORDER BY datetime
        """
        
        prices_pullback = conn.execute(query_pullback, [
            phase1_end.strftime('%Y-%m-%d %H:%M:%S'),
            pullback_end.strftime('%Y-%m-%d %H:%M:%S')
        ]).df()
        
        if len(prices_pullback) < 1:
            pullback_pips = 0
            end_price = prices_phase1['close'].iloc[-1]
        else:
            end_price = prices_pullback['close'].iloc[-1]
            
            if phase1_direction == 1:
                pullback_pips = (extreme_price - end_price) * 10000
            else:
                pullback_pips = (end_price - extreme_price) * 10000
        
        # Impact NET
        impact_net_pips = abs(phase1_pips) - abs(pullback_pips)
        
        results.append({
            'time_group': time_group,
            'num_events': group['num_events'],
            'max_score': group['max_empirical_score'],
            'max_surprise': group['max_surprise_pct'],
            'phase1_pips': abs(phase1_pips),
            'phase1_direction': phase1_direction,
            'pullback_pips': abs(pullback_pips),
            'impact_net_pips': impact_net_pips,
            'pullback_ratio': abs(pullback_pips) / abs(phase1_pips) if phase1_pips != 0 else 0
        })
        
        if (idx + 1) % 10 == 0:
            print(f"   Traité {idx + 1}/{len(groups_df)} groupes...")
        
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"   ⚠️  Erreur {time_group}: {str(e)[:60]}")

print(f"\n   ✅ Calcul terminé : {len(results)} groupes analysés")
if errors > 0:
    print(f"   ⚠️  {errors} erreurs")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : ANALYSE DES RÉSULTATS
# ═══════════════════════════════════════════════════════════════

df = pd.DataFrame(results)

if len(df) == 0:
    print("\n❌ Aucune donnée calculée !")
    conn.close()
    exit(1)

print("\n📊 ÉTAPE 3 : STATISTIQUES (CAS EXTRÊMES SURPRISE >30%)")
print("="*80)

print(f"\n   Nombre de groupes : {len(df)}")
print(f"\n   PHASE 1 :")
print(f"      Moyenne  : {df['phase1_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['phase1_pips'].median():.2f} pips")
print(f"      Min      : {df['phase1_pips'].min():.2f} pips")
print(f"      Max      : {df['phase1_pips'].max():.2f} pips")

print(f"\n   PULLBACK :")
print(f"      Moyenne  : {df['pullback_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['pullback_pips'].median():.2f} pips")
print(f"      Ratio moyen : {df['pullback_ratio'].mean():.1%}")

print(f"\n   IMPACT NET :")
print(f"      Moyenne  : {df['impact_net_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['impact_net_pips'].median():.2f} pips")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : CAS 11 SEPTEMBRE
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🎯 ÉTAPE 4 : CAS 11 SEPTEMBRE 2025")
print("="*80)

sept11 = df[df['time_group'].astype(str).str.contains('2025-09-11 14:30')]

if len(sept11) > 0:
    print("\n✅ 11 SEPTEMBRE ANALYSÉ !\n")
    row = sept11.iloc[0]
    
    print(f"   📋 DONNÉES ÉVÉNEMENT :")
    print(f"      Time group    : {row['time_group']}")
    print(f"      Nb événements : {row['num_events']}")
    print(f"      Score MAX     : {row['max_score']:.2f}")
    print(f"      Surprise MAX  : {row['max_surprise']:.1f}%")
    
    print(f"\n   📊 MOUVEMENTS CALCULÉS (depuis prices_1m) :")
    print(f"      Phase 1       : {row['phase1_pips']:.2f} pips")
    print(f"      Direction     : {'UP ⬆️' if row['phase1_direction'] == 1 else 'DOWN ⬇️'}")
    print(f"      Pullback      : {row['pullback_pips']:.2f} pips")
    print(f"      Ratio pullback: {row['pullback_ratio']:.1%}")
    print(f"      Impact NET    : {row['impact_net_pips']:.2f} pips")
    
    print(f"\n   📊 COMPARAISON SESSION 20 (données MT5) :")
    print(f"      {'':20s} {'Session 20':>12s} {'Calculé':>12s} {'Écart':>12s}")
    print(f"      {'-'*60}")
    print(f"      {'Phase 1':20s} {522:12.2f} {row['phase1_pips']:12.2f} {abs(522-row['phase1_pips']):12.2f}")
    print(f"      {'Pullback':20s} {114:12.2f} {row['pullback_pips']:12.2f} {abs(114-row['pullback_pips']):12.2f}")
    print(f"      {'Impact NET':20s} {408:12.2f} {row['impact_net_pips']:12.2f} {abs(408-row['impact_net_pips']):12.2f}")
    
    # Évaluation
    phase1_match = abs(522 - row['phase1_pips']) < 50
    pullback_match = abs(114 - row['pullback_pips']) < 30
    
    print(f"\n   💡 ÉVALUATION :")
    if phase1_match and pullback_match:
        print(f"      ✅ Calcul CORRECT - Données concordent avec Session 20")
    elif phase1_match:
        print(f"      ⚠️  Phase 1 OK mais Pullback différent")
    else:
        print(f"      ❌ Écarts significatifs - Vérifier calcul ou données MT5")
else:
    print("\n❌ 11 septembre NON trouvé !")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5 : TOP 10 CAS EXTRÊMES
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🏆 ÉTAPE 5 : TOP 10 CAS EXTRÊMES PAR IMPACT NET")
print("="*80)

top10 = df.nlargest(10, 'impact_net_pips')

print(f"\n{'Date':20s} {'Score':>7s} {'Surp':>7s} {'Events':>7s} {'Phase1':>9s} {'Pull':>9s} {'NET':>9s}")
print("-" * 85)

for _, row in top10.iterrows():
    date_str = str(row['time_group'])[:16]
    marker = "🎯" if '2025-09-11 14:30' in date_str else "  "
    print(f"{marker} {date_str:18s} {row['max_score']:7.2f} {row['max_surprise']:6.1f}% "
          f"{row['num_events']:7d} {row['phase1_pips']:9.2f} "
          f"{row['pullback_pips']:9.2f} {row['impact_net_pips']:9.2f}")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 6 : SAUVEGARDER
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💾 ÉTAPE 6 : SAUVEGARDE")
print("="*80)

csv_file = 'extreme_cases_surprise30_session23.csv'
df.to_csv(csv_file, index=False)
print(f"\n   ✅ {len(df)} cas sauvegardés : {csv_file}")

conn.close()

print("\n" + "="*80)
print("✅ ANALYSE CAS EXTRÊMES TERMINÉE")
print("="*80)

print("\n📊 TOKENS : ~92,000 / 190,000 utilisés (48%)")
print("\n💡 Prochaine étape : Créer formule V4 basée sur ces cas extrêmes")
