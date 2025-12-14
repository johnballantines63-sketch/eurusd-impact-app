"""
Téléchargement historique complet JBlanked API - Session 123 Étape 2

Télécharge tous les événements économiques 2015-2025 depuis JBlanked API
pour remplir la base de données avec des données complètes
(Actual/Forecast/Previous).

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Étape 2
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class JBlankedDownloader:
    """Téléchargeur historique JBlanked API"""
    
    def __init__(self, api_key: str, output_dir: Path):
        """
        Initialiser téléchargeur
        
        Args:
            api_key: Clé API JBlanked
            output_dir: Dossier de sortie pour fichiers JSON
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.base_url = "https://www.jblanked.com/news/api/forex-factory/calendar/range/"
        
        # Statistiques
        self.stats = {
            'years_downloaded': [],
            'years_failed': [],
            'total_events': 0,
            'download_times': {},
            'errors': []
        }
    
    def download_year(self, year: int) -> Optional[List[Dict]]:
        """
        Télécharger tous événements d'une année
        
        Args:
            year: Année à télécharger (2015-2025)
        
        Returns:
            Liste événements ou None si erreur
        """
        print(f"\n📅 ANNÉE {year}")
        print("-" * 70)
        
        # Dates début/fin
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # URL et paramètres
        headers = {
            'Authorization': f'Api-Key {self.api_key}',
            'Accept': 'application/json'
        }
        
        params = {
            'from': start_date,
            'to': end_date
        }
        
        url = self.base_url
        
        print(f"   Période: {start_date} → {end_date}")
        print(f"   URL: {url}")
        
        # Chronomètre
        start_time = time.time()
        
        try:
            # Requête
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=60
            )
            
            download_time = time.time() - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Durée: {download_time:.2f}s")
            
            if response.status_code == 200:
                # Parser JSON
                data = response.json()
                
                if isinstance(data, list):
                    print(f"   ✅ SUCCÈS - {len(data)} événements")
                    
                    # Sauvegarder
                    output_file = self.output_dir / f"events_{year}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    # Taille fichier
                    file_size = output_file.stat().st_size / 1024  # KB
                    print(f"   💾 Sauvegardé: {output_file.name} ({file_size:.1f} KB)")
                    
                    # Stats
                    self.stats['years_downloaded'].append(year)
                    self.stats['total_events'] += len(data)
                    self.stats['download_times'][year] = download_time
                    
                    return data
                
                else:
                    print(f"   ❌ ERREUR - Réponse non-liste: {type(data)}")
                    self.stats['years_failed'].append(year)
                    self.stats['errors'].append({
                        'year': year,
                        'error': 'Response not a list',
                        'type': str(type(data))
                    })
                    return None
            
            elif response.status_code == 401:
                print(f"   ❌ ERREUR 401 - API Key invalide ou expirée")
                print(f"   Message: {response.text[:200]}")
                self.stats['years_failed'].append(year)
                self.stats['errors'].append({
                    'year': year,
                    'error': '401 Unauthorized',
                    'message': response.text[:200]
                })
                return None
            
            elif response.status_code == 429:
                print(f"   ⚠️  ERREUR 429 - Rate limit atteint")
                print(f"   Attente 60 secondes avant retry...")
                time.sleep(60)
                # Retry une fois
                return self.download_year(year)
            
            else:
                print(f"   ❌ ERREUR {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                self.stats['years_failed'].append(year)
                self.stats['errors'].append({
                    'year': year,
                    'error': f'HTTP {response.status_code}',
                    'message': response.text[:200]
                })
                return None
        
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT - Requête trop longue (>60s)")
            self.stats['years_failed'].append(year)
            self.stats['errors'].append({
                'year': year,
                'error': 'Timeout',
                'message': 'Request timeout after 60s'
            })
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERREUR CONNEXION: {e}")
            self.stats['years_failed'].append(year)
            self.stats['errors'].append({
                'year': year,
                'error': 'Connection error',
                'message': str(e)
            })
            return None
        
        except Exception as e:
            print(f"   ❌ ERREUR INATTENDUE: {e}")
            self.stats['years_failed'].append(year)
            self.stats['errors'].append({
                'year': year,
                'error': 'Unexpected error',
                'message': str(e)
            })
            return None
    
    def download_all_years(
        self,
        start_year: int = 2015,
        end_year: int = 2025,
        delay_seconds: float = 2.0
    ) -> None:
        """
        Télécharger toutes les années
        
        Args:
            start_year: Année de début (défaut: 2015)
            end_year: Année de fin (défaut: 2025)
            delay_seconds: Délai entre requêtes (défaut: 2s)
        """
        print("=" * 70)
        print("TÉLÉCHARGEMENT HISTORIQUE JBLANKED 2015-2025")
        print("=" * 70)
        print()
        print(f"Période: {start_year} → {end_year}")
        print(f"Années à télécharger: {end_year - start_year + 1}")
        print(f"Délai entre requêtes: {delay_seconds}s (rate limiting)")
        print(f"Output: {self.output_dir}")
        print()
        
        # Chronomètre total
        total_start = time.time()
        
        # Télécharger chaque année
        for year in range(start_year, end_year + 1):
            self.download_year(year)
            
            # Rate limiting (sauf dernière année)
            if year < end_year:
                print(f"\n⏳ Attente {delay_seconds}s (rate limiting)...")
                time.sleep(delay_seconds)
        
        # Durée totale
        total_time = time.time() - total_start
        
        # Rapport final
        self.print_final_report(total_time)
    
    def print_final_report(self, total_time: float) -> None:
        """
        Afficher rapport final
        
        Args:
            total_time: Durée totale téléchargement
        """
        print("\n" + "=" * 70)
        print("RAPPORT FINAL TÉLÉCHARGEMENT")
        print("=" * 70)
        
        # Succès
        print(f"\n✅ ANNÉES TÉLÉCHARGÉES ({len(self.stats['years_downloaded'])} années):")
        for year in sorted(self.stats['years_downloaded']):
            duration = self.stats['download_times'].get(year, 0)
            print(f"   {year} - {duration:.2f}s")
        
        # Échecs
        if self.stats['years_failed']:
            print(f"\n❌ ANNÉES ÉCHOUÉES ({len(self.stats['years_failed'])} années):")
            for year in sorted(self.stats['years_failed']):
                print(f"   {year}")
            
            # Détails erreurs
            print(f"\n🔍 DÉTAILS ERREURS:")
            for error in self.stats['errors']:
                print(f"   {error['year']}: {error['error']}")
                if 'message' in error:
                    print(f"      → {error['message'][:100]}")
        
        # Statistiques globales
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   Total événements: {self.stats['total_events']:,}")
        print(f"   Durée totale: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"   Fichiers créés: {len(self.stats['years_downloaded'])}")
        
        # Estimation par année
        if len(self.stats['years_downloaded']) > 0:
            avg_events = self.stats['total_events'] / len(self.stats['years_downloaded'])
            print(f"   Moyenne par année: {avg_events:.0f} événements")
        
        # Fichiers créés
        print(f"\n📁 FICHIERS CRÉÉS:")
        files = sorted(self.output_dir.glob("events_*.json"))
        for file in files:
            size = file.stat().st_size / 1024
            print(f"   {file.name} ({size:.1f} KB)")
        
        # Critères succès
        print(f"\n✅ CRITÈRES SUCCÈS:")
        
        expected_years = 11  # 2015-2025
        success_rate = len(self.stats['years_downloaded']) / expected_years * 100
        
        print(f"   Années téléchargées: {len(self.stats['years_downloaded'])}/{expected_years} ({success_rate:.0f}%)")
        
        if len(self.stats['years_downloaded']) >= expected_years:
            print(f"   ✅ TOUTES ANNÉES TÉLÉCHARGÉES")
        elif len(self.stats['years_downloaded']) >= expected_years * 0.9:
            print(f"   ⚠️  PRESQUE COMPLET (>90%)")
        else:
            print(f"   ❌ TÉLÉCHARGEMENT INCOMPLET (<90%)")
        
        if self.stats['total_events'] >= 5000:
            print(f"   ✅ OBJECTIF 5,000+ ÉVÉNEMENTS ATTEINT")
        else:
            print(f"   ⚠️  Moins de 5,000 événements ({self.stats['total_events']})")
        
        print()
        
        # Sauvegarder rapport JSON
        report_file = self.output_dir / 'download_report.json'
        report_data = {
            'download_date': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'stats': self.stats
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Rapport sauvegardé: {report_file.name}")
        print()


def main():
    """Fonction principale"""
    
    # Configuration
    API_KEY = "dDHtBWTu.4pZsVUuSaGY51HHDq2gHVbI9HOECbSPy"  # CLÉ VIP
    OUTPUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'jblanked_raw'
    
    print("=" * 70)
    print("SESSION 123 - ÉTAPE 2 : TÉLÉCHARGEMENT HISTORIQUE JBLANKED")
    print("=" * 70)
    print()
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Output: {OUTPUT_DIR}")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Téléchargement 11 années (2015-2025)")
    print("   - Durée estimée: 1-2 heures")
    print("   - Rate limiting: 2 secondes entre requêtes")
    print("   - Ne pas interrompre le processus")
    print()
    
    # Confirmation
    input("Appuyez sur ENTRÉE pour démarrer le téléchargement...")
    print()
    
    # Créer downloader
    downloader = JBlankedDownloader(
        api_key=API_KEY,
        output_dir=OUTPUT_DIR
    )
    
    # Télécharger toutes les années
    downloader.download_all_years(
        start_year=2015,
        end_year=2025,
        delay_seconds=2.0
    )
    
    # Conclusion
    print("=" * 70)
    print("ÉTAPE 2 TERMINÉE")
    print("=" * 70)
    print()
    print("Prochaine étape:")
    print("  ÉTAPE 3: Mapping et nettoyage des données")
    print()


if __name__ == '__main__':
    main()
