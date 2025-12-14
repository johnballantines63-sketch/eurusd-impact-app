#!/usr/bin/env python3
"""
SESSION 109 - PHASE 1 : CALCUL METRIQUES TENDANCE (APPROCHE CORRECTE)
======================================================================
UTILISE LES INVERSIONS DEJA DETECTEES en Session 107-108
Calcule les 9 metriques manquantes sur les MEMES donnees

Auteur : Andre Valentin
Date : 3 novembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timezone, timedelta
from scipy.stats import linregress, spearmanr

# Setup paths
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

print("="*80)
print("SESSION 109 - PHASE 1 : CALCUL METRIQUES (METHODE CORRECTE)")
print("="*80)
print()
print("APPROCHE : Utiliser inversions Session 107-108")
print("  1. Charger CSV existants")
print("  2. Reconstituer datetime inversion")
print("  3. Charger prix MEMES periodes")
print("  4. Calculer 9 metriques manquantes")
print()

# Import config
import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

print(f"DB: {db_path}")

if not db_path.exists():
    print(f"DB introuvable: {db_path}")
    sys.exit(1)

# Connexion DB
conn = duckdb.connect(str(db_path))
print("Connexion DB etablie")


def calculate_additional_metrics(df_trend):
    """
    Calcule les 9 metriques manquantes sur donnees tendance.
    
    On a DEJA dans les CSV Session 107-108 :
    - r2_inversion (r2_linear)
    - duration_hours
    - amplitude_inversion (amplitude_pips)
    
    On calcule :
    - r_pearson (avec signe)
    - slope_pips_hour
    - r2_poly2, r2_poly3
    - rho_spearman
    - adx
    - volatility_pips
    - hurst
    - autocorr_lag1
    """
    if len(df_trend) < 24:  # Min 2h
        return None
    
    metrics = {}
    
    # Preparer donnees
    df_trend = df_trend.copy()
    df_trend['seconds'] = (df_trend['datetime'] - df_trend['datetime'].iloc[0]).dt.total_seconds()
    X = df_trend['seconds'].values
    y = df_trend['close'].values
    
    # ========== LINEAIRES ==========
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        
        # 1. R Pearson (avec signe)
        metrics['r_pearson'] = r_value
        
        # 2. Pente (pips/heure)
        metrics['slope_pips_hour'] = slope * 10000 * 3600
        
    except Exception as e:
        print(f"    Erreur lineaire: {e}")
        metrics['r_pearson'] = 0.0
        metrics['slope_pips_hour'] = 0.0
    
    # ========== NON-LINEAIRES ==========
    try:
        # 3. R2 Polynomial degre 2
        coeffs2 = np.polyfit(X, y, deg=2)
        y_pred2 = np.polyval(coeffs2, X)
        ss_res2 = np.sum((y - y_pred2)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        metrics['r2_poly2'] = 1 - (ss_res2 / ss_tot) if ss_tot > 0 else 0.0
        
        # 4. R2 Polynomial degre 3
        coeffs3 = np.polyfit(X, y, deg=3)
        y_pred3 = np.polyval(coeffs3, X)
        ss_res3 = np.sum((y - y_pred3)**2)
        metrics['r2_poly3'] = 1 - (ss_res3 / ss_tot) if ss_tot > 0 else 0.0
        
        # 5. Spearman Rho
        rho, p_rho = spearmanr(X, y)
        metrics['rho_spearman'] = rho
        
    except Exception as e:
        print(f"    Erreur non-lineaire: {e}")
        metrics['r2_poly2'] = 0.0
        metrics['r2_poly3'] = 0.0
        metrics['rho_spearman'] = 0.0
    
    # ========== TRADING ==========
    try:
        # 6. ADX
        try:
            from ta.trend import ADXIndicator
            adx_indicator = ADXIndicator(
                high=df_trend['high'],
                low=df_trend['low'],
                close=df_trend['close'],
                window=14
            )
            adx_series = adx_indicator.adx()
            metrics['adx'] = adx_series.iloc[-1] if len(adx_series) > 0 and not pd.isna(adx_series.iloc[-1]) else 0.0
        except:
            metrics['adx'] = 0.0
        
        # 7. Volatilite (std pips)
        metrics['volatility_pips'] = df_trend['close'].std() * 10000
        
    except Exception as e:
        print(f"    Erreur trading: {e}")
        metrics['adx'] = 0.0
        metrics['volatility_pips'] = 0.0
    
    # ========== AVANCEES ==========
    try:
        # 8. Hurst Exponent
        try:
            from hurst import compute_Hc
            H, c, data = compute_Hc(df_trend['close'].values, kind='price', simplified=True)
            metrics['hurst'] = H
        except:
            metrics['hurst'] = 0.5
        
        # 9. Autocorrelation Lag 1
        try:
            from statsmodels.tsa.stattools import acf
            autocorr = acf(df_trend['close'].values, nlags=1, fft=False)
            metrics['autocorr_lag1'] = autocorr[1] if len(autocorr) > 1 else 0.0
        except:
            metrics['autocorr_lag1'] = 0.0
        
    except Exception as e:
        print(f"    Erreur avancees: {e}")
        metrics['hurst'] = 0.5
        metrics['autocorr_lag1'] = 0.0
    
    return metrics


def process_date_from_existing(row, cluster_num, conn):
    """
    Traiter une date en utilisant inversion DEJA detectee.
    
    row contient :
    - date
    - amp_optimal
    - r2_inversion (deja calcule)
    - duration_hours (deja calcule)
    - amplitude_inversion (deja calcule)
    - reversal_type
    """
    date_str = row['date']
    print(f"\nTraitement {date_str} (Cluster #{cluster_num})")
    
    # Event datetime
    event_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    if cluster_num == 3:
        # CPI : 14:30 Bern = 12:30 UTC
        event_dt = event_date.replace(hour=12, minute=30, second=0, tzinfo=timezone.utc)
    else:
        # Manufacturing : 15:45 Bern = 13:45 UTC
        event_dt = event_date.replace(hour=13, minute=45, second=0, tzinfo=timezone.utc)
    
    # Reconstituer datetime inversion
    duration_hours = row['duration_hours']
    inversion_dt = event_dt - timedelta(hours=duration_hours)
    
    print(f"  Event: {event_dt}")
    print(f"  Inversion: {inversion_dt} ({row['reversal_type']})")
    print(f"  Duree: {duration_hours:.2f}h")
    
    # Charger prix entre inversion et event
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_1m
    WHERE datetime >= '{inversion_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime <= '{event_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df_trend = conn.execute(query).fetchdf()
    
    if len(df_trend) < 24:
        print(f"  Pas assez de donnees: {len(df_trend)} bougies")
        return None
    
    df_trend['datetime'] = pd.to_datetime(df_trend['datetime'])
    print(f"  {len(df_trend)} bougies chargees")
    
    # Calculer metriques manquantes
    additional_metrics = calculate_additional_metrics(df_trend)
    
    if additional_metrics is None:
        print(f"  Erreur calcul metriques")
        return None
    
    # Assembler resultat COMPLET
    result = {
        'date': date_str,
        'cluster': cluster_num,
        'amp_optimal': row['amp_optimal'],
        # Metriques DEJA dans CSV
        'r2_linear': row['r2_inversion'],  # r2_inversion = r2_linear
        'duration_hours': duration_hours,
        'amplitude_pips': row.get('amplitude_inversion', 0.0),
        'reversal_type': row['reversal_type'],
        # Metriques NOUVELLES
        **additional_metrics
    }
    
    print(f"  Metriques calculees:")
    print(f"    R2 linear (CSV): {result['r2_linear']:.4f}")
    print(f"    R Pearson: {additional_metrics['r_pearson']:+.4f}")
    print(f"    ADX: {additional_metrics['adx']:.2f}")
    print(f"    Hurst: {additional_metrics['hurst']:.4f}")
    
    return result


def main():
    """
    Script principal Phase 1 (approche correcte).
    """
    print("\n" + "="*80)
    print("CHARGEMENT DONNEES SESSION 107-108")
    print("="*80)
    
    # Charger CSV Cluster #3
    cluster3_path = project_root / "eurusd_clean" / "scripts" / "session107" / "cluster3_inversion_analysis.csv"
    df_c3 = pd.read_csv(cluster3_path)
    print(f"Cluster #3: {len(df_c3)} dates")
    
    # Charger CSV Cluster #1
    cluster1_path = project_root / "eurusd_clean" / "scripts" / "session108" / "cluster1_inversion_analysis.csv"
    df_c1 = pd.read_csv(cluster1_path)
    print(f"Cluster #1: {len(df_c1)} dates")
    
    print(f"\nTOTAL: {len(df_c3) + len(df_c1)} dates a traiter")
    
    # Traiter chaque date
    results = []
    
    # Cluster #3
    print("\n" + "="*80)
    print("TRAITEMENT CLUSTER #3")
    print("="*80)
    
    for i, (idx, row) in enumerate(df_c3.iterrows(), 1):
        print(f"\n[{i}/{len(df_c3)}]")
        result = process_date_from_existing(row, 3, conn)
        if result is not None:
            results.append(result)
    
    # Cluster #1
    print("\n" + "="*80)
    print("TRAITEMENT CLUSTER #1")
    print("="*80)
    
    for i, (idx, row) in enumerate(df_c1.iterrows(), 1):
        print(f"\n[{i}/{len(df_c1)}]")
        result = process_date_from_existing(row, 1, conn)
        if result is not None:
            results.append(result)
    
    # Sauvegarder
    print("\n" + "="*80)
    print("SAUVEGARDE RESULTATS")
    print("="*80)
    
    df_results = pd.DataFrame(results)
    
    output_path = project_root / "eurusd_clean" / "scripts" / "session109" / "phase1_all_metrics_17dates.csv"
    df_results.to_csv(output_path, index=False)
    
    print(f"Resultats sauvegardes: {output_path}")
    print(f"{len(df_results)} lignes x {len(df_results.columns)} colonnes")
    
    # Statistiques
    print("\n" + "="*80)
    print("STATISTIQUES METRIQUES")
    print("="*80)
    
    metrics_cols = [
        'r2_linear', 'r_pearson', 'slope_pips_hour', 'duration_hours',
        'r2_poly2', 'r2_poly3', 'rho_spearman',
        'adx', 'amplitude_pips', 'volatility_pips',
        'hurst', 'autocorr_lag1'
    ]
    
    for metric in metrics_cols:
        if metric in df_results.columns:
            mean_val = df_results[metric].mean()
            std_val = df_results[metric].std()
            min_val = df_results[metric].min()
            max_val = df_results[metric].max()
            print(f"{metric:20s}: {mean_val:8.4f} +/- {std_val:6.4f}  [{min_val:8.4f}, {max_val:8.4f}]")
    
    print("\n" + "="*80)
    print("PHASE 1 TERMINEE")
    print("="*80)
    print(f"Fichier genere: phase1_all_metrics_17dates.csv")
    print(f"Prochaine etape: Phase 2 - Test 96 correlations")
    
    conn.close()


if __name__ == "__main__":
    main()
