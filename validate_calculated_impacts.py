#!/usr/bin/env python3
"""
VALIDATION DES IMPACTS CALCULÉS

Script de vérification pour s'assurer que les impacts calculés
sont cohérents et réalistes avant de les utiliser.
"""

import duckdb
import pandas as pd
import numpy as np

def validate_impacts():
    """Valide les impacts calculés"""
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=False)
    
    print("=" * 80)
    print("🔍 VALIDATION DES IMPACTS CALCULÉS")
    print("=" * 80)
    
    # 1. Vérifier que la table existe
    print("\n1️⃣ Vérification existence de la table...")
    
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    
    if 'event_impacts_calculated' not in table_names:
        print("   ❌ Table event_impacts_calculated n'existe pas encore")
        print("   → Lance d'abord : python3 calculate_real_impacts.py")
        return
    
    print("   ✅ Table trouvée")
    
    # 2. Statistiques de base
    print("\n2️⃣ Statistiques de base:")
    
    count = conn.execute("SELECT COUNT(*) FROM event_impacts_calculated").fetchone()[0]
    print(f"   • Nombre total d'impacts : {count}")
    
    stats = conn.execute("""
        SELECT 
            MIN(mfe_pips) as min_mfe,
            MAX(mfe_pips) as max_mfe,
            AVG(mfe_pips) as avg_mfe,
            MIN(mae_pips) as min_mae,
            MAX(mae_pips) as max_mae,
            AVG(mae_pips) as avg_mae,
            AVG(ttr_minutes) as avg_ttr,
            COUNT(*) FILTER (WHERE ttr_minutes IS NOT NULL) as n_with_ttr
        FROM event_impacts_calculated
    """).fetchdf()
    
    print(f"   • MFE : min={stats['min_mfe'][0]:.1f}, max={stats['max_mfe'][0]:.1f}, avg={stats['avg_mfe'][0]:.1f} pips")
    print(f"   • MAE : min={stats['min_mae'][0]:.1f}, max={stats['max_mae'][0]:.1f}, avg={stats['avg_mae'][0]:.1f} pips")
    print(f"   • TTR moyen : {stats['avg_ttr'][0]:.1f} minutes")
    print(f"   • Événements avec TTR : {stats['n_with_ttr'][0]} ({stats['n_with_ttr'][0]/count*100:.1f}%)")
    
    # 3. Vérifier valeurs aberrantes
    print("\n3️⃣ Détection de valeurs aberrantes:")
    
    # MFE > 200 pips serait très inhabituel pour EUR/USD
    high_mfe = conn.execute("""
        SELECT COUNT(*) 
        FROM event_impacts_calculated 
        WHERE mfe_pips > 200
    """).fetchone()[0]
    
    if high_mfe > 0:
        print(f"   ⚠️ {high_mfe} événements avec MFE > 200 pips (inhabituel)")
        examples = conn.execute("""
            SELECT ts_utc, event_title, mfe_pips 
            FROM event_impacts_calculated 
            WHERE mfe_pips > 200 
            LIMIT 5
        """).fetchdf()
        print(examples.to_string(index=False))
    else:
        print(f"   ✅ Aucun MFE > 200 pips")
    
    # MFE < 1 pip serait trop faible
    low_mfe = conn.execute("""
        SELECT COUNT(*) 
        FROM event_impacts_calculated 
        WHERE mfe_pips < 1
    """).fetchone()[0]
    
    if low_mfe > 0:
        print(f"   ⚠️ {low_mfe} événements avec MFE < 1 pip ({low_mfe/count*100:.1f}%)")
    else:
        print(f"   ✅ Aucun MFE < 1 pip")
    
    # 4. Comparaison par niveau d'impact
    print("\n4️⃣ Impacts par niveau d'importance:")
    
    by_level = conn.execute("""
        SELECT 
            impact_level,
            COUNT(*) as n_events,
            AVG(mfe_pips) as avg_mfe,
            MIN(mfe_pips) as min_mfe,
            MAX(mfe_pips) as max_mfe,
            AVG(empirical_score) as avg_score
        FROM event_impacts_calculated
        GROUP BY impact_level
        ORDER BY impact_level
    """).fetchdf()
    
    print(by_level.to_string(index=False))
    
    # Vérifier que HIGH > MEDIUM > LOW
    if len(by_level) == 3:
        high_avg = by_level[by_level['impact_level'] == 'HIGH']['avg_mfe'].values[0]
        medium_avg = by_level[by_level['impact_level'] == 'MEDIUM']['avg_mfe'].values[0]
        low_avg = by_level[by_level['impact_level'] == 'LOW']['avg_mfe'].values[0]
        
        if high_avg > medium_avg > low_avg:
            print("   ✅ Cohérence : HIGH > MEDIUM > LOW")
        else:
            print("   ⚠️ Incohérence dans les niveaux d'impact")
    
    # 5. Test sur 11 septembre 2025
    print("\n5️⃣ Validation sur le 11 septembre 2025:")
    
    sept_11 = conn.execute("""
        SELECT 
            strftime(ts_utc, '%H:%M') as time,
            event_title,
            empirical_score,
            mfe_pips,
            direction
        FROM event_impacts_calculated
        WHERE CAST(ts_utc AS DATE) = '2025-09-11'
            AND strftime(ts_utc, '%H:%M') = '14:30'
        ORDER BY mfe_pips DESC
        LIMIT 10
    """).fetchdf()
    
    if len(sept_11) > 0:
        print(sept_11.to_string(index=False))
        
        max_impact = sept_11['mfe_pips'].max()
        print(f"\n   • Impact MAX à 14:30 : {max_impact:.1f} pips")
        print(f"   • Observation MT5 : 43 pips")
        print(f"   • Écart : {abs(max_impact - 43):.1f} pips")
        
        if abs(max_impact - 43) < 10:
            print("   ✅ Très proche de l'observation MT5 !")
        elif abs(max_impact - 43) < 20:
            print("   ✅ Proche de l'observation MT5")
        else:
            print("   ⚠️ Écart significatif avec MT5")
    else:
        print("   ⚠️ Pas de données pour le 11 septembre 2025 à 14:30")
    
    # 6. Distribution des impacts
    print("\n6️⃣ Distribution des MFE:")
    
    distribution = conn.execute("""
        SELECT 
            CASE 
                WHEN mfe_pips < 10 THEN '0-10 pips'
                WHEN mfe_pips < 20 THEN '10-20 pips'
                WHEN mfe_pips < 30 THEN '20-30 pips'
                WHEN mfe_pips < 50 THEN '30-50 pips'
                ELSE '50+ pips'
            END as range,
            COUNT(*) as n_events,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
        FROM event_impacts_calculated
        GROUP BY range
        ORDER BY range
    """).fetchdf()
    
    print(distribution.to_string(index=False))
    
    # 7. Corrélation score vs MFE
    print("\n7️⃣ Corrélation score empirique vs MFE:")
    
    corr_data = conn.execute("""
        SELECT 
            empirical_score,
            mfe_pips
        FROM event_impacts_calculated
        WHERE empirical_score IS NOT NULL
    """).fetchdf()
    
    if len(corr_data) > 10:
        correlation = corr_data[['empirical_score', 'mfe_pips']].corr().iloc[0, 1]
        print(f"   • Corrélation : {correlation:.3f}")
        
        if correlation > 0.7:
            print("   ✅ Forte corrélation (score prédit bien l'impact)")
        elif correlation > 0.5:
            print("   ✅ Bonne corrélation")
        else:
            print("   ⚠️ Corrélation faible")
    
    # 8. Recommandations
    print("\n" + "=" * 80)
    print("📋 RECOMMANDATIONS")
    print("=" * 80)
    
    issues = []
    
    if high_mfe > count * 0.01:  # Plus de 1% avec MFE > 200
        issues.append("⚠️ Trop d'événements avec MFE très élevé (> 200 pips)")
    
    if low_mfe > count * 0.1:  # Plus de 10% avec MFE < 1
        issues.append("⚠️ Beaucoup d'événements avec MFE très faible (< 1 pip)")
    
    if len(sept_11) > 0 and abs(sept_11['mfe_pips'].max() - 43) > 20:
        issues.append("⚠️ Écart significatif avec observation MT5 du 11 sept")
    
    if len(issues) > 0:
        print("\n🔧 Points à vérifier :")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Suggestions :")
        print("   • Vérifier les données de prix (prices_1m)")
        print("   • Ajuster les paramètres de calcul (lookback/lookforward)")
        print("   • Filtrer les événements avec données incomplètes")
    else:
        print("\n✅ VALIDATION RÉUSSIE")
        print("   Les impacts calculés semblent cohérents et réalistes.")
        print("   Vous pouvez procéder à la ré-entraînement de la formule.")
    
    conn.close()

if __name__ == '__main__':
    validate_impacts()
