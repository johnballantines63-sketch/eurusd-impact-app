"""
VÉRIFICATION INTÉGRITÉ SESSION 88
Vérifie que tous les fichiers sont corrects avant tests
"""

import sys
from pathlib import Path

print("="*80)
print("🔍 VÉRIFICATION INTÉGRITÉ SESSION 88")
print("="*80)

errors = []
warnings = []
success = []

# ============================================================================
# 1. VÉRIFIER FICHIERS EXISTENT
# ============================================================================

print("\n📁 Vérification fichiers...")

files_to_check = [
    ('fx_impact_app/src/formulas_validated.py', 'CRITIQUE'),
    ('eurusd_clean/scripts/session84/validate_predictions_vs_reality.py', 'CRITIQUE'),
    ('eurusd_clean/scripts/session88/test_amplification_0108.py', 'CRITIQUE'),
    ('eurusd_clean/scripts/session88/test_multi_dates.py', 'CRITIQUE'),
    ('eurusd_clean/scripts/session88/adjust_coefficient.py', 'IMPORTANT'),
    ('eurusd_clean/scripts/session88/README.md', 'IMPORTANT'),
    ('eurusd_clean/docs/SESSION88_RAPPORT.md', 'IMPORTANT'),
    ('eurusd_clean/docs/MESSAGE_SESSION88_SESSION89.md', 'IMPORTANT'),
]

base_path = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC')

for file_path, importance in files_to_check:
    full_path = base_path / file_path
    
    if full_path.exists():
        success.append(f"✅ {file_path}")
    else:
        if importance == 'CRITIQUE':
            errors.append(f"❌ MANQUANT CRITIQUE: {file_path}")
        else:
            warnings.append(f"⚠️ Manquant: {file_path}")

# ============================================================================
# 2. VÉRIFIER FONCTION AMPLIFICATION ÉTENDUE
# ============================================================================

print("\n🔧 Vérification fonction amplification étendue...")

try:
    sys.path.insert(0, str(base_path / 'fx_impact_app/src'))
    from formulas_validated import calculate_amplification_extended
    
    # Tests de base
    test_cases = [
        (10, 1.0, "Zone 1"),
        (22.5, 1.75, "Zone 2 - S51"),
        (33, 2.61, "Zone 2 - S51"),
        (50, 3.21, "Zone 3"),
        (100, 5.0, "Zone 3"),
        (500, 9.69, "Zone 4 CIBLE"),
    ]
    
    all_ok = True
    for surprise, expected, label in test_cases:
        result = calculate_amplification_extended(surprise)
        diff = abs(result - expected)
        
        if diff < 0.05:  # Tolérance 0.05
            success.append(f"✅ {label}: {surprise}% → {result:.2f}x (attendu {expected:.2f}x)")
        else:
            errors.append(f"❌ {label}: {surprise}% → {result:.2f}x (attendu {expected:.2f}x, écart {diff:.2f})")
            all_ok = False
    
    if all_ok:
        success.append("✅ Tous les tests amplification étendue OK")
    
except Exception as e:
    errors.append(f"❌ Erreur import calculate_amplification_extended: {e}")

# ============================================================================
# 3. VÉRIFIER INTÉGRATION SCRIPT VALIDATION
# ============================================================================

print("\n🔗 Vérification intégration script validation...")

try:
    script_path = base_path / 'eurusd_clean/scripts/session84/validate_predictions_vs_reality.py'
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier import
    if 'calculate_amplification_extended' in content:
        success.append("✅ Import calculate_amplification_extended trouvé")
    else:
        errors.append("❌ Import calculate_amplification_extended MANQUANT")
    
    # Vérifier utilisation
    if 'amplification = calculate_amplification_extended(surprise_max)' in content:
        success.append("✅ Utilisation calculate_amplification_extended ligne ~148")
    else:
        warnings.append("⚠️ Utilisation calculate_amplification_extended non détectée (peut être formatting)")
    
    # Vérifier ancien code supprimé
    if 'amplification = min(surprise_max / 10, 2.5)' in content:
        warnings.append("⚠️ Ancien code amplification toujours présent (possible commentaire)")
    else:
        success.append("✅ Ancien code amplification supprimé")
    
except Exception as e:
    errors.append(f"❌ Erreur vérification script validation: {e}")

# ============================================================================
# 4. VÉRIFIER BASE DE DONNÉES
# ============================================================================

print("\n💾 Vérification base de données...")

try:
    import duckdb
    
    db_path = base_path / 'fx_impact_app/data/warehouse.duckdb'
    
    if db_path.exists():
        success.append(f"✅ Base de données trouvée: {db_path.name}")
        
        # Test connexion
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Vérifier tables
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = ['events', 'event_families', 'prices_1m']
        for table in required_tables:
            if table in table_names:
                success.append(f"✅ Table {table} existe")
            else:
                errors.append(f"❌ Table {table} MANQUANTE")
        
        # Vérifier données 01.08.2025
        result = conn.execute("""
            SELECT COUNT(*) 
            FROM events 
            WHERE DATE(ts_utc) = '2025-08-01' 
              AND country = 'US'
        """).fetchone()
        
        if result and result[0] > 0:
            success.append(f"✅ Données 01.08.2025 trouvées ({result[0]} événements)")
        else:
            warnings.append("⚠️ Aucun événement US le 01.08.2025")
        
        conn.close()
        
    else:
        errors.append(f"❌ Base de données MANQUANTE: {db_path}")
    
except Exception as e:
    errors.append(f"❌ Erreur vérification base de données: {e}")

# ============================================================================
# 5. RÉSUMÉ
# ============================================================================

print("\n" + "="*80)
print("📊 RÉSUMÉ VÉRIFICATION")
print("="*80)

print(f"\n✅ Succès : {len(success)}")
for msg in success:
    print(f"   {msg}")

if warnings:
    print(f"\n⚠️ Avertissements : {len(warnings)}")
    for msg in warnings:
        print(f"   {msg}")

if errors:
    print(f"\n❌ Erreurs : {len(errors)}")
    for msg in errors:
        print(f"   {msg}")

print("\n" + "="*80)

if errors:
    print("❌ VÉRIFICATION ÉCHOUÉE - Corriger erreurs avant tests")
    print("="*80)
    sys.exit(1)
elif warnings:
    print("⚠️ VÉRIFICATION OK avec avertissements - Tests possibles")
    print("="*80)
    sys.exit(0)
else:
    print("✅✅✅ VÉRIFICATION COMPLÈTE RÉUSSIE !")
    print("="*80)
    print("\n🚀 PRÊT POUR TESTS !")
    print("\nCommandes :")
    print("  cd eurusd_clean/scripts/session88")
    print("  python test_amplification_0108.py")
    print("="*80)
    sys.exit(0)
