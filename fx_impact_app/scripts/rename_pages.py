# fx_impact_app/scripts/rename_pages.py
from __future__ import annotations
import argparse, shutil, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "fx_impact_app" / "streamlit_app" / "pages"
BACKUP_DIR = PAGES / ("_backup_" + datetime.now().strftime("%Y%m%d-%H%M%S"))

# Cible canonique: NN[a]-Slug-With-Dashes.py
def to_canonical(name: str) -> str:
    # accepte "7b_Simultaneous_Screener.py" ou "07b-Simultaneous_Screener.py"
    m = re.match(r"^(\d+)([a-z])?[-_](.+?)\.py$", name, re.IGNORECASE)
    if not m:  # laisse tel quel si pas compatible
        return name
    num = int(m.group(1))
    suf = (m.group(2) or "").lower()
    slug = m.group(3)
    slug = re.sub(r"[_\s]+", "-", slug)  # espaces/underscores -> tirets
    return f"{num:02d}{suf}-{slug}.py"

def main(apply: bool):
    PAGES.mkdir(parents=True, exist_ok=True)
    changes = []
    for p in sorted(PAGES.glob("*.py")):
        if p.name.startswith("_"):  # ignore helpers
            continue
        target = to_canonical(p.name)
        if target != p.name:
            changes.append((p.name, target))

    if not changes:
        print("✔ Rien à renommer.")
        return

    print("Propositions de renommage:")
    for a, b in changes:
        print(f" - {a}  ->  {b}")

    if not apply:
        print("\n(Mode dry-run) Ajoute --apply pour exécuter.")
        return

    BACKUP_DIR.mkdir(exist_ok=True)
    print(f"\nSauvegarde originale dans: {BACKUP_DIR}")
    for a, b in changes:
        src = PAGES / a
        dst = PAGES / b
        shutil.copy2(src, BACKUP_DIR / a)
        src.rename(dst)
    print("✔ Renommage terminé.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Exécuter le renommage (sinon dry-run).")
    args = ap.parse_args()
    main(args.apply)
