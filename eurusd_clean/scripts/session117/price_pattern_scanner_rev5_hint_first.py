"""
Price Pattern Scanner + Plots (rev 5 – first-after-hint selection)
------------------------------------------------------------------
But: pour les journées comme le 11/09, démarrer la Wave 1 à 14:30 si un spike >= seuil
apparaît APRÈS 14:30. Sinon, on retombe sur le pic "max" de la fenêtre.
=> On n'impose PAS 14:30 tous les jours, seulement quand un vrai spike existe.

Changements clés:
- detect_spike_in_window(): recense tous les écarts (en pips) à la MM5 >= seuil,
  choisit le **premier** index >= event_hint_time (ex "14:30") s'il existe;
  sinon, choisit l'index du **max** global.
- baseline = moyenne des BASELINE_N barres AVANT l'index choisi.
- paramètres: self.peak_select_mode = "first_after_hint" | "max"
"""

import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
import pytz

import matplotlib.pyplot as plt

PIP = 0.0001

def mid_from_hl(high: float, low: float) -> float:
    return (high + low) / 2.0

def pips_diff(p1: float, p2: float) -> float:
    return abs(p1 - p2) * 10000.0

class PricePatternScanner:
    def __init__(self, db_path: str = "data/warehouse.duckdb"):
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

        # Seuils & fenêtres
        self.MIN_SPIKE_PIPS = 35.0
        self.ROLL_N = 5                 # moyenne mobile pour repérer les écarts
        self.BASELINE_N = 5             # baseline locale = N barres avant le pic choisi
        self.PULLBACK_WIN_MIN = 30
        self.WAVE2_WIN_MIN = 30
        self.PULLBACK_DOUBLE_MIN = 0.25
        self.PULLBACK_DOUBLE_MAX = 0.70
        self.PULLBACK_SINGLE_MAX = 0.30
        self.ALPHA_WAVE2_OVER_WAVE1 = 0.60

        # Sélection de pic
        self.event_hint_time: Optional[str] = "14:30"
        self.peak_select_mode: str = "first_after_hint"  # ou "max"

        # Dossier plots
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
        """
        Détecte un spike significatif :
        - calcule mid & MM(ROLL_N),
        - calcule dev_pips = |mid - MM| en pips,
        - candidats = indices où dev_pips >= min_spike_pips,
        - si mode "first_after_hint": prend le **premier** candidat >= event_hint_time,
          sinon prend index du **max** global (fallback si aucun après hint).
        - baseline = moyenne des BASELINE_N barres **avant** l'indice choisi.
        """
        if len(prices) < max(self.BASELINE_N + 1, self.ROLL_N + 1):
            return None
        if min_spike_pips is None:
            min_spike_pips = self.MIN_SPIKE_PIPS

        mids = [(r[0], mid_from_hl(r[2], r[3])) for r in prices]
        times = [t for (t, _) in mids]
        vals  = [v for (_, v) in mids]

        # MM simple
        roll = []
        for i in range(len(vals)):
            if i < self.ROLL_N - 1:
                roll.append(None)
            else:
                roll.append(sum(vals[i-self.ROLL_N+1:i+1]) / self.ROLL_N)

        # Ecart en pips
        dev_pips = [pips_diff(vals[i], roll[i]) if roll[i] is not None else 0.0 for i in range(len(vals))]

        # Candidats >= seuil
        cand_idx = [i for i in range(len(dev_pips)) if dev_pips[i] >= min_spike_pips]
        if not cand_idx:
            return None

        chosen = None
        if self.peak_select_mode == "first_after_hint" and self.event_hint_time:
            try:
                hh, mm = map(int, self.event_hint_time.split(":"))
                hint_dt = times[0].replace(hour=hh, minute=mm, second=0, microsecond=0)
                if times[0].tzinfo:
                    hint_dt = hint_dt.replace(tzinfo=times[0].tzinfo)
                for i in cand_idx:
                    if times[i] >= hint_dt:
                        chosen = i
                        break
            except Exception:
                chosen = None

        if chosen is None:
            # Fallback: max global
            chosen = max(cand_idx, key=lambda i: dev_pips[i])

        # Baseline locale
        base_start = max(0, chosen - self.BASELINE_N)
        base_end   = chosen
        if base_end - base_start < self.BASELINE_N:
            return None

        baseline = sum(vals[base_start:base_end]) / self.BASELINE_N
        baseline_time = times[base_start]
        peak_price = vals[chosen]
        peak_time  = times[chosen]
        spike = pips_diff(peak_price, baseline)
        if spike < min_spike_pips:
            return None

        direction = "bullish" if peak_price > baseline else "bearish"
        return {
            "baseline_price": baseline,
            "baseline_time": baseline_time,
            "peak_price": peak_price,
            "peak_time": peak_time,
            "spike_pips": spike,
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

    # ------------------------- Plot ------------------------------
    def plot_detection(self, extended_window: List[tuple], pattern: Dict, idx: int) -> str:
        if not extended_window or "pattern" not in pattern:
            return ""
        times = [r[0] for r in extended_window]
        mids  = [mid_from_hl(r[2], r[3]) for r in extended_window]

        plt.figure(figsize=(10,5))
        plt.plot(times, mids, linewidth=2)
        plt.title(f"EUR/USD – {pattern['pattern']} | impact {pattern['total_impact_pips']:.1f} pips")
        plt.xlabel("Heure"); plt.ylabel("Mid price")

        for k in ["baseline_time","peak1_time","pullback_time","wave2_peak_time"]:
            if pattern.get(k): plt.axvline(pattern[k], linestyle="--", linewidth=1)

        for label, tk, pk in [("Baseline","baseline_time","baseline_price"),
                              ("Peak1","peak1_time","peak1_price"),
                              ("Pullback","pullback_time","pullback_price"),
                              ("Wave2","wave2_peak_time","wave2_peak_price")]:
            t = pattern.get(tk); p = pattern.get(pk)
            if t and p:
                plt.scatter([t], [p]); plt.text(t, p, label, ha="left", va="bottom")

        # Event hint
        if self.event_hint_time:
            try:
                hh, mm = map(int, self.event_hint_time.split(":"))
                hint_dt = times[0].replace(hour=hh, minute=mm, second=0, microsecond=0)
                if times[0].tzinfo:
                    hint_dt = hint_dt.replace(tzinfo=times[0].tzinfo)
                if times[0] <= hint_dt <= times[-1]:
                    plt.axvline(hint_dt, linestyle=":", linewidth=1)
                    plt.text(hint_dt, min(mids), f"Event hint {self.event_hint_time}", rotation=90, va="bottom")
            except Exception:
                pass

        plt.tight_layout()
        out = self.plots_dir / f"{pattern['pattern']}_{pattern.get('peak1_time').strftime('%Y%m%d_%H%M')}.png"
        plt.savefig(out, dpi=150); plt.close()
        return str(out)

    # ------------------------- Scan ------------------------------
    def scan_period(self, start_date: str, end_date: str, min_spike_pips: float = 35.0, trading_hours_only: bool = True) -> List[Dict]:
        print(f"\n🔍 SCAN PÉRIODE : {start_date} → {end_date}")
        print(f"   Seuil spike : {min_spike_pips} pips | Horaires trading : {trading_hours_only}")
        print("=" * 60)

        bern_tz = pytz.timezone('Europe/Zurich')
        start_dt = bern_tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end_dt = bern_tz.localize(datetime.strptime(end_date, "%Y-%m-%d"))

        patterns_found: List[Dict] = []
        idx = 0; current_date = start_dt
        while current_date <= end_dt:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1); continue

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
                    window_start += timedelta(minutes=30); continue

                spike = self.detect_spike_in_window(prices, min_spike_pips=min_spike_pips)
                if spike:
                    extended_end = spike["peak_time"] + timedelta(minutes=60)
                    extended_prices = self.get_price_window(spike["baseline_time"], extended_end)
                    pattern = self.analyze_pattern(spike, extended_prices)
                    if pattern.get("pattern") in {"double_wave","single_wave_fort","intermediate"}:
                        patterns_found.append(pattern)
                        png = self.plot_detection(extended_prices, pattern, idx)
                        if png: print(f"🖼️  Plot → {png}")
                        print(f"✅ {current_date.date()} | {pattern['pattern'].upper()} | impact {pattern['total_impact_pips']:.1f} pips | peak1 {pattern['peak1_time']}")
                        window_start = spike["peak_time"] + timedelta(minutes=60); idx += 1
                    else:
                        window_start += timedelta(minutes=30)
                else:
                    window_start += timedelta(minutes=30)

            current_date += timedelta(days=1)

        print("\n" + "=" * 60)
        print(f"✅ SCAN TERMINÉ : {len(patterns_found)} patterns détectés")
        return patterns_found

    def export_results(self, patterns: List[Dict], output_file: str = "patterns_detected.json", output_csv: Optional[str] = "patterns_detected.csv"):
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
    print("🚀 SCANNER PRICE PATTERNS - rev 5 (first-after-hint)")
    print("=" * 60)

    scanner = PricePatternScanner(
        db_path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    )
    scanner.event_hint_time = "14:30"
    scanner.peak_select_mode = "first_after_hint"  # comportement demandé

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
