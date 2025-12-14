"""
Price Pattern Scanner + Plots (Double Wave / Single Wave Fort)
--------------------------------------------------------------
Version: rev 3 (plots)
- Conserve la logique de "price_pattern_scanner_fixed.py" (rev 2)
- Ajoute la génération automatique de graphiques PNG pour chaque pattern détecté
  avec annotations des points clés (baseline, peak1, pullback, wave2).

Usage:
  python price_pattern_scanner_with_plots.py

Sorties:
  - patterns_detected.json / .csv (comme avant)
  - dossier "plots_double_wave/" avec 1 PNG par détection
"""

import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
import pytz
import os

import matplotlib.pyplot as plt

PIP = 0.0001

def mid_from_hl(high: float, low: float) -> float:
    return (high + low) / 2.0

def pips_diff(p1: float, p2: float) -> float:
    return abs(p1 - p2) * 10000.0

class PricePatternScanner:
    """Scanner de patterns de prix EUR/USD + génération de graphiques"""

    def __init__(self, db_path: str = "data/warehouse.duckdb"):
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

        # Seuils
        self.MIN_SPIKE_PIPS = 35.0
        self.PULLBACK_WIN_MIN = 30   # fenêtre max pour trouver le pullback après pic1
        self.WAVE2_WIN_MIN = 30      # fenêtre max pour trouver le pic2 après pullback
        self.PULLBACK_DOUBLE_MIN = 0.25
        self.PULLBACK_DOUBLE_MAX = 0.70
        self.PULLBACK_SINGLE_MAX = 0.30
        self.ALPHA_WAVE2_OVER_WAVE1 = 0.60

        # Répertoire de sortie plots
        self.plots_dir = Path(__file__).parent / "plots_double_wave"
        self.plots_dir.mkdir(exist_ok=True)

    # ------------------------- Connexion -------------------------
    def connect(self):
        self.conn = duckdb.connect(self.db_path, read_only=True)
        print(f"✅ Connecté à {self.db_path}")
        
    def disconnect(self):
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")

    # ------------------------- Données ---------------------------
    def get_price_window(self, start_time: datetime, end_time: datetime) -> List[tuple]:
        """
        Retourne [(datetime, open, high, low, close)] depuis la vue prices_bern (timezone Berne).
        """
        assert self.conn is not None, "Non connecté à DuckDB"
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime BETWEEN ? AND ?
        ORDER BY datetime
        """
        return self.conn.execute(query, [start_time, end_time]).fetchall()

    # ------------------------- Spike -----------------------------
    def detect_spike_in_window(self, prices: List[tuple], min_spike_pips: Optional[float] = None) -> Optional[Dict]:
        if len(prices) < 6:
            return None
        if min_spike_pips is None:
            min_spike_pips = self.MIN_SPIKE_PIPS

        mids: List[Tuple[datetime, float]] = [(r[0], mid_from_hl(r[2], r[3])) for r in prices]
        baseline = sum([m[1] for m in mids[:5]]) / 5.0
        baseline_time = mids[0][0]

        max_spike_pips = 0.0
        peak_time = None
        peak_price = None
        for ts, px in mids[5:]:
            spike = pips_diff(px, baseline)
            if spike > max_spike_pips:
                max_spike_pips = spike
                peak_time = ts
                peak_price = px

        if max_spike_pips < min_spike_pips or peak_time is None or peak_price is None:
            return None

        direction = "bullish" if peak_price > baseline else "bearish"
        return {
            "baseline_price": baseline,
            "baseline_time": baseline_time,
            "peak_price": peak_price,
            "peak_time": peak_time,
            "spike_pips": max_spike_pips,
            "direction": direction,
        }

    # ------------------------- Pattern ---------------------------
    def analyze_pattern(self, spike_data: Dict, extended_window: List[tuple]) -> Dict:
        peak_time = spike_data["peak_time"]
        peak_price = spike_data["peak_price"]
        baseline = spike_data["baseline_price"]
        direction = spike_data["direction"]

        mids: List[Tuple[datetime, float]] = [(r[0], mid_from_hl(r[2], r[3])) for r in extended_window]
        if not mids:
            return {"pattern": "insufficient_data", "details": "fenêtre étendue vide"}

        after = [(t, m) for (t, m) in mids if t > peak_time]
        if len(after) < 5:
            return {"pattern": "insufficient_data", "details": "moins de 5 minutes après le pic"}

        pullback_window = [(t, m) for (t, m) in after if (t - peak_time) <= timedelta(minutes=self.PULLBACK_WIN_MIN)]
        if len(pullback_window) < 2:
            return {"pattern": "insufficient_data", "details": "pas assez de données pour pullback"}

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

        wave2_search = [(t, m) for (t, m) in after if t > pullback_time and (t - pullback_time) <= timedelta(minutes=self.WAVE2_WIN_MIN)]
        wave2_peak_price = None
        wave2_peak_time = None
        if wave2_search:
            if direction == "bullish":
                wave2_peak_price = max([m for (_, m) in wave2_search])
                wave2_idx = [m for (_, m) in wave2_search].index(wave2_peak_price)
            else:
                wave2_peak_price = min([m for (_, m) in wave2_search])
                wave2_idx = [m for (_, m) in wave2_search].index(wave2_peak_price)
            wave2_peak_time = wave2_search[wave2_idx][0]

        result = {
            "spike_pips": spike_data["spike_pips"],
            "direction": direction,
            "baseline_price": baseline,
            "baseline_time": spike_data["baseline_time"],
            "peak1_price": peak_price,
            "peak1_time": peak_time,
            "pullback_price": pullback_price,
            "pullback_time": pullback_time,
            "pullback_pips": pullback_pips,
            "pullback_ratio": pullback_ratio,
        }

        # Double wave?
        if wave2_peak_price is not None:
            wave2_valid_break = (wave2_peak_price > peak_price) if direction == "bullish" else (wave2_peak_price < peak_price)
            wave2_from_baseline = pips_diff(wave2_peak_price, baseline)
            extension_factor = wave2_from_baseline / max(spike_data["spike_pips"], 1e-9)
            wave2_from_pullback = pips_diff(wave2_peak_price, pullback_price)
            wave1_from_baseline = pips_diff(peak_price, baseline)

            if (self.PULLBACK_DOUBLE_MIN <= pullback_ratio <= self.PULLBACK_DOUBLE_MAX and
                wave2_valid_break and
                (extension_factor >= 1.0 or wave2_from_pullback >= self.ALPHA_WAVE2_OVER_WAVE1 * wave1_from_baseline)):
                result.update({
                    "pattern": "double_wave",
                    "wave2_peak_price": wave2_peak_price,
                    "wave2_peak_time": wave2_peak_time,
                    "wave2_from_baseline_pips": wave2_from_baseline,
                    "wave2_from_pullback_pips": wave2_from_pullback,
                    "extension_factor": extension_factor,
                    "total_impact_pips": wave2_from_baseline,
                })
                return result

        if pullback_ratio < self.PULLBACK_SINGLE_MAX:
            result.update({
                "pattern": "single_wave_fort",
                "total_impact_pips": spike_data["spike_pips"],
            })
            return result

        result.update({
            "pattern": "intermediate",
            "total_impact_pips": spike_data["spike_pips"],
            "note": "Pullback 30–50% ou wave2 non confirmée",
        })
        return result

    # ------------------------- Plotting --------------------------
    def plot_detection(self, extended_window: List[tuple], pattern: Dict, idx: int) -> str:
        """
        Sauvegarde un graphique PNG avec annotations des points clés pour une détection.
        Retourne le chemin du fichier PNG.
        """
        if not extended_window or "pattern" not in pattern:
            return ""

        # Reconstituer séries temporelles
        times = [r[0] for r in extended_window]
        mids  = [mid_from_hl(r[2], r[3]) for r in extended_window]

        # Points clés
        baseline_time = pattern.get("baseline_time")
        peak1_time = pattern.get("peak1_time")
        pullback_time = pattern.get("pullback_time")
        wave2_time = pattern.get("wave2_peak_time", None)

        baseline_price = pattern.get("baseline_price")
        peak1_price = pattern.get("peak1_price")
        pullback_price = pattern.get("pullback_price")
        wave2_price = pattern.get("wave2_peak_price", None)

        # Création du plot
        plt.figure(figsize=(10, 5))
        plt.plot(times, mids, linewidth=2)
        plt.title(f"EUR/USD – {pattern['pattern']} | impact {pattern['total_impact_pips']:.1f} pips")
        plt.xlabel("Heure")
        plt.ylabel("Mid price")

        # Annotations verticales
        if baseline_time: plt.axvline(baseline_time, linestyle="--", linewidth=1)
        if peak1_time:    plt.axvline(peak1_time, linestyle="--", linewidth=1)
        if pullback_time: plt.axvline(pullback_time, linestyle="--", linewidth=1)
        if wave2_time:    plt.axvline(wave2_time, linestyle="--", linewidth=1)

        # Points et labels
        if baseline_time and baseline_price:
            plt.scatter([baseline_time], [baseline_price])
            plt.text(baseline_time, baseline_price, "Baseline", ha="left", va="bottom")
        if peak1_time and peak1_price:
            plt.scatter([peak1_time], [peak1_price])
            plt.text(peak1_time, peak1_price, "Peak1", ha="left", va="bottom")
        if pullback_time and pullback_price:
            plt.scatter([pullback_time], [pullback_price])
            plt.text(pullback_time, pullback_price, "Pullback", ha="left", va="bottom")
        if wave2_time and wave2_price:
            plt.scatter([wave2_time], [wave2_price])
            plt.text(wave2_time, wave2_price, "Wave2", ha="left", va="bottom")

        plt.tight_layout()

        # Sauvegarde
        dt_label = peak1_time.strftime("%Y%m%d_%H%M") if peak1_time else f"idx{idx:04d}"
        fname = f"{pattern['pattern']}_{dt_label}.png"
        out_path = str(self.plots_dir / fname)
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    # ------------------------- Scan & export ---------------------
    def scan_period(self, start_date: str, end_date: str, min_spike_pips: float = 40.0, trading_hours_only: bool = True) -> List[Dict]:
        print(f"\n🔍 SCAN PÉRIODE : {start_date} → {end_date}")
        print(f"   Seuil spike : {min_spike_pips} pips | Horaires trading : {trading_hours_only}")
        print("=" * 60)

        bern_tz = pytz.timezone('Europe/Zurich')
        start_dt = bern_tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end_dt = bern_tz.localize(datetime.strptime(end_date, "%Y-%m-%d"))

        patterns_found: List[Dict] = []
        idx = 0
        current_date = start_dt

        while current_date <= end_dt:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            if trading_hours_only:
                scan_start = current_date.replace(hour=13, minute=0, second=0, microsecond=0)
                scan_end   = current_date.replace(hour=16, minute=0, second=0, microsecond=0)
            else:
                scan_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                scan_end   = current_date.replace(hour=23, minute=59, second=59, microsecond=0)

            window_start = scan_start
            while window_start < scan_end:
                window_end = window_start + timedelta(minutes=90)
                prices = self.get_price_window(window_start, window_end)

                if len(prices) < 6:
                    window_start += timedelta(minutes=30)
                    continue

                spike = self.detect_spike_in_window(prices, min_spike_pips=min_spike_pips)
                if spike:
                    extended_end = spike["peak_time"] + timedelta(minutes=60)
                    extended_prices = self.get_price_window(spike["baseline_time"], extended_end)

                    pattern = self.analyze_pattern(spike, extended_prices)
                    if pattern.get("pattern") in {"double_wave", "single_wave_fort", "intermediate"}:
                        patterns_found.append(pattern)
                        # Plot pour cette détection
                        png = self.plot_detection(extended_prices, pattern, idx)
                        if png:
                            print(f"🖼️  Plot sauvegardé → {png}")
                        print(f"✅ {current_date.date()} | {pattern['pattern'].upper()} | impact {pattern['total_impact_pips']:.1f} pips | peak1 {pattern['peak1_time']}")
                        window_start = spike["peak_time"] + timedelta(minutes=60)
                        idx += 1
                    else:
                        window_start += timedelta(minutes=30)
                else:
                    window_start += timedelta(minutes=30)

            current_date += timedelta(days=1)

        print("\n" + "=" * 60)
        print(f"✅ SCAN TERMINÉ : {len(patterns_found)} patterns détectés")
        return patterns_found

    def export_results(self, patterns: List[Dict], output_file: str = "patterns_detected.json", output_csv: Optional[str] = "patterns_detected.csv"):
        # JSON
        serializable = []
        for p in patterns:
            q = dict(p)
            for k in ["baseline_time", "peak1_time", "pullback_time", "wave2_peak_time"]:
                if k in q and isinstance(q[k], datetime):
                    q[k] = q[k].isoformat()
            serializable.append(q)
        out_json = Path(__file__).parent / output_file
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats exportés (JSON) : {out_json}")

        # CSV
        if output_csv:
            import csv
            out_csv = Path(__file__).parent / output_csv
            keys = sorted({k for p in patterns for k in p.keys()})
            with open(out_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for p in patterns:
                    row = {}
                    for k in keys:
                        v = p.get(k)
                        if isinstance(v, datetime):
                            v = v.isoformat()
                        row[k] = v
                    w.writerow(row)
            print(f"💾 Résultats exportés (CSV)  : {out_csv}")

def main():
    print("=" * 60)
    print("🚀 SCANNER PRICE PATTERNS - SESSION 117 (rev 3: plots)")
    print("   Approche Bottom-Up : Prix → Events")
    print("=" * 60)

    scanner = PricePatternScanner(
        db_path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    )

    try:
        scanner.connect()
        patterns = scanner.scan_period(
            start_date="2024-01-01",
            end_date="2025-11-06",
            min_spike_pips=35.0,
            trading_hours_only=True
        )
        scanner.export_results(patterns)
    finally:
        scanner.disconnect()

    print("\n✅ SCAN TERMINÉ")

if __name__ == "__main__":
    main()
