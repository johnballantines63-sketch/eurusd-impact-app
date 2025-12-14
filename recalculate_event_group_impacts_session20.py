#!/usr/bin/env python3
"""
🔄 RECALCUL COMPLET event_group_impacts - SESSION 20

Objectif : Recalculer event_group_impacts avec les VRAIES données de Session 19 :
- Nouveaux event_key avec suffixes (_mom, _yoy, _qoq)
- Calcul correct des surprises depuis les nouveaux champs
- Intégration comparison, period, change_percentage
- MFE/MAE calculés depuis prices_1m

IMPORTANT : Ce script va :
1. Backup l'ancienne table event_group_impacts
2. Supprimer l'ancienne table
3. Recréer avec les données propres

Date : 19 octobre 2025
Session : 20
Durée estimée : 30-60 minutes
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Connexion DB
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*80)
print("🔄 RECALCUL COMPLET event_group_impacts")
print("="*80)

# ============================================================================
# ÉTAPE 0 : BACKUP DE L'ANCIENNE TABLE
# ============================================================================

print("\n📦 Backup de l'ancienne table...")

# Vérifier si la table existe
try:
    count_old = conn.execute("SELECT COUNT(*) FROM event_group_impacts").fetchone()[0]
    print(f"   - Ancienne table : {count_old} lignes")
    
    # Créer backup
    backup_name = f"event_group_impacts_backup_session20_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM event_group_impacts")
    print(f"   ✅ Backup créé : {backup_name}")
    
    # Supprimer l'ancienne table
    conn.execute("DROP TABLE event_group_impacts")
    print(f"   ✅ Ancienne table supprimée")
    
except Exception as e:
    print(f"   ⚠️ Pas d'ancienne table à sauvegarder : {e}")

# ============================================================================
# ÉTAPE 1 : GROUPER LES ÉVÉNEMENTS PAR MINUTE
# ============================================================================

print("\n📊 Groupement des événements par minute...")

query_events = """
SELECT 
    strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') as time_group,
    e.ts_utc,
    e.country,
    e.event_key,
    e.event_title,
    e.actual,
    e.estimate,
    e.previous,
    e.comparison,
    e.period,
    e.change,
    e.change_percentage,
    e.event_type,
    e.importance_n,
    ef.empirical_score,
    ef.family,
    ef.avg_movement_pips,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ABS((e.actual - e.estimate) / e.estimate)
        WHEN e.change_percentage IS NOT NULL
        THEN ABS(e.change_percentage) / 100.0
        ELSE 0
    END as surprise
FROM events e
LEFT JOIN event_families ef 
    ON REPLACE(REPLACE(REPLACE(e.event_key, '_mom', ''), '_yoy', ''), '_qoq', '') = ef.event_key
    AND e.country = ef.country
WHERE e.actual IS NOT NULL
  AND e.importance_n >= 1
ORDER BY time_group, e.country, e.event_key
"""

print("   - Récupération des événements...")
df_events = conn.execute(query_events).df()
print(f"   ✅ {len(df_events)} événements récupérés")

# Conversion des timestamps en datetime
df_events['time_group'] = pd.to_datetime(df_events['time_group'])
df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])

# ============================================================================
# ÉTAPE 2 : AGRÉGATION PAR GROUPE TEMPOREL
# ============================================================================

print("\n🔢 Agrégation des événements par groupe temporel...")

grouped = df_events.groupby('time_group')

group_stats = []

for time_group, group in grouped:
    stats = {
        'time_group': time_group,
        'num_events': len(group),
        'event_keys': ' + '.join(sorted(set(str(k) for k in group['event_key'] if pd.notna(k)))),
        'event_titles': ' | '.join(sorted(set(str(t)[:50] for t in group['event_title'] if pd.notna(t)))[:3]),
        'countries': ' + '.join(sorted(set(str(c) for c in group['country'] if pd.notna(c)))),
        'families': ' + '.join(sorted(set(str(f) for f in group['family'] if pd.notna(f)))),
        'max_empirical_score': group['empirical_score'].max() if group['empirical_score'].notna().any() else None,
        'mean_empirical_score': group['empirical_score'].mean() if group['empirical_score'].notna().any() else None,
        'max_surprise': group['surprise'].max() if group['surprise'].notna().any() else 0,
        'mean_surprise': group['surprise'].mean() if group['surprise'].notna().any() else 0,
        'impact_levels': ' + '.join(sorted(set(str(il) for il in group['importance_n'] if pd.notna(il)))),
        'max_importance': group['importance_n'].max() if group['importance_n'].notna().any() else 0,
        # Nouveaux champs
        'comparisons': ' + '.join(sorted(set(str(c) for c in group['comparison'] if pd.notna(c)))),
        'periods': ' + '.join(sorted(set(str(p) for p in group['period'] if pd.notna(p)))),
        'event_types': ' + '.join(sorted(set(str(et) for et in group['event_type'] if pd.notna(et)))[:3]),
    }
    group_stats.append(stats)

df_groups = pd.DataFrame(group_stats)

print(f"   ✅ {len(df_groups)} groupes temporels créés")
print(f"   - Période : {df_groups['time_group'].min()} → {df_groups['time_group'].max()}")
print(f"   - Groupes simples (1 evt) : {len(df_groups[df_groups['num_events']==1])}")
print(f"   - Groupes multiples (2+ evt) : {len(df_groups[df_groups['num_events']>1])}")

# ============================================================================
# ÉTAPE 3 : RÉCUPÉRATION DES PRIX
# ============================================================================

print("\n💹 Récupération des prix minute par minute...")

# Période complète à couvrir
min_date = df_groups['time_group'].min() - timedelta(minutes=30)
max_date = df_groups['time_group'].max() + timedelta(hours=2)

query_prices = f"""
SELECT 
    datetime as ts_utc,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '{min_date.strftime('%Y-%m-%d %H:%M:%S')}'
  AND datetime <= '{max_date.strftime('%Y-%m-%d %H:%M:%S')}'
ORDER BY datetime
"""

print(f"   - Période : {min_date} → {max_date}")
df_prices = conn.execute(query_prices).df()
print(f"   ✅ {len(df_prices)} bougies récupérées")

df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'])
df_prices = df_prices.set_index('ts_utc').sort_index()

# ============================================================================
# ÉTAPE 4 : CALCUL DES IMPACTS (MFE, MAE, TTR)
# ============================================================================

print("\n📈 Calcul des impacts pour chaque groupe...")
print("   (Ceci peut prendre 30-60 minutes...)")

def calculate_group_impact(time_group, prices_df, lookforward_window=60):
    """
    Calcule MFE, MAE, TTR pour un groupe d'événements
    
    Args:
        time_group: Timestamp du groupe
        prices_df: DataFrame des prix indexé par timestamp
        lookforward_window: Fenêtre en minutes (60 min par défaut)
    
    Returns:
        dict avec mfe_pips, mae_pips, ttr_minutes, etc.
    """
    try:
        # Trouver le prix de référence (juste avant l'événement)
        ref_time = time_group - timedelta(minutes=1)
        
        # Si pas de prix exact, prendre le plus proche dans les 5 min avant
        if ref_time not in prices_df.index:
            mask = (prices_df.index >= time_group - timedelta(minutes=5)) & (prices_df.index < time_group)
            if mask.any():
                ref_time = prices_df[mask].index[-1]
            else:
                return None
        
        reference_price = prices_df.loc[ref_time, 'close']
        
        # Fenêtre d'observation (60 minutes après l'événement)
        end_time = time_group + timedelta(minutes=lookforward_window)
        
        mask = (prices_df.index >= time_group) & (prices_df.index <= end_time)
        window_prices = prices_df[mask]
        
        if len(window_prices) == 0:
            return None
        
        # Calcul MFE (Maximum Favorable Excursion)
        max_price = window_prices['high'].max()
        min_price = window_prices['low'].min()
        
        mfe_up = (max_price - reference_price) * 10000  # En pips
        mfe_down = (reference_price - min_price) * 10000
        
        if abs(mfe_up) > abs(mfe_down):
            mfe_pips = mfe_up
            direction = 'UP'
            peak_price = max_price
        else:
            mfe_pips = mfe_down
            direction = 'DOWN'
            peak_price = min_price
        
        # MAE (Maximum Adverse Excursion)
        if direction == 'UP':
            mae_pips = mfe_down
        else:
            mae_pips = mfe_up
        
        # Range
        range_pips = (max_price - min_price) * 10000
        
        # TTR (Time To Return) - temps pour atteindre 80% du MFE
        target_80pct = reference_price + (peak_price - reference_price) * 0.8
        
        ttr_minutes = None
        peak_time = None
        
        for idx, row in window_prices.iterrows():
            if direction == 'UP' and row['high'] >= target_80pct:
                ttr_minutes = (idx - time_group).total_seconds() / 60
                break
            elif direction == 'DOWN' and row['low'] <= target_80pct:
                ttr_minutes = (idx - time_group).total_seconds() / 60
                break
        
        # Trouver le temps du pic
        if direction == 'UP':
            peak_idx = window_prices['high'].idxmax()
        else:
            peak_idx = window_prices['low'].idxmin()
        
        peak_time = peak_idx
        
        # Prix final (fin de fenêtre)
        final_price = window_prices.iloc[-1]['close']
        net_movement_pips = (final_price - reference_price) * 10000
        
        return {
            'mfe_pips': abs(mfe_pips),
            'mae_pips': abs(mae_pips),
            'range_pips': range_pips,
            'ttr_minutes': ttr_minutes,
            'direction': direction,
            'net_movement_pips': net_movement_pips,
            'reference_price': reference_price,
            'peak_price': peak_price,
            'peak_time': peak_time,
            'max_price': max_price,
            'min_price': min_price,
            'final_price': final_price,
            'lookforward_window': lookforward_window
        }
        
    except Exception as e:
        print(f"      ⚠️ Erreur pour {time_group}: {e}")
        return None

# Calculer les impacts
impacts_list = []
total_groups = len(df_groups)
start_time = time.time()

for idx, row in df_groups.iterrows():
    if (idx + 1) % 100 == 0:
        elapsed = time.time() - start_time
        progress = (idx + 1) / total_groups * 100
        eta = elapsed / (idx + 1) * (total_groups - idx - 1)
        print(f"   - Progression : {idx+1}/{total_groups} ({progress:.1f}%) - ETA: {eta/60:.1f} min")
    
    time_group = row['time_group']
    impact = calculate_group_impact(time_group, df_prices)
    
    if impact:
        impacts_list.append({
            'time_group': time_group,
            **impact
        })

df_impacts = pd.DataFrame(impacts_list)

print(f"\n   ✅ Impacts calculés : {len(df_impacts)} / {total_groups} groupes ({len(df_impacts)/total_groups*100:.1f}%)")
print(f"   - Temps écoulé : {(time.time() - start_time)/60:.1f} minutes")

# ============================================================================
# ÉTAPE 5 : FUSION DES DONNÉES
# ============================================================================

print("\n🔗 Fusion des groupes avec les impacts...")

df_final = df_groups.merge(df_impacts, on='time_group', how='left')

print(f"   ✅ {len(df_final)} lignes dans la table finale")
print(f"   - Avec impact : {df_final['mfe_pips'].notna().sum()} ({df_final['mfe_pips'].notna().sum()/len(df_final)*100:.1f}%)")

# Ajouter date de calcul
df_final['calculation_date'] = datetime.now()

# ============================================================================
# ÉTAPE 6 : CRÉATION DE LA NOUVELLE TABLE
# ============================================================================

print("\n💾 Création de la nouvelle table event_group_impacts...")

# Créer la table
conn.execute("""
CREATE TABLE event_group_impacts (
    time_group TIMESTAMP WITH TIME ZONE,
    num_events BIGINT,
    event_keys VARCHAR,
    event_titles VARCHAR,
    countries VARCHAR,
    families VARCHAR,
    max_empirical_score DOUBLE,
    mean_empirical_score DOUBLE,
    max_surprise DOUBLE,
    mean_surprise DOUBLE,
    impact_levels VARCHAR,
    max_importance BIGINT,
    comparisons VARCHAR,
    periods VARCHAR,
    event_types VARCHAR,
    mfe_pips DOUBLE,
    mae_pips DOUBLE,
    range_pips DOUBLE,
    ttr_minutes DOUBLE,
    direction VARCHAR,
    net_movement_pips DOUBLE,
    reference_price DOUBLE,
    peak_price DOUBLE,
    peak_time TIMESTAMP WITH TIME ZONE,
    max_price DOUBLE,
    min_price DOUBLE,
    final_price DOUBLE,
    lookforward_window BIGINT,
    calculation_date TIMESTAMP
)
""")

print("   ✅ Structure de table créée")

# Insérer les données
print("   - Insertion des données...")

conn.register('df_final_view', df_final)
conn.execute("""
INSERT INTO event_group_impacts
SELECT * FROM df_final_view
""")

count_inserted = conn.execute("SELECT COUNT(*) FROM event_group_impacts").fetchone()[0]
print(f"   ✅ {count_inserted} lignes insérées")

# ============================================================================
# ÉTAPE 7 : VÉRIFICATIONS ET STATISTIQUES
# ============================================================================

print("\n" + "="*80)
print("📊 STATISTIQUES DE LA NOUVELLE TABLE")
print("="*80)

stats_query = """
SELECT 
    COUNT(*) as total_groups,
    SUM(CASE WHEN mfe_pips IS NOT NULL THEN 1 ELSE 0 END) as groups_with_impact,
    AVG(mfe_pips) as avg_mfe,
    MAX(mfe_pips) as max_mfe,
    AVG(max_surprise) as avg_surprise,
    AVG(max_empirical_score) as avg_score,
    SUM(CASE WHEN num_events = 1 THEN 1 ELSE 0 END) as single_events,
    SUM(CASE WHEN num_events > 1 THEN 1 ELSE 0 END) as multi_events,
    SUM(CASE WHEN comparisons != '' THEN 1 ELSE 0 END) as groups_with_comparison,
    SUM(CASE WHEN periods != '' THEN 1 ELSE 0 END) as groups_with_period
FROM event_group_impacts
"""

stats = conn.execute(stats_query).fetchdf()

print(f"\n📈 Résumé :")
print(f"   - Total groupes : {stats['total_groups'][0]}")
print(f"   - Avec impact calculé : {stats['groups_with_impact'][0]} ({stats['groups_with_impact'][0]/stats['total_groups'][0]*100:.1f}%)")
print(f"   - Impact moyen : {stats['avg_mfe'][0]:.1f} pips")
print(f"   - Impact max : {stats['max_mfe'][0]:.1f} pips")
print(f"   - Surprise moyenne : {stats['avg_surprise'][0]*100:.1f}%")
print(f"   - Score moyen : {stats['avg_score'][0]:.1f}")
print(f"\n📊 Distribution :")
print(f"   - Événements simples : {stats['single_events'][0]}")
print(f"   - Événements multiples : {stats['multi_events'][0]}")
print(f"\n🆕 Nouveaux champs :")
print(f"   - Avec comparison : {stats['groups_with_comparison'][0]} ({stats['groups_with_comparison'][0]/stats['total_groups'][0]*100:.1f}%)")
print(f"   - Avec period : {stats['groups_with_period'][0]} ({stats['groups_with_period'][0]/stats['total_groups'][0]*100:.1f}%)")

# ============================================================================
# ÉTAPE 8 : VALIDATION CAS 11 SEPTEMBRE
# ============================================================================

print("\n" + "="*80)
print("🔍 VALIDATION CAS 11 SEPTEMBRE 2025")
print("="*80)

sept11_query = """
SELECT 
    time_group,
    num_events,
    event_keys,
    max_empirical_score,
    max_surprise,
    comparisons,
    mfe_pips,
    direction
FROM event_group_impacts
WHERE strftime(time_group, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
"""

sept11 = conn.execute(sept11_query).fetchdf()

if len(sept11) > 0:
    print(f"\n✅ Groupe 11 septembre 14:30 trouvé :")
    row = sept11.iloc[0]
    print(f"   - Événements : {row['event_keys']}")
    print(f"   - Nombre : {row['num_events']}")
    print(f"   - Max score : {row['max_empirical_score']:.1f}")
    print(f"   - Max surprise : {row['max_surprise']*100:.1f}%")
    print(f"   - Comparisons : {row['comparisons']}")
    print(f"   - Impact MFE : {row['mfe_pips']:.1f} pips")
    print(f"   - Direction : {row['direction']}")
    
    print(f"\n📊 Comparaison avec graphiques MT5 :")
    print(f"   - DB calcule : {row['mfe_pips']:.1f} pips (fenêtre 60 min)")
    print(f"   - MT5 Phase 1 : 522 pips")
    print(f"   - Ratio : {522 / row['mfe_pips']:.2f}x")
    
    if row['max_surprise'] > 0.25:
        print(f"\n   ✅ Surprise élevée détectée ({row['max_surprise']*100:.0f}%) - Bon !")
    else:
        print(f"\n   ⚠️ Surprise sous-estimée ({row['max_surprise']*100:.0f}% vs 33% attendu)")
else:
    print("   ⚠️ Groupe 11 septembre 14:30 NON TROUVÉ")

# ============================================================================
# ÉTAPE 9 : SAUVEGARDE RAPPORT
# ============================================================================

print("\n💾 Génération du rapport...")

report_lines = [
    "# 📊 RAPPORT RECALCUL event_group_impacts - SESSION 20",
    "",
    f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"**Durée totale :** {(time.time() - start_time)/60:.1f} minutes",
    "",
    "## Statistiques",
    "",
    f"- **Total groupes :** {stats['total_groups'][0]}",
    f"- **Avec impact :** {stats['groups_with_impact'][0]} ({stats['groups_with_impact'][0]/stats['total_groups'][0]*100:.1f}%)",
    f"- **Impact moyen :** {stats['avg_mfe'][0]:.1f} pips",
    f"- **Impact max :** {stats['max_mfe'][0]:.1f} pips",
    f"- **Surprise moyenne :** {stats['avg_surprise'][0]*100:.1f}%",
    "",
    "## Nouveaux champs intégrés",
    "",
    f"- **Comparisons (MoM/YoY) :** {stats['groups_with_comparison'][0]} groupes",
    f"- **Periods :** {stats['groups_with_period'][0]} groupes",
    "",
    "## Validation 11 septembre",
    "",
]

if len(sept11) > 0:
    row = sept11.iloc[0]
    report_lines.extend([
        f"- **Impact calculé :** {row['mfe_pips']:.1f} pips",
        f"- **Surprise :** {row['max_surprise']*100:.1f}%",
        f"- **Comparisons :** {row['comparisons']}",
        f"- **Score :** {row['max_empirical_score']:.1f}",
    ])

report_content = "\n".join(report_lines)

with open('RAPPORT_RECALCUL_EVENT_GROUP_IMPACTS_SESSION20.md', 'w') as f:
    f.write(report_content)

print("   ✅ Rapport sauvegardé : RAPPORT_RECALCUL_EVENT_GROUP_IMPACTS_SESSION20.md")

# ============================================================================
# ÉTAPE 10 : NETTOYAGE ET FIN
# ============================================================================

print("\n" + "="*80)
print("✅ RECALCUL TERMINÉ AVEC SUCCÈS !")
print("="*80)

print(f"\n🎉 Nouvelle table event_group_impacts créée avec {count_inserted} groupes")
print(f"   - Ancienne table sauvegardée en backup")
print(f"   - Nouveaux champs intégrés (comparison, period, etc.)")
print(f"   - Surprises recalculées correctement")
print(f"   - Impacts MFE/MAE calculés depuis prices_1m")

print("\n💡 Prochaines étapes :")
print("   1. Re-lancer remeasure_v2_with_clean_data_session20.py")
print("   2. Re-lancer explore_new_fields_predictive_power_session20.py")
print("   3. Analyser les nouveaux résultats !")

conn.close()

print("\n" + "="*80)
