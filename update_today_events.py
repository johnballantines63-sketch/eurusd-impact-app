#!/usr/bin/env python3
"""
Mise à jour des événements du jour depuis EODHD API
Réutilise le système existant dans eodhd_client.py
À lancer chaque matin avant le trading (08:00)
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import duckdb

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path, get_eod_key
from eodhd_client import fetch_calendar_json, calendar_to_events_df, upsert_events


class TodayEventsUpdater:
    """Mise à jour événements du jour via EODHD"""
    
    def __init__(self):
        self.db_path = get_db_path()
        
        # Vérifier que EODHD_API_KEY existe
        try:
            get_eod_key()
        except RuntimeError as e:
            raise ValueError(f"❌ {e}")
    
    def fetch_today_events(self, countries=['US', 'EU']):
        """Récupère événements du jour depuis EODHD"""
        
        print(f"📡 Récupération événements du jour...")
        print(f"   Pays: {', '.join(countries)}")
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        try:
            # Utiliser la fonction existante
            items = fetch_calendar_json(
                d1=today,
                d2=tomorrow,
                countries=countries,
                importance=None  # Tous niveaux d'importance
            )
            
            if not items:
                print("⚠️ Aucun événement retourné par l'API")
                return None
            
            print(f"✅ {len(items)} événements récupérés")
            
            # Normaliser en DataFrame
            df = calendar_to_events_df(items)
            
            if df.empty:
                print("⚠️ DataFrame vide après normalisation")
                return None
            
            print(f"✅ {len(df)} événements normalisés")
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur API: {e}")
            return None
    
    def update_database(self, df):
        """Met à jour la DB avec les événements"""
        
        if df is None or df.empty:
            print("⚠️ Aucun événement à mettre à jour")
            return 0
        
        print(f"\n💾 Mise à jour de la base de données...")
        
        try:
            conn = duckdb.connect(self.db_path)
            
            # Utiliser la fonction upsert existante
            count = upsert_events(conn, df)
            
            conn.close()
            
            print(f"✅ {count} événements traités (INSERT/UPDATE)")
            
            return count
            
        except Exception as e:
            print(f"❌ Erreur DB: {e}")
            return 0
    
    def run(self, countries=['US', 'EU']):
        """Exécution complète"""
        
        print("🔄 MISE À JOUR ÉVÉNEMENTS DU JOUR (EODHD)")
        print("=" * 70)
        print(f"📅 Date: {date.today().strftime('%Y-%m-%d')}")
        print(f"⏰ Heure: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 1. Récupérer depuis EODHD
        df = self.fetch_today_events(countries)
        
        if df is None:
            print("\n❌ Échec récupération événements")
            return False
        
        # 2. Mettre à jour DB
        total = self.update_database(df)
        
        print("\n" + "=" * 70)
        
        if total > 0:
            print(f"✅ SUCCÈS: {total} événements traités")
            print("\n🎯 Prochaines étapes:")
            print("   1. Ouvrir Streamlit")
            print("   2. Aller dans Planificateur Multi-Événements")
            print("   3. Charger événements du jour")
            print("   4. Vérifier que Previous/Estimate sont remplis")
            
            # Afficher quelques exemples
            if not df.empty:
                print("\n📋 Exemples d'événements mis à jour:")
                sample = df[df['importance_n'].notna()].head(5)
                for idx, row in sample.iterrows():
                    country = row.get('country', 'N/A')
                    title = row.get('event_title', 'N/A')
                    prev = row.get('previous', 'N/A')
                    est = row.get('estimate', 'N/A')
                    print(f"   • {country} - {title}")
                    print(f"     Previous: {prev}, Estimate: {est}")
            
            return True
        else:
            print("⚠️ Aucune mise à jour effectuée")
            return False


def main():
    """Point d'entrée"""
    
    try:
        updater = TodayEventsUpdater()
        
        # Pays à mettre à jour (US + EU par défaut)
        countries = ['US', 'EU']
        
        success = updater.run(countries)
        
        sys.exit(0 if success else 1)
        
    except ValueError as e:
        print(f"\n❌ Erreur configuration: {e}")
        print("\n💡 Solution:")
        print("   1. Vérifier que EODHD_API_KEY est dans .env")
        print("   2. Format: EODHD_API_KEY=votre_clé_ici")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
