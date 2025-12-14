"""
VIDAGE TABLE EVENTS - Session 113
==================================

Vide complètement la table events avant réimport.

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

print("=" * 80)
print("VIDAGE TABLE EVENTS")
print("=" * 80)

# Vérifier sauvegarde
backup_path = DB_PATH.parent / "warehouse.duckdb copie"
if backup_path.exists():
    backup_size = backup_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Sauvegarde trouvée: {backup_path.name}")
    print(f"   Taille: {backup_size:.1f} MB")
else:
    print(f"\n⚠️  ATTENTION: Pas de sauvegarde trouvée !")
    print(f"   Créer une copie de {DB_PATH.name} avant de continuer")
    response = input("\nContinuer quand même ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Annulé")
        sys.exit(1)

# Compter événements actuels
conn = duckdb.connect(str(DB_PATH))

count_before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

print(f"\n📊 État actuel:")
print(f"   Événements: {count_before:,}")

if count_before == 0:
    print("\n✅ Table déjà vide, rien à faire")
    conn.close()
    sys.exit(0)

print(f"\n⚠️  ATTENTION: Suppression de {count_before:,} événements")
response = input("\nConfirmer la suppression ? (oui/non): ")

if response.lower() != 'oui':
    print("❌ Annulé")
    conn.close()
    sys.exit(1)

# Suppression
print("\n🗑️  Suppression en cours...")
conn.execute("DELETE FROM events")

count_after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

conn.close()

print(f"\n✅ TERMINÉ")
print("=" * 80)
print(f"Événements avant: {count_before:,}")
print(f"Événements après: {count_after:,}")
print(f"Supprimés: {count_before - count_after:,}")
print("=" * 80)

print("\n🚀 PROCHAINE ÉTAPE:")
print("   python scripts/session113/reimport_simple_test.py")
