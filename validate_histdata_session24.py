#!/usr/bin/env python3
"""
Script Session 24 : Télécharger et valider données HistData.com
Objectif : Vérifier si le 11 septembre donne 522 pips avec une autre source
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
from zipfile import ZipFile
from io import BytesIO
import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from fx_impact_app.src.config import get_db_path

def download_histdata_month(year, month, pair='eurusd'):
    """
    Télécharge les données 1m depuis HistData.com
    
    Args:
        year: Année (ex: 2025)
        month: Mois (ex: 9)
        pair: Paire forex (défaut: 'eurusd')
    
    Returns:
        DataFrame avec colonnes [datetime, open, high, low, close, volume]
    """
    # Format du nom de fichier HistData
    # Ex: HISTDATA_COM_ASCII_EURUSD_M12025.zip
    month_str = f"{month:02d}"
    filename = f"HISTDATA_COM_ASCII_{pair.upper()}_M1{year}{month_str}.zip"
    
    # URL de téléchargement
    # HistData utilise un pattern spécifique
    base_url = "https://www.histdata.com/download-free-forex-historical-data/"
    download_url = f"http://www.histdata.com/get.php?file=ninja-trader/{pair.upper()}/{year}/{month_str}/{filename}"
    
    print(f"📥 Téléchargement depuis HistData.com...")
    print(f"   Pair: {pair.upper()}")
    print(f"   Période: {year}-{month_str}")
    print(f"   URL: {download_url}")
    
    try:
        # Télécharger le fichier ZIP
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(download_url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code != 200:
            print(f"❌ Erreur téléchargement: {response.status_code}")
            print(f"   Peut-être que les données ne sont pas disponibles pour cette période")
            print(f"\n💡 Alternative: Télécharger manuellement depuis:")
            print(f"   https://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/{year}/{month_str}")
            return None
        
        print(f"✅ Fichier téléchargé: {len(response.content)} bytes")
        
        # Extraire le ZIP
        with ZipFile(BytesIO(response.content)) as zip_file:
            # Lister les fichiers dans le ZIP
            file_list = zip_file.namelist()
            print(f"   Fichiers dans ZIP: {file_list}")
            
            # Trouver le fichier CSV
            csv_file = None
            for f in file_list:
                if f.endswith('.csv') or f.endswith('.txt'):
                    csv_file = f
                    break
            
            if not csv_file:
                print(f"❌ Aucun fichier CSV trouvé dans le ZIP")
                return None
            
            print(f"   Extraction: {csv_file}")
            
            # Lire le CSV
            with zip_file.open(csv_file) as f:
                # Format HistData: YYYYMMDD HHMMSS,Open,High,Low,Close,Volume
                df = pd.read_csv(f, 
                                names=['datetime_str', 'open', 'high', 'low', 'close', 'volume'],
                                header=None)
                
                print(f"✅ {len(df)} lignes lues")
                
                # Parser datetime
                # Format: 20250901 000000
                df['datetime'] = pd.to_datetime(df['datetime_str'], format='%Y%m%d %H%M%S', utc=True)
                
                # Supprimer colonne temporaire
                df = df.drop('datetime_str', axis=1)
                
                # Réordonner colonnes
                df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
                
                # Convertir en numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Supprimer NaN
                df = df.dropna(subset=['datetime', 'close'])
                
                # Trier
                df = df.sort_values('datetime').reset_index(drop=True)
                
                print(f"✅ {len(df)} lignes après nettoyage")
                print(f"   Période: {df['datetime'].min()} → {df['datetime'].max()}")
                
                return df
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_september_11_histdata(df):
    """
    Valide le 11 septembre 2025 sur données HistData
    
    Args:
        df: DataFrame HistData
    
    Returns:
        Tuple (phase1_pips, pullback_pips, is_valid)
    """
    if df is None or df.empty:
        return None, None, False
    
    print(f"\n{'=' * 80}")
    print("🔍 VALIDATION CRITIQUE: 11 SEPTEMBRE 2025 (HISTDATA)")
    print("=" * 80)
    
    # Phase 1: 14:30-14:45 UTC
    phase1_df = df[
        (df['datetime'] >= '2025-09-11 14:30:00') &
        (df['datetime'] < '2025-09-11 14:45:00')
    ].copy()
    
    if phase1_df.empty:
        print("❌ Aucune donnée pour Phase 1 (14:30-14:45)")
        return None, None, False
    
    print(f"\n📊 Phase 1 (14:30-14:45 UTC):")
    print(f"   Lignes: {len(phase1_df)}")
    print(f"   Période: {phase1_df.iloc[0]['datetime']} → {phase1_df.iloc[-1]['datetime']}")
    
    # Calculer mouvement Phase 1
    start_price = phase1_df.iloc[0]['close']
    high_price = phase1_df['high'].max()
    low_price = phase1_df['low'].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    phase1_pips = max(move_up, move_down)
    direction_p1 = "UP" if move_up > move_down else "DOWN"
    
    print(f"   Prix départ: {start_price:.5f}")
    print(f"   Prix HIGH: {high_price:.5f}")
    print(f"   Prix LOW: {low_price:.5f}")
    print(f"   Mouvement UP: {move_up:.2f} pips")
    print(f"   Mouvement DOWN: {move_down:.2f} pips")
    print(f"   ➡️ PHASE 1: {phase1_pips:.2f} pips {direction_p1}")
    
    # Pullback: 14:45-15:00 UTC
    pullback_df = df[
        (df['datetime'] >= '2025-09-11 14:45:00') &
        (df['datetime'] < '2025-09-11 15:00:00')
    ].copy()
    
    pullback_pips = None
    if not pullback_df.empty:
        print(f"\n📊 Pullback (14:45-15:00 UTC):")
        print(f"   Lignes: {len(pullback_df)}")
        
        # Prix de départ pullback = prix fin phase 1
        pullback_start = phase1_df.iloc[-1]['close']
        pullback_high = pullback_df['high'].max()
        pullback_low = pullback_df['low'].min()
        
        # Mouvement inverse attendu
        if direction_p1 == "UP":
            # Phase 1 UP → Pullback DOWN attendu
            pullback_pips = (pullback_start - pullback_low) * 10000
            print(f"   Pullback DOWN: {pullback_pips:.2f} pips")
        else:
            # Phase 1 DOWN → Pullback UP attendu
            pullback_pips = (pullback_high - pullback_start) * 10000
            print(f"   Pullback UP: {pullback_pips:.2f} pips")
    
    # Validation
    print(f"\n🎯 VALIDATION:")
    print(f"   Phase 1 attendu: 522 pips ±50")
    print(f"   Phase 1 obtenu: {phase1_pips:.2f} pips")
    print(f"   Écart: {abs(phase1_pips - 522):.2f} pips")
    
    if pullback_pips:
        print(f"   Pullback attendu: 114 pips ±20")
        print(f"   Pullback obtenu: {pullback_pips:.2f} pips")
        print(f"   Écart: {abs(pullback_pips - 114):.2f} pips")
    
    # Critère de succès
    is_valid = 450 <= phase1_pips <= 600
    
    if is_valid:
        print(f"\n   ✅ VALIDATION RÉUSSIE!")
        print(f"   Les données HistData correspondent à la référence MT5")
    else:
        print(f"\n   ❌ VALIDATION ÉCHOUÉE!")
        print(f"   Les données HistData ne correspondent PAS à MT5")
    
    return phase1_pips, pullback_pips, is_valid

def compare_sources(df_histdata, db_path):
    """
    Compare HistData vs EODHD pour le 11 septembre
    """
    print(f"\n{'=' * 80}")
    print("📊 COMPARAISON HISTDATA vs EODHD")
    print("=" * 80)
    
    with duckdb.connect(db_path) as con:
        # Récupérer EODHD pour même période
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime < '2025-09-11 14:45:00'
        ORDER BY datetime
        """
        
        df_eodhd = con.execute(query).df()
        
        if df_eodhd.empty:
            print("❌ Pas de données EODHD pour comparaison")
            return
        
        # Calculer mouvement EODHD
        eodhd_start = df_eodhd.iloc[0]['close']
        eodhd_high = df_eodhd['high'].max()
        eodhd_low = df_eodhd['low'].min()
        eodhd_up = (eodhd_high - eodhd_start) * 10000
        eodhd_down = (eodhd_start - eodhd_low) * 10000
        eodhd_movement = max(eodhd_up, eodhd_down)
        
        # HistData
        phase1_hist = df_histdata[
            (df_histdata['datetime'] >= '2025-09-11 14:30:00') &
            (df_histdata['datetime'] < '2025-09-11 14:45:00')
        ]
        
        if phase1_hist.empty:
            print("❌ Pas de données HistData pour comparaison")
            return
        
        hist_start = phase1_hist.iloc[0]['close']
        hist_high = phase1_hist['high'].max()
        hist_low = phase1_hist['low'].min()
        hist_up = (hist_high - hist_start) * 10000
        hist_down = (hist_start - hist_low) * 10000
        hist_movement = max(hist_up, hist_down)
        
        print(f"\n📊 Comparaison 11 septembre 14:30-14:45:")
        print(f"\n   EODHD:")
        print(f"      Prix départ: {eodhd_start:.5f}")
        print(f"      Mouvement: {eodhd_movement:.2f} pips")
        print(f"      Lignes: {len(df_eodhd)}")
        
        print(f"\n   HistData:")
        print(f"      Prix départ: {hist_start:.5f}")
        print(f"      Mouvement: {hist_movement:.2f} pips")
        print(f"      Lignes: {len(phase1_hist)}")
        
        print(f"\n   Différence:")
        price_diff = abs(eodhd_start - hist_start) * 10000
        movement_diff = abs(eodhd_movement - hist_movement)
        
        print(f"      Prix départ: {price_diff:.2f} pips")
        print(f"      Mouvement: {movement_diff:.2f} pips")
        
        if price_diff < 2 and movement_diff < 5:
            print(f"\n   ✅ Sources COHÉRENTES (différence minime)")
        elif movement_diff < 20:
            print(f"\n   ⚠️ Sources SIMILAIRES (petites variations normales)")
        else:
            print(f"\n   ❌ Sources DIFFÉRENTES (écart significatif)")

def save_to_temp_table(df, db_path):
    """Sauvegarde HistData dans une table temporaire pour comparaison"""
    print(f"\n💾 Sauvegarde dans table temporaire...")
    
    with duckdb.connect(db_path) as con:
        con.execute("SET TimeZone='UTC'")
        
        # Créer table temporaire
        con.execute("""
            CREATE TABLE IF NOT EXISTS prices_1m_histdata (
                datetime TIMESTAMPTZ,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE
            )
        """)
        
        # Vider si existe
        con.execute("DELETE FROM prices_1m_histdata")
        
        # Insérer
        con.register("histdata_temp", df)
        con.execute("""
            INSERT INTO prices_1m_histdata
            SELECT * FROM histdata_temp
        """)
        con.unregister("histdata_temp")
        
        count = con.execute("SELECT COUNT(*) FROM prices_1m_histdata").fetchone()[0]
        print(f"✅ {count} lignes sauvegardées dans prices_1m_histdata")

def main():
    print("=" * 80)
    print("🔍 SESSION 24 - VALIDATION HISTDATA.COM")
    print("=" * 80)
    print("\nObjectif: Vérifier si septembre 2025 donne 522 pips avec HistData")
    
    db_path = get_db_path()
    
    # Télécharger septembre 2025
    print(f"\n{'=' * 80}")
    print("ÉTAPE 1: TÉLÉCHARGEMENT HISTDATA")
    print("=" * 80)
    
    df = download_histdata_month(2025, 9, 'eurusd')
    
    if df is None:
        print("\n" + "=" * 80)
        print("⚠️ TÉLÉCHARGEMENT AUTOMATIQUE ÉCHOUÉ")
        print("=" * 80)
        print("\n💡 Solution manuelle:")
        print("1. Aller sur: https://www.histdata.com/download-free-forex-data/")
        print("2. Sélectionner:")
        print("   - ASCII format")
        print("   - 1 Minute Bar Quotes")
        print("   - EUR/USD")
        print("   - 2025")
        print("   - September")
        print("3. Télécharger le ZIP")
        print("4. Extraire le CSV")
        print("5. Relancer ce script avec le chemin du CSV:")
        print("   python3 validate_histdata_session24.py --csv /chemin/vers/fichier.csv")
        return False
    
    # Validation 11 septembre
    print(f"\n{'=' * 80}")
    print("ÉTAPE 2: VALIDATION 11 SEPTEMBRE")
    print("=" * 80)
    
    phase1, pullback, is_valid = validate_september_11_histdata(df)
    
    # Comparaison avec EODHD
    print(f"\n{'=' * 80}")
    print("ÉTAPE 3: COMPARAISON SOURCES")
    print("=" * 80)
    
    compare_sources(df, db_path)
    
    # Sauvegarder pour analyses futures
    save_to_temp_table(df, db_path)
    
    # Résumé final
    print(f"\n{'=' * 80}")
    print("📋 RÉSUMÉ FINAL")
    print("=" * 80)
    
    print(f"\n🎯 Résultats:")
    print(f"   Phase 1 HistData: {phase1:.2f} pips" if phase1 else "   Phase 1: NON CALCULÉ")
    print(f"   Pullback HistData: {pullback:.2f} pips" if pullback else "   Pullback: NON CALCULÉ")
    print(f"   Attendu MT5 Session 20: 522 pips Phase 1, 114 pips Pullback")
    
    if is_valid:
        print(f"\n✅ CONCLUSION: HistData VALIDE les 522 pips")
        print(f"   → MT5 Session 20 avait raison")
        print(f"   → EODHD a des données de moins bonne qualité")
        print(f"\n💡 RECOMMANDATION:")
        print(f"   Utiliser HistData.com comme source de données")
        print(f"   Télécharger 2022-2025 complet")
    else:
        print(f"\n❌ CONCLUSION: HistData NE valide PAS les 522 pips")
        print(f"   → MT5 Session 20 avait probablement une anomalie")
        print(f"   → EODHD et HistData sont cohérents")
        print(f"\n💡 RECOMMANDATION:")
        print(f"   Continuer avec EODHD (source fiable et automatisée)")
        print(f"   Accepter que le 11 septembre = ~47 pips")
    
    return is_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
