#!/usr/bin/env python3
"""
Examen source prix 1m actuelle - Session 23
============================================
Vérifier d'où viennent les prix et leur qualité
"""

import duckdb
import pandas as pd

print("="*80)
print("🔍 EXAMEN SOURCE PRIX 1M ACTUELLE")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : STRUCTURE ET VOLUME
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 1 : STRUCTURE PRICES_1M")
print("="*80)

schema = conn.execute("DESCRIBE prices_1m").fetchall()
print(f"\nColonnes :")
for col in schema:
    print(f"   • {col[0]:20s} {col[1]}")

# Compter les lignes
total = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
print(f"\n   Total lignes : {total:,}")

# Période couverte
period = conn.execute("""
    SELECT 
        MIN(datetime) as first_date,
        MAX(datetime) as last_date
    FROM prices_1m
""").fetchone()

print(f"\n   Période couverte :")
print(f"      Début : {period[0]}")
print(f"      Fin   : {period[1]}")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : DONNÉES 11 SEPTEMBRE 2025
# ═══════════════════════════════════════════════════════════════

print("\n📊 ÉTAPE 2 : DONNÉES 11 SEPTEMBRE 2025 14:30")
print("="*80)

# Vérifier si on a des données pour cette date
sept11_count = conn.execute("""
    SELECT COUNT(*)
    FROM prices_1m
    WHERE datetime >= '2025-09-11 14:30:00'
      AND datetime <= '2025-09-11 15:00:00'
""").fetchone()[0]

print(f"\n   Données disponibles 14:30-15:00 : {sept11_count} lignes")

if sept11_count > 0:
    # Récupérer les données
    sept11_data = conn.execute("""
        SELECT 
            datetime,
            open,
            high,
            low,
            close,
            volume
        FROM prices_1m
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime <= '2025-09-11 15:00:00'
        ORDER BY datetime
    """).df()
    
    print(f"\n   Détails minute par minute :")
    print(f"   {'Time':20s} {'Open':>10s} {'High':>10s} {'Low':>10s} {'Close':>10s} {'Volume':>10s}")
    print(f"   " + "-"*75)
    
    for _, row in sept11_data.iterrows():
        print(f"   {str(row['datetime'])[:16]:20s} {row['open']:10.5f} {row['high']:10.5f} "
              f"{row['low']:10.5f} {row['close']:10.5f} {row['volume']:10d}")
    
    # Calculer le mouvement
    if len(sept11_data) >= 2:
        start_price = sept11_data['close'].iloc[0]
        max_price = sept11_data['high'].max()
        min_price = sept11_data['low'].min()
        end_price = sept11_data['close'].iloc[-1]
        
        movement_up = (max_price - start_price) * 10000
        movement_down = (start_price - min_price) * 10000
        
        print(f"\n   📊 ANALYSE MOUVEMENT :")
        print(f"      Prix début (14:30) : {start_price:.5f}")
        print(f"      Prix max           : {max_price:.5f}")
        print(f"      Prix min           : {min_price:.5f}")
        print(f"      Prix fin (15:00)   : {end_price:.5f}")
        print(f"      ")
        print(f"      Mouvement UP       : {movement_up:.2f} pips")
        print(f"      Mouvement DOWN     : {movement_down:.2f} pips")
        print(f"      Mouvement MAX      : {max(abs(movement_up), abs(movement_down)):.2f} pips")
        
        print(f"\n   💡 COMPARAISON SESSION 20 :")
        print(f"      Attendu Session 20 : 522 pips")
        print(f"      Calculé ici        : {max(abs(movement_up), abs(movement_down)):.2f} pips")
        print(f"      Écart              : {abs(522 - max(abs(movement_up), abs(movement_down))):.2f} pips")
        
        if max(abs(movement_up), abs(movement_down)) < 100:
            print(f"\n   ❌ PROBLÈME : Mouvement beaucoup trop faible !")
            print(f"      Les données prices_1m semblent incorrectes")
else:
    print(f"\n   ❌ Aucune donnée pour le 11 septembre 2025 !")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : VÉRIFIER AUTRES TABLES DE PRIX
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ÉTAPE 3 : AUTRES TABLES DE PRIX")
print("="*80)

tables = conn.execute("SHOW TABLES").fetchall()
price_tables = [t[0] for t in tables if 'price' in t[0].lower()]

print(f"\nTables de prix disponibles : {len(price_tables)}\n")

for table in price_tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    
    if count > 0:
        period = conn.execute(f"""
            SELECT MIN(datetime) as min_date, MAX(datetime) as max_date 
            FROM {table}
        """).fetchone()
        
        # Vérifier 11 sept
        sept11_check = 0
        try:
            sept11_check = conn.execute(f"""
                SELECT COUNT(*) 
                FROM {table}
                WHERE datetime >= '2025-09-11 14:30:00'
                  AND datetime <= '2025-09-11 15:00:00'
            """).fetchone()[0]
        except:
            pass
        
        marker = "🎯" if sept11_check > 0 else "  "
        print(f"{marker} {table:25s} : {count:8,} lignes | {str(period[0])[:10]} → {str(period[1])[:10]} | 11sept: {sept11_check}")

# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : RECOMMANDATIONS
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💡 ÉTAPE 4 : RECOMMANDATIONS")
print("="*80)

if sept11_count == 0:
    print("\n❌ PROBLÈME CRITIQUE : Aucune donnée 11 septembre dans prices_1m")
    print("\n💡 ACTIONS NÉCESSAIRES :")
    print("   1. Vérifier quelle table contient les bonnes données")
    print("   2. Réimporter les prix depuis la source correcte")
    print("   3. Valider que les nouveaux prix correspondent à Session 20")
elif sept11_count > 0 and max(abs(movement_up), abs(movement_down)) < 100:
    print("\n⚠️  DONNÉES PRÉSENTES MAIS SUSPECTES")
    print("\n💡 POSSIBILITÉS :")
    print("   A) Les prix sont dans une autre unité (pas EURUSD standard)")
    print("   B) Les données sont incomplètes ou erronées")
    print("   C) La période Session 20 était différente (30 min ? 60 min ?)")
    print("\n   RECOMMANDATION : Réimporter depuis source fiable")
else:
    print("\n✅ Les données semblent correctes")

# Chercher scripts d'import existants
print("\n📁 Scripts d'import à examiner :")
import os
import glob

scripts = []
for pattern in ['*import*.py', '*price*.py', '*eodhd*.py']:
    scripts.extend(glob.glob(pattern))

if scripts:
    print(f"\n   Trouvé {len(scripts)} scripts potentiels :")
    for script in sorted(set(scripts))[:10]:
        print(f"      • {script}")
else:
    print(f"\n   Aucun script d'import évident trouvé")

conn.close()

print("\n" + "="*80)
print("✅ EXAMEN TERMINÉ")
print("="*80)

print("\n📊 TOKENS : ~95,000 / 190,000 utilisés (50%)")
