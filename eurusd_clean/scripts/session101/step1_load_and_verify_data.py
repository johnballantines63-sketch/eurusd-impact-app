"""
SESSION 101 - ÉTAPE 1 : Chargement et vérification données impacts corrects
==========================================================================

Objectif : Charger real_impacts_TIMEZONE_FIX_FINAL.csv et vérifier données
"""

import pandas as pd
from pathlib import Path

def main():
    # Chemin fichier impacts corrects
    csv_path = Path(__file__).parent.parent / "session99" / "real_impacts_TIMEZONE_FIX_FINAL.csv"
    
    print("=" * 80)
    print("SESSION 101 - ÉTAPE 1 : CHARGEMENT DONNÉES")
    print("=" * 80)
    print()
    
    # Charger données
    print(f"📁 Chargement : {csv_path.name}")
    df = pd.read_csv(csv_path)
    
    # Dédupliquer les dates (il y a des doublons dans le CSV)
    print(f"   Lignes brutes : {len(df)}")
    df_unique = df.drop_duplicates(subset=['date']).copy()
    print(f"   Dates uniques : {len(df_unique)}")
    print()
    
    # Statistiques impacts
    print("📊 STATISTIQUES IMPACTS RÉELS")
    print("-" * 80)
    print(f"Impact moyen   : {df_unique['impact_pips'].mean():.1f} pips")
    print(f"Impact médian  : {df_unique['impact_pips'].median():.1f} pips")
    print(f"Impact min     : {df_unique['impact_pips'].min():.1f} pips")
    print(f"Impact max     : {df_unique['impact_pips'].max():.1f} pips")
    print(f"Écart-type     : {df_unique['impact_pips'].std():.1f} pips")
    print()
    
    # Distribution impacts
    print("📈 DISTRIBUTION IMPACTS")
    print("-" * 80)
    ranges = [
        (0, 10, "Très faible"),
        (10, 20, "Faible"),
        (20, 40, "Moyen"),
        (40, 60, "Fort"),
        (60, 200, "Très fort")
    ]
    
    for min_val, max_val, label in ranges:
        count = len(df_unique[(df_unique['impact_pips'] >= min_val) & (df_unique['impact_pips'] < max_val)])
        pct = count / len(df_unique) * 100
        print(f"{label:12} ({min_val:3d}-{max_val:3d} pips) : {count:2d} dates ({pct:5.1f}%)")
    print()
    
    # Top 10 impacts
    print("🔝 TOP 10 IMPACTS")
    print("-" * 80)
    top10 = df_unique.nlargest(10, 'impact_pips')[['date', 'impact_pips', 'ttr_minutes']]
    for idx, row in top10.iterrows():
        print(f"{row['date']} : {row['impact_pips']:6.1f} pips (TTR: {row['ttr_minutes']:5.1f} min)")
    print()
    
    # Validation cas référence
    print("✅ VALIDATION CAS RÉFÉRENCE")
    print("-" * 80)
    ref_date = '2025-09-11'
    ref_row = df_unique[df_unique['date'] == ref_date]
    
    if len(ref_row) == 1:
        ref_impact = ref_row.iloc[0]['impact_pips']
        ref_ttr = ref_row.iloc[0]['ttr_minutes']
        print(f"Date référence : {ref_date}")
        print(f"Impact mesuré  : {ref_impact:.1f} pips")
        print(f"TTR mesuré     : {ref_ttr:.1f} minutes")
        print(f"Impact attendu : 57.1 pips")
        print(f"Écart          : {abs(ref_impact - 57.1):.1f} pips")
        
        if abs(ref_impact - 57.1) < 1.0:
            print("✅ VALIDATION OK (écart < 1 pip)")
        else:
            print("⚠️  ATTENTION : Écart > 1 pip")
    else:
        print(f"❌ Date référence {ref_date} non trouvée!")
    
    print()
    print("=" * 80)
    print("✅ ÉTAPE 1 TERMINÉE : Données chargées et vérifiées")
    print("=" * 80)
    
    return df_unique

if __name__ == "__main__":
    df = main()
