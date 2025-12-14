#!/usr/bin/env python3
"""
🔬 EXPLORATION POUVOIR PRÉDICTIF DES NOUVEAUX CHAMPS - SESSION 20

Objectif : Analyser les 5 nouveaux champs de l'API EODHD pour voir s'ils
peuvent améliorer nos prédictions :

1. comparison (mom/yoy/qoq) - Distingue les versions mensuelles/annuelles
2. period (Jan, Feb, Q1, etc.) - Période de référence
3. change - Changement absolu vs previous
4. change_percentage - Changement % vs previous  
5. event_type - Type d'événement selon EODHD

Questions à explorer :
- change_percentage est-il meilleur que notre calcul de surprise ?
- period influence-t-il l'impact (volatilité saisonnière) ?
- comparison : MoM a-t-il plus d'impact que YoY ?
- event_type révèle-t-il des patterns ?

Date : 19 octobre 2025
Session : 20
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime

# Connexion DB
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*80)
print("🔬 EXPLORATION POUVOIR PRÉDICTIF NOUVEAUX CHAMPS")
print("="*80)

# ============================================================================
# ÉTAPE 1 : RÉCUPÉRATION DONNÉES AVEC NOUVEAUX CHAMPS
# ============================================================================

print("\n📊 Récupération données avec nouveaux champs...")

query = """
WITH event_agg AS (
    SELECT 
        strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') as time_group,
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
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate)
            ELSE 0
        END as surprise_calculated,
        CASE
            WHEN e.change_percentage IS NOT NULL
            THEN ABS(e.change_percentage) / 100.0
            ELSE NULL
        END as surprise_from_api
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.importance_n >= 2
      AND e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
)
SELECT 
    ea.time_group,
    ea.country,
    ea.event_key,
    ea.comparison,
    ea.period,
    ea.change_percentage,
    ea.event_type,
    ea.family,
    ea.empirical_score,
    ea.surprise_calculated,
    ea.surprise_from_api,
    egi.mfe_pips
FROM event_agg ea
INNER JOIN event_group_impacts egi
    ON ea.time_group = egi.time_group
WHERE egi.mfe_pips IS NOT NULL
  AND ea.empirical_score IS NOT NULL
ORDER BY ea.time_group
"""

df = conn.execute(query).df()

print(f"✅ {len(df)} événements récupérés (avec impact calculé)")
print(f"   - Avec comparison : {df['comparison'].notna().sum()} ({df['comparison'].notna().sum()/len(df)*100:.1f}%)")
print(f"   - Avec period : {df['period'].notna().sum()} ({df['period'].notna().sum()/len(df)*100:.1f}%)")
print(f"   - Avec change_percentage : {df['change_percentage'].notna().sum()} ({df['change_percentage'].notna().sum()/len(df)*100:.1f}%)")
print(f"   - Avec event_type : {df['event_type'].notna().sum()} ({df['event_type'].notna().sum()/len(df)*100:.1f}%)")

# ============================================================================
# ÉTAPE 2 : COMPARAISON surprise_calculated vs surprise_from_api
# ============================================================================

print("\n" + "="*80)
print("📊 A. COMPARAISON : Notre surprise VS change_percentage API")
print("="*80)

# Filtrer événements ayant les deux
df_both = df[(df['surprise_calculated'] > 0) & (df['surprise_from_api'].notna())].copy()

print(f"\n{len(df_both)} événements ont les deux valeurs")

# Corrélation
if len(df_both) > 10:
    corr_surprise = df_both['surprise_calculated'].corr(df_both['surprise_from_api'])
    print(f"   Corrélation surprise_calculated / surprise_from_api : {corr_surprise:.3f}")
    
    # Différence moyenne
    df_both['surprise_diff'] = abs(df_both['surprise_calculated'] - df_both['surprise_from_api'])
    mean_diff = df_both['surprise_diff'].mean() * 100
    print(f"   Différence absolue moyenne : {mean_diff:.1f} points de %")
    
    # Cas où elles diffèrent beaucoup (>10 points)
    big_diffs = df_both[df_both['surprise_diff'] > 0.10]
    print(f"   Cas avec différence >10 points : {len(big_diffs)} ({len(big_diffs)/len(df_both)*100:.1f}%)")
    
    # Quelle version corrèle mieux avec impact ?
    corr_calc_impact = df_both['surprise_calculated'].corr(df_both['mfe_pips'])
    corr_api_impact = df_both['surprise_from_api'].corr(df_both['mfe_pips'])
    
    print(f"\n📈 Corrélation avec impact réel (mfe_pips) :")
    print(f"   surprise_calculated → impact : {corr_calc_impact:.3f}")
    print(f"   surprise_from_api   → impact : {corr_api_impact:.3f}")
    
    if corr_api_impact > corr_calc_impact:
        diff = corr_api_impact - corr_calc_impact
        print(f"   ✅ change_percentage API est MEILLEUR (+{diff:.3f} points)")
    elif corr_calc_impact > corr_api_impact:
        diff = corr_calc_impact - corr_api_impact
        print(f"   ✅ Notre calcul est MEILLEUR (+{diff:.3f} points)")
    else:
        print(f"   ⚪ Équivalents")
    
    # Exemples de grandes différences
    if len(big_diffs) > 0:
        print(f"\n🔍 Exemples de grandes différences :")
        sample = big_diffs.nlargest(5, 'surprise_diff')
        for idx, row in sample.iterrows():
            print(f"\n   {row['time_group']} - {row['event_key']}")
            print(f"      Calculated : {row['surprise_calculated']*100:.1f}%")
            print(f"      API        : {row['surprise_from_api']*100:.1f}%")
            print(f"      Diff       : {row['surprise_diff']*100:.1f} points")
            print(f"      Impact     : {row['mfe_pips']:.1f} pips")

else:
    print("⚠️ Pas assez de données pour analyse")

# ============================================================================
# ÉTAPE 3 : ANALYSE comparison (MoM vs YoY vs QoQ)
# ============================================================================

print("\n" + "="*80)
print("📊 B. ANALYSE comparison : MoM vs YoY vs QoQ")
print("="*80)

df_comp = df[df['comparison'].notna()].copy()

if len(df_comp) > 50:
    print(f"\n{len(df_comp)} événements avec comparison défini")
    
    # Distribution
    comp_counts = df_comp['comparison'].value_counts()
    print(f"\nDistribution :")
    for comp, count in comp_counts.items():
        pct = count / len(df_comp) * 100
        print(f"   {comp:<10} : {count:>6} ({pct:>5.1f}%)")
    
    # Impact moyen par type
    print(f"\n📈 Impact moyen par type de comparison :")
    for comp in ['mom', 'yoy', 'qoq']:
        data_comp = df_comp[df_comp['comparison'] == comp]
        if len(data_comp) > 5:
            mean_impact = data_comp['mfe_pips'].mean()
            median_impact = data_comp['mfe_pips'].median()
            mean_surprise = data_comp['surprise_calculated'].mean() * 100
            print(f"   {comp.upper():<10} : {mean_impact:>6.1f} pips (médiane: {median_impact:.1f}, surprise moy: {mean_surprise:.1f}%)")
    
    # Test statistique simplifié : MoM vs YoY (sans scipy)
    mom_data = df_comp[df_comp['comparison'] == 'mom']['mfe_pips']
    yoy_data = df_comp[df_comp['comparison'] == 'yoy']['mfe_pips']
    
    if len(mom_data) > 5 and len(yoy_data) > 5:
        # Test t manuel (approximatif)
        mean_diff = mom_data.mean() - yoy_data.mean()
        std_pooled = np.sqrt((mom_data.std()**2 / len(mom_data)) + (yoy_data.std()**2 / len(yoy_data)))
        t_stat = mean_diff / std_pooled if std_pooled > 0 else 0
        
        print(f"\n📊 Test statistique (MoM vs YoY) :")
        print(f"   MoM moyenne  : {mom_data.mean():.1f} pips (n={len(mom_data)})")
        print(f"   YoY moyenne  : {yoy_data.mean():.1f} pips (n={len(yoy_data)})")
        print(f"   Différence   : {mean_diff:.1f} pips")
        print(f"   t-statistic  : {t_stat:.3f}")
        
        if abs(t_stat) > 2:  # Approximation pour p < 0.05
            print(f"   ✅ Différence probablement SIGNIFICATIVE (|t| > 2)")
            if mom_data.mean() > yoy_data.mean():
                ratio = mom_data.mean() / yoy_data.mean()
                print(f"   💡 MoM a {ratio:.2f}x plus d'impact que YoY")
            else:
                ratio = yoy_data.mean() / mom_data.mean()
                print(f"   💡 YoY a {ratio:.2f}x plus d'impact que MoM")
        else:
            print(f"   ⚪ Différence probablement non significative (|t| < 2)")
    
    # Analyse : même événement MoM vs YoY
    print(f"\n🔍 Analyse des événements ayant MoM ET YoY simultanés :")
    
    # Grouper par time_group
    grouped = df_comp.groupby(['time_group'])
    simultaneous = []
    
    for time_group, group in grouped:
        if len(group) > 1:
            comparisons = group['comparison'].unique()
            if 'mom' in comparisons and 'yoy' in comparisons:
                simultaneous.append(group)
    
    if len(simultaneous) > 0:
        print(f"   Trouvé {len(simultaneous)} cas avec MoM + YoY simultanés")
        
        # Analyse d'un exemple
        if len(simultaneous) > 0:
            sample = simultaneous[0]
            print(f"\n   Exemple : {sample.iloc[0]['time_group']}")
            for idx, row in sample.iterrows():
                print(f"      {row['comparison'].upper()} - {row['event_key']} : surprise {row['surprise_calculated']*100:.1f}%, impact {row['mfe_pips']:.1f} pips")
    else:
        print(f"   Aucun cas trouvé (événements MoM et YoY arrivent à des timestamps différents)")

else:
    print("⚠️ Pas assez de données pour analyse")

# ============================================================================
# ÉTAPE 4 : ANALYSE period (volatilité saisonnière)
# ============================================================================

print("\n" + "="*80)
print("📊 C. ANALYSE period : Volatilité saisonnière")
print("="*80)

df_period = df[df['period'].notna()].copy()

if len(df_period) > 50:
    print(f"\n{len(df_period)} événements avec period défini")
    
    # Extraire le mois (si format "Jan", "Feb", etc.)
    df_period['month'] = df_period['period'].str[:3]
    
    # Impact moyen par mois
    print(f"\n📈 Impact moyen par période :")
    month_stats = df_period.groupby('month').agg({
        'mfe_pips': ['mean', 'median', 'count']
    }).round(1)
    
    month_stats.columns = ['mean_impact', 'median_impact', 'count']
    month_stats = month_stats.sort_values('mean_impact', ascending=False)
    
    print(month_stats.head(10))
    
    # Identifier mois avec volatilité la plus élevée
    top_volatile = month_stats.nlargest(3, 'mean_impact')
    print(f"\n🔥 Top 3 périodes les plus volatiles :")
    for month in top_volatile.index:
        mean = top_volatile.loc[month, 'mean_impact']
        count = int(top_volatile.loc[month, 'count'])
        print(f"   {month} : {mean:.1f} pips (n={count})")
    
    # Test : Décembre vs reste de l'année (sans scipy)
    dec_data = df_period[df_period['month'] == 'Dec']['mfe_pips']
    other_data = df_period[df_period['month'] != 'Dec']['mfe_pips']
    
    if len(dec_data) > 5 and len(other_data) > 5:
        mean_diff = dec_data.mean() - other_data.mean()
        std_pooled = np.sqrt((dec_data.std()**2 / len(dec_data)) + (other_data.std()**2 / len(other_data)))
        t_stat = mean_diff / std_pooled if std_pooled > 0 else 0
        
        print(f"\n📊 Test (Décembre vs autres mois) :")
        print(f"   Décembre  : {dec_data.mean():.1f} pips (n={len(dec_data)})")
        print(f"   Autres    : {other_data.mean():.1f} pips (n={len(other_data)})")
        print(f"   t-stat    : {t_stat:.3f}")
        
        if abs(t_stat) > 2:
            print(f"   ✅ Décembre est probablement SIGNIFICATIVEMENT différent")
        else:
            print(f"   ⚪ Pas de différence significative")

else:
    print("⚠️ Pas assez de données pour analyse")

# ============================================================================
# ÉTAPE 5 : ANALYSE event_type
# ============================================================================

print("\n" + "="*80)
print("📊 D. ANALYSE event_type : Patterns par type EODHD")
print("="*80)

df_type = df[df['event_type'].notna()].copy()

if len(df_type) > 50:
    print(f"\n{len(df_type)} événements avec event_type défini")
    
    # Top types par fréquence
    type_counts = df_type['event_type'].value_counts().head(10)
    print(f"\nTop 10 types les plus fréquents :")
    for event_type, count in type_counts.items():
        pct = count / len(df_type) * 100
        mean_impact = df_type[df_type['event_type'] == event_type]['mfe_pips'].mean()
        print(f"   {event_type:<30} : {count:>4} ({pct:>5.1f}%) - impact moy: {mean_impact:.1f} pips")
    
    # Statistiques par type
    print(f"\n📈 Statistiques par event_type (min 10 occurrences) :")
    type_stats = df_type.groupby('event_type').agg({
        'mfe_pips': ['mean', 'std', 'count'],
        'surprise_calculated': 'mean'
    }).round(2)
    
    type_stats.columns = ['mean_impact', 'std_impact', 'count', 'mean_surprise']
    type_stats = type_stats[type_stats['count'] >= 10]
    type_stats = type_stats.sort_values('mean_impact', ascending=False)
    
    print(type_stats.head(10))

else:
    print("⚠️ Pas assez de données pour analyse")

# ============================================================================
# ÉTAPE 6 : SYNTHÈSE ET RECOMMANDATIONS
# ============================================================================

print("\n" + "="*80)
print("🎯 SYNTHÈSE ET RECOMMANDATIONS")
print("="*80)

recommendations = []

# A. change_percentage
if len(df_both) > 10:
    if corr_api_impact > corr_calc_impact:
        delta = corr_api_impact - corr_calc_impact
        if delta > 0.05:
            recommendations.append(f"✅ PRIORITAIRE : Utiliser change_percentage au lieu de notre calcul (+{delta:.3f} corrélation)")
        else:
            recommendations.append(f"⚪ OPTIONNEL : change_percentage légèrement meilleur (+{delta:.3f})")
    else:
        recommendations.append(f"⚪ Garder notre calcul de surprise (meilleur)")

# B. comparison
if len(df_comp) > 50 and len(mom_data) > 5 and len(yoy_data) > 5:
    mom_mean = mom_data.mean()
    yoy_mean = yoy_data.mean()
    
    if abs(t_stat) > 2 and abs(mom_mean - yoy_mean) > 2:
        ratio = mom_mean / yoy_mean if mom_mean > yoy_mean else yoy_mean / mom_mean
        winner = "MoM" if mom_mean > yoy_mean else "YoY"
        recommendations.append(f"✅ IMPORTANT : Différencier {winner} (facteur {ratio:.2f}x)")
    else:
        recommendations.append(f"⚪ comparison : pas d'impact significatif détecté")

# C. period
if len(df_period) > 50 and len(dec_data) > 5 and len(other_data) > 5:
    if abs(t_stat) > 2:
        ratio = dec_data.mean() / other_data.mean()
        if ratio > 1.2 or ratio < 0.8:
            recommendations.append(f"✅ CONSIDÉRER : Ajustement saisonnier (Dec: ×{ratio:.2f})")
        else:
            recommendations.append(f"⚪ period : différence statistique mais faible effet")
    else:
        recommendations.append(f"⚪ period : pas d'effet saisonnier significatif")

# D. event_type
if len(df_type) > 50:
    recommendations.append(f"⚪ event_type : À investiguer plus en profondeur (données qualitatives)")

print("\n🎯 Recommandations pour formule V3 :")
for i, rec in enumerate(recommendations, 1):
    print(f"   {i}. {rec}")

# Suggestion de formule V3
print(f"\n💡 Suggestion formule V3 :")
print(f"   V2 actuelle : impact = base × amplification(surprise, score) × 0.758")

if any("change_percentage" in r for r in recommendations):
    print(f"   → Remplacer surprise par change_percentage quand disponible")

if any("Différencier" in r for r in recommendations) and len(mom_data) > 5 and len(yoy_data) > 5:
    if mom_mean > yoy_mean:
        print(f"   → Ajouter facteur comparison : MoM ×{mom_mean/yoy_mean:.2f}, YoY ×1.0")
    else:
        print(f"   → Ajouter facteur comparison : YoY ×{yoy_mean/mom_mean:.2f}, MoM ×1.0")

if any("saisonnier" in r for r in recommendations) and len(dec_data) > 5:
    ratio_dec = dec_data.mean() / other_data.mean()
    print(f"   → Ajouter facteur period : Dec ×{ratio_dec:.2f}")

print("\n💾 Données explorées sauvegardées dans la DB (accessible via requêtes SQL)")

print("\n" + "="*80)
print("✅ EXPLORATION TERMINÉE")
print("="*80)

conn.close()
