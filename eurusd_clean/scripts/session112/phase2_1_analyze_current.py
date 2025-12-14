#!/usr/bin/env python3
"""
ANALYSE SITUATION ACTUELLE - Avant restructuration
===================================================

Identifie tous les fichiers et DB pour préparer la migration.

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 2
"""

from pathlib import Path
import os

print("="*80)
print("🔍 ANALYSE SITUATION ACTUELLE")
print("="*80)

base = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")

# ══════════════════════════════════════════════════════════════════════
# 1. LOCALISER TOUTES LES DB
# ══════════════════════════════════════════════════════════════════════

print("\n📊 BASES DE DONNÉES:")
print("-"*80)

dbs = list(base.rglob("warehouse.duckdb"))

for i, db in enumerate(dbs, 1):
    size_mb = db.stat().st_size / (1024 * 1024)
    rel_path = db.relative_to(base)
    print(f"\n{i}. {rel_path}")
    print(f"   Taille: {size_mb:.2f} MB")
    
    # Vérifier si vue prices_bern existe
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        
        # Tester vue
        try:
            count = con.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
            print(f"   ✅ Vue prices_bern: {count:,} lignes")
            has_vue = True
        except:
            print(f"   ❌ Pas de vue prices_bern")
            has_vue = False
        
        # Compter events
        count_events = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        print(f"   Events: {count_events:,}")
        
        # Compter prices
        count_prices = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        print(f"   Prices: {count_prices:,}")
        
        if has_vue:
            print(f"   🎯 DB PRINCIPALE (avec vue)")
        
        con.close()
    except Exception as e:
        print(f"   ⚠️ Erreur lecture: {e}")

# ══════════════════════════════════════════════════════════════════════
# 2. MODULES PYTHON VALIDÉS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📦 MODULES PYTHON VALIDÉS:")
print("-"*80)

modules = [
    "fx_impact_app/src/formulas_validated.py",
    "fx_impact_app/src/impact_measurement.py",
    "fx_impact_app/src/event_loader.py",
    "fx_impact_app/src/cluster_impact_calculator.py",
]

for module in modules:
    path = base / module
    if path.exists():
        size_kb = path.stat().st_size / 1024
        print(f"✅ {module} ({size_kb:.1f} KB)")
    else:
        print(f"❌ {module} (introuvable)")

# ══════════════════════════════════════════════════════════════════════
# 3. PLANIFICATEURS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📱 PLANIFICATEURS STREAMLIT:")
print("-"*80)

planif_dir = base / "fx_impact_app" / "streamlit_app" / "pages"

if planif_dir.exists():
    planifs = sorted(planif_dir.glob("*Planificateur*.py"))
    
    print(f"\n{len(planifs)} versions trouvées:")
    
    for p in planifs:
        size_kb = p.stat().st_size / 1024
        print(f"  • {p.name} ({size_kb:.1f} KB)")
    
    # Identifier le plus récent
    if planifs:
        newest = max(planifs, key=lambda x: x.stat().st_mtime)
        print(f"\n🎯 Plus récent: {newest.name}")
else:
    print("❌ Dossier planificateurs introuvable")

# ══════════════════════════════════════════════════════════════════════
# 4. SCRIPTS VALIDÉS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🧪 SCRIPTS VALIDÉS:")
print("-"*80)

scripts_dir = base / "eurusd_clean" / "scripts"

if scripts_dir.exists():
    sessions = sorted([d for d in scripts_dir.iterdir() if d.is_dir()])
    
    print(f"\n{len(sessions)} sessions de scripts:")
    for s in sessions[-5:]:  # 5 dernières
        count = len(list(s.glob("*.py")))
        print(f"  • {s.name}: {count} scripts")
else:
    print("❌ Dossier scripts introuvable")

# ══════════════════════════════════════════════════════════════════════
# 5. DOCUMENTATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📚 DOCUMENTATION:")
print("-"*80)

docs_dir = base / "eurusd_clean" / "docs"

if docs_dir.exists():
    docs = sorted(docs_dir.glob("*.md"))
    
    print(f"\n{len(docs)} fichiers markdown:")
    for d in docs:
        size_kb = d.stat().st_size / 1024
        print(f"  • {d.name} ({size_kb:.1f} KB)")
else:
    print("❌ Dossier docs introuvable")

# ══════════════════════════════════════════════════════════════════════
# RECOMMANDATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💡 RECOMMANDATION RESTRUCTURATION")
print("="*80)

print(f"""
Structure proposée:

eurusd_clean/                     ← TOUT CENTRALISÉ
├── data/
│   └── warehouse.duckdb         ← DB UNIQUE (avec vue prices_bern)
│
├── src/
│   ├── core/                    ← Modules validés
│   │   ├── __init__.py
│   │   ├── formulas_validated.py
│   │   ├── impact_measurement.py
│   │   ├── event_loader.py
│   │   └── cluster_impact_calculator.py
│   ├── analysis/                ← Scripts d'analyse
│   └── config.py                ← Configuration centralisée
│
├── streamlit_app/               ← Application Streamlit
│   ├── app.py                   ← Page principale
│   ├── pages/
│   │   └── Planificateur.py    ← UN SEUL validé
│   └── components/              ← Composants réutilisables
│
├── scripts/                     ← Scripts de validation
│   ├── session112/              ← Session actuelle
│   └── archive/                 ← Anciennes sessions
│
├── docs/                        ← Documentation
│   ├── SOLUTION_DEFINITIVE_TIMEZONE.md
│   ├── PROJECT_STATE.md
│   └── guides/
│
└── tests/                       ← Tests unitaires (futur)

Avantages:
✅ Tout au même endroit
✅ Structure claire et logique
✅ Un seul chemin vers la DB
✅ Facile à naviguer
✅ Prêt pour production
""")

print("="*80)
print("FIN ANALYSE")
print("="*80)
