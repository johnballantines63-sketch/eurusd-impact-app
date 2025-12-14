#!/usr/bin/env python3
"""
RECALCUL MÉTRIQUES 44 DATES - MÉTHODE OPTIMISÉE SESSION 103
============================================================

Recalcule les métriques de tendance pour les 44 dates
en utilisant la nouvelle méthode validée (TOP-N + dynamique)

Sortie : CSV avec métriques correctes pour calibration
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]  # eurusd_news_impact_calculator_MPC
eurusd_clean = project_root / "eurusd_clean"
fx_impact_app = project_root / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))
sys.path.insert(0, str(eurusd_clean / "app"))

from config import get_db_path

# Import direct pour éviter __init__.py
sys.path.insert(0, str(eurusd_clean / "app" / "utils"))
from detect_trend_optimized import detect_trend_dynamic, calculate_trend_strength_score

print("=" * 80)
print("RECALCUL MÉTRIQUES 44 DATES - MÉTHODE OPTIMISÉE")
print("=" * 80)

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

print("\n📂 Chargement données...")

# Charger résultats existants (pour amp_parfaite, impact_real, etc.)
csv_path = eurusd_clean / "scripts" / "session102" / "analysis_real_data_complete.csv"

if not csv_path.exists():
    print(f"❌ Fichier introuvable : {csv_path}")
    sys.exit(1)

df = pd.read_csv(csv_path)
print(f"✅ Chargé {len(df)} dates")

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)
print(f"✅ Connexion DB : {db_path}")

# ============================================================================
# RECALCUL MÉTRIQUES
# ============================================================================

print(f"\n📊 Recalcul métriques tendance (méthode optimisée)...")
print(f"   Méthode : TOP-N extrema + détection dynamique")
print(f"   Fenêtre : 14 jours (au lieu de 72h)")
print("\n")

tendances_optimisees = []

for idx, row in df.iterrows():
    date_str = row['date']
    
    # Parser date
    try:
        event_dt = pd.to_datetime(date_str)
    except:
        print(f"⚠️  {date_str} : Erreur parsing date")
        tendances_optimisees.append(None)
        continue
    
    # Événement à 14:30 Bern (+02:00) → 12:30 UTC
    event_time_utc = event_dt.replace(hour=12, minute=30, second=0)
    
    # Détecter tendance avec méthode optimisée
    try:
        trend_info = detect_trend_dynamic(event_time_utc, conn)
        tendances_optimisees.append(trend_info)
        
        # Affichage progrès
        if trend_info:
            print(f"   ✅ {date_str} : {trend_info['duration_hours']:.1f}h, {trend_info['amplitude_pips']:.1f} pips, R²={trend_info['r_squared']:.3f}")
        else:
            print(f"   ⚠️  {date_str} : Aucune tendance détectée")
            
    except Exception as e:
        print(f"   ❌ {date_str} : Erreur - {e}")
        tendances_optimisees.append(None)
    
    # Progrès
    if (idx + 1) % 10 == 0:
        print(f"\n   Progression : {idx + 1}/{len(df)} dates traitées\n")

conn.close()

print(f"\n✅ Recalcul terminé")

# ============================================================================
# AJOUT COLONNES
# ============================================================================

print(f"\n📊 Création colonnes métriques optimisées...")

# Ajouter colonnes
df['trend_type_optimized'] = [t['type'] if t else None for t in tendances_optimisees]
df['trend_reversal_datetime'] = [t['reversal_datetime'] if t else None for t in tendances_optimisees]
df['trend_reversal_price'] = [t['reversal_price'] if t else None for t in tendances_optimisees]
df['trend_duration_optimized'] = [t['duration_hours'] if t else None for t in tendances_optimisees]
df['trend_amplitude_optimized'] = [t['amplitude_pips'] if t else None for t in tendances_optimisees]
df['trend_r2_optimized'] = [t['r_squared'] if t else None for t in tendances_optimisees]
df['trend_direction'] = [t['direction'] if t else None for t in tendances_optimisees]
df['trend_end_price'] = [t['end_price'] if t else None for t in tendances_optimisees]

# Score force
df['trend_strength_score'] = [calculate_trend_strength_score(t) for t in tendances_optimisees]

# ============================================================================
# STATISTIQUES
# ============================================================================

print(f"\n{'='*80}")
print("STATISTIQUES MÉTRIQUES OPTIMISÉES")
print(f"{'='*80}")

df_valid = df.dropna(subset=['trend_duration_optimized'])

print(f"\n✅ {len(df_valid)}/{len(df)} dates avec métriques valides ({len(df_valid)/len(df)*100:.1f}%)")

if len(df_valid) > 0:
    print(f"\n📊 Statistiques tendances :")
    print(f"   Durée moyenne     : {df_valid['trend_duration_optimized'].mean():.1f}h (std={df_valid['trend_duration_optimized'].std():.1f}h)")
    print(f"   Durée min/max     : {df_valid['trend_duration_optimized'].min():.1f}h / {df_valid['trend_duration_optimized'].max():.1f}h")
    print(f"\n   Amplitude moyenne : {df_valid['trend_amplitude_optimized'].mean():.1f} pips (std={df_valid['trend_amplitude_optimized'].std():.1f})")
    print(f"   Amplitude min/max : {df_valid['trend_amplitude_optimized'].min():.1f} / {df_valid['trend_amplitude_optimized'].max():.1f} pips")
    print(f"\n   R² moyen          : {df_valid['trend_r2_optimized'].mean():.3f}")
    print(f"   Score force moyen : {df_valid['trend_strength_score'].mean():.1f}/100")
    
    # Distribution directions
    print(f"\n   Distribution directions :")
    print(f"   - UP (haussier)   : {(df_valid['trend_direction'] == 'UP').sum()} ({(df_valid['trend_direction'] == 'UP').sum() / len(df_valid) * 100:.1f}%)")
    print(f"   - DOWN (baissier) : {(df_valid['trend_direction'] == 'DOWN').sum()} ({(df_valid['trend_direction'] == 'DOWN').sum() / len(df_valid) * 100:.1f}%)")
    
    # Comparaison vs anciennes métriques (si disponibles)
    if 'trend_duration_proper' in df.columns:
        print(f"\n📊 Comparaison vs anciennes métriques (72h) :")
        df_compare = df.dropna(subset=['trend_duration_proper', 'trend_duration_optimized'])
        if len(df_compare) > 0:
            print(f"   Durée ancienne    : {df_compare['trend_duration_proper'].mean():.1f}h")
            print(f"   Durée optimisée   : {df_compare['trend_duration_optimized'].mean():.1f}h")
            print(f"   Amélioration      : +{df_compare['trend_duration_optimized'].mean() - df_compare['trend_duration_proper'].mean():.1f}h ({(df_compare['trend_duration_optimized'].mean() / df_compare['trend_duration_proper'].mean() - 1) * 100:+.1f}%)")
            
            print(f"\n   Amplitude ancienne: {df_compare['trend_amplitude_proper'].mean():.1f} pips")
            print(f"   Amplitude optimisée: {df_compare['trend_amplitude_optimized'].mean():.1f} pips")
            print(f"   Amélioration      : +{df_compare['trend_amplitude_optimized'].mean() - df_compare['trend_amplitude_proper'].mean():.1f} pips ({(df_compare['trend_amplitude_optimized'].mean() / df_compare['trend_amplitude_proper'].mean() - 1) * 100:+.1f}%)")

# ============================================================================
# EXPORT
# ============================================================================

output_path = eurusd_clean / "scripts" / "session102" / "analysis_real_data_optimized.csv"
df.to_csv(output_path, index=False)

print(f"\n💾 Données exportées : {output_path.name}")
print(f"   Colonnes ajoutées :")
print(f"   - trend_type_optimized")
print(f"   - trend_reversal_datetime")
print(f"   - trend_reversal_price")
print(f"   - trend_duration_optimized")
print(f"   - trend_amplitude_optimized")
print(f"   - trend_r2_optimized")
print(f"   - trend_direction")
print(f"   - trend_end_price")
print(f"   - trend_strength_score")

print(f"\n{'='*80}")
print("RECALCUL TERMINÉ !")
print(f"{'='*80}")

print(f"\n🎯 Prochaine étape :")
print(f"   → Lancer calibration avec métriques optimisées")
print(f"   → python3 calibrate_amp_formula_optimized.py")
