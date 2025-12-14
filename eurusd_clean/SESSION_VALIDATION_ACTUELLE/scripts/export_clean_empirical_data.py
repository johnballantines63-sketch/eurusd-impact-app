#!/usr/bin/env python3
"""
Export Propre pour Analyse Empirique Directionnelle EURUSD

Objectif :
1. Générer prices.csv (3 ans, M1, UTC strict)
2. Générer events.csv (US + EU/BCE + techniques, format LONG)
3. Validation complète avec rapport

Date : 2025-12-07
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
if not DB_PATH.exists():
    DB_PATH = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb')

OUTPUT_DIR = Path(__file__).parent.parent / 'outputs'

# Période : 3 ans glissants
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=3*365)

def floor_to_minute(dt):
    """Snap timestamp vers le bas à la minute"""
    return dt.replace(second=0, microsecond=0)

def export_prices():
    """Exporte prix EURUSD sur 3 ans (M1, UTC)"""
    print("="*80)
    print("📊 EXPORT PRIX (prices.csv)")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    start_str = START_DATE.strftime('%Y-%m-%d %H:%M:%S')
    end_str = END_DATE.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Période : {start_str} → {end_str}")
    print()
    
    # Essayer d'abord prices_1m_v (vue avec ts_utc)
    query = f"""
    SELECT 
        ts_utc,
        close
    FROM prices_1m_v
    WHERE ts_utc >= '{start_str}'::TIMESTAMP
      AND ts_utc < '{end_str}'::TIMESTAMP
    ORDER BY ts_utc
    """
    
    try:
        df = conn.execute(query).df()
    except Exception as e:
        print(f"⚠️  Erreur avec prices_1m_v : {e}")
        print("   Tentative avec prices_1m...")
        
        # Fallback sur prices_1m avec conversion datetime
        query = f"""
        SELECT 
            datetime as ts_utc,
            close
        FROM prices_1m
        WHERE datetime >= '{start_str}'::TIMESTAMP
          AND datetime < '{end_str}'::TIMESTAMP
        ORDER BY datetime
        """
        df = conn.execute(query).df()
    
    conn.close()
    
    if len(df) == 0:
        print("❌ Aucun prix trouvé")
        return None, None
    
    # Convertir ts_utc en datetime si string
    if df['ts_utc'].dtype == 'object':
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # S'assurer que ts_utc est timezone-aware UTC
    if df['ts_utc'].dt.tz is None:
        # Supposer UTC si pas de timezone
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)
    else:
        # Convertir en UTC si autre timezone
        df['ts_utc'] = df['ts_utc'].dt.tz_convert('UTC')
    
    # Snap vers minute (floor)
    df['ts_utc'] = df['ts_utc'].apply(floor_to_minute)
    
    # Formater en ISO 8601 UTC
    df['ts_utc'] = df['ts_utc'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')
    
    # Réorganiser colonnes
    df_output = df[['ts_utc', 'close']].copy()
    
    # Sauvegarder
    output_file = OUTPUT_DIR / 'prices.csv'
    df_output.to_csv(output_file, index=False)
    
    print(f"✅ Prix exportés : {output_file}")
    print(f"   Total : {len(df_output):,} lignes")
    print(f"   Colonnes : {', '.join(df_output.columns)}")
    print()
    
    return df_output, output_file

def export_events():
    """Exporte événements US + EU/BCE + techniques (format LONG)"""
    print("="*80)
    print("📅 EXPORT ÉVÉNEMENTS (events.csv)")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    start_str = START_DATE.strftime('%Y-%m-%d')
    end_str = END_DATE.strftime('%Y-%m-%d')
    
    print(f"Période : {start_str} → {end_str}")
    print()
    
    # Vérifier pays disponibles
    countries_query = """
    SELECT DISTINCT country 
    FROM events 
    WHERE country IS NOT NULL
    ORDER BY country
    """
    countries = conn.execute(countries_query).df()['country'].tolist()
    print(f"Pays disponibles : {', '.join(countries)}")
    print()
    
    # Extraire événements US + EU (incluant ECB, BCE, etc.)
    # EU peut être codé comme 'EU', 'EC', 'EZ', 'DE', 'FR', etc.
    query = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.actual,
        e.estimate,
        e.previous,
        ef.family,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) >= '{start_str}'
      AND DATE(e.ts_utc) < '{end_str}'
      AND (
          e.country = 'US' 
          OR e.country IN ('EU', 'EC', 'EZ', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'FI', 'IE', 'GR')
          OR LOWER(e.event_title) LIKE '%ecb%'
          OR LOWER(e.event_title) LIKE '%bce%'
          OR LOWER(e.event_title) LIKE '%european central bank%'
          OR LOWER(e.event_key) LIKE '%ecb%'
          OR LOWER(e.event_key) LIKE '%bce%'
      )
    ORDER BY e.ts_utc, e.event_key
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if len(df) == 0:
        print("❌ Aucun événement trouvé")
        return None, None
    
    print(f"✅ {len(df)} événements trouvés")
    print()
    
    # Normaliser event_key (lowercase, espaces normalisés)
    df['event_key'] = df['event_key'].astype(str).str.lower().str.strip()
    df['event_key'] = df['event_key'].str.replace(r'\s+', ' ', regex=True)
    
    # Convertir ts_utc en datetime
    if df['ts_utc'].dtype == 'object':
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # S'assurer UTC
    if df['ts_utc'].dt.tz is None:
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)
    else:
        df['ts_utc'] = df['ts_utc'].dt.tz_convert('UTC')
    
    # Snap vers minute (floor)
    df['ts_utc'] = df['ts_utc'].apply(floor_to_minute)
    
    # Formater en ISO 8601 UTC
    df['ts_utc'] = df['ts_utc'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')
    
    # Réorganiser colonnes selon format demandé
    df_output = df[[
        'ts_utc',
        'event_key',
        'family',
        'country',
        'actual',
        'estimate',
        'previous',
        'event_title'
    ]].copy()
    
    # Remplacer NaN par chaîne vide pour actual/estimate/previous si besoin
    # (ou garder NaN selon préférence)
    
    # Sauvegarder
    output_file = OUTPUT_DIR / 'events.csv'
    df_output.to_csv(output_file, index=False, na_rep='')
    
    print(f"✅ Événements exportés : {output_file}")
    print(f"   Total : {len(df_output):,} lignes")
    print(f"   Colonnes : {', '.join(df_output.columns)}")
    print()
    
    return df_output, output_file

def generate_validation_report(df_prices, df_events, prices_file, events_file):
    """Génère rapport de validation"""
    print("="*80)
    print("📋 RAPPORT DE VALIDATION")
    print("="*80)
    print()
    
    report_lines = []
    report_lines.append("="*80)
    report_lines.append("RAPPORT DE VALIDATION - EXPORT EMPIRIQUE EURUSD")
    report_lines.append("="*80)
    report_lines.append("")
    report_lines.append(f"Date génération : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 1. PRIX
    report_lines.append("─"*80)
    report_lines.append("1. PRIX (prices.csv)")
    report_lines.append("─"*80)
    
    if df_prices is not None and len(df_prices) > 0:
        # Convertir ts_utc en datetime pour analyse
        df_prices_ts = df_prices.copy()
        df_prices_ts['ts_utc'] = pd.to_datetime(df_prices_ts['ts_utc'])
        
        min_ts = df_prices_ts['ts_utc'].min()
        max_ts = df_prices_ts['ts_utc'].max()
        
        report_lines.append(f"Fichier : {prices_file}")
        report_lines.append(f"Range temporel : {min_ts} → {max_ts}")
        report_lines.append(f"Total lignes : {len(df_prices):,}")
        report_lines.append(f"Colonnes : {', '.join(df_prices.columns)}")
        
        # Fréquence dominante
        df_prices_ts['dt'] = df_prices_ts['ts_utc'].diff()
        mode_dt = df_prices_ts['dt'].mode()
        if len(mode_dt) > 0:
            mode_minutes = mode_dt.iloc[0].total_seconds() / 60
            report_lines.append(f"Fréquence dominante : {mode_minutes:.0f} minutes")
        
        # Trous dans grille
        expected_minutes = (max_ts - min_ts).total_seconds() / 60
        actual_count = len(df_prices)
        completeness = (actual_count / expected_minutes * 100) if expected_minutes > 0 else 0
        report_lines.append(f"Complétude : {completeness:.2f}% ({actual_count}/{expected_minutes:.0f} minutes attendues)")
        
        # Stats prix
        report_lines.append(f"Prix min : {df_prices['close'].min():.5f}")
        report_lines.append(f"Prix max : {df_prices['close'].max():.5f}")
        report_lines.append(f"Prix moyen : {df_prices['close'].mean():.5f}")
    else:
        report_lines.append("❌ Aucune donnée prix")
    
    report_lines.append("")
    
    # 2. ÉVÉNEMENTS
    report_lines.append("─"*80)
    report_lines.append("2. ÉVÉNEMENTS (events.csv)")
    report_lines.append("─"*80)
    
    if df_events is not None and len(df_events) > 0:
        # Convertir ts_utc en datetime pour analyse
        df_events_ts = df_events.copy()
        df_events_ts['ts_utc'] = pd.to_datetime(df_events_ts['ts_utc'])
        
        min_ts = df_events_ts['ts_utc'].min()
        max_ts = df_events_ts['ts_utc'].max()
        
        report_lines.append(f"Fichier : {events_file}")
        report_lines.append(f"Range temporel : {min_ts} → {max_ts}")
        report_lines.append(f"Total lignes : {len(df_events):,}")
        report_lines.append(f"Colonnes : {', '.join(df_events.columns)}")
        
        # Event keys uniques
        unique_keys = df_events['event_key'].nunique()
        report_lines.append(f"Event keys uniques : {unique_keys}")
        
        # Top 10 familles
        top_families = df_events['family'].value_counts().head(10)
        report_lines.append("")
        report_lines.append("Top 10 familles :")
        for family, count in top_families.items():
            report_lines.append(f"   {family}: {count}")
        
        # Pays
        countries = df_events['country'].value_counts()
        report_lines.append("")
        report_lines.append("Répartition par pays :")
        for country, count in countries.items():
            report_lines.append(f"   {country}: {count}")
        
        # Champs manquants
        report_lines.append("")
        report_lines.append("Champs manquants :")
        for col in ['actual', 'estimate', 'previous']:
            if col in df_events.columns:
                missing = df_events[col].isna().sum()
                pct = (missing / len(df_events) * 100) if len(df_events) > 0 else 0
                report_lines.append(f"   {col}: {missing} ({pct:.1f}%)")
    else:
        report_lines.append("❌ Aucune donnée événement")
    
    report_lines.append("")
    
    # 3. ALIGNEMENT TEMPOREL
    report_lines.append("─"*80)
    report_lines.append("3. ALIGNEMENT TEMPOREL")
    report_lines.append("─"*80)
    
    if df_prices is not None and df_events is not None:
        prices_min = pd.to_datetime(df_prices['ts_utc']).min()
        prices_max = pd.to_datetime(df_prices['ts_utc']).max()
        events_min = pd.to_datetime(df_events['ts_utc']).min()
        events_max = pd.to_datetime(df_events['ts_utc']).max()
        
        report_lines.append(f"Prix range : {prices_min} → {prices_max}")
        report_lines.append(f"Events range : {events_min} → {events_max}")
        
        overlap_start = max(prices_min, events_min)
        overlap_end = min(prices_max, events_max)
        
        if overlap_start <= overlap_end:
            report_lines.append(f"✅ Overlap : {overlap_start} → {overlap_end}")
        else:
            report_lines.append("⚠️  Pas d'overlap temporel")
    
    report_lines.append("")
    report_lines.append("="*80)
    
    # Sauvegarder rapport
    report_text = "\n".join(report_lines)
    report_file = OUTPUT_DIR / 'validation_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # Afficher
    print(report_text)
    
    return report_file

def main():
    print("="*80)
    print("EXPORT PROPRE POUR ANALYSE EMPIRIQUE EURUSD")
    print("="*80)
    print()
    
    # Export prix
    df_prices, prices_file = export_prices()
    
    # Export événements
    df_events, events_file = export_events()
    
    # Générer rapport
    if df_prices is not None or df_events is not None:
        report_file = generate_validation_report(df_prices, df_events, prices_file, events_file)
        
        print()
        print("="*80)
        print("✅ EXPORT TERMINÉ")
        print("="*80)
        print()
        print("📁 Fichiers générés :")
        if prices_file:
            print(f"   📊 {prices_file}")
        if events_file:
            print(f"   📅 {events_file}")
        if report_file:
            print(f"   📋 {report_file}")
        print()

if __name__ == '__main__':
    main()


