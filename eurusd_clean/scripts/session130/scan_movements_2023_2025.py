#!/usr/bin/env python3
"""
SCANNER MOUVEMENTS COMPLET 2023-2025 - SESSION 130
==================================================

Scanner tous mouvements > 35 pips sur 3 ans (2023-2025) avec :
- Détection patterns (DoubleWave, SingleWave, ZigZag)
- Enrichissement événements causaux (±30 min)
- Métriques détaillées par mouvement
- Output JSON structuré pour workflow 10 étapes

APPROCHE : Bottom-up (prix → patterns → events)
SEUIL : 35 pips (validé Session 117)
PÉRIODE : 2023-01-01 à 2025-11-07

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import duckdb
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pytz

# Import utils timezone (OBLIGATOIRE)
import sys
sys.path.append(str(Path(__file__).parent / '../session129'))
from utils_timezone import ensure_bern_time, TZ_BERN

# Constantes
DB_PATH = "data/warehouse.duckdb"
PIP = 0.0001
MIN_SPIKE_PIPS = 35.0
BASELINE_N = 5
SPIKE_LOOKAHEAD_MIN = 6
PULLBACK_WIN_MIN = 30
WAVE2_WIN_MIN = 40

# Seuils classification patterns
PULLBACK_DOUBLE_MIN = 0.25
PULLBACK_DOUBLE_MAX = 0.70
PULLBACK_SINGLE_MAX = 0.30
ALPHA_WAVE2_OVER_WAVE1 = 0.60

# Période scan
START_DATE = "2023-01-01"
END_DATE = "2025-11-07"

# Output
OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "movements_2023_2025_complete.json"


def mid_from_hl(high: float, low: float) -> float:
    """Calcule prix mid depuis high/low"""
    return (high + low) / 2.0


def pips_diff(p1: float, p2: float) -> float:
    """Différence en pips entre 2 prix"""
    return abs(p1 - p2) * 10000.0


class MovementScanner:
    """Scanner mouvements forts 2023-2025 avec détection patterns"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.movements = []
        
    def connect(self):
        """Connexion DB"""
        self.conn = duckdb.connect(self.db_path, read_only=True)
        print(f"✅ Connecté à {self.db_path}")
        
    def disconnect(self):
        """Déconnexion DB"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")
    
    def get_price_window(self, start_time: datetime, end_time: datetime) -> List[tuple]:
        """Charge prix pour fenêtre temporelle"""
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime BETWEEN ? AND ?
        ORDER BY datetime
        """
        return self.conn.execute(query, [start_time, end_time]).fetchall()
    
    def detect_spike_in_window(self, prices: List[tuple]) -> Optional[Dict]:
        """
        Détecte spike principal dans fenêtre (baseline locale + lookahead).
        
        Returns:
            Dict avec baseline_time, baseline_price, peak_time, peak_price, spike_pips, direction
        """
        if len(prices) < BASELINE_N + SPIKE_LOOKAHEAD_MIN:
            return None
        
        mids = [(r[0], (r[2] + r[3]) / 2.0) for r in prices]
        times = [t for (t, _) in mids]
        vals = [v for (_, v) in mids]
        
        # Calculer deviation pour chaque point
        max_dev = 0.0
        chosen_idx = None
        
        for i in range(BASELINE_N, len(vals) - SPIKE_LOOKAHEAD_MIN):
            # Baseline locale
            base = sum(vals[i - BASELINE_N:i]) / BASELINE_N
            
            # Lookahead window
            j_max = min(len(vals) - 1, i + SPIKE_LOOKAHEAD_MIN)
            local_max = max(vals[i:j_max + 1])
            local_min = min(vals[i:j_max + 1])
            
            # Deviation
            dev_up = (local_max - base) * 10000.0
            dev_down = (base - local_min) * 10000.0
            dev = max(dev_up, dev_down)
            
            if dev > max_dev and dev >= MIN_SPIKE_PIPS:
                max_dev = dev
                chosen_idx = i
        
        if chosen_idx is None:
            return None
        
        # Calculer spike pour indice choisi
        base = sum(vals[chosen_idx - BASELINE_N:chosen_idx]) / BASELINE_N
        j_max = min(len(vals) - 1, chosen_idx + SPIKE_LOOKAHEAD_MIN)
        local_max = max(vals[chosen_idx:j_max + 1])
        local_min = min(vals[chosen_idx:j_max + 1])
        
        # Direction et peak
        if abs(local_max - base) >= abs(base - local_min):
            peak_price = local_max
            k = vals[chosen_idx:j_max + 1].index(local_max)
            peak_time = times[chosen_idx + k]
            direction = "bullish"
        else:
            peak_price = local_min
            k = vals[chosen_idx:j_max + 1].index(local_min)
            peak_time = times[chosen_idx + k]
            direction = "bearish"
        
        spike_pips = abs(peak_price - base) * 10000.0
        
        if spike_pips < MIN_SPIKE_PIPS:
            return None
        
        return {
            "baseline_time": times[chosen_idx - BASELINE_N],
            "baseline_price": base,
            "peak_time": peak_time,
            "peak_price": peak_price,
            "spike_pips": spike_pips,
            "direction": direction
        }
    
    def analyze_pattern(self, spike_data: Dict, extended_window: List[tuple]) -> Dict:
        """
        Analyse pattern du mouvement (DoubleWave, SingleWave, ZigZag, etc.)
        
        Critères classification :
        - DoubleWave : 2 pics, pullback 25-70%, Wave2 > Wave1
        - SingleWave Fort : 1 pic > 40 pips, pullback < 30%
        - SingleWave Intermediate : 1 pic 20-40 pips, pullback < 30%
        - ZigZag : 3+ pics, pullback < 60%
        """
        peak_time = spike_data["peak_time"]
        peak_price = spike_data["peak_price"]
        baseline = spike_data["baseline_price"]
        direction = spike_data["direction"]
        
        mids = [(r[0], mid_from_hl(r[2], r[3])) for r in extended_window]
        after = [(t, m) for (t, m) in mids if t > peak_time]
        
        if len(after) < 5:
            return {"pattern": "insufficient_data"}
        
        # Recherche pullback dans 30 min
        pullback_window = [(t, m) for (t, m) in after 
                          if (t - peak_time) <= timedelta(minutes=PULLBACK_WIN_MIN)]
        
        if len(pullback_window) < 2:
            return {"pattern": "insufficient_data"}
        
        # Trouver pullback
        if direction == "bullish":
            pullback_price = min([m for (_, m) in pullback_window])
            pullback_idx = [m for (_, m) in pullback_window].index(pullback_price)
        else:
            pullback_price = max([m for (_, m) in pullback_window])
            pullback_idx = [m for (_, m) in pullback_window].index(pullback_price)
        
        pullback_time = pullback_window[pullback_idx][0]
        
        wave1_pips = pips_diff(peak_price, baseline)
        pullback_pips = pips_diff(peak_price, pullback_price)
        pullback_ratio = pullback_pips / max(wave1_pips, 1e-9)
        
        # Recherche Wave2 dans 40 min après pullback
        wave2_search = [(t, m) for (t, m) in after 
                       if t > pullback_time 
                       and (t - pullback_time) <= timedelta(minutes=WAVE2_WIN_MIN)]
        
        wave2_peak_price = None
        wave2_peak_time = None
        wave2_pips = 0.0
        
        if wave2_search:
            if direction == "bullish":
                wave2_peak_price = max([m for (_, m) in wave2_search])
                wave2_idx = [m for (_, m) in wave2_search].index(wave2_peak_price)
            else:
                wave2_peak_price = min([m for (_, m) in wave2_search])
                wave2_idx = [m for (_, m) in wave2_search].index(wave2_peak_price)
            
            wave2_peak_time = wave2_search[wave2_idx][0]
            wave2_pips = pips_diff(wave2_peak_price, pullback_price)
        
        # Classification pattern
        pattern = "unknown"
        
        # DOUBLE WAVE
        if (wave2_peak_price is not None and 
            PULLBACK_DOUBLE_MIN <= pullback_ratio <= PULLBACK_DOUBLE_MAX and
            wave2_pips >= ALPHA_WAVE2_OVER_WAVE1 * wave1_pips):
            
            # Sous-classification Overlap vs Cascade
            timing_delta_min = (pullback_time - peak_time).total_seconds() / 60.0
            if timing_delta_min < 20:
                pattern = "DoubleWave_Overlap"
            else:
                pattern = "DoubleWave_Cascade"
        
        # SINGLE WAVE
        elif pullback_ratio < PULLBACK_SINGLE_MAX:
            if wave1_pips > 40:
                pattern = "SingleWave_Fort"
            elif wave1_pips >= 20:
                pattern = "SingleWave_Intermediate"
            else:
                pattern = "SingleWave_Weak"
        
        # ZIG ZAG (3+ pics, pullback modéré)
        elif pullback_ratio < 0.60:
            # Compter pics après pullback
            remaining = [(t, m) for (t, m) in after if t > pullback_time]
            if len(remaining) > 5:
                pattern = "ZigZag"
            else:
                pattern = "Complex"
        
        else:
            pattern = "Other"
        
        return {
            "pattern": pattern,
            "wave1_pips": wave1_pips,
            "pullback_time": pullback_time,
            "pullback_price": pullback_price,
            "pullback_pips": pullback_pips,
            "pullback_ratio": pullback_ratio,
            "wave2_peak_time": wave2_peak_time,
            "wave2_peak_price": wave2_peak_price,
            "wave2_pips": wave2_pips
        }
    
    def find_causal_events(self, spike_time: datetime, window_minutes: int = 30) -> List[Dict]:
        """
        Trouve événements causaux dans fenêtre ±window_minutes.
        
        Returns:
            Liste dicts avec event_key, ts_utc, country, actual, forecast, previous
        """
        # Fenêtre recherche
        start_search = spike_time - timedelta(minutes=window_minutes)
        end_search = spike_time + timedelta(minutes=window_minutes)
        
        # Query events (utiliser utils_timezone pour conversion)
        query = """
        SELECT 
            event_key,
            ts_utc,
            country,
            actual,
            estimate as forecast,
            previous,
            importance_n
        FROM events
        WHERE ts_utc BETWEEN ? AND ?
          AND importance_n >= 2
        ORDER BY ts_utc
        """
        
        results = self.conn.execute(query, [start_search, end_search]).fetchall()
        
        events = []
        for row in results:
            events.append({
                "event_key": row[0],
                "ts_utc": row[1].isoformat() if row[1] else None,
                "country": row[2],
                "actual": row[3],
                "forecast": row[4],
                "previous": row[5],
                "importance": "HIGH" if row[6] == 3 else "MEDIUM"
            })
        
        return events
    
    def scan_date(self, date: datetime) -> Optional[Dict]:
        """
        Scanne une journée complète pour détecter mouvements forts.
        
        Returns:
            Dict mouvement si détecté, None sinon
        """
        # Fenêtre complète journée
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        # Charger prix
        prices = self.get_price_window(start_time, end_time)
        
        if len(prices) < 100:  # Minimum data
            return None
        
        # Détecter spike
        spike_data = self.detect_spike_in_window(prices)
        
        if spike_data is None:
            return None
        
        # Analyser pattern (fenêtre étendue +2h après spike)
        peak_time = spike_data["peak_time"]
        extended_start = start_time
        extended_end = peak_time + timedelta(hours=2)
        extended_prices = self.get_price_window(extended_start, extended_end)
        
        pattern_data = self.analyze_pattern(spike_data, extended_prices)
        
        # Trouver événements causaux
        events = self.find_causal_events(peak_time, window_minutes=30)
        
        # Assembler résultat
        movement = {
            "date": date.strftime("%Y-%m-%d"),
            "baseline_time": spike_data["baseline_time"].isoformat(),
            "baseline_price": spike_data["baseline_price"],
            "peak_time": spike_data["peak_time"].isoformat(),
            "peak_price": spike_data["peak_price"],
            "direction": spike_data["direction"],
            "impact_pips": spike_data["spike_pips"],
            "pattern": pattern_data["pattern"],
            "wave1_pips": pattern_data.get("wave1_pips", 0),
            "pullback_time": pattern_data.get("pullback_time").isoformat() if pattern_data.get("pullback_time") else None,
            "pullback_ratio": pattern_data.get("pullback_ratio", 0),
            "wave2_pips": pattern_data.get("wave2_pips", 0),
            "events": events,
            "n_events": len(events)
        }
        
        return movement
    
    def scan_period(self, start_date: str, end_date: str):
        """
        Scanne période complète jour par jour.
        
        Args:
            start_date: Date début format YYYY-MM-DD
            end_date: Date fin format YYYY-MM-DD
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
        
        print(f"\n🔍 Scan période {start_date} → {end_date}")
        print(f"Seuil détection : {MIN_SPIKE_PIPS} pips")
        print("-" * 80)
        
        current = start_dt
        total_days = (end_dt - start_dt).days
        detected = 0
        
        while current <= end_dt:
            # Scan journée
            movement = self.scan_date(current)
            
            if movement:
                detected += 1
                self.movements.append(movement)
                
                # Log résultat
                pattern = movement["pattern"]
                impact = movement["impact_pips"]
                n_events = movement["n_events"]
                date_str = current.strftime("%Y-%m-%d")
                
                print(f"✅ {date_str} | {pattern:25s} | {impact:6.1f} pips | {n_events} events")
            
            # Jour suivant
            current += timedelta(days=1)
        
        print("-" * 80)
        print(f"\n📊 RÉSULTATS SCAN")
        print(f"Période scannée : {total_days} jours")
        print(f"Mouvements détectés : {detected}")
        print(f"Taux détection : {100.0 * detected / max(total_days, 1):.1f}%")
    
    def save_results(self, output_file: Path):
        """Sauvegarde résultats JSON"""
        
        # Statistiques patterns
        pattern_counts = {}
        for m in self.movements:
            pattern = m["pattern"]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Impact moyen par pattern
        pattern_impacts = {}
        for pattern in pattern_counts:
            impacts = [m["impact_pips"] for m in self.movements if m["pattern"] == pattern]
            pattern_impacts[pattern] = sum(impacts) / len(impacts) if impacts else 0
        
        # Assembler output
        output = {
            "metadata": {
                "scan_date": datetime.now().isoformat(),
                "period_start": START_DATE,
                "period_end": END_DATE,
                "threshold_pips": MIN_SPIKE_PIPS,
                "total_movements": len(self.movements)
            },
            "statistics": {
                "pattern_counts": pattern_counts,
                "pattern_avg_impact": pattern_impacts
            },
            "movements": self.movements
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Résultats sauvegardés : {output_file}")
        print(f"   Total mouvements : {len(self.movements)}")
        print(f"\n📈 Distribution patterns :")
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            avg_impact = pattern_impacts[pattern]
            pct = 100.0 * count / len(self.movements)
            print(f"   {pattern:25s} : {count:3d} ({pct:5.1f}%) | Avg: {avg_impact:6.1f} pips")


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("SCANNER MOUVEMENTS 2023-2025 - SESSION 130")
    print("=" * 80)
    
    scanner = MovementScanner(DB_PATH)
    
    try:
        # Connexion
        scanner.connect()
        
        # Scan période
        scanner.scan_period(START_DATE, END_DATE)
        
        # Sauvegarde
        scanner.save_results(OUTPUT_FILE)
        
        print("\n✅ SCAN TERMINÉ AVEC SUCCÈS")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        scanner.disconnect()


if __name__ == "__main__":
    main()
