"""
Script pour télécharger warehouse.duckdb depuis Google Drive
Utilisé au démarrage de l'app Streamlit Cloud
"""
import os
import gdown
from pathlib import Path

def download_database():
    """
    Télécharge warehouse.duckdb depuis Google Drive si absent localement
    """
    # Chemin vers la base de données
    db_path = Path(__file__).parent.parent / "data" / "warehouse.duckdb"
    
    # Si la base existe déjà, ne pas re-télécharger
    if db_path.exists():
        print(f"✅ Base de données déjà présente: {db_path}")
        return str(db_path)
    
    print("📥 Téléchargement de warehouse.duckdb depuis Google Drive...")
    
    # Créer le dossier data s'il n'existe pas
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # URL Google Drive
    # Format: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    # FILE_ID extrait: 1Kr4t_X-D12rex48s-FfdxR4UhxR7h-g-
    gdrive_file_id = os.getenv("GDRIVE_DB_FILE_ID", "1Kr4t_X-D12rex48s-FfdxR4UhxR7h-g-")
    
    try:
        # Télécharger depuis Google Drive
        gdown.download(
            f"https://drive.google.com/uc?id={gdrive_file_id}",
            str(db_path),
            quiet=False
        )
        print(f"✅ Base de données téléchargée: {db_path}")
        print(f"📊 Taille: {db_path.stat().st_size / (1024*1024):.1f} MB")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        raise
    
    return str(db_path)

if __name__ == "__main__":
    # Test du script
    download_database()
