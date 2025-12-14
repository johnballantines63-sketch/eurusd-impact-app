#!/usr/bin/env python3
"""
Vérification et Correction Mesures Réelles
===========================================

Objectif : Vérifier que le CSV contient les bonnes mesures en comparant
avec les données DB et l'anchor_time réel du pipeline
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from core.price_loader_finnhub import measure_impact_from_finnhub, get_finnhub_prices_at_event_time
from scripts.run_pipeline_complete import PipelineExecutor

# Fichiers CSV
CSV_IMPACTS = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures.csv'
CSV_TEST_RESULTS = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'test_pipeline_mouvements_forts.csv'

print('='*100)
print('VÉRIFICATION ET CORRECTION MESURES RÉELLES')
print('='*100)
print()

# Charger CSV existants
if CSV_IMPACTS.exists():
    df_impacts = pd.read_csv(CSV_IMPACTS)
    print(f'✅ CSV impacts chargé : {len(df_impacts)} dates')
else:
    df_impacts = pd.DataFrame()
    print(f'⚠️ CSV impacts non trouvé, création nouveau')

if CSV_TEST_RESULTS.exists():
    df_test = pd.read_csv(CSV_TEST_RESULTS)
    print(f'✅ CSV test résultats chargé : {len(df_test)} dates')
else:
    df_test = pd.DataFrame()
    print(f'⚠️ CSV test résultats non trouvé')

print()

# Initialiser pipeline
executor = PipelineExecutor(DB_PATH, verbose=False)

# Dates à vérifier (depuis CSV ou liste fixe)
if not df_impacts.empty:
    dates_to_check = df_impacts['date'].unique().tolist()
else:
    dates_to_check = [
        '2025-09-11',
        '2025-08-01',
        '2025-11-20',
        '2025-10-10',
        '2025-06-23',
        '2025-01-15',
        '2025-05-29',
        '2024-09-11',
        '2025-02-12',
        '2025-11-26',
    ]

print(f'📅 Dates à vérifier : {len(dates_to_check)}')
print()

results = []

for date_str in dates_to_check:
    print('='*100)
    print(f'📅 VÉRIFICATION : {date_str}')
    print('='*100)
    print()
    
    try:
        # 1. Obtenir anchor_time réel depuis pipeline
        print('1️⃣ OBTENIR ANCHOR_TIME RÉEL')
        print('-'*100)
        
        result_pipeline = executor.execute_complete_pipeline(date_str)
        
        if not result_pipeline.get('success'):
            print(f'❌ Erreur pipeline: {result_pipeline.get("error")}')
            results.append({
                'date': date_str,
                'success': False,
                'error': result_pipeline.get('error', 'Unknown')
            })
            continue
        
        cluster_info = result_pipeline.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        if anchor_time is None:
            print(f'❌ Anchor time non trouvé')
            results.append({
                'date': date_str,
                'success': False,
                'error': 'Anchor time not found'
            })
            continue
        
        # Convertir en datetime si nécessaire
        if isinstance(anchor_time, str):
            anchor_time = pd.to_datetime(anchor_time)
        
        print(f'Anchor time réel : {anchor_time}')
        print()
        
        # 2. Mesurer impact réel avec anchor_time correct depuis DB directement
        print('2️⃣ MESURER IMPACT RÉEL AVEC ANCHOR_TIME CORRECT')
        print('-'*100)
        
        # S'assurer que anchor_time a timezone
        if anchor_time.tzinfo is None:
            tz_bern = pytz.timezone('Europe/Zurich')
            anchor_time = tz_bern.localize(anchor_time)
        
        # Charger prix depuis DB directement
        df_prices = get_finnhub_prices_at_event_time(
            db_path=DB_PATH,
            event_timestamp_bern=anchor_time,
            lookback_minutes=5,
            lookahead_minutes=120
        )
        
        if df_prices.empty:
            print(f'❌ Erreur: Aucun prix trouvé pour {anchor_time}')
            results.append({
                'date': date_str,
                'success': False,
                'error': 'No price data found'
            })
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        # Trouver baseline (OPEN première bougie à ou après anchor_time)
        prices_at_anchor = df_prices[df_prices['datetime'] >= anchor_time]
        if not prices_at_anchor.empty:
            baseline_measured = prices_at_anchor.iloc[0]['open']
            baseline_time_measured = prices_at_anchor.iloc[0]['datetime']
        else:
            # Fallback: CLOSE dernière bougie avant anchor_time
            prices_before = df_prices[df_prices['datetime'] < anchor_time]
            if not prices_before.empty:
                baseline_measured = prices_before.iloc[-1]['close']
                baseline_time_measured = prices_before.iloc[-1]['datetime']
            else:
                print(f'❌ Erreur: Impossible de trouver baseline')
                results.append({
                    'date': date_str,
                    'success': False,
                    'error': 'Cannot find baseline'
                })
                continue
        
        # Calculer impact bidirectionnel
        prices_after = df_prices[df_prices['datetime'] >= anchor_time].copy()
        prices_after['pips_high'] = (prices_after['high'] - baseline_measured) * 10000
        prices_after['pips_low'] = (baseline_measured - prices_after['low']) * 10000
        
        peak_high = prices_after['pips_high'].max()
        peak_low = prices_after['pips_low'].max()
        
        if peak_high > peak_low:
            impact_measured = peak_high
            direction_measured = 1  # UP
            peak_idx = prices_after['pips_high'].idxmax()
            peak_measured = prices_after.loc[peak_idx, 'high']
            peak_time_measured = prices_after.loc[peak_idx, 'datetime']
        else:
            impact_measured = peak_low
            direction_measured = -1  # DOWN
            peak_idx = prices_after['pips_low'].idxmax()
            peak_measured = prices_after.loc[peak_idx, 'low']
            peak_time_measured = prices_after.loc[peak_idx, 'datetime']
        
        print(f'Baseline mesurée : {baseline_time_measured.strftime("%H:%M")} @ {baseline_measured:.5f}')
        print(f'Peak mesuré : {peak_time_measured.strftime("%H:%M")} @ {peak_measured:.5f}')
        print(f'Direction : {"UP" if direction_measured == 1 else "DOWN" if direction_measured == -1 else "UNKNOWN"}')
        print(f'Impact mesuré : {impact_measured:.2f} pips')
        print()
        
        # 3. Comparer avec CSV existant
        print('3️⃣ COMPARAISON AVEC CSV')
        print('-'*100)
        
        csv_row = df_impacts[df_impacts['date'] == date_str] if not df_impacts.empty else pd.DataFrame()
        
        if not csv_row.empty:
            csv_impact = csv_row.iloc[0].get('impact_real_pips')
            csv_event_time = csv_row.iloc[0].get('event_time', '14:30')
            csv_timezone = csv_row.iloc[0].get('timezone', 'Europe/Zurich')
            
            print(f'CSV impact : {csv_impact:.2f} pips' if pd.notna(csv_impact) else 'CSV impact : Non disponible')
            print(f'CSV event_time : {csv_event_time}')
            print(f'CSV timezone : {csv_timezone}')
            print()
            
            if pd.notna(csv_impact):
                diff = abs(impact_measured - csv_impact)
                pct_diff = (diff / csv_impact * 100) if csv_impact > 0 else 0
                
                print(f'Différence : {diff:.2f} pips ({pct_diff:.1f}%)')
                
                if diff < 1:
                    print(f'✅ Valeurs identiques (différence < 1 pip)')
                elif diff < 5:
                    print(f'✅ Valeurs proches (différence < 5 pips)')
                elif diff < 20:
                    print(f'⚠️ Différence modérée (différence < 20 pips)')
                else:
                    print(f'❌ Différence importante (différence ≥ 20 pips)')
                    print(f'   → CSV doit être mis à jour')
            else:
                print(f'⚠️ CSV impact non disponible')
        else:
            print(f'⚠️ Date non trouvée dans CSV')
            csv_impact = None
        
        # 4. Analyser prix réels depuis DB
        print()
        print('4️⃣ ANALYSE PRIX RÉELS DEPUIS DB')
        print('-'*100)
        
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Fenêtre événement : ±2h autour de anchor_time
        window_start = anchor_time - pd.Timedelta(hours=1)
        window_end = anchor_time + pd.Timedelta(hours=2)
        
        query_m1 = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start.isoformat()}' 
          AND datetime <= '{window_end.isoformat()}'
        ORDER BY datetime ASC
        """
        
        df_m1 = conn.execute(query_m1).df()
        conn.close()
        
        if not df_m1.empty:
            df_m1['datetime'] = pd.to_datetime(df_m1['datetime'])
            df_m1 = df_m1.set_index('datetime')
            
            # Trouver baseline réelle (prix à anchor_time)
            prices_at_anchor = df_m1[df_m1.index >= anchor_time]
            if not prices_at_anchor.empty:
                baseline_real = prices_at_anchor.iloc[0]['open']
                baseline_real_time = prices_at_anchor.index[0]
            else:
                baseline_real = df_m1.iloc[0]['close']
                baseline_real_time = df_m1.index[0]
            
            # Trouver pic réel dans fenêtre événement
            peak_real_event = df_m1['high'].max()
            peak_real_event_time = df_m1['high'].idxmax()
            real_amp_event = (peak_real_event - baseline_real) * 10000
            
            print(f'Baseline réelle (à anchor_time) : {baseline_real_time.strftime("%H:%M")} @ {baseline_real:.5f}')
            print(f'Pic réel (fenêtre événement ±2h) : {peak_real_event_time.strftime("%H:%M")} @ {peak_real_event:.5f}')
            print(f'Amplitude réelle (fenêtre événement) : {real_amp_event:.2f} pips')
            print()
            
            # Comparer avec impact mesuré
            diff_measure = abs(impact_measured - real_amp_event)
            print(f'🔍 COMPARAISON MESURE vs RÉEL DB')
            print('-'*100)
            print(f'Impact mesuré (measure_impact_from_finnhub) : {impact_measured:.2f} pips')
            print(f'Amplitude réelle DB (fenêtre événement) : {real_amp_event:.2f} pips')
            print(f'Différence : {diff_measure:.2f} pips')
            
            if diff_measure < 1:
                print(f'✅ Impact mesuré correspond à amplitude réelle DB')
            elif diff_measure < 5:
                print(f'✅ Impact mesuré proche de amplitude réelle DB')
            else:
                print(f'⚠️ Différence entre impact mesuré et amplitude réelle DB')
                print(f'   → Possible problème baseline ou fenêtre mesure')
        else:
            print(f'❌ Aucune donnée M1 trouvée')
            real_amp_event = None
        
        # Enregistrer résultats
        results.append({
            'date': date_str,
            'success': True,
            'anchor_time': str(anchor_time),
            'baseline_measured': baseline_measured,
            'peak_measured': peak_measured,
            'peak_time_measured': str(peak_time_measured) if peak_time_measured else None,
            'impact_measured': impact_measured,
            'direction_measured': direction_measured,
            'real_amp_event': real_amp_event if 'real_amp_event' in locals() else None,
            'csv_impact': csv_impact if 'csv_impact' in locals() and pd.notna(csv_impact) else None,
            'diff_csv': abs(impact_measured - csv_impact) if 'csv_impact' in locals() and pd.notna(csv_impact) else None,
            'diff_db': abs(impact_measured - real_amp_event) if 'real_amp_event' in locals() and real_amp_event is not None else None
        })
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        results.append({
            'date': date_str,
            'success': False,
            'error': str(e)
        })
        print()

# Créer DataFrame résultats
df_results = pd.DataFrame(results)

# Sauvegarder résultats
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'verification_mesures_reelles.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_results.to_csv(output_file, index=False)
print(f'💾 Résultats sauvegardés : {output_file}')
print()

# Créer CSV corrigé avec nouvelles mesures
print('5️⃣ CRÉATION CSV CORRIGÉ')
print('-'*100)

df_corrected = df_results[df_results['success'] == True].copy()
df_corrected = df_corrected[[
    'date',
    'anchor_time',
    'impact_measured',
    'baseline_measured',
    'peak_measured',
    'peak_time_measured',
    'direction_measured',
    'real_amp_event',
    'csv_impact',
    'diff_csv',
    'diff_db'
]].copy()

df_corrected.columns = [
    'date',
    'anchor_time',
    'impact_real_pips',
    'baseline_price',
    'peak_price',
    'peak_time',
    'direction',
    'real_amp_event_db',
    'csv_impact_old',
    'diff_csv',
    'diff_db'
]

# Ajouter colonnes timezone et notes
df_corrected['timezone'] = 'Europe/Zurich'
df_corrected['notes'] = df_corrected.apply(
    lambda row: f"Mesuré avec anchor_time réel: {row['anchor_time']}", axis=1
)

# Réorganiser colonnes
df_corrected = df_corrected[[
    'date',
    'anchor_time',
    'timezone',
    'impact_real_pips',
    'baseline_price',
    'peak_price',
    'peak_time',
    'direction',
    'real_amp_event_db',
    'csv_impact_old',
    'diff_csv',
    'diff_db',
    'notes'
]]

# Sauvegarder CSV corrigé
output_file_corrected = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures_CORRIGE.csv'
df_corrected.to_csv(output_file_corrected, index=False)
print(f'💾 CSV corrigé sauvegardé : {output_file_corrected}')
print()

# Résumé
print('='*100)
print('📊 RÉSUMÉ')
print('='*100)
print()

df_success = df_results[df_results['success'] == True]

if not df_success.empty:
    print(f'✅ Dates vérifiées avec succès : {len(df_success)}/{len(dates_to_check)}')
    print()
    
    # Statistiques différences CSV
    if 'diff_csv' in df_success.columns:
        diffs_csv = df_success['diff_csv'].dropna()
        if not diffs_csv.empty:
            print(f'📈 STATISTIQUES DIFFÉRENCES CSV')
            print('-'*100)
            print(f'   Moyenne : {diffs_csv.mean():.2f} pips')
            print(f'   Médiane : {diffs_csv.median():.2f} pips')
            print(f'   Max : {diffs_csv.max():.2f} pips')
            print()
            
            # Classification
            identiques = len(diffs_csv[diffs_csv < 1])
            proches = len(diffs_csv[(diffs_csv >= 1) & (diffs_csv < 5)])
            moderees = len(diffs_csv[(diffs_csv >= 5) & (diffs_csv < 20)])
            importantes = len(diffs_csv[diffs_csv >= 20])
            
            print(f'📊 CLASSIFICATION DIFFÉRENCES CSV')
            print('-'*100)
            print(f'   ✅ Identiques (< 1 pip) : {identiques}/{len(diffs_csv)} ({identiques/len(diffs_csv)*100:.1f}%)')
            print(f'   ✅ Proches (1-5 pips) : {proches}/{len(diffs_csv)} ({proches/len(diffs_csv)*100:.1f}%)')
            print(f'   ⚠️ Modérées (5-20 pips) : {moderees}/{len(diffs_csv)} ({moderees/len(diffs_csv)*100:.1f}%)')
            print(f'   ❌ Importantes (≥ 20 pips) : {importantes}/{len(diffs_csv)} ({importantes/len(diffs_csv)*100:.1f}%)')
            print()
    
    # Statistiques différences DB
    if 'diff_db' in df_success.columns:
        diffs_db = df_success['diff_db'].dropna()
        if not diffs_db.empty:
            print(f'📈 STATISTIQUES DIFFÉRENCES DB')
            print('-'*100)
            print(f'   Moyenne : {diffs_db.mean():.2f} pips')
            print(f'   Médiane : {diffs_db.median():.2f} pips')
            print(f'   Max : {diffs_db.max():.2f} pips')
            print()
    
    # Dates avec différences importantes
    if 'diff_csv' in df_success.columns:
        dates_importantes = df_success[df_success['diff_csv'] >= 20]
        if not dates_importantes.empty:
            print(f'⚠️ DATES AVEC DIFFÉRENCES IMPORTANTES (≥ 20 pips)')
            print('-'*100)
            for _, row in dates_importantes.iterrows():
                print(f'   {row["date"]} : CSV {row["csv_impact"]:.2f} pips vs Mesuré {row["impact_measured"]:.2f} pips (diff: {row["diff_csv"]:.2f} pips)')
            print()

print('='*100)
print('✅ VÉRIFICATION TERMINÉE')
print('='*100)

