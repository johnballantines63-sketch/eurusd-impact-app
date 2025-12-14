#!/usr/bin/env python3
"""
Stratification Ratios V8 - Multi-Wave Patterns

Objectif : Stratifier les ratios Leg1/Leg2 par buckets dès que N≥30.

Buckets :
- Par cluster_type (CPI / Jobs / CPI+Jobs)
- Par strength (Low / Medium / High)
- Par pattern (Double-wave / Zig-zag)
- Par direction (UP / DOWN)
- Combo (cluster × strength × pattern)

Critères robustesse :
- N≥5 : Stats descriptives OK
- N≥10 : Bootstrap CI fiables
- N≥30 : Recalibrage définitif

Usage:
    python3 stratify_ratios_v8.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import os

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Importer bootstrap_ci depuis recalibrate_ratios_bootstrap
from recalibrate_ratios_bootstrap import bootstrap_ci

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_N_DESC = 5      # Minimum pour stats descriptives
MIN_N_BOOT = 10     # Minimum pour bootstrap CI
MIN_N_FINAL = 30    # Minimum pour recalibrage définitif

STRENGTH_BUCKETS = [
    ("low",   lambda z: abs(z) < 1.5),
    ("med",   lambda z: 1.5 <= abs(z) < 2.0),
    ("high",  lambda z: abs(z) >= 2.0),
]

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute colonnes leg1_ratio et leg2_ratio."""
    df = df.copy()
    df["leg1_ratio"] = df["leg1_amp_pips"] / df["total_amp_pips"]
    df["leg2_ratio"] = df["leg2_amp_pips"] / df["total_amp_pips"]
    return df


def bucket_strength(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute colonne strength_bucket selon trigger_strength."""
    df = df.copy()
    df["strength_bucket"] = None
    
    for name, rule in STRENGTH_BUCKETS:
        mask = df["trigger_strength"].apply(rule)
        df.loc[mask, "strength_bucket"] = name
    
    return df


def summarize_group(sub: pd.DataFrame) -> dict:
    """Calcule stats descriptives + bootstrap CI pour un groupe."""
    out = {
        "N": len(sub),
        "leg1_med": np.median(sub["leg1_ratio"]),
        "leg2_med": np.median(sub["leg2_ratio"]),
        "leg1_q25": np.percentile(sub["leg1_ratio"], 25),
        "leg1_q75": np.percentile(sub["leg1_ratio"], 75),
        "leg2_q25": np.percentile(sub["leg2_ratio"], 25),
        "leg2_q75": np.percentile(sub["leg2_ratio"], 75),
    }
    
    # Bootstrap CI si N suffisant
    if len(sub) >= MIN_N_BOOT:
        out["leg1_ci90"] = bootstrap_ci(sub["leg1_ratio"].values, ci=(5, 95))
        out["leg2_ci90"] = bootstrap_ci(sub["leg2_ratio"].values, ci=(5, 95))
    else:
        out["leg1_ci90"] = None
        out["leg2_ci90"] = None
    
    return out


def stratify(df: pd.DataFrame, by_cols: list) -> pd.DataFrame:
    """Stratifie par colonnes et calcule stats par groupe."""
    rows = []
    grouped = df.groupby(by_cols)
    
    for key, sub in grouped:
        if len(sub) < MIN_N_DESC:
            continue
        
        stats = summarize_group(sub)
        
        # Construire ligne résultat
        if isinstance(key, tuple):
            row = dict(zip(by_cols, key))
        else:
            row = {by_cols[0]: key}
        
        row.update(stats)
        rows.append(row)
    
    return pd.DataFrame(rows)


def tag_robustness(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute colonne robustness selon N."""
    df = df.copy()
    df["robustness"] = df["N"].apply(
        lambda n: "final" if n >= MIN_N_FINAL else
                  "bootstrap_ok" if n >= MIN_N_BOOT else
                  "descriptive_only"
    )
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Charger résultats scan
    patterns_file = SCRIPT_DIR / 'outputs' / 'direction_router_test' / 'patterns_detected.csv'
    
    if not patterns_file.exists():
        print("❌ Fichier patterns_detected.csv non trouvé")
        print("   Lance d'abord : python3 scan_patterns_historique_complet.py")
        return
    
    df = pd.read_csv(patterns_file)
    
    # Filtrer multi-wave uniques avec métadonnées complètes
    mw = df[df["pattern_type"].isin(["double_wave", "zig_zag"])].drop_duplicates(subset=["date"])
    mw = mw.dropna(subset=["leg1_amp_pips", "leg2_amp_pips", "total_amp_pips"])
    
    if len(mw) == 0:
        print("❌ Aucun multi-wave avec métadonnées complètes")
        return
    
    print("=" * 80)
    print("STRATIFICATION RATIOS V8")
    print("=" * 80)
    print()
    print(f"📊 {len(mw)} multi-wave uniques avec métadonnées complètes")
    print()
    
    # Ajouter ratios et buckets
    mw = add_ratios(mw)
    mw = bucket_strength(mw)
    
    # Log N brut par axe (debug V8)
    print("=" * 80)
    print("N BRUT PAR AXE (DEBUG)")
    print("=" * 80)
    print()
    print(f"Cluster types : {mw['cluster_type'].value_counts().to_dict()}")
    print(f"Strength buckets : {mw['strength_bucket'].value_counts().to_dict()}")
    print(f"Patterns : {mw['pattern_type'].value_counts().to_dict()}")
    print(f"Directions : {mw['direction_first_leg'].value_counts().to_dict()}")
    print()
    
    # Stratifier par différents axes
    outputs = {}
    
    print("Stratification par cluster_type...")
    outputs["by_cluster"] = stratify(mw, ["cluster_type"])
    
    print("Stratification par strength...")
    outputs["by_strength"] = stratify(mw, ["strength_bucket"])
    
    print("Stratification par pattern...")
    outputs["by_pattern"] = stratify(mw, ["pattern_type"])
    
    print("Stratification par direction...")
    outputs["by_direction"] = stratify(mw, ["direction_first_leg"])
    
    print("Stratification combo (cluster × strength × pattern)...")
    outputs["combo"] = stratify(mw, ["cluster_type", "strength_bucket", "pattern_type"])
    
    # Tag robustness
    for name, t in outputs.items():
        if len(t) == 0:
            continue
        outputs[name] = tag_robustness(t)
    
    # Sauvegarder résultats
    out_dir = SCRIPT_DIR / 'outputs' / 'direction_router_test' / 'v8_stratification'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print()
    print("=" * 80)
    print("RÉSULTATS STRATIFICATION")
    print("=" * 80)
    print()
    
    for name, t in outputs.items():
        if len(t) == 0:
            # Log N brut pour debug
            if name == "by_strength":
                n_raw = mw["strength_bucket"].value_counts().to_dict()
                print(f"⚠️  {name} : Aucun bucket avec N≥{MIN_N_DESC} (N brut: {n_raw})")
            elif name == "combo":
                n_raw_total = len(mw)
                print(f"⚠️  {name} : Aucun bucket avec N≥{MIN_N_DESC} (N total: {n_raw_total})")
            else:
                print(f"⚠️  {name} : Aucun bucket avec N≥{MIN_N_DESC}")
            continue
        
        output_file = out_dir / f"{name}.csv"
        t.to_csv(output_file, index=False)
        
        print(f"📊 {name.upper()}")
        print(f"   Buckets : {len(t)}")
        print(f"   Robustness : {t['robustness'].value_counts().to_dict()}")
        print(f"   💾 Sauvegardé : {output_file}")
        print()
        
        # Afficher résumé
        for idx, row in t.iterrows():
            bucket_name = " × ".join([str(row[col]) for col in t.columns if col not in ['N', 'leg1_med', 'leg2_med', 'leg1_q25', 'leg1_q75', 'leg2_q25', 'leg2_q75', 'leg1_ci90', 'leg2_ci90', 'robustness']])
            print(f"   {bucket_name} : N={int(row['N'])}, Leg1={row['leg1_med']:.1%}, Leg2={row['leg2_med']:.1%} [{row['robustness']}]")
        print()
    
    print("=" * 80)
    print("✅ STRATIFICATION V8 TERMINÉE")
    print("=" * 80)
    print()
    print(f"💾 Résultats dans : {out_dir}")
    print()
    
    # Recommandations
    print("=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    print()
    
    n_total = len(mw)
    if n_total < MIN_N_FINAL:
        print(f"⚠️  N={n_total} < {MIN_N_FINAL}")
        print("   → Attendre N≥30 pour recalibrage définitif")
        print("   → Utiliser ratios Session 64 (40/60) comme prior")
    else:
        print(f"✅ N={n_total} ≥ {MIN_N_FINAL}")
        print("   → Recalibrage définitif possible")
        print("   → Vérifier buckets avec robustness='final'")
    
    print()

if __name__ == "__main__":
    main()

