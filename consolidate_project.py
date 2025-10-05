# consolidate_project.py
from pathlib import Path

def consolidate():
    output = Path("project_complete.txt")
    root = Path("fx_impact_app")
    
    if not root.exists():
        print(f"❌ Dossier {root} introuvable")
        print(f"Répertoire actuel: {Path.cwd()}")
        return
    
    with output.open("w", encoding="utf-8") as out:
        out.write("=== STRUCTURE DU PROJET ===\n\n")
        
        # Structure (optionnel, nécessite: pip install pathlib)
        for p in sorted(root.rglob("*")):
            if any(skip in str(p) for skip in ["__pycache__", ".pyc", ".git", "node_modules"]):
                continue
            indent = "  " * (len(p.relative_to(root).parts) - 1)
            if p.is_file():
                out.write(f"{indent}📄 {p.name}\n")
            elif p.is_dir():
                out.write(f"{indent}📁 {p.name}/\n")
        
        out.write("\n" + "="*60 + "\n\n")
        
        # Fichiers config
        for fname in ["requirements.txt", "README.md", ".env.example"]:
            fpath = Path(fname)
            if fpath.exists():
                out.write(f"=== FICHIER: {fname} ===\n")
                out.write(fpath.read_text(encoding="utf-8"))
                out.write("\n\n")
        
        # Sources
        src_dir = root / "src"
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.py")):
                out.write(f"=== FICHIER: {f.relative_to(root.parent)} ===\n")
                out.write(f.read_text(encoding="utf-8"))
                out.write("\n\n")
        
        # Streamlit
        home = root / "streamlit_app" / "Home.py"
        if home.exists():
            out.write(f"=== FICHIER: {home.relative_to(root.parent)} ===\n")
            out.write(home.read_text(encoding="utf-8"))
            out.write("\n\n")
        
        pages_dir = root / "streamlit_app" / "pages"
        if pages_dir.exists():
            for f in sorted(pages_dir.glob("*.py")):
                out.write(f"=== FICHIER: {f.relative_to(root.parent)} ===\n")
                out.write(f.read_text(encoding="utf-8"))
                out.write("\n\n")
    
    size = output.stat().st_size
    lines = len(output.read_text().splitlines())
    print(f"✅ Créé: {output}")
    print(f"   Taille: {size:,} octets")
    print(f"   Lignes: {lines:,}")

if __name__ == "__main__":
    consolidate()
