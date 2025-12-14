#!/usr/bin/env python3
"""
VALIDATION DES IMPACTS GROUPÉS

Objectif : Valider que le nouveau calcul groupé est correct
           en comparant avec les mesures manuelles MT5

Validations :
  1. Vérifier 11 septembre 2025
  2. Comparer avec mesures MT5 (111.5 pips)
  3. Comparer avec ancien script (59.2 pips)
  4. Analyser plusieurs dates de référence
"""

import duckdb
import pandas as pd
from datetime import datetime

def validate_sept_11():
    """Valide spécifiquement le 11 septembre 2025"""
    
    print("=" * 80)
    print("🔍 VALIDATION - 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)
    
    # Charger les impacts groupés du 11 septembre
    query = """
    SELECT 
        strftime(time_group, '%H:%M:%S') as time,
        num_events,
        event_titles,
        max_empirical_score,
        range_pips,
        mfe_pips,
        mae_pips,
        direction,
        net_movement_pips,
        reference_price,
        max_price,
        min_price,
        peak_price
    FROM event_group_impacts
    WHERE CAST(time_group AS DATE) = '2025-09-11'
    ORDER BY time_group
    """
    
    df = conn.execute(query).fetchdf()
    
    if len(df) == 0:
        print("❌ Aucune donnée trouvée pour le 11 septembre 2025")
        print("   Assure-toi d'avoir exécuté calculate_grouped_impacts.py d'abord")
        conn.close()
        return
    
    print(f"\n📊 {len(df)} groupes temporels trouvés\n")
    print(df.to_string(index=False))
    
    # Validation spécifique du groupe 14:30
    print("\n" + "=" * 80)
    print("🎯 VALIDATION CRITIQUE - GROUPE 14:30")
    print("=" * 80)
    
    group_1430 = df[df['time'] == '14:30:00']
    
    if len(group_1430) == 0:
        print("❌ Groupe 14:30 non trouvé !")
        conn.close()
        return
    
    row = group_1430.iloc[0]
    
    print(f"\n📋 Données calculées:")
    print(f"   • Nombre d'événements : {row['num_events']}")
    print(f"   • Score max : {row['max_empirical_score']}")
    print(f"   • Range calculé : {row['range_pips']:.2f} pips")
    print(f"   • MFE : {row['mfe_pips']:.2f} pips")
    print(f"   • MAE : {row['mae_pips']:.2f} pips")
    print(f"   • Direction : {row['direction']}")
    print(f"   • Mouvement net : {row['net_movement_pips']:.2f} pips")
    
    print(f"\n📏 Prix observés:")
    print(f"   • Référence (14:25) : {row['reference_price']:.5f}")
    print(f"   • Prix max : {row['max_price']:.5f}")
    print(f"   • Prix min : {row['min_price']:.5f}")
    print(f"   • Prix pic : {row['peak_price']:.5f}")
    
    # Comparaison avec MT5
    print(f"\n📊 Comparaison avec mesures MT5:")
    
    mt5_range = 111.5  # Mesuré manuellement
    mt5_ref = 1.16810
    mt5_low = 1.16075
    mt5_high = 1.17190
    
    print(f"\n   MT5 (mesuré manuellement):")
    print(f"   • Référence : {mt5_ref:.5f}")
    print(f"   • Prix bas : {mt5_low:.5f}")
    print(f"   • Prix haut : {mt5_high:.5f}")
    print(f"   • Range : {mt5_range:.1f} pips")
    
    print(f"\n   Script v8 (nouveau calcul):")
    print(f"   • Référence : {row['reference_price']:.5f}")
    print(f"   • Prix bas : {row['min_price']:.5f}")
    print(f"   • Prix haut : {row['max_price']:.5f}")
    print(f"   • Range : {row['range_pips']:.1f} pips")
    
    # Calcul des écarts
    range_diff = abs(row['range_pips'] - mt5_range)
    range_diff_pct = range_diff / mt5_range * 100
    
    ref_diff = abs(row['reference_price'] - mt5_ref)
    low_diff = abs(row['min_price'] - mt5_low)
    high_diff = abs(row['max_price'] - mt5_high)
    
    print(f"\n   Écarts:")
    print(f"   • Range : {range_diff:.1f} pips ({range_diff_pct:.1f}%)")
    print(f"   • Référence : {ref_diff*10000:.1f} pips")
    print(f"   • Prix bas : {low_diff*10000:.1f} pips")
    print(f"   • Prix haut : {high_diff*10000:.1f} pips")
    
    # Verdict
    print(f"\n   Verdict:")
    if range_diff_pct < 10:
        print(f"   ✅ EXCELLENT ! Écart < 10% avec MT5")
    elif range_diff_pct < 20:
        print(f"   ⚠️ ACCEPTABLE. Écart < 20% avec MT5")
    elif range_diff_pct < 30:
        print(f"   ⚠️ MOYEN. Écart ~{range_diff_pct:.0f}% avec MT5")
    else:
        print(f"   ❌ PROBLÈME. Écart > 30% avec MT5 - à investiguer")
    
    # Comparaison avec ancien script
    print("\n" + "=" * 80)
    print("📊 COMPARAISON AVEC ANCIEN SCRIPT")
    print("=" * 80)
    
    try:
        old_query = """
        SELECT 
            COUNT(*) as num_lignes,
            AVG(mfe_pips) as avg_mfe,
            MIN(mfe_pips) as min_mfe,
            MAX(mfe_pips) as max_mfe
        FROM event_impacts_calculated
        WHERE CAST(ts_utc AS DATE) = '2025-09-11'
            AND strftime(ts_utc, '%H:%M') = '14:30'
        """
        
        old_data = conn.execute(old_query).fetchdf()
        
        if len(old_data) > 0 and old_data['num_lignes'].iloc[0] > 0:
            print(f"\n   Ancien script (calculate_real_impacts.py):")
            print(f"   • Nombre de lignes : {old_data['num_lignes'].iloc[0]:.0f}")
            print(f"   • MFE moyen : {old_data['avg_mfe'].iloc[0]:.1f} pips")
            print(f"   • MFE min : {old_data['min_mfe'].iloc[0]:.1f} pips")
            print(f"   • MFE max : {old_data['max_mfe'].iloc[0]:.1f} pips")
            
            print(f"\n   Nouveau script (calculate_grouped_impacts.py):")
            print(f"   • Nombre de lignes : 1 (groupé)")
            print(f"   • Range : {row['range_pips']:.1f} pips")
            
            print(f"\n   Différence:")
            print(f"   • Ancien : {old_data['num_lignes'].iloc[0]:.0f} lignes dupliquées")
            print(f"   • Nouveau : 1 ligne unique")
            print(f"   • Gain : {(1 - 1/old_data['num_lignes'].iloc[0])*100:.0f}% de réduction")
            
            print(f"\n   Impact mesuré:")
            print(f"   • Ancien : {old_data['avg_mfe'].iloc[0]:.1f} pips (sous-estimé)")
            print(f"   • Nouveau : {row['range_pips']:.1f} pips")
            print(f"   • MT5 : {mt5_range:.1f} pips (référence)")
        else:
            print("\n   ⚠️ Ancien calcul non trouvé (normal si pas encore exécuté)")
    
    except Exception as e:
        print(f"\n   ⚠️ Impossible de comparer avec ancien calcul: {e}")
    
    conn.close()
    
    print("\n" + "=" * 80)


def analyze_distribution():
    """Analyse la distribution des impacts groupés"""
    
    print("\n" + "=" * 80)
    print("📊 ANALYSE DE DISTRIBUTION")
    print("=" * 80)
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)
    
    # Distribution par taille de groupe
    print("\n1️⃣ Distribution par nombre d'événements:")
    
    query = """
    SELECT 
        num_events,
        COUNT(*) as n_groupes,
        AVG(range_pips) as avg_range,
        AVG(mfe_pips) as avg_mfe,
        MAX(range_pips) as max_range
    FROM event_group_impacts
    GROUP BY num_events
    ORDER BY num_events
    """
    
    df = conn.execute(query).fetchdf()
    print(df.to_string(index=False))
    
    # Distribution par direction
    print("\n2️⃣ Distribution par direction:")
    
    query = """
    SELECT 
        direction,
        COUNT(*) as n_groupes,
        AVG(range_pips) as avg_range,
        AVG(mfe_pips) as avg_mfe
    FROM event_group_impacts
    GROUP BY direction
    """
    
    df = conn.execute(query).fetchdf()
    print(df.to_string(index=False))
    
    # Top 10 des plus gros impacts
    print("\n3️⃣ Top 10 des plus gros impacts (range):")
    
    query = """
    SELECT 
        strftime(time_group, '%Y-%m-%d %H:%M') as datetime,
        num_events,
        range_pips,
        mfe_pips,
        direction,
        event_titles
    FROM event_group_impacts
    ORDER BY range_pips DESC
    LIMIT 10
    """
    
    df = conn.execute(query).fetchdf()
    print(df.to_string(index=False))
    
    conn.close()


def check_data_quality():
    """Vérifie la qualité des données"""
    
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION QUALITÉ DES DONNÉES")
    print("=" * 80)
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)
    
    # 1. Vérifier cohérence range = max - min
    print("\n1️⃣ Vérification cohérence range:")
    
    query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN ABS(range_pips - ABS((max_price - min_price)/0.0001)) < 0.1 THEN 1 ELSE 0 END) as coherent,
        SUM(CASE WHEN ABS(range_pips - ABS((max_price - min_price)/0.0001)) >= 0.1 THEN 1 ELSE 0 END) as incoherent
    FROM event_group_impacts
    """
    
    df = conn.execute(query).fetchdf()
    
    total = df['total'].iloc[0]
    coherent = df['coherent'].iloc[0]
    incoherent = df['incoherent'].iloc[0]
    
    print(f"   • Total : {total}")
    print(f"   • Cohérents : {coherent} ({coherent/total*100:.1f}%)")
    print(f"   • Incohérents : {incoherent} ({incoherent/total*100:.1f}%)")
    
    if incoherent == 0:
        print(f"   ✅ Tous les ranges sont cohérents !")
    else:
        print(f"   ⚠️ {incoherent} groupes ont un range incohérent")
    
    # 2. Vérifier valeurs aberrantes
    print("\n2️⃣ Détection de valeurs aberrantes:")
    
    query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN range_pips > 500 THEN 1 ELSE 0 END) as extreme_high,
        SUM(CASE WHEN range_pips < 1 THEN 1 ELSE 0 END) as extreme_low,
        AVG(range_pips) as avg_range,
        MEDIAN(range_pips) as median_range,
        STDDEV(range_pips) as std_range
    FROM event_group_impacts
    """
    
    df = conn.execute(query).fetchdf()
    
    print(f"   • Total : {df['total'].iloc[0]}")
    print(f"   • Ranges > 500 pips : {df['extreme_high'].iloc[0]}")
    print(f"   • Ranges < 1 pip : {df['extreme_low'].iloc[0]}")
    print(f"   • Moyenne : {df['avg_range'].iloc[0]:.1f} pips")
    print(f"   • Médiane : {df['median_range'].iloc[0]:.1f} pips")
    print(f"   • Écart-type : {df['std_range'].iloc[0]:.1f} pips")
    
    # 3. Vérifier TTR
    print("\n3️⃣ Time To Return (TTR):")
    
    query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN ttr_minutes IS NOT NULL THEN 1 ELSE 0 END) as with_ttr,
        SUM(CASE WHEN ttr_minutes IS NULL THEN 1 ELSE 0 END) as without_ttr,
        AVG(ttr_minutes) as avg_ttr,
        MEDIAN(ttr_minutes) as median_ttr
    FROM event_group_impacts
    """
    
    df = conn.execute(query).fetchdf()
    
    total = df['total'].iloc[0]
    with_ttr = df['with_ttr'].iloc[0]
    without_ttr = df['without_ttr'].iloc[0]
    
    print(f"   • Total : {total}")
    print(f"   • Avec TTR : {with_ttr} ({with_ttr/total*100:.1f}%)")
    print(f"   • Sans TTR : {without_ttr} ({without_ttr/total*100:.1f}%)")
    print(f"   • TTR moyen : {df['avg_ttr'].iloc[0]:.1f} min")
    print(f"   • TTR médian : {df['median_ttr'].iloc[0]:.1f} min")
    
    conn.close()


def main():
    """Fonction principale"""
    
    # Validation du 11 septembre
    validate_sept_11()
    
    # Analyse de distribution
    analyze_distribution()
    
    # Vérification qualité
    check_data_quality()
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    main()
