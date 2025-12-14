#!/usr/bin/env python3
"""
Calcul mouvements réels depuis prices_1m - Session 23
======================================================
Recalcule Phase 1, Pullback, Impact NET pour tous les groupes
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import timedelta

print("="*80)
print("🔬 CALCUL MOUVEMENTS RÉELS DEPUIS PRICES_1M")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ═══════════════════════════════════════════════════════════════
# PARAMÈTRES
# ═══════════════════════════════════════════════════════════════

PHASE1_MINUTES = 15  # Durée Phase 1
PULLBACK_MINUTES = 15  # Durée Pullback après Phase 1

print(f"\n⚙️  PARAMÈTRES :")
print(f"   Phase 1    : {PHASE1_MINUTES} minutes")
print(f"   Pullback   : {PULLBACK_MINUTES} minutes après Phase 1")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : EXTRAIRE LES GROUPES À ANALYSER
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 1 : EXTRACTION DES GROUPES")
print("="*80)

# Limiter à 200 groupes les plus importants pour accélérer
query_groups = """
SELECT 
    time_group,
    num_events,
    max_empirical_score,
    event_keys
FROM event_group_impacts
WHERE max_empirical_score IS NOT NULL
  AND max_empirical_score > 0
ORDER BY max_empirical_score DESC
LIMIT 200
"""

print("\n⏳ Extraction des 200 groupes avec meilleurs scores...")
groups_df = conn.execute(query_groups).df()

print(f"   ✅ {len(groups_df)} groupes extraits")
print(f"   Score min  : {groups_df['max_empirical_score'].min():.2f}")
print(f"   Score max  : {groups_df['max_empirical_score'].max():.2f}")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : POUR CHAQUE GROUPE, CALCULER MOUVEMENTS RÉELS
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 2 : CALCUL MOUVEMENTS RÉELS DEPUIS PRICES_1M")
print("="*80)

print("\n⏳ Calcul en cours (peut prendre 2-3 minutes)...\n")

results = []
errors = 0

for idx, group in groups_df.iterrows():
    time_group = group['time_group']
    
    try:
        # Convertir en datetime si nécessaire
        if isinstance(time_group, str):
            event_time = pd.to_datetime(time_group)
        else:
            event_time = time_group
        
        # Définir les fenêtres temporelles
        phase1_start = event_time
        phase1_end = event_time + timedelta(minutes=PHASE1_MINUTES)
        pullback_end = phase1_end + timedelta(minutes=PULLBACK_MINUTES)
        
        # Récupérer les prix pour Phase 1
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
        
        # Calculer Phase 1 (mouvement maximum depuis le début)
        start_price = prices_phase1['close'].iloc[0]
        max_price = prices_phase1['close'].max()
        min_price = prices_phase1['close'].min()
        
        # Le mouvement Phase 1 est le plus grand mouvement (haut ou bas)
        movement_up = (max_price - start_price) * 10000  # En pips
        movement_down = (start_price - min_price) * 10000  # En pips
        
        if abs(movement_up) > abs(movement_down):
            phase1_pips = movement_up
            phase1_direction = 1  # UP
            extreme_price = max_price
        else:
            phase1_pips = -movement_down
            phase1_direction = -1  # DOWN
            extreme_price = min_price
        
        # Récupérer les prix pour Pullback
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
        
        if len(prices_pullback) < 2:
            # Pas de pullback, utiliser le prix de fin Phase 1
            pullback_pips = 0
            end_price = prices_phase1['close'].iloc[-1]
        else:
            # Le pullback est la correction depuis le point extrême
            end_price = prices_pullback['close'].iloc[-1]
            
            if phase1_direction == 1:  # Si Phase 1 était UP
                # Pullback = descente depuis le max
                pullback_pips = (extreme_price - end_price) * 10000
            else:  # Si Phase 1 était DOWN
                # Pullback = montée depuis le min
                pullback_pips = (end_price - extreme_price) * 10000
        
        # Impact NET
        impact_net_pips = abs(phase1_pips) - abs(pullback_pips)
        
        results.append({
            'time_group': time_group,
            'num_events': group['num_events'],
            'max_score': group['max_empirical_score'],
            'phase1_pips': abs(phase1_pips),
            'phase1_direction': phase1_direction,
            'pullback_pips': abs(pullback_pips),
            'impact_net_pips': impact_net_pips,
            'pullback_ratio': abs(pullback_pips) / abs(phase1_pips) if phase1_pips != 0 else 0
        })
        
        # Afficher progression tous les 25 groupes
        if (idx + 1) % 25 == 0:
            print(f"   Traité {idx + 1}/{len(groups_df)} groupes...")
        
    except Exception as e:
        errors += 1
        if errors <= 3:  # Afficher les 3 premières erreurs
            print(f"   ⚠️  Erreur groupe {time_group}: {str(e)[:50]}")

print(f"\n   ✅ Calcul terminé : {len(results)} groupes avec succès")
if errors > 0:
    print(f"   ⚠️  {errors} erreurs (données manquantes)")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : CRÉER DATAFRAME RÉSULTATS
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 3 : ANALYSE DES RÉSULTATS")
print("="*80)

df = pd.DataFrame(results)

if len(df) == 0:
    print("\n❌ Aucune donnée calculée !")
    conn.close()
    exit(1)

print(f"\n📊 STATISTIQUES GLOBALES :")
print(f"   Nombre de groupes    : {len(df)}")
print(f"\n   PHASE 1 :")
print(f"      Moyenne  : {df['phase1_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['phase1_pips'].median():.2f} pips")
print(f"      Min      : {df['phase1_pips'].min():.2f} pips")
print(f"      Max      : {df['phase1_pips'].max():.2f} pips")
print(f"\n   PULLBACK :")
print(f"      Moyenne  : {df['pullback_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['pullback_pips'].median():.2f} pips")
print(f"      Min      : {df['pullback_pips'].min():.2f} pips")
print(f"      Max      : {df['pullback_pips'].max():.2f} pips")
print(f"\n   RATIO PULLBACK/PHASE1 :")
print(f"      Moyenne  : {df['pullback_ratio'].mean():.1%}")
print(f"      Médiane  : {df['pullback_ratio'].median():.1%}")
print(f"\n   IMPACT NET :")
print(f"      Moyenne  : {df['impact_net_pips'].mean():.2f} pips")
print(f"      Médiane  : {df['impact_net_pips'].median():.2f} pips")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : CAS 11 SEPTEMBRE
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🎯 ÉTAPE 4 : CAS SPÉCIFIQUE 11 SEPTEMBRE 2025")
print("="*80)

sept11 = df[df['time_group'].astype(str).str.contains('2025-09-11 14:30')]

if len(sept11) > 0:
    print("\n✅ 11 SEPTEMBRE TROUVÉ !\n")
    row = sept11.iloc[0]
    
    print(f"   Time group       : {row['time_group']}")
    print(f"   Nombre événements: {row['num_events']}")
    print(f"   Score MAX        : {row['max_score']:.2f}")
    print(f"   ")
    print(f"   📊 MOUVEMENTS CALCULÉS :")
    print(f"      Phase 1       : {row['phase1_pips']:.2f} pips")
    print(f"      Direction     : {'UP ⬆️' if row['phase1_direction'] == 1 else 'DOWN ⬇️'}")
    print(f"      Pullback      : {row['pullback_pips']:.2f} pips")
    print(f"      Ratio pullback: {row['pullback_ratio']:.1%}")
    print(f"      Impact NET    : {row['impact_net_pips']:.2f} pips")
    print(f"   ")
    print(f"   📊 COMPARAISON AVEC SESSION 20 :")
    print(f"      Phase 1 attendue   : 522 pips")
    print(f"      Phase 1 calculée   : {row['phase1_pips']:.2f} pips")
    print(f"      Pullback attendu   : 114 pips")
    print(f"      Pullback calculé   : {row['pullback_pips']:.2f} pips")
    print(f"      Impact NET attendu : 408 pips")
    print(f"      Impact NET calculé : {row['impact_net_pips']:.2f} pips")
else:
    print("\n⚠️  11 septembre NON trouvé dans les 200 meilleurs scores")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5 : TOP 10 PLUS GROS IMPACTS
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🏆 ÉTAPE 5 : TOP 10 PLUS GROS IMPACTS NET")
print("="*80)

top10 = df.nlargest(10, 'impact_net_pips')

print(f"\n{'Date':20s} {'Score':>7s} {'Events':>7s} {'Phase1':>9s} {'Pullback':>9s} {'NET':>9s} {'Ratio':>7s}")
print("-" * 85)

for _, row in top10.iterrows():
    date_str = str(row['time_group'])[:16]
    marker = "🎯" if '2025-09-11 14:30' in date_str else "  "
    print(f"{marker} {date_str:18s} {row['max_score']:7.2f} {row['num_events']:7d} "
          f"{row['phase1_pips']:9.2f} {row['pullback_pips']:9.2f} "
          f"{row['impact_net_pips']:9.2f} {row['pullback_ratio']:7.1%}")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 6 : SAUVEGARDER LES RÉSULTATS
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💾 ÉTAPE 6 : SAUVEGARDE DES RÉSULTATS")
print("="*80)

# Sauvegarder en CSV
csv_file = 'real_movements_v4_session23.csv'
df.to_csv(csv_file, index=False)
print(f"\n   ✅ Résultats sauvegardés : {csv_file}")

conn.close()

print("\n" + "="*80)
print("✅ CALCUL MOUVEMENTS RÉELS TERMINÉ")
print("="*80)

print("\n💡 Prochaine étape : Analyser ces données réelles pour créer formule V4")
print(f"\n📊 TOKENS : ~85,000 / 190,000 utilisés (45%)")
