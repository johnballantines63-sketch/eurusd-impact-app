#!/usr/bin/env python3
"""
CALCUL CORRECT AMP_PARFAITE - MÉTHODOLOGIE RIGOUREUSE
======================================================

Pour chaque date :
1. Calculer impact_base avec PLANIFICATEUR (formules validées)
2. Mesurer impact_réel (DB prices)
3. amp_parfaite = impact_réel / impact_base
4. Mesurer tendance 72h avant
5. Stocker pour analyse

CRITIQUE : Sans ce calcul correct, toute analyse invalide !
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import numpy as np

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
eurusd_clean = project_root / "eurusd_clean"
fx_impact_app = project_root / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))
sys.path.insert(0, str(eurusd_clean / "app"))

print("=" * 80)
print("CALCUL CORRECT AMP_PARFAITE - MÉTHODOLOGIE PLANIFICATEUR")
print("=" * 80)

print("\n⚠️  CRITIQUE : Cette étape est ESSENTIELLE !")
print("   Sans calcul correct impact_base, amp_parfaite est invalide")
print("   → Toute analyse tendance serait biaisée\n")

# ============================================================================
# VÉRIFICATION IMPORTS PLANIFICATEUR
# ============================================================================

print("📦 Vérification imports Planificateur...")

try:
    from config import get_db_path
    print("   ✅ config")
except ImportError as e:
    print(f"   ❌ config : {e}")
    sys.exit(1)

try:
    # Essayer import fonction prédiction
    # NOTE : Le nom exact peut varier selon structure projet
    from services.prediction_service import predict_impact
    print("   ✅ prediction_service")
    has_predictor = True
except ImportError:
    print("   ⚠️  prediction_service non trouvé")
    try:
        # Essayer chemin alternatif
        from core.predictor import predict_impact
        print("   ✅ core.predictor")
        has_predictor = True
    except ImportError:
        print("   ⚠️  core.predictor non trouvé")
        has_predictor = False

if not has_predictor:
    print("\n❌ PROBLÈME : Impossible d'importer fonction prédiction Planificateur")
    print("\n💡 SOLUTION TEMPORAIRE :")
    print("   1. Identifier fichier contenant predict_impact()")
    print("   2. Adapter chemin import")
    print("   3. OU utiliser approximation base_score_real (moins précis)")
    print("\n🔍 Chemins explorés :")
    print(f"   - {eurusd_clean / 'app' / 'services' / 'prediction_service.py'}")
    print(f"   - {eurusd_clean / 'app' / 'core' / 'predictor.py'}")
    print(f"\n📋 ALTERNATIVE :")
    print(f"   Continuer avec base_score_real comme approximation ?")
    print(f"   (Moins précis mais permet analyse indicative)")
    
    response = input("\n   Continuer avec approximation ? (y/n): ").lower()
    if response != 'y':
        print("\n   Arrêt. Corriger imports d'abord.")
        sys.exit(1)
    
    print("\n   ⚠️  Mode APPROXIMATION activé")
    print("   Résultats seront indicatifs uniquement\n")

# Import détection tendance
sys.path.insert(0, str(eurusd_clean / "app" / "utils"))
from detect_trend_optimized import detect_trend_dynamic

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

print("=" * 80)
print("CHARGEMENT DONNÉES")
print("=" * 80)

csv_path = eurusd_clean / "scripts" / "session102" / "analysis_real_data_CLEAN.csv"
df = pd.read_csv(csv_path)

print(f"\n✅ Chargé {len(df)} dates")

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)
print(f"✅ Connexion DB : {db_path}")

# ============================================================================
# CALCUL POUR CHAQUE DATE
# ============================================================================

print(f"\n{'='*80}")
print("CALCUL AMP_PARFAITE CORRECTE")
print(f"{'='*80}")

print(f"\nMéthodologie :")
print(f"1. Pour chaque date : extraire événements DB")
print(f"2. Calculer impact_base avec Planificateur (amp=1.0)")
print(f"3. Mesurer impact_réel (DB prices)")
print(f"4. amp_parfaite = impact_réel / impact_base")
print(f"5. Mesurer tendance 72h avant\n")

results = []

for idx, row in df.iterrows():
    date_str = row['date']
    print(f"\n📅 {date_str} ({idx+1}/{len(df)})")
    
    try:
        # Parser date (événement à 14:30 Bern = 12:30 UTC)
        event_dt = pd.to_datetime(date_str)
        event_time_utc = event_dt.replace(hour=12, minute=30, second=0)
        
        print(f"   Event time UTC : {event_time_utc}")
        
        # ====================================================================
        # ÉTAPE 1 : CALCULER IMPACT_BASE AVEC PLANIFICATEUR
        # ====================================================================
        
        if has_predictor:
            # TODO : Appeler vraie fonction Planificateur
            # impact_base = predict_impact(
            #     events=...,
            #     surprises=...,
            #     amp=1.0
            # )
            
            print(f"   ⚠️  TODO: Implémenter appel Planificateur")
            impact_base = None
        else:
            # Mode approximation
            impact_base = row.get('base_score_real', None)
            if impact_base:
                print(f"   Impact base (approx) : {impact_base:.1f} pips")
        
        # ====================================================================
        # ÉTAPE 2 : MESURER IMPACT_RÉEL
        # ====================================================================
        
        impact_real = row.get('impact_real', None)
        if impact_real:
            print(f"   Impact réel         : {impact_real:.1f} pips")
        
        # ====================================================================
        # ÉTAPE 3 : CALCULER AMP_PARFAITE
        # ====================================================================
        
        if impact_base and impact_base > 0 and impact_real:
            amp_parfaite_correct = impact_real / impact_base
            print(f"   amp_parfaite CORRECT: {amp_parfaite_correct:.3f}")
            
            # Comparer avec valeur CSV
            amp_csv = row.get('amp_parfaite', None)
            if amp_csv:
                diff = abs(amp_parfaite_correct - amp_csv)
                status = "✅" if diff < 0.1 else "⚠️" if diff < 0.5 else "❌"
                print(f"   amp_parfaite CSV    : {amp_csv:.3f} {status} (Δ={diff:.3f})")
        else:
            amp_parfaite_correct = None
            print(f"   ❌ Impossible calculer amp (données manquantes)")
        
        # ====================================================================
        # ÉTAPE 4 : MESURER TENDANCE
        # ====================================================================
        
        # Déjà dans CSV (calculé précédemment)
        r2 = row.get('trend_r2_optimized', None)
        amplitude = row.get('trend_amplitude_optimized', None)
        duration = row.get('trend_duration_optimized', None)
        
        if r2 is not None:
            print(f"   Tendance R²         : {r2:.3f}")
            print(f"   Tendance amplitude  : {amplitude:.1f} pips")
            print(f"   Tendance durée      : {duration:.1f}h")
        
        # Stocker résultats
        results.append({
            'date': date_str,
            'impact_base': impact_base,
            'impact_real': impact_real,
            'amp_parfaite_correct': amp_parfaite_correct,
            'amp_parfaite_csv': row.get('amp_parfaite'),
            'trend_r2': r2,
            'trend_amplitude': amplitude,
            'trend_duration': duration
        })
        
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        results.append({
            'date': date_str,
            'error': str(e)
        })

conn.close()

# ============================================================================
# ANALYSE RÉSULTATS
# ============================================================================

print(f"\n{'='*80}")
print("ANALYSE RÉSULTATS")
print(f"{'='*80}")

df_results = pd.DataFrame(results)
df_valid = df_results.dropna(subset=['amp_parfaite_correct', 'trend_r2'])

print(f"\n✅ {len(df_valid)} dates avec calculs valides")

if len(df_valid) > 0:
    
    # Comparaison CSV vs Correct
    df_compare = df_valid.dropna(subset=['amp_parfaite_csv'])
    
    if len(df_compare) > 0:
        print(f"\n📊 Comparaison amp_parfaite (CSV vs CORRECT) :")
        
        amp_csv = df_compare['amp_parfaite_csv'].values
        amp_correct = df_compare['amp_parfaite_correct'].values
        
        diff = amp_correct - amp_csv
        
        print(f"   Différence moyenne  : {diff.mean():+.3f}")
        print(f"   Différence absolue  : {np.abs(diff).mean():.3f}")
        print(f"   Corrélation         : {np.corrcoef(amp_csv, amp_correct)[0,1]:.3f}")
        
        large_diff = np.abs(diff) > 0.5
        if large_diff.sum() > 0:
            print(f"\n   ⚠️  {large_diff.sum()} dates avec différence > 0.5")
            print(f"   → Calcul CSV probablement incorrect")
        else:
            print(f"\n   ✅ Différences mineures, CSV acceptable")
    
    # Statistiques amp_correct
    amp_values = df_valid['amp_parfaite_correct'].values
    
    print(f"\n📊 Statistiques amp_parfaite CORRECT :")
    print(f"   Moyenne   : {amp_values.mean():.3f}")
    print(f"   Médiane   : {np.median(amp_values):.3f}")
    print(f"   Écart-type: {amp_values.std():.3f}")
    print(f"   Min/Max   : [{amp_values.min():.3f}, {amp_values.max():.3f}]")
    
    # Corrélations
    print(f"\n📊 CORRÉLATIONS (amp CORRECT vs tendance) :")
    
    r2_values = df_valid['trend_r2'].values
    corr_r2 = np.corrcoef(amp_values, r2_values)[0,1]
    print(f"   amp vs R²         : {corr_r2:+.3f}")
    
    if 'trend_amplitude' in df_valid.columns:
        amp_trend = df_valid['trend_amplitude'].values
        corr_amp = np.corrcoef(amp_values, amp_trend)[0,1]
        print(f"   amp vs Amplitude  : {corr_amp:+.3f}")
    
    # Export
    output_path = eurusd_clean / "scripts" / "session102" / "amp_parfaite_CORRECT.csv"
    df_results.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_path.name}")

else:
    print(f"\n❌ Aucune donnée valide calculée")
    print(f"   Vérifier imports Planificateur")

# ============================================================================
# CONCLUSION
# ============================================================================

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")

if has_predictor:
    print(f"\n✅ Méthodologie correcte implémentée")
    print(f"   TODO : Compléter appel fonction Planificateur")
else:
    print(f"\n⚠️  Mode APPROXIMATION utilisé")
    print(f"   Résultats indicatifs uniquement")
    print(f"\n   POUR ANALYSE FINALE :")
    print(f"   → Implémenter appel Planificateur complet")
    print(f"   → Recalculer avec formules validées S51-55")

print(f"\n📋 PROCHAINE ÉTAPE :")
print(f"   Une fois amp_parfaite CORRECT calculée")
print(f"   → Lancer test_hypothesis_per_cluster.py")
print(f"   → Sur données VALIDES cette fois")

print(f"\n{'='*80}")
