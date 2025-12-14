"""
SESSION 101 - ÉTAPE 2 : Calcul R² tendance 72h avant événement
==============================================================

Pour chaque date CPI, calculer le R² de la régression linéaire
sur les prix 72 heures AVANT l'événement.

R² élevé = tendance forte avant événement
R² faible = prix latéral avant événement

Hypothèse : R² corrèle avec amplification nécessaire
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import duckdb
import sys

# Ajouter le chemin vers app pour imports
sys.path.insert(0, str(Path(__file__).parents[2]))

from app.config import config

def calculate_r_squared_72h(event_timestamp_utc: pd.Timestamp, conn) -> float:
    """
    Calcule R² régression linéaire sur prix 72h avant événement.
    
    Args:
        event_timestamp_utc: Timestamp événement en UTC
        conn: Connexion DuckDB
    
    Returns:
        float: R² (0-1), ou 0 si erreur
    """
    try:
        # Fenêtre 72h avant événement
        start_time = event_timestamp_utc - timedelta(hours=72)
        end_time = event_timestamp_utc
        
        # Query prix (table prices_1m)
        query = """
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime >= ?
          AND datetime < ?
        ORDER BY datetime ASC
        """
        
        df = conn.execute(query, [start_time, end_time]).df()
        
        if len(df) < 100:
            # Pas assez de données pour régression fiable
            print(f"    ⚠️  Seulement {len(df)} points (minimum 100)")
            return 0.0
        
        # Préparer données régression
        prices = df['close'].values
        t = np.arange(1, len(prices) + 1)  # Temps 1, 2, 3, ...
        
        # Calcul régression linéaire (méthode moindres carrés)
        t_mean = np.mean(t)
        y_mean = np.mean(prices)
        
        numerator = np.sum((t - t_mean) * (prices - y_mean))
        denominator = np.sum((t - t_mean) ** 2)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * t_mean
        
        # Prédictions
        y_pred = slope * t + intercept
        
        # Calcul R²
        ss_total = np.sum((prices - y_mean) ** 2)
        ss_residual = np.sum((prices - y_pred) ** 2)
        
        if ss_total == 0:
            return 0.0
        
        r_squared = 1 - (ss_residual / ss_total)
        
        # R² peut être négatif si modèle pire que moyenne
        # On clamp entre 0 et 1
        r_squared = max(0.0, min(1.0, r_squared))
        
        return r_squared
        
    except Exception as e:
        print(f"    ❌ Erreur calcul R² : {e}")
        return 0.0


def main():
    print("=" * 80)
    print("SESSION 101 - ÉTAPE 2 : CALCUL R² TENDANCE 72H")
    print("=" * 80)
    print()
    
    # Charger impacts
    csv_path = Path(__file__).parent.parent / "session99" / "real_impacts_TIMEZONE_FIX_FINAL.csv"
    print(f"📁 Chargement impacts : {csv_path.name}")
    df_impacts = pd.read_csv(csv_path)
    
    # Dédupliquer
    df_impacts = df_impacts.drop_duplicates(subset=['date']).copy()
    print(f"   {len(df_impacts)} dates uniques")
    print()
    
    # Connexion DB
    db_path = Path(config.get_db_path())
    print(f"🔌 Connexion DB : {db_path.name}")
    
    if not db_path.exists():
        print(f"❌ Base de données introuvable : {db_path}")
        return
    
    conn = duckdb.connect(str(db_path), read_only=True)
    print("   ✅ Connexion établie")
    print()
    
    # Calcul R² pour chaque date
    print("📊 CALCUL R² POUR CHAQUE DATE")
    print("-" * 80)
    
    results = []
    
    for idx, row in df_impacts.iterrows():
        date_str = row['date']
        impact_pips = row['impact_pips']
        
        # Conversion timestamp UTC
        event_timestamp_bern = pd.to_datetime(row['event_timestamp_bern'])
        event_timestamp_utc = event_timestamp_bern - timedelta(hours=2)
        
        print(f"{date_str} (Impact: {impact_pips:6.1f} pips)")
        print(f"   Event UTC : {event_timestamp_utc}")
        
        # Calcul R²
        r_squared = calculate_r_squared_72h(event_timestamp_utc, conn)
        
        print(f"   R² 72h    : {r_squared:.4f}")
        print()
        
        results.append({
            'date': date_str,
            'event_timestamp_utc': event_timestamp_utc,
            'impact_pips': impact_pips,
            'ttr_minutes': row['ttr_minutes'],
            'r_squared_72h': r_squared
        })
    
    conn.close()
    
    # Créer DataFrame résultats
    df_results = pd.DataFrame(results)
    
    # Sauvegarder
    output_path = Path(__file__).parent / "r2_72h_results.csv"
    df_results.to_csv(output_path, index=False)
    
    print("=" * 80)
    print("✅ ÉTAPE 2 TERMINÉE")
    print("=" * 80)
    print()
    print(f"📊 STATISTIQUES R²")
    print("-" * 80)
    print(f"R² moyen  : {df_results['r_squared_72h'].mean():.4f}")
    print(f"R² médian : {df_results['r_squared_72h'].median():.4f}")
    print(f"R² min    : {df_results['r_squared_72h'].min():.4f}")
    print(f"R² max    : {df_results['r_squared_72h'].max():.4f}")
    print()
    
    # Distribution R²
    print("📈 DISTRIBUTION R²")
    print("-" * 80)
    ranges = [
        (0.0, 0.2, "Très faible"),
        (0.2, 0.4, "Faible"),
        (0.4, 0.6, "Moyen"),
        (0.6, 0.8, "Fort"),
        (0.8, 1.0, "Très fort")
    ]
    
    for min_val, max_val, label in ranges:
        count = len(df_results[(df_results['r_squared_72h'] >= min_val) & 
                               (df_results['r_squared_72h'] < max_val)])
        pct = count / len(df_results) * 100 if len(df_results) > 0 else 0
        print(f"{label:12} ({min_val:.1f}-{max_val:.1f}) : {count:2d} dates ({pct:5.1f}%)")
    
    print()
    print(f"💾 Résultats sauvegardés : {output_path.name}")
    print()
    
    # Cas référence
    ref = df_results[df_results['date'] == '2025-09-11']
    if len(ref) == 1:
        print("✅ CAS RÉFÉRENCE 2025-09-11")
        print("-" * 80)
        print(f"Impact   : {ref.iloc[0]['impact_pips']:.1f} pips")
        print(f"R² 72h   : {ref.iloc[0]['r_squared_72h']:.4f}")
        print()
    
    return df_results


if __name__ == "__main__":
    df = main()
