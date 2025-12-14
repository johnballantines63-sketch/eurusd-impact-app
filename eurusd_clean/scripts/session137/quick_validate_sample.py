"""
VALIDATION RAPIDE ÉCHANTILLON DOUBLE_WAVE
Session 138

Mission:
- Extraire détails prix de 3 cas DOUBLE_WAVE
- Vérifier visuellement les patterns
- Valider métriques (peaks, troughs, ratios)

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import timedelta

# =============================================================================
# CONFIGURATION
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
SAMPLE_CSV = Path(__file__).parent / "sample_doublewave_verification.csv"

# Sélectionner 3 cas pour validation rapide
TEST_CASES = [
    17,   # DOUBLE_WAVE_UP - impact 95.4p, dip 0.328 (proche borne)
    1,    # DOUBLE_WAVE_UP - impact 53.3p, dip 0.465 (médian)
    310,  # DOUBLE_WAVE_DOWN - impact 80.1p, rise 0.682 (cas #310)
]

print("=" * 80)
print("VALIDATION RAPIDE ÉCHANTILLON - 3 CAS")
print("=" * 80)

# =============================================================================
# CHARGER ÉCHANTILLON
# =============================================================================

print("\n📊 CHARGEMENT ÉCHANTILLON")
print("-" * 80)

df_sample = pd.read_csv(SAMPLE_CSV)
df_sample['movement_datetime'] = pd.to_datetime(df_sample['movement_datetime'], utc=True)

print(f"   ✅ {len(df_sample)} cas dans échantillon")

# Connecter DB
conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"   ✅ Connexion DB établie")

# =============================================================================
# FONCTION EXTRACTION DÉTAILS
# =============================================================================

def extract_case_details(movement_id, df_sample, conn):
    """Extraire détails prix pour un cas"""
    
    row = df_sample[df_sample['movement_id'] == movement_id].iloc[0]
    
    print(f"\n{'=' * 80}")
    print(f"CAS #{movement_id} - {row['pattern_type']}")
    print(f"{'=' * 80}")
    
    print(f"\n📋 INFORMATIONS MOUVEMENT")
    print(f"   datetime     : {row['movement_datetime']}")
    print(f"   direction    : {row['direction']}")
    print(f"   impact       : {row['impact_pips']:.1f} pips")
    print(f"   num_events   : {row['num_events']}")
    print(f"   total_score  : {row['total_score']:.1f}")
    
    # Charger prix
    start_time = row['movement_datetime'] - timedelta(minutes=10)
    end_time = row['movement_datetime'] + timedelta(minutes=120)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    if len(df_prices) == 0:
        print("\n   ❌ Aucun prix disponible")
        return
    
    baseline = df_prices['close'].iloc[0]
    
    print(f"\n📊 PRIX")
    print(f"   Baseline     : {baseline:.5f}")
    print(f"   Points prix  : {len(df_prices)}")
    print(f"   Période      : {df_prices['datetime'].iloc[0]} → {df_prices['datetime'].iloc[-1]}")
    
    # Métriques pattern
    print(f"\n🎯 MÉTRIQUES PATTERN")
    
    if row['pattern_type'] == 'DOUBLE_WAVE_UP':
        peak1_amp = row['peak1_amplitude_pips']
        peak2_amp = row['peak2_amplitude_pips']
        dip_ratio = row['dip_ratio']
        peak1_time = row['peak1_time_min']
        peak2_time = row['peak2_time_min']
        
        print(f"   Peak1 amplitude  : {peak1_amp:.1f} pips @ {peak1_time:.1f} min")
        print(f"   Peak2 amplitude  : {peak2_amp:.1f} pips @ {peak2_time:.1f} min")
        print(f"   Dip ratio        : {dip_ratio:.3f} {'✅' if 0.30 <= dip_ratio <= 0.70 else '❌'}")
        print(f"   Trough price     : {row['trough_price']:.5f}")
        
        # Calculs manuels pour vérification
        peak1_price = row['peak1_price']
        trough_price = row['trough_price']
        
        dip_pips = (peak1_price - trough_price) * 10000
        dip_ratio_calc = dip_pips / peak1_amp if peak1_amp > 0 else 0
        
        print(f"\n   ✅ VÉRIFICATION CALCULS:")
        print(f"      Dip (peak1-trough) : {dip_pips:.1f} pips")
        print(f"      Dip ratio calculé  : {dip_ratio_calc:.3f}")
        print(f"      Match dip_ratio    : {'✅' if abs(dip_ratio - dip_ratio_calc) < 0.01 else '❌'}")
        
    elif row['pattern_type'] == 'DOUBLE_WAVE_DOWN':
        trough1_amp = row['trough1_amplitude_pips']
        trough2_amp = row['trough2_amplitude_pips']
        rise_ratio = row['rise_ratio']
        trough1_time = row['trough1_time_min']
        trough2_time = row['trough2_time_min']
        
        print(f"   Trough1 amplitude: {trough1_amp:.1f} pips @ {trough1_time:.1f} min")
        print(f"   Trough2 amplitude: {trough2_amp:.1f} pips @ {trough2_time:.1f} min")
        print(f"   Rise ratio       : {rise_ratio:.3f} {'✅' if 0.30 <= rise_ratio <= 0.70 else '❌'}")
        print(f"   Peak price       : {row['peak_price']:.5f}")
        
        # Calculs manuels
        trough1_price = row['trough1_price']
        peak_price = row['peak_price']
        
        rise_pips = (peak_price - trough1_price) * 10000
        rise_ratio_calc = rise_pips / trough1_amp if trough1_amp > 0 else 0
        
        print(f"\n   ✅ VÉRIFICATION CALCULS:")
        print(f"      Rise (peak-trough1): {rise_pips:.1f} pips")
        print(f"      Rise ratio calculé : {rise_ratio_calc:.3f}")
        print(f"      Match rise_ratio   : {'✅' if abs(rise_ratio - rise_ratio_calc) < 0.01 else '❌'}")
    
    # Statistiques prix dans fenêtre
    print(f"\n📈 STATISTIQUES PRIX (fenêtre 130min)")
    print(f"   HIGH max  : {df_prices['high'].max():.5f} (+{(df_prices['high'].max()-baseline)*10000:.1f} pips)")
    print(f"   LOW min   : {df_prices['low'].min():.5f} ({(df_prices['low'].min()-baseline)*10000:.1f} pips)")
    print(f"   Range     : {(df_prices['high'].max() - df_prices['low'].min())*10000:.1f} pips")
    
    # Validation cohérence
    print(f"\n✅ VALIDATION COHÉRENCE")
    
    if row['direction'] == 'UP':
        if row['pattern_type'].endswith('_UP'):
            print(f"   ✅ Direction cohérente (UP → pattern _UP)")
        else:
            print(f"   ❌ Direction incohérente")
    elif row['direction'] == 'DOWN':
        if row['pattern_type'].endswith('_DOWN'):
            print(f"   ✅ Direction cohérente (DOWN → pattern _DOWN)")
        else:
            print(f"   ❌ Direction incohérente")
    
    if row['pattern_type'] == 'DOUBLE_WAVE_UP':
        if row['peak1_amplitude_pips'] >= 20:
            print(f"   ✅ Peak1 >= 20 pips (MIN_AMPLITUDE)")
        else:
            print(f"   ❌ Peak1 < 20 pips")
            
        if row['trough_price'] > baseline:
            print(f"   ✅ Trough > baseline")
        else:
            print(f"   ⚠️ Trough <= baseline (CRASH_RECOVERY ?)")
            
    elif row['pattern_type'] == 'DOUBLE_WAVE_DOWN':
        if row['trough1_amplitude_pips'] >= 20:
            print(f"   ✅ Trough1 >= 20 pips (MIN_AMPLITUDE)")
        else:
            print(f"   ❌ Trough1 < 20 pips")
            
        if row['peak_price'] < baseline:
            print(f"   ✅ Peak < baseline")
        else:
            print(f"   ⚠️ Peak >= baseline (SPIKE_REVERSAL ?)")
    
    # Événements
    if pd.notna(row['event_keys']):
        events = str(row['event_keys']).split(',')
        print(f"\n📅 ÉVÉNEMENTS ({len(events)})")
        for i, event in enumerate(events[:5], 1):
            print(f"   {i}. {event.strip()}")
        if len(events) > 5:
            print(f"   ... et {len(events)-5} autres")

# =============================================================================
# EXTRACTION 3 CAS
# =============================================================================

for case_id in TEST_CASES:
    if case_id in df_sample['movement_id'].values:
        extract_case_details(case_id, df_sample, conn)
    else:
        print(f"\n⚠️ Cas #{case_id} non trouvé dans échantillon")

# =============================================================================
# SYNTHÈSE
# =============================================================================

print(f"\n{'=' * 80}")
print("SYNTHÈSE VALIDATION RAPIDE")
print(f"{'=' * 80}")

print(f"\n📊 3 CAS VÉRIFIÉS:")
print(f"   - Cas #17  : DOUBLE_WAVE_UP (impact 95.4p, dip 0.328)")
print(f"   - Cas #1   : DOUBLE_WAVE_UP (impact 53.3p, dip 0.465)")
print(f"   - Cas #310 : DOUBLE_WAVE_DOWN (impact 80.1p, rise 0.682)")

print(f"\n✅ POINTS DE CONTRÔLE:")
print(f"   1. Métriques cohérentes avec calculs manuels")
print(f"   2. Direction patterns cohérente avec direction mouvement")
print(f"   3. MIN_AMPLITUDE >= 20 pips respecté")
print(f"   4. dip/rise_ratio dans [0.30, 0.70]")
print(f"   5. Position trough/peak vs baseline cohérente")

print(f"\n🎯 CONCLUSION:")
print(f"   Si tous les checks sont ✅ → Algorithme v2 validé")
print(f"   Si des ❌ apparaissent → Investigation nécessaire")

print(f"\n{'=' * 80}")

conn.close()
