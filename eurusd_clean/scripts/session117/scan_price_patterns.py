"""
Scanner de patterns de prix EUR/USD (Approche Bottom-Up)

Session 117 - Détection empirique des spikes réels puis mapping vers events

Algorithme:
1. Scanner prices_1m pour spikes > 40 pips
2. Détecter pattern: Double Wave vs Single Wave Fort
3. Enrichir avec métadonnées temporelles
4. Export dataset pour validation formule

Auteur: André Valentin avec Claude
Date: 06 novembre 2025
"""

import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path
import pytz


class PricePatternScanner:
    """Scanner de patterns de prix EUR/USD"""
    
    def __init__(self, db_path: str = "data/warehouse.duckdb"):
        """
        Initialise le scanner
        
        Args:
            db_path: Chemin vers la base DuckDB
        """
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connexion à la base de données"""
        self.conn = duckdb.connect(self.db_path, read_only=True)
        print(f"✅ Connecté à {self.db_path}")
        
    def disconnect(self):
        """Fermeture connexion"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")
    
    def get_price_window(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[tuple]:
        """
        Récupère les prix dans une fenêtre temporelle
        
        TIMEZONE (Session 112):
        ======================
        Utilise vue prices_bern pour conversion automatique timezone.
        Événement 14:30 Bern → Chercher prices_bern à 14:30 (vue fait la conversion).
        
        Args:
            start_time: Début fenêtre (heure Bern)
            end_time: Fin fenêtre (heure Bern)
            
        Returns:
            List de tuples (datetime, open, high, low, close)
        """
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime BETWEEN ? AND ?
        ORDER BY datetime
        """
        
        result = self.conn.execute(
            query, 
            [start_time, end_time]
        ).fetchall()
        
        return result
    
    def calculate_mid_price(self, high: float, low: float) -> float:
        """Calcule le prix mid depuis high/low"""
        return (high + low) / 2
    
    def pips_difference(self, price1: float, price2: float) -> float:
        """
        Calcule différence en pips (EUR/USD)
        
        Args:
            price1: Prix 1
            price2: Prix 2
            
        Returns:
            Différence en pips (4 décimales)
        """
        return abs(price1 - price2) * 10000
    
    def detect_spike_in_window(
        self,
        prices: List[tuple],
        min_spike_pips: float = 40.0
    ) -> Optional[Dict]:
        """
        Détecte un spike significatif dans une fenêtre de prix
        
        Args:
            prices: Liste (datetime, open, high, low, close)
            min_spike_pips: Seuil minimum en pips
            
        Returns:
            Dict avec métadonnées spike ou None
        """
        if len(prices) < 5:
            return None
        
        # Calculer prix mid pour chaque point (high+low)/2
        mid_prices = [
            (p[0], self.calculate_mid_price(p[2], p[3]))  # p[2]=high, p[3]=low
            for p in prices
        ]
        
        # Baseline : moyenne premiers 5 points
        baseline = sum([p[1] for p in mid_prices[:5]]) / 5
        
        # Chercher max spike depuis baseline
        max_spike_pips = 0
        max_spike_time = None
        max_spike_price = None
        
        for timestamp, price in mid_prices[5:]:
            spike_pips = self.pips_difference(price, baseline)
            if spike_pips > max_spike_pips:
                max_spike_pips = spike_pips
                max_spike_time = timestamp
                max_spike_price = price
        
        # Vérifier seuil
        if max_spike_pips < min_spike_pips:
            return None
        
        return {
            'baseline_price': baseline,
            'baseline_time': mid_prices[0][0],
            'peak_price': max_spike_price,
            'peak_time': max_spike_time,
            'spike_pips': max_spike_pips,
            'direction': 'bullish' if max_spike_price > baseline else 'bearish'
        }
    
    def analyze_pattern(
        self,
        spike_data: Dict,
        extended_window: List[tuple]
    ) -> Dict:
        """
        Analyse le pattern après le spike (Double Wave vs Single Wave Fort)
        
        Args:
            spike_data: Dict retourné par detect_spike_in_window()
            extended_window: Données prix 60 min après peak
            
        Returns:
            Dict avec classification pattern + métadonnées
        """
        peak_time = spike_data['peak_time']
        peak_price = spike_data['peak_price']
        baseline = spike_data['baseline_price']
        direction = spike_data['direction']
        
        # Filtrer prix APRÈS peak
        mid_prices_after_peak = [
            (p[0], self.calculate_mid_price(p[2], p[3]))  # p[2]=high, p[3]=low
            for p in extended_window
            if p[0] > peak_time
        ]
        
        if len(mid_prices_after_peak) < 10:
            return {
                'pattern': 'insufficient_data',
                'details': 'Moins de 10 minutes après peak'
            }
        
        # ÉTAPE 1 : Détecter pullback
        # Chercher minimum (si bullish) ou maximum (si bearish) après peak
        if direction == 'bullish':
            pullback_price = min([p[1] for p in mid_prices_after_peak[:30]])  # 30 min max
            pullback_idx = [p[1] for p in mid_prices_after_peak[:30]].index(pullback_price)
        else:
            pullback_price = max([p[1] for p in mid_prices_after_peak[:30]])
            pullback_idx = [p[1] for p in mid_prices_after_peak[:30]].index(pullback_price)
        
        pullback_time = mid_prices_after_peak[pullback_idx][0]
        pullback_pips = self.pips_difference(peak_price, pullback_price)
        pullback_ratio = pullback_pips / spike_data['spike_pips']
        
        # ÉTAPE 2 : Chercher Wave 2 (après pullback)
        prices_after_pullback = [
            (p[0], p[1]) 
            for p in mid_prices_after_peak 
            if p[0] > pullback_time
        ]
        
        wave2_peak = None
        wave2_time = None
        
        if len(prices_after_pullback) >= 5:
            if direction == 'bullish':
                wave2_peak = max([p[1] for p in prices_after_pullback])
                wave2_idx = [p[1] for p in prices_after_pullback].index(wave2_peak)
            else:
                wave2_peak = min([p[1] for p in prices_after_pullback])
                wave2_idx = [p[1] for p in prices_after_pullback].index(wave2_peak)
            
            wave2_time = prices_after_pullback[wave2_idx][0]
        
        # CLASSIFICATION PATTERN
        pattern_result = {
            'spike_pips': spike_data['spike_pips'],
            'direction': direction,
            'baseline_price': baseline,
            'baseline_time': spike_data['baseline_time'],
            'peak1_price': peak_price,
            'peak1_time': peak_time,
            'pullback_price': pullback_price,
            'pullback_time': pullback_time,
            'pullback_pips': pullback_pips,
            'pullback_ratio': pullback_ratio,
        }
        
        # DOUBLE WAVE : pullback > 50% ET wave2 existe ET wave2 > peak1
        if wave2_peak and pullback_ratio > 0.5:
            wave2_from_baseline = self.pips_difference(wave2_peak, baseline)
            extension_factor = wave2_from_baseline / spike_data['spike_pips']
            
            if extension_factor >= 1.0:
                pattern_result.update({
                    'pattern': 'double_wave',
                    'wave2_peak_price': wave2_peak,
                    'wave2_peak_time': wave2_time,
                    'wave2_from_baseline_pips': wave2_from_baseline,
                    'extension_factor': extension_factor,
                    'total_impact_pips': wave2_from_baseline
                })
                return pattern_result
        
        # SINGLE WAVE FORT : pullback < 30%
        if pullback_ratio < 0.3:
            pattern_result.update({
                'pattern': 'single_wave_fort',
                'total_impact_pips': spike_data['spike_pips']
            })
            return pattern_result
        
        # CAS INTERMÉDIAIRE (pullback 30-50%)
        pattern_result.update({
            'pattern': 'intermediate',
            'total_impact_pips': spike_data['spike_pips'],
            'note': 'Pullback entre 30-50%, non classé Double/Single'
        })
        
        return pattern_result
    
    def scan_period(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2025-11-06",
        min_spike_pips: float = 40.0,
        trading_hours_only: bool = True
    ) -> List[Dict]:
        """
        Scanne une période pour détecter tous les patterns
        
        Args:
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            min_spike_pips: Seuil détection spike
            trading_hours_only: Filtrer 13:00-16:00 uniquement
            
        Returns:
            Liste de patterns détectés
        """
        print(f"\n🔍 SCAN PÉRIODE : {start_date} → {end_date}")
        print(f"   Seuil spike : {min_spike_pips} pips")
        print(f"   Horaires trading : {trading_hours_only}")
        print("=" * 60)
        
        # Convertir dates avec timezone Bern (pour compatibilité avec prices_bern)
        bern_tz = pytz.timezone('Europe/Zurich')
        start_dt = bern_tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end_dt = bern_tz.localize(datetime.strptime(end_date, "%Y-%m-%d"))
        
        patterns_found = []
        current_date = start_dt
        
        # Scanner jour par jour
        while current_date <= end_dt:
            # Exclure week-ends
            if current_date.weekday() >= 5:  # Samedi=5, Dimanche=6
                current_date = current_date + timedelta(days=1)
                continue
            
            # Fenêtre horaire
            if trading_hours_only:
                scan_start = current_date.replace(hour=13, minute=0, second=0)
                scan_end = current_date.replace(hour=16, minute=0, second=0)
            else:
                scan_start = current_date.replace(hour=0, minute=0, second=0)
                scan_end = current_date.replace(hour=23, minute=59, second=59)
            
            # Scanner par fenêtres glissantes de 90 minutes
            window_start = scan_start
            while window_start < scan_end:
                window_end = window_start + timedelta(minutes=90)
                
                # Récupérer prix
                prices = self.get_price_window(window_start, window_end)
                
                if len(prices) < 5:
                    window_start += timedelta(minutes=30)  # Décalage 30 min
                    continue
                
                # Détecter spike
                spike = self.detect_spike_in_window(prices, min_spike_pips)
                
                if spike:
                    # Récupérer fenêtre étendue (60 min après peak)
                    extended_end = spike['peak_time'] + timedelta(minutes=60)
                    extended_prices = self.get_price_window(
                        spike['baseline_time'],
                        extended_end
                    )
                    
                    # Analyser pattern
                    pattern = self.analyze_pattern(spike, extended_prices)
                    
                    # Ajouter à résultats si pattern significatif
                    if pattern.get('pattern') in ['double_wave', 'single_wave_fort', 'intermediate']:
                        patterns_found.append(pattern)
                        
                        # Afficher détection
                        print(f"\n✅ PATTERN DÉTECTÉ : {current_date.date()}")
                        print(f"   Type : {pattern['pattern'].upper()}")
                        print(f"   Impact : {pattern['total_impact_pips']:.1f} pips")
                        print(f"   Peak1 : {pattern['peak1_time']}")
                        
                        # Sauter au-delà du pattern détecté
                        window_start = spike['peak_time'] + timedelta(minutes=60)
                    else:
                        window_start = window_start + timedelta(minutes=30)
                else:
                    window_start = window_start + timedelta(minutes=30)
            
            current_date = current_date + timedelta(days=1)
        
        print("\n" + "=" * 60)
        print(f"✅ SCAN TERMINÉ : {len(patterns_found)} patterns détectés")
        
        return patterns_found
    
    def export_results(
        self,
        patterns: List[Dict],
        output_file: str = "patterns_detected.json"
    ):
        """
        Exporte les résultats en JSON
        
        Args:
            patterns: Liste patterns détectés
            output_file: Nom fichier output
        """
        # Convertir datetime en string pour JSON
        patterns_serializable = []
        for p in patterns:
            p_copy = p.copy()
            for key in ['baseline_time', 'peak1_time', 'pullback_time']:
                if key in p_copy and p_copy[key]:
                    p_copy[key] = p_copy[key].isoformat()
            
            if 'wave2_peak_time' in p_copy and p_copy['wave2_peak_time']:
                p_copy['wave2_peak_time'] = p_copy['wave2_peak_time'].isoformat()
            
            patterns_serializable.append(p_copy)
        
        # Export
        output_path = Path(__file__).parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_serializable, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats exportés : {output_path}")
        
        # Statistiques
        double_wave = sum(1 for p in patterns if p['pattern'] == 'double_wave')
        single_wave = sum(1 for p in patterns if p['pattern'] == 'single_wave_fort')
        intermediate = sum(1 for p in patterns if p['pattern'] == 'intermediate')
        
        print(f"\n📊 STATISTIQUES :")
        print(f"   Total patterns : {len(patterns)}")
        print(f"   Double Wave : {double_wave}")
        print(f"   Single Wave Fort : {single_wave}")
        print(f"   Intermédiaire : {intermediate}")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 SCANNER PRICE PATTERNS - SESSION 117")
    print("   Approche Bottom-Up : Prix → Events")
    print("=" * 60)
    
    # Initialiser scanner
    scanner = PricePatternScanner(
        db_path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    )
    
    try:
        # Connexion
        scanner.connect()
        
        # Scanner période complète
        patterns = scanner.scan_period(
            start_date="2024-01-01",
            end_date="2025-11-06",
            min_spike_pips=40.0,
            trading_hours_only=True
        )
        
        # Exporter résultats
        scanner.export_results(patterns)
        
    finally:
        # Fermer connexion
        scanner.disconnect()
    
    print("\n✅ SCAN TERMINÉ")


if __name__ == "__main__":
    main()
