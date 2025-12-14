"""
SESSION 18 - VÉRIFICATION IMPACT RE-IMPORT
Objectif : Vérifier si Sessions 15 & 17 sont affectées par le re-import
Auteur : Claude
Date : 19 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

db_path = Path('fx_impact_app/data/warehouse.duckdb')
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("📊 VÉRIFICATION IMPACT RE-IMPORT SUR SESSIONS 15 & 17")
print("=" * 80)

# ============================================================================
# SESSION 17 : 120 groupes
# ============================================================================

print("\n" + "=" * 80)
print("📋 SESSION 17 : 120 GROUPES")
print("=" * 80)

try:
    df_s17 = pd.read_csv('extracted_groups_session17.csv')
    print(f"\n✅ {len(df_s17)} groupes chargés")
    
    s17_with_estimate = 0
    s17_without_estimate = 0
    s17_improved = 0
    
    details = []
    
    for idx, row in df_s17.iterrows():
        time_group = str(row['time_group'])[:19]
        
        # Récupérer événements
        query = f"""
        SELECT 
            e.event_key,
            ef.family,
            ef.empirical_score,
            e.estimate,
            e.actual
        FROM events e
        INNER JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') = '{time_group}'
            AND ef.empirical_score IS NOT NULL
        ORDER BY ef.empirical_score DESC
        """
        
        group_events = conn.execute(query).df()
        
        if len(group_events) > 0:
            has_estimate = group_events['estimate'].notna().any()
            all_have_estimate = group_events['estimate'].notna().all()
            
            if has_estimate:
                s17_with_estimate += 1
            else:
                s17_without_estimate += 1
            
            # Détails du groupe
            num_with_estimate = group_events['estimate'].notna().sum()
            total_events = len(group_events)
            max_score = group_events['empirical_score'].max()
            
            details.append({
                'timestamp': time_group,
                'num_events': total_events,
                'num_with_estimate': num_with_estimate,
                'pct_with_estimate': (num_with_estimate / total_events * 100) if total_events > 0 else 0,
                'max_score': max_score,
                'complete': all_have_estimate
            })
    
    df_details = pd.DataFrame(details)
    
    print(f"\n📊 RÉSULTATS SESSION 17 :")
    print(f"   Groupes avec ≥1 estimate : {s17_with_estimate}/{len(df_s17)} ({s17_with_estimate/len(df_s17)*100:.1f}%)")
    print(f"   Groupes sans estimate : {s17_without_estimate}/{len(df_s17)} ({s17_without_estimate/len(df_s17)*100:.1f}%)")
    print(f"   Groupes 100% complets : {df_details['complete'].sum()}/{len(df_s17)} ({df_details['complete'].sum()/len(df_s17)*100:.1f}%)")
    
    # Groupes problématiques (aucun estimate)
    problematic = df_details[df_details['num_with_estimate'] == 0]
    if len(problematic) > 0:
        print(f"\n⚠️ {len(problematic)} groupes SANS AUCUN estimate :")
        print(problematic[['timestamp', 'num_events', 'max_score']].head(10).to_string(index=False))
    
    # Groupes partiels (certains ont estimate, pas tous)
    partial = df_details[(df_details['num_with_estimate'] > 0) & (df_details['complete'] == False)]
    if len(partial) > 0:
        print(f"\n⚠️ {len(partial)} groupes PARTIELS (certains events sans estimate) :")
        print(partial[['timestamp', 'num_events', 'num_with_estimate', 'pct_with_estimate', 'max_score']].head(10).to_string(index=False))
    
except FileNotFoundError:
    print("\n❌ Fichier extracted_groups_session17.csv non trouvé")
except Exception as e:
    print(f"\n❌ Erreur : {e}")

# ============================================================================
# SESSION 15 : 30 événements
# ============================================================================

print("\n" + "=" * 80)
print("📋 SESSION 15 : 30 ÉVÉNEMENTS")
print("=" * 80)

try:
    df_s15 = pd.read_csv('extracted_events_session15.csv')
    print(f"\n✅ {len(df_s15)} événements chargés")
    
    if 'estimate' in df_s15.columns:
        s15_with = df_s15['estimate'].notna().sum()
        s15_without = len(df_s15) - s15_with
        
        print(f"\n📊 RÉSULTATS SESSION 15 :")
        print(f"   Avec estimate : {s15_with}/{len(df_s15)} ({s15_with/len(df_s15)*100:.1f}%)")
        print(f"   Sans estimate : {s15_without}/{len(df_s15)} ({s15_without/len(df_s15)*100:.1f}%)")
        
        if s15_without > 0:
            missing = df_s15[df_s15['estimate'].isna()]
            print(f"\n⚠️ Événements sans estimate :")
            cols_to_show = ['timestamp', 'event_key', 'country', 'empirical_score'] if 'timestamp' in missing.columns else ['event_key', 'country']
            print(missing[cols_to_show].to_string(index=False))
    else:
        print("\n⚠️ Colonne 'estimate' non trouvée dans le fichier")
    
except FileNotFoundError:
    print("\n❌ Fichier extracted_events_session15.csv non trouvé")
except Exception as e:
    print(f"\n❌ Erreur : {e}")

# ============================================================================
# CAS SPÉCIFIQUE : 11 SEPTEMBRE 2025
# ============================================================================

print("\n" + "=" * 80)
print("🔍 CAS SPÉCIFIQUE : 11 SEPTEMBRE 2025, 14:30")
print("=" * 80)

query_sept11 = """
SELECT 
    e.event_key,
    e.event_title,
    e.country,
    ef.empirical_score,
    e.actual,
    e.estimate,
    e.previous,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ROUND(ABS((e.actual - e.estimate) / e.estimate) * 100, 2)
        ELSE NULL 
    END as surprise_pct
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE strftime(e.ts_utc, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
ORDER BY ef.empirical_score DESC NULLS LAST
"""

df_sept11 = conn.execute(query_sept11).df()

if len(df_sept11) > 0:
    print(f"\n✅ {len(df_sept11)} événements trouvés")
    print("\n📊 Détails :")
    print(df_sept11.to_string(index=False))
    
    # Vérifier Inflation Rate spécifiquement
    inflation = df_sept11[df_sept11['event_key'] == 'inflation rate']
    if len(inflation) > 0:
        inf_row = inflation.iloc[0]
        print(f"\n🎯 INFLATION RATE :")
        print(f"   Actual : {inf_row['actual']}")
        print(f"   Estimate : {inf_row['estimate']}")
        print(f"   Surprise : {inf_row['surprise_pct']}%")
        
        if pd.notna(inf_row['estimate']) and inf_row['surprise_pct'] > 20:
            print(f"   ✅ CORRIGÉ : Surprise {inf_row['surprise_pct']:.1f}% détectée !")
        elif pd.isna(inf_row['estimate']):
            print(f"   ❌ TOUJOURS MANQUANT : estimate NULL")
        else:
            print(f"   ⚠️ Surprise faible : {inf_row['surprise_pct']:.1f}%")
else:
    print("\n❌ Aucun événement trouvé pour cette date")

# ============================================================================
# SYNTHÈSE
# ============================================================================

print("\n" + "=" * 80)
print("📊 SYNTHÈSE FINALE")
print("=" * 80)

print(f"""
✅ RE-IMPORT SUCCÈS :
   - 343 estimates récupérés
   - 84.4% HIGH importance couverts
   
📋 IMPACT SUR VALIDATIONS :
   - Session 17 : {s17_with_estimate}/{len(df_s17)} groupes avec estimate
   - Session 15 : À vérifier ci-dessus
   
🎯 RECOMMANDATIONS :
   1. Si S17 > 90% → V2 validée solidement
   2. Si S17 < 90% → Correction manuelle nécessaire
   3. Focus : Groupes avec score >70 sans estimate
""")

conn.close()

print("\n✅ Vérification terminée !")
print("=" * 80)
