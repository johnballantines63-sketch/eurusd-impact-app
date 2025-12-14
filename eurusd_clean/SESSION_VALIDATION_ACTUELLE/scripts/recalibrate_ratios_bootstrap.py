#!/usr/bin/env python3
"""
Recalibrage ratios leg1/leg2 avec bootstrap (N=9, prudence)

Objectif : Sortir des stats descriptives et des CI bootstrap
sans figer des ratios définitifs (N trop faible).

Approche :
- Stats descriptives : median, Q25, Q75
- Bootstrap 1000× pour CI 80-90%
- Split double_wave vs zig_zag
- Comparaison avec ratios Session 64
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

SCRIPT_DIR = Path(__file__).parent


def bootstrap_ci(data: np.ndarray, n_boot: int = 2000, ci=(5, 95)):
    """Retourne l'intervalle de confiance bootstrap (percentiles) de la médiane."""
    if len(data) == 0:
        return None
    meds = []
    n = len(data)
    for _ in range(n_boot):
        sample = np.random.choice(data, size=n, replace=True)
        meds.append(np.median(sample))
    return np.percentile(meds, ci)


def main():
    # Charger résultats scan
    patterns_file = SCRIPT_DIR / 'outputs' / 'direction_router_test' / 'patterns_detected.csv'
    if not patterns_file.exists():
        print("❌ Fichier patterns_detected.csv non trouvé")
        print("   Lance d'abord : python3 scan_patterns_historique_complet.py")
        return
    
    df = pd.read_csv(patterns_file)
    
    # Filtrer multi-wave uniques
    multi_wave = df[df['pattern_type'].isin(['double_wave', 'zig_zag'])].drop_duplicates(subset=['date'])
    
    if len(multi_wave) == 0:
        print("❌ Aucun multi-wave trouvé")
        return
    
    print("=" * 80)
    print("RECALIBRAGE RATIOS LEG1/LEG2 (BOOTSTRAP)")
    print("=" * 80)
    print()
    print(f"📊 {len(multi_wave)} cas multi-wave uniques")
    print(f"   - double_wave : {len(multi_wave[multi_wave['pattern_type'] == 'double_wave'])}")
    print(f"   - zig_zag : {len(multi_wave[multi_wave['pattern_type'] == 'zig_zag'])}")
    print()
    
    # Filtrer cas avec métadonnées complètes
    multi_wave_complete = multi_wave[
        pd.notna(multi_wave['leg1_amp_pips']) &
        pd.notna(multi_wave['leg2_amp_pips']) &
        pd.notna(multi_wave['total_amp_pips'])
    ].copy()
    
    if len(multi_wave_complete) == 0:
        print("❌ Aucun cas avec métadonnées complètes")
        return
    
    print(f"✅ {len(multi_wave_complete)} cas avec métadonnées complètes")
    print()
    
    # Calculer ratios
    multi_wave_complete['leg1_ratio'] = (
        multi_wave_complete['leg1_amp_pips'] / 
        multi_wave_complete['total_amp_pips']
    )
    multi_wave_complete['leg2_ratio'] = (
        multi_wave_complete['leg2_amp_pips'] / 
        multi_wave_complete['total_amp_pips']
    )
    
    # Stats descriptives globales
    print("=" * 80)
    print("STATS DESCRIPTIVES GLOBALES")
    print("=" * 80)
    print()
    
    leg1_ratios = multi_wave_complete['leg1_ratio'].values
    leg2_ratios = multi_wave_complete['leg2_ratio'].values
    retrace_ratios = multi_wave_complete['retrace_ratio'].dropna().values
    
    print("Ratio Leg1 / Total :")
    print(f"   Median : {np.median(leg1_ratios):.2%}")
    print(f"   Q25 : {np.percentile(leg1_ratios, 25):.2%}")
    print(f"   Q75 : {np.percentile(leg1_ratios, 75):.2%}")
    print(f"   Mean : {np.mean(leg1_ratios):.2%}")
    print(f"   Std : {np.std(leg1_ratios):.2%}")
    print()
    
    print("Ratio Leg2 / Total :")
    print(f"   Median : {np.median(leg2_ratios):.2%}")
    print(f"   Q25 : {np.percentile(leg2_ratios, 25):.2%}")
    print(f"   Q75 : {np.percentile(leg2_ratios, 75):.2%}")
    print(f"   Mean : {np.mean(leg2_ratios):.2%}")
    print(f"   Std : {np.std(leg2_ratios):.2%}")
    print()
    
    if len(retrace_ratios) > 0:
        print("Retrace Ratio :")
        print(f"   Median : {np.median(retrace_ratios):.2%}")
        print(f"   Q25 : {np.percentile(retrace_ratios, 25):.2%}")
        print(f"   Q75 : {np.percentile(retrace_ratios, 75):.2%}")
        print(f"   Mean : {np.mean(retrace_ratios):.2%}")
        print()
    
    # Split par pattern type
    print("=" * 80)
    print("SPLIT PAR PATTERN TYPE")
    print("=" * 80)
    print()
    
    for pattern_type in ['double_wave', 'zig_zag']:
        subset = multi_wave_complete[multi_wave_complete['pattern_type'] == pattern_type]
        if len(subset) == 0:
            continue
        
        print(f"📊 {pattern_type.upper()} (N={len(subset)})")
        print()
        
        leg1_subset = subset['leg1_ratio'].values
        leg2_subset = subset['leg2_ratio'].values
        
        print(f"   Leg1 / Total :")
        print(f"      Median : {np.median(leg1_subset):.2%}")
        print(f"      Q25-Q75 : [{np.percentile(leg1_subset, 25):.2%}, {np.percentile(leg1_subset, 75):.2%}]")
        print()
        
        print(f"   Leg2 / Total :")
        print(f"      Median : {np.median(leg2_subset):.2%}")
        print(f"      Q25-Q75 : [{np.percentile(leg2_subset, 25):.2%}, {np.percentile(leg2_subset, 75):.2%}]")
        print()
    
    # Split par cluster_type (si N suffisant)
    print("=" * 80)
    print("SPLIT PAR CLUSTER TYPE")
    print("=" * 80)
    print()
    
    for ctype in multi_wave_complete['cluster_type'].unique():
        sub = multi_wave_complete[multi_wave_complete['cluster_type'] == ctype]
        if len(sub) < 5:  # Minimum 5 pour stats significatives
            continue
        
        print(f"📊 {ctype.upper()} (N={len(sub)})")
        print()
        
        leg1_sub = sub['leg1_ratio'].values
        leg2_sub = sub['leg2_ratio'].values
        
        print(f"   Leg1 / Total :")
        print(f"      Median : {np.median(leg1_sub):.2%}")
        print(f"      Q25-Q75 : [{np.percentile(leg1_sub, 25):.2%}, {np.percentile(leg1_sub, 75):.2%}]")
        print()
        
        print(f"   Leg2 / Total :")
        print(f"      Median : {np.median(leg2_sub):.2%}")
        print(f"      Q25-Q75 : [{np.percentile(leg2_sub, 25):.2%}, {np.percentile(leg2_sub, 75):.2%}]")
        print()
        
        # Bootstrap CI pour ce cluster
        leg1_ci = bootstrap_ci(leg1_sub, ci=(5, 95))
        leg2_ci = bootstrap_ci(leg2_sub, ci=(5, 95))
        if leg1_ci is not None and leg2_ci is not None:
            print(f"   Bootstrap CI90 :")
            print(f"      Leg1 : [{leg1_ci[0]:.2%}, {leg1_ci[1]:.2%}]")
            print(f"      Leg2 : [{leg2_ci[0]:.2%}, {leg2_ci[1]:.2%}]")
            print()
    
    # Bootstrap pour CI
    print("=" * 80)
    print("BOOTSTRAP (1000×) - CI 80-90%")
    print("=" * 80)
    print()
    
    n_bootstrap = 1000
    n_samples = len(multi_wave_complete)
    
    # Bootstrap leg1_ratio
    leg1_bootstrap = []
    leg2_bootstrap = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(leg1_ratios, size=n_samples, replace=True)
        leg1_bootstrap.append(np.median(sample))
        
        sample = np.random.choice(leg2_ratios, size=n_samples, replace=True)
        leg2_bootstrap.append(np.median(sample))
    
    leg1_bootstrap = np.array(leg1_bootstrap)
    leg2_bootstrap = np.array(leg2_bootstrap)
    
    # CI 80%
    leg1_ci80 = np.percentile(leg1_bootstrap, [10, 90])
    leg2_ci80 = np.percentile(leg2_bootstrap, [10, 90])
    
    # CI 90%
    leg1_ci90 = np.percentile(leg1_bootstrap, [5, 95])
    leg2_ci90 = np.percentile(leg2_bootstrap, [5, 95])
    
    print("Ratio Leg1 / Total (bootstrap median) :")
    print(f"   CI 80% : [{leg1_ci80[0]:.2%}, {leg1_ci80[1]:.2%}]")
    print(f"   CI 90% : [{leg1_ci90[0]:.2%}, {leg1_ci90[1]:.2%}]")
    print()
    
    print("Ratio Leg2 / Total (bootstrap median) :")
    print(f"   CI 80% : [{leg2_ci80[0]:.2%}, {leg2_ci80[1]:.2%}]")
    print(f"   CI 90% : [{leg2_ci90[0]:.2%}, {leg2_ci90[1]:.2%}]")
    print()
    
    # Bootstrap par pattern type (CI 90%)
    print("=" * 80)
    print("BOOTSTRAP PAR PATTERN TYPE (CI 90%)")
    print("=" * 80)
    for ptype in ["double_wave", "zig_zag"]:
        sub = multi_wave_complete[multi_wave_complete["pattern_type"] == ptype]
        if len(sub) == 0:
            continue
        leg1 = sub["leg1_ratio"].values
        leg2 = sub["leg2_ratio"].values
        leg1_ci = bootstrap_ci(leg1, ci=(5, 95))
        leg2_ci = bootstrap_ci(leg2, ci=(5, 95))
        print(f"\n📊 {ptype.upper()} (N={len(sub)})")
        print(f"   Leg1 median CI90 : [{leg1_ci[0]:.2%}, {leg1_ci[1]:.2%}]")
        print(f"   Leg2 median CI90 : [{leg2_ci[0]:.2%}, {leg2_ci[1]:.2%}]")

    # Bootstrap retrace_ratio pour double_wave
    dw = multi_wave_complete[
        (multi_wave_complete["pattern_type"] == "double_wave")
        & (multi_wave_complete["retrace_ratio"].notna())
    ]
    if len(dw) > 0:
        rr = dw["retrace_ratio"].dropna().values
        rr_ci = bootstrap_ci(rr, ci=(5, 95))
        print("\nRetrace_ratio DOUBLE_WAVE median CI90 :", [f"{v:.2%}" for v in rr_ci])

    # Comparaison avec Session 64
    print("=" * 80)
    print("COMPARAISON AVEC RATIOS SESSION 64")
    print("=" * 80)
    print()
    
    # Ratios Session 64 (à ajuster selon valeurs réelles)
    session64_leg1 = 0.40  # Exemple, à vérifier
    session64_leg2 = 0.60  # Exemple, à vérifier
    
    print(f"Session 64 (prior) :")
    print(f"   Leg1 : {session64_leg1:.0%}")
    print(f"   Leg2 : {session64_leg2:.0%}")
    print()
    
    print(f"Empirique (median) :")
    print(f"   Leg1 : {np.median(leg1_ratios):.0%}")
    print(f"   Leg2 : {np.median(leg2_ratios):.0%}")
    print()
    
    # Écart
    ecart_leg1 = abs(np.median(leg1_ratios) - session64_leg1)
    ecart_leg2 = abs(np.median(leg2_ratios) - session64_leg2)
    
    print(f"Écart :")
    print(f"   Leg1 : {ecart_leg1:.0%}")
    print(f"   Leg2 : {ecart_leg2:.0%}")
    print()
    
    # Recommandation
    print("=" * 80)
    print("RECOMMANDATION")
    print("=" * 80)
    print()
    
    if ecart_leg1 > 0.10 or ecart_leg2 > 0.10:
        print("⚠️  Écart significatif avec Session 64")
        print("   → Ajuster ratios si écart > 10%")
    else:
        print("✅ Écart faible avec Session 64")
        print("   → Garder ratios Session 64 comme prior")
    
    print()
    if n_samples < 30:
        print(f"⚠️  N={n_samples} < 30 → ratios à garder comme prior, pas définitifs.")
        print("   → Attendre N≥30 pour recalibrage robuste")
        print("   → Utiliser CI bootstrap pour évaluer incertitude")
    else:
        print(f"✅ N={n_samples} ≥ 30 → recalibrage robuste possible")
        print("   → Ratios peuvent être considérés comme définitifs")
    print()
    
    # Sauvegarder résultats
    output_file = SCRIPT_DIR / 'outputs' / 'direction_router_test' / 'ratios_recalibration.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = pd.DataFrame({
        'metric': ['leg1_ratio', 'leg2_ratio'],
        'median': [np.median(leg1_ratios), np.median(leg2_ratios)],
        'q25': [np.percentile(leg1_ratios, 25), np.percentile(leg2_ratios, 25)],
        'q75': [np.percentile(leg1_ratios, 75), np.percentile(leg2_ratios, 75)],
        'ci80_low': [leg1_ci80[0], leg2_ci80[0]],
        'ci80_high': [leg1_ci80[1], leg2_ci80[1]],
        'ci90_low': [leg1_ci90[0], leg2_ci90[0]],
        'ci90_high': [leg1_ci90[1], leg2_ci90[1]],
        'session64_prior': [session64_leg1, session64_leg2],
        'ecart': [ecart_leg1, ecart_leg2]
    })
    
    results.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()

if __name__ == '__main__':
    main()

