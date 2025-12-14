#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V4 Scoring Builder
==================
- event_scores_empirical_v4: scores empiriques par event_key depuis prices_finnhub_m1
- kernel_weights_v4: poids appris par event_key sur kernels (daily_pattern_truth_v4)
- scoring panel: calcule global score direction + impact

DuckDB:
- events_enriched_v1(ts_utc, ts_local, date_local, country, event_key, importance_n, ...)
- prices_finnhub_m1(datetime, open, high, low, close, volume)
- daily_pattern_truth_v4(date_local, kernel_keys_json, direction, impact_mfe_pips, ...)
"""

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import pandas as pd


PIP_SIZE = 0.0001  # EURUSD


# -----------------------------
# Helpers dates / panel
# -----------------------------
def parse_dates_string(dates_str: str) -> List[str]:
    dates = [d.strip() for d in dates_str.split(",") if d.strip()]
    out = []
    for d in dates:
        dt = pd.to_datetime(d, format="%Y-%m-%d")
        out.append(dt.strftime("%Y-%m-%d"))
    # unique + sorted
    out = sorted(list(dict.fromkeys(out)))
    return out


def read_panel_file(panel_file: str) -> List[str]:
    p = Path(panel_file)
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        raise FileNotFoundError(f"Panel file not found: {p}")
    df = pd.read_csv(p)
    if "date_local" not in df.columns:
        raise ValueError(f"panel-file must contain a 'date_local' column, got columns={list(df.columns)}")
    dates = []
    for v in df["date_local"].dropna().astype(str).tolist():
        try:
            dt = pd.to_datetime(v)
            dates.append(dt.strftime("%Y-%m-%d"))
        except Exception:
            continue
    dates = sorted(list(set(dates)))
    if not dates:
        raise ValueError(f"No valid dates in {p}")
    return dates


# -----------------------------
# Kernel builder fallback
# -----------------------------
def build_kernel_keys_fallback(
    conn: duckdb.DuckDBPyConnection,
    date_local: str,
    kernel_country: str = "US",
    importance_min: int = 3,
    window_start_local: str = "13:00:00",
    window_end_local: str = "16:00:00",
) -> List[str]:
    """
    Fallback si daily_pattern_truth_v4 n'a pas la date:
    - filtre events_enriched_v1 sur date_local + pays + importance + fenêtre horaire local
    - t0 = premier event (ts_local min)
    - kernel = events dans [t0, t0+60s]
    """
    q = """
    SELECT ts_local, event_key, country, importance_n
    FROM events_enriched_v1
    WHERE date_local = CAST(? AS DATE)
    """
    df = conn.execute(q, [date_local]).df()
    if df.empty:
        return []

    df["ts_local"] = pd.to_datetime(df["ts_local"], utc=True)

    # filtres kernel
    if kernel_country:
        dfk = df[df["country"] == kernel_country].copy()
    else:
        dfk = df.copy()

    if "importance_n" in dfk.columns and importance_min is not None:
        dfk = dfk[dfk["importance_n"] >= importance_min].copy()

    # fenêtre horaire locale (ts_local contient TZ)
    try:
        ws = pd.to_datetime(f"{date_local} {window_start_local}").time()
        we = pd.to_datetime(f"{date_local} {window_end_local}").time()
        dfk["time_local"] = dfk["ts_local"].dt.tz_convert("Europe/Madrid").dt.time
        dfk = dfk[(dfk["time_local"] >= ws) & (dfk["time_local"] <= we)].copy()
    except Exception:
        pass

    if dfk.empty:
        dfk = df.copy()

    dfk = dfk.sort_values("ts_local")
    t0 = dfk.iloc[0]["ts_local"]

    t1 = t0 + pd.Timedelta(seconds=60)
    df_kernel = dfk[(dfk["ts_local"] >= t0) & (dfk["ts_local"] <= t1)].copy()

    keys = df_kernel["event_key"].dropna().astype(str).unique().tolist()
    return sorted(keys)


# -----------------------------
# Price window loader + impact calc
# -----------------------------
def load_prices_window(conn, t0_utc: pd.Timestamp, minutes_after: int) -> pd.DataFrame:
    """
    Load M1 prices around t0 with enough rows to compute baseline + future window.
    We load [t0-5min, t0+minutes_after] to ensure baseline.
    """
    t_start = (t0_utc - pd.Timedelta(minutes=5)).isoformat()
    t_end = (t0_utc + pd.Timedelta(minutes=minutes_after)).isoformat()

    q = """
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE datetime >= CAST(? AS TIMESTAMPTZ)
      AND datetime <= CAST(? AS TIMESTAMPTZ)
    ORDER BY datetime
    """
    df = conn.execute(q, [t_start, t_end]).df()
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df


def compute_event_impact_from_prices(
    prices: pd.DataFrame,
    t0_utc: pd.Timestamp,
    minutes_after: int,
) -> Optional[Tuple[float, int]]:
    """
    baseline = last close <= t0 (in the loaded window)
    window = [t0, t0+minutes_after]
    impact_pips = max( max(high)-baseline, baseline-min(low) ) / pip
    dir = +1 if up>=down else -1
    """
    if prices.empty:
        return None

    t0_utc = pd.to_datetime(t0_utc, utc=True)

    # baseline: last close at or before t0
    before = prices[prices["datetime"] <= t0_utc]
    if before.empty:
        return None
    baseline = float(before.iloc[-1]["close"])

    after_end = t0_utc + pd.Timedelta(minutes=minutes_after)
    win = prices[(prices["datetime"] >= t0_utc) & (prices["datetime"] <= after_end)]
    if win.empty:
        return None

    max_high = float(win["high"].max())
    min_low = float(win["low"].min())

    up = max_high - baseline
    down = baseline - min_low
    impact = max(up, down) / PIP_SIZE
    direction = 1 if up >= down else -1
    return impact, direction


def compute_release_impact_abs(
    prices: pd.DataFrame,
    t0_utc: pd.Timestamp,
    minutes_after: int,
) -> Optional[float]:
    """
    Compute absolute impact (pips) for a release.
    Returns impact_abs_pips (always positive, absolute value).
    """
    if prices.empty:
        return None

    t0_utc = pd.to_datetime(t0_utc, utc=True)

    # baseline: last close at or before t0
    before = prices[prices["datetime"] <= t0_utc]
    if before.empty:
        return None
    baseline = float(before.iloc[-1]["close"])

    after_end = t0_utc + pd.Timedelta(minutes=minutes_after)
    win = prices[(prices["datetime"] >= t0_utc) & (prices["datetime"] <= after_end)]
    if win.empty:
        return None

    max_high = float(win["high"].max())
    min_low = float(win["low"].min())

    up = max_high - baseline
    down = baseline - min_low
    impact_abs = max(up, down) / PIP_SIZE
    return float(impact_abs)


# -----------------------------
# Table creation / write helpers
# -----------------------------
def ensure_tables(conn: duckdb.DuckDBPyConnection, read_only: bool):
    if read_only:
        return

    # Check if table exists and get current schema
    table_exists = False
    try:
        conn.execute("SELECT 1 FROM event_scores_empirical_v4 LIMIT 1")
        table_exists = True
    except Exception:
        pass
    
    if not table_exists:
        # Create new table with V4 schema
        conn.execute("""
        CREATE TABLE event_scores_empirical_v4 (
            event_key VARCHAR,
            window_years INTEGER,
            after_minutes INTEGER,
            n_releases INTEGER,
            median_impact_pips DOUBLE,
            p80_impact_pips DOUBLE,
            p80_shrunk DOUBLE,
            hit_ratio DOUBLE,
            hit_ratio_shrunk DOUBLE,
            score_0_100 DOUBLE,
            reliability VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
    else:
        # Table exists: check if migration needed
        info = conn.execute("PRAGMA table_info('event_scores_empirical_v4')").df()
        column_names = set(info['name'].values)
        
        required_columns = {
            'n_releases', 'p80_shrunk', 'hit_ratio_shrunk', 'reliability'
        }
        missing_columns = required_columns - column_names
        
        if missing_columns:
            # Migration: backup, recreate with new schema
            print(f"🔄 Migration nécessaire: colonnes manquantes {missing_columns}")
            conn.execute("DROP TABLE IF EXISTS event_scores_empirical_v4_bak")
            conn.execute("CREATE TABLE event_scores_empirical_v4_bak AS SELECT * FROM event_scores_empirical_v4")
            
            # Drop and recreate
            conn.execute("DROP TABLE event_scores_empirical_v4")
            conn.execute("""
            CREATE TABLE event_scores_empirical_v4 (
                event_key VARCHAR,
                window_years INTEGER,
                after_minutes INTEGER,
                n_releases INTEGER,
                median_impact_pips DOUBLE,
                p80_impact_pips DOUBLE,
                p80_shrunk DOUBLE,
                hit_ratio DOUBLE,
                hit_ratio_shrunk DOUBLE,
                score_0_100 DOUBLE,
                reliability VARCHAR,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            print("✅ Table migrée vers schéma V4 (backup: event_scores_empirical_v4_bak)")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS kernel_weights_v4 (
        event_key VARCHAR,
        w_dir DOUBLE,
        w_impact DOUBLE,
        intercept_dir DOUBLE,
        intercept_impact DOUBLE,
        train_window_years INTEGER,
        n_days INTEGER,
        metrics_json VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)


def delete_insert_event_scores(conn, df_scores: pd.DataFrame, read_only: bool):
    if read_only:
        return
    conn.execute("DELETE FROM event_scores_empirical_v4;")
    conn.register("tmp_scores", df_scores)
    conn.execute("""
    INSERT INTO event_scores_empirical_v4 (
      event_key,
      window_years,
      after_minutes,
      n_releases,
      median_impact_pips,
      p80_impact_pips,
      p80_shrunk,
      hit_ratio,
      hit_ratio_shrunk,
      score_0_100,
      reliability,
      updated_at
    )
    SELECT
      event_key,
      window_years,
      after_minutes,
      n_releases,
      median_impact_pips,
      p80_impact_pips,
      p80_shrunk,
      hit_ratio,
      hit_ratio_shrunk,
      score_0_100,
      reliability,
      CURRENT_TIMESTAMP AS updated_at
    FROM tmp_scores
    """)
    conn.unregister("tmp_scores")


def delete_insert_kernel_weights(conn, df_w: pd.DataFrame, read_only: bool):
    if read_only:
        return
    conn.execute("DELETE FROM kernel_weights_v4;")
    conn.register("tmp_w", df_w)
    conn.execute("""
    INSERT INTO kernel_weights_v4 (
      event_key,
      w_dir,
      w_impact,
      intercept_dir,
      intercept_impact,
      train_window_years,
      n_days,
      metrics_json,
      updated_at
    )
    SELECT
      event_key,
      w_dir,
      w_impact,
      intercept_dir,
      intercept_impact,
      train_window_years,
      n_days,
      metrics_json,
      CURRENT_TIMESTAMP AS updated_at
    FROM tmp_w
    """)
    conn.unregister("tmp_w")


# -----------------------------
# Scoring functions
# -----------------------------
def apply_bayesian_shrinkage(value: float, n: int, global_value: float, k: int = 20) -> float:
    """
    Empirical Bayes shrinkage towards global prior.
    p80_shrunk = (n * p80 + k * p80_global) / (n + k)
    """
    if n <= 0:
        return global_value
    return float((n * value + k * global_value) / (n + k))


def apply_hit_ratio_shrinkage(hits: int, n: int, global_hit_ratio: float, k: int = 20) -> float:
    """
    Beta-Binomial shrinkage for hit ratio.
    Prior: Beta(α=k*global_hit, β=k*(1-global_hit))
    Posterior mean: (hits + α) / (n + α + β)
    """
    if n <= 0:
        return global_hit_ratio
    alpha = k * global_hit_ratio
    beta = k * (1.0 - global_hit_ratio)
    return float((hits + alpha) / (n + alpha + beta))


def compute_scores_0_100(
    df_scores: pd.DataFrame,
    min_n: int = 20
) -> pd.Series:
    """
    Compute score_0_100 for all rows using percentile ranking on score_raw = p80_shrunk * hit_ratio_shrunk.
    Then apply reliability_weight based on n_releases.
    """
    if df_scores.empty:
        return pd.Series([], dtype=float)
    
    # Compute raw scores
    score_raw = df_scores["p80_shrunk"] * df_scores["hit_ratio_shrunk"]
    
    # Percentile rank normalization (0-100)
    score_0_100 = score_raw.rank(pct=True) * 100.0
    
    # Apply reliability weight
    reliability_weight = (df_scores["n_releases"] / min_n).clip(upper=1.0)
    score_final = score_0_100 * reliability_weight
    
    return score_final


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def reliability_weight(reliability: str, n_releases: int, min_n: int = 20) -> float:
    """
    Compute reliability weight for event scoring.
    - high: weight = 1.0
    - low: weight = min(1.0, n_releases / min_n) (degraded)
    """
    if reliability == "high":
        return 1.0
    # low
    return min(1.0, max(0.0, n_releases / float(min_n)))


def aggregate_release_score(key_rows: List[Dict[str, float]]) -> float:
    """
    Aggregate scores at release level to avoid bundle duplication.
    Takes max to represent the "best proxy" of release importance.
    """
    if not key_rows:
        return 0.0
    return max(r["score_weighted"] for r in key_rows)


# -----------------------------
# 1) Build event empirical scores (OPTION A: Release-level)
# -----------------------------
def build_event_scores(conn, years: int, after_min: int, read_only: bool, min_n: int = 20, k_shrink: int = 20) -> pd.DataFrame:
    """
    Compute empirical impact distribution per event_key using RELEASE-LEVEL approach (Option A).
    
    Process:
    1. Extract unique releases: release_id = country + '|' + DATE_TRUNC('minute', ts_utc)
    2. Compute impact once per release (no duplication)
    3. Map each release to its event_keys
    4. Aggregate by event_key across releases
    5. Apply Bayesian shrinkage (p80, hit_ratio)
    6. Compute score_0_100 with reliability weight
    
    Args:
        min_n: Minimum number of releases to consider score "reliable" (default: 20)
        k_shrink: Shrinkage parameter for Bayesian shrinkage (default: 20)
    """
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=years * 365)).isoformat()

    # Step 1: Extract unique releases and their event_keys
    q_releases = """
    SELECT DISTINCT
        country,
        DATE_TRUNC('minute', ts_utc) AS release_ts_utc_min,
        ts_utc,
        event_key
    FROM events_enriched_v1
    WHERE ts_utc >= CAST(? AS TIMESTAMPTZ)
      AND event_key IS NOT NULL
      AND country IS NOT NULL
    ORDER BY ts_utc
    """
    df_events = conn.execute(q_releases, [cutoff]).df()
    if df_events.empty:
        return pd.DataFrame(columns=[
            "event_key","window_years","after_minutes","n_releases",
            "median_impact_pips","p80_impact_pips","p80_shrunk",
            "hit_ratio","hit_ratio_shrunk","score_0_100","reliability"
        ])

    df_events["ts_utc"] = pd.to_datetime(df_events["ts_utc"], utc=True)
    df_events["release_ts_utc_min"] = pd.to_datetime(df_events["release_ts_utc_min"], utc=True)
    
    # Build release_id
    df_events["release_id"] = df_events["country"].astype(str) + "|" + df_events["release_ts_utc_min"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Step 2: Compute impact once per release
    release_impacts = {}  # release_id -> impact_abs_pips
    release_keys = {}  # release_id -> list of event_keys
    
    for release_id in df_events["release_id"].unique():
        # Get first ts_utc for this release (all should be same minute)
        release_rows = df_events[df_events["release_id"] == release_id]
        t0_utc = release_rows.iloc[0]["release_ts_utc_min"]
        
        # Get all event_keys for this release
        event_keys = release_rows["event_key"].dropna().unique().tolist()
        release_keys[release_id] = event_keys
        
        # Compute impact (once per release)
        prices = load_prices_window(conn, t0_utc, after_min)
        impact_abs = compute_release_impact_abs(prices, t0_utc, after_min)
        if impact_abs is not None:
            release_impacts[release_id] = float(impact_abs)

    if not release_impacts:
        return pd.DataFrame(columns=[
            "event_key","window_years","after_minutes","n_releases",
            "median_impact_pips","p80_impact_pips","p80_shrunk",
            "hit_ratio","hit_ratio_shrunk","score_0_100","reliability"
        ])

    # Step 3: Map releases to event_keys and aggregate
    # Build event_key -> list of release impacts
    event_release_impacts = {}  # event_key -> [impact1, impact2, ...]
    
    for release_id, impact in release_impacts.items():
        for event_key in release_keys.get(release_id, []):
            if event_key not in event_release_impacts:
                event_release_impacts[event_key] = []
            event_release_impacts[event_key].append(impact)

    # Step 4: Compute global priors for shrinkage
    all_impacts = list(release_impacts.values())
    global_p80 = float(pd.Series(all_impacts).quantile(0.80))
    global_median = float(pd.Series(all_impacts).median())
    threshold_pips = global_median  # Threshold for hit ratio
    global_hit_ratio = float(sum(1 for imp in all_impacts if imp >= threshold_pips) / len(all_impacts)) if all_impacts else 0.5

    # Step 5: Aggregate by event_key with shrinkage
    agg_rows = []
    
    for event_key, impacts in event_release_impacts.items():
        if not impacts:
            continue
        
        n_releases = len(impacts)
        impacts_series = pd.Series(impacts)
        
        median_impact = float(impacts_series.median())
        p80_impact = float(impacts_series.quantile(0.80))
        
        # Apply shrinkage
        p80_shrunk = apply_bayesian_shrinkage(p80_impact, n_releases, global_p80, k_shrink)
        
        # Hit ratio: P(impact >= threshold)
        hits = sum(1 for imp in impacts if imp >= threshold_pips)
        hit_ratio = float(hits / n_releases) if n_releases > 0 else 0.0
        hit_ratio_shrunk = apply_hit_ratio_shrinkage(hits, n_releases, global_hit_ratio, k_shrink)
        
        # Reliability
        reliability = "high" if n_releases >= min_n else "low"
        
        agg_rows.append({
            "event_key": event_key,
            "window_years": years,
            "after_minutes": after_min,
            "n_releases": n_releases,
            "median_impact_pips": median_impact,
            "p80_impact_pips": p80_impact,
            "p80_shrunk": p80_shrunk,
            "hit_ratio": hit_ratio,
            "hit_ratio_shrunk": hit_ratio_shrunk,
            "score_0_100": 0.0,  # Will compute after
            "reliability": reliability
        })

    df_scores = pd.DataFrame(agg_rows)
    
    # Step 6: Compute scores with percentile ranking
    if not df_scores.empty:
        df_scores["score_0_100"] = compute_scores_0_100(df_scores, min_n)
        df_scores = df_scores.sort_values(["score_0_100", "n_releases"], ascending=[False, False])

    delete_insert_event_scores(conn, df_scores, read_only)
    return df_scores


# -----------------------------
# 2) Fit kernel weights (direction + impact)
# -----------------------------
def fit_kernel_weights(conn, years: int, read_only: bool, min_n: int = 20) -> pd.DataFrame:
    """
    Fit simple additive weights with bundle deduplication:
    - w_dir: log-odds contribution for direction up/down
    - w_impact: linear contribution for impact
    
    Anti-bundle duplication: keys in same release are weighted by 1/n_keys_in_release.
    Reliability weighting: low reliability keys are weighted down.
    
    Version v1 (robuste, sans sklearn):
    - w_dir(event_key) = log( (P(up|key)+eps) / (P(down|key)+eps) )
    - intercept_dir = log(P(up)/P(down))
    - w_impact(event_key) = mean(impact | key present) - mean(impact overall)
    - intercept_impact = mean(impact overall)
    """
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=years * 365)).isoformat()

    q = """
    SELECT date_local, kernel_keys_json, direction, impact_mfe_pips
    FROM daily_pattern_truth_v4
    WHERE date_local >= CAST(? AS DATE)
    """
    df = conn.execute(q, [cutoff]).df()
    if df.empty:
        return pd.DataFrame(columns=[
            "event_key","w_dir","w_impact","intercept_dir","intercept_impact",
            "train_window_years","n_days","metrics_json"
        ])

    # Load event scores for reliability weighting
    df_scores = load_event_scores(conn)
    reliability_lookup = {}
    n_releases_lookup = {}
    if not df_scores.empty:
        for _, row in df_scores.iterrows():
            key = str(row["event_key"])
            reliability_lookup[key] = str(row["reliability"])
            n_releases_lookup[key] = int(row["n_releases"])

    # Parse kernels and map to releases for deduplication
    kernels_with_releases = []
    for _, r in df.iterrows():
        date_local = str(r["date_local"])
        try:
            keys = json.loads(r["kernel_keys_json"]) if isinstance(r["kernel_keys_json"], str) else []
        except Exception:
            keys = []
        direction = int(r["direction"]) if pd.notna(r["direction"]) else 0
        impact = float(r["impact_mfe_pips"]) if pd.notna(r["impact_mfe_pips"]) else 0.0
        
        # Map keys to releases (dedupe bundles)
        releases = fetch_kernel_releases_for_date(conn, date_local, keys)
        
        # Build release_id -> weight mapping (1/n_keys_in_release for dedup)
        release_weights = {}  # release_id -> weight (1/n_keys_in_release)
        key_to_release_id = {}  # key -> release_id (for lookup)
        for release in releases:
            n_keys_in_release = len(release["keys"])
            weight = 1.0 / n_keys_in_release if n_keys_in_release > 0 else 0.0
            release_id = release["release_id"]
            release_weights[release_id] = weight
            for key in release["keys"]:
                # If key appears in multiple releases, keep the one with higher weight
                existing_release_id = key_to_release_id.get(key)
                if existing_release_id is None or weight > release_weights.get(existing_release_id, 0.0):
                    key_to_release_id[key] = release_id
        
        kernels_with_releases.append((keys, direction, impact, release_weights, key_to_release_id))

    # Global priors
    dirs = [d for _, d, _, _, _ in kernels_with_releases if d in (-1, 1)]
    if not dirs:
        p_up = 0.5
        p_down = 0.5
    else:
        p_up = sum(1 for d in dirs if d == 1) / len(dirs)
        p_down = 1.0 - p_up
    eps = 1e-6
    intercept_dir = math.log((p_up + eps) / (p_down + eps))

    impacts_all = [imp for _, _, imp, _, _ in kernels_with_releases if imp > 0]
    mean_impact = float(sum(impacts_all) / len(impacts_all)) if impacts_all else 0.0
    intercept_impact = mean_impact

    # Accumulate per key with bundle deduplication and reliability weighting
    stats = {}  # key -> counts (weighted)
    for keys, d, imp, release_weights, key_to_release_id in kernels_with_releases:
        keyset = set([k for k in keys if k])
        default_weight = 1.0 / len(keyset) if keyset else 0.0
        
        for k in keyset:
            # Bundle deduplication weight: 1/n_keys_in_release
            release_id = key_to_release_id.get(k)
            if release_id and release_id in release_weights:
                bundle_weight = release_weights[release_id]
            else:
                bundle_weight = default_weight
            
            # Reliability weight
            reliability = reliability_lookup.get(k, "low")
            n_releases = n_releases_lookup.get(k, 0)
            rel_weight = reliability_weight(reliability, n_releases, min_n)
            
            # Combined weight
            total_weight = bundle_weight * rel_weight
            
            s = stats.setdefault(k, {"up": 0.0, "down": 0.0, "n_dir": 0.0, "imp_sum": 0.0, "imp_n": 0.0})
            if d == 1:
                s["up"] += total_weight
                s["n_dir"] += total_weight
            elif d == -1:
                s["down"] += total_weight
                s["n_dir"] += total_weight
            if imp > 0:
                s["imp_sum"] += imp * total_weight
                s["imp_n"] += total_weight

    rows = []
    for k, s in stats.items():
        up = s["up"]
        down = s["down"]
        # w_dir = log odds difference vs global (normalized by n_dir)
        if s["n_dir"] > 0:
            p_up_key = up / s["n_dir"]
            p_down_key = down / s["n_dir"]
        else:
            p_up_key = p_up
            p_down_key = p_down
        w_dir = math.log((p_up_key + eps) / (p_down_key + eps)) - intercept_dir

        # w_impact = mean(impact|key) - mean(impact)
        mean_k = (s["imp_sum"] / s["imp_n"]) if s["imp_n"] > 0 else mean_impact
        w_imp = float(mean_k - mean_impact)

        rows.append((k, float(w_dir), float(w_imp)))

    df_w = pd.DataFrame(rows, columns=["event_key","w_dir","w_impact"])
    df_w["intercept_dir"] = float(intercept_dir)
    df_w["intercept_impact"] = float(intercept_impact)
    df_w["train_window_years"] = int(years)
    df_w["n_days"] = int(len(df))

    # métriques simples
    metrics = {
        "p_up": p_up,
        "mean_impact": mean_impact,
        "n_days_total": int(len(df)),
        "n_keys": int(len(df_w)),
        "method": "v1_empirical_additive_bundle_dedup"
    }
    df_w["metrics_json"] = json.dumps(metrics)

    delete_insert_kernel_weights(conn, df_w, read_only)
    return df_w.sort_values("w_impact", ascending=False)


# -----------------------------
# 3) Score panel dates
# -----------------------------
def load_weights(conn) -> Tuple[Dict[str, float], Dict[str, float], float, float]:
    df = conn.execute("SELECT * FROM kernel_weights_v4").df()
    if df.empty:
        return {}, {}, 0.0, 0.0
    w_dir = dict(zip(df["event_key"].astype(str), df["w_dir"].astype(float)))
    w_imp = dict(zip(df["event_key"].astype(str), df["w_impact"].astype(float)))
    intercept_dir = float(df["intercept_dir"].iloc[0])
    intercept_imp = float(df["intercept_impact"].iloc[0])
    return w_dir, w_imp, intercept_dir, intercept_imp


def load_event_scores(conn) -> pd.DataFrame:
    """Load event_scores_empirical_v4 for reliability weighting."""
    try:
        df = conn.execute("SELECT event_key, score_0_100, p80_shrunk, hit_ratio_shrunk, reliability, n_releases FROM event_scores_empirical_v4").df()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_kernel_releases_for_date(
    conn: duckdb.DuckDBPyConnection,
    date_local: str,
    kernel_keys: List[str]
) -> List[Dict[str, any]]:
    """
    Map kernel event_keys to releases (release_id) for a given date.
    Returns list of {release_id, country, ts_utc_minute, keys[]} to dedupe bundles.
    """
    if not kernel_keys:
        return []
    
    # Build query with keys filter (DuckDB: use IN with list)
    keys_str = "', '".join([k.replace("'", "''") for k in kernel_keys])
    
    q = f"""
    SELECT DISTINCT
        country,
        DATE_TRUNC('minute', ts_utc) AS ts_utc_minute,
        event_key
    FROM events_enriched_v1
    WHERE date_local = CAST(? AS DATE)
      AND event_key IN ('{keys_str}')
    ORDER BY ts_utc_minute, country
    """
    
    df = conn.execute(q, [date_local]).df()
    if df.empty:
        return []
    
    df["ts_utc_minute"] = pd.to_datetime(df["ts_utc_minute"], utc=True)
    
    # Build release_id and group by release
    df["release_id"] = df["country"].astype(str) + "|" + df["ts_utc_minute"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    releases = []
    for release_id, g in df.groupby("release_id", sort=True):
        releases.append({
            "release_id": release_id,
            "country": g["country"].iloc[0],
            "ts_utc_minute": g["ts_utc_minute"].iloc[0],
            "keys": sorted(g["event_key"].unique().tolist())
        })
    
    return releases


def get_kernel_keys_for_date(conn, date_local: str) -> List[str]:
    df = conn.execute("""
    SELECT kernel_keys_json
    FROM daily_pattern_truth_v4
    WHERE date_local = CAST(? AS DATE)
    """, [date_local]).df()
    if not df.empty and isinstance(df.iloc[0]["kernel_keys_json"], str):
        try:
            keys = json.loads(df.iloc[0]["kernel_keys_json"])
            return sorted([k for k in keys if k])
        except Exception:
            pass
    # fallback build
    return build_kernel_keys_fallback(conn, date_local)


def score_dates(
    conn,
    dates: List[str],
    out_dir: Path,
    min_n: int = 20,
    temp: float = 1.6,
    clip_logit: float = 8.0,
    eps: float = 1e-12
) -> Path:
    """
    Score dates with bundle deduplication and reliability weighting.
    
    For each date:
    1. Get kernel keys
    2. Map keys to releases (dedupe bundles)
    3. For each release: aggregate scores with reliability weights
    4. Sum release scores for global score (raw, unbounded)
    5. Normalize score_0_100 as percentile rank on panel
    
    Invariants:
    - 0 <= score_0_100 <= 100
    - 0 < prob_up < 1 (clamped to avoid exact 0/1)
    - prob_up + prob_down = 1
    - impact_pred_pips >= 0
    """
    # Load weights (if available) and event scores
    w_dir, w_imp, b_dir, b_imp = load_weights(conn)
    df_scores = load_event_scores(conn)
    
    # Build lookup dicts for event scores
    score_lookup = {}
    p80_lookup = {}
    hit_shrunk_lookup = {}
    reliability_lookup = {}
    n_releases_lookup = {}
    
    if not df_scores.empty:
        for _, row in df_scores.iterrows():
            key = str(row["event_key"])
            score_lookup[key] = float(row["score_0_100"])
            p80_lookup[key] = float(row["p80_shrunk"])
            hit_shrunk_lookup[key] = float(row["hit_ratio_shrunk"])
            reliability_lookup[key] = str(row["reliability"])
            n_releases_lookup[key] = int(row["n_releases"])
    
    rows = []
    for d in dates:
        # Get kernel keys
        keys = get_kernel_keys_for_date(conn, d)
        
        # Map keys to releases (dedupe bundles)
        releases = fetch_kernel_releases_for_date(conn, d, keys)
        
        # Aggregate scores by release (bundle dedup happens here)
        release_scores = []
        release_impacts = []
        release_dir_terms = []  # directional contributions, per release
        
        for release in releases:
            release_keys = release["keys"]
            
            # For each key in release, compute weighted score
            key_rows = []
            for key in release_keys:
                score_raw = score_lookup.get(key, 0.0)
                p80_shrunk = p80_lookup.get(key, 0.0)
                hit_shrunk = hit_shrunk_lookup.get(key, 0.0)
                reliability = reliability_lookup.get(key, "low")
                n_releases = n_releases_lookup.get(key, 0)
                
                # Apply reliability weight
                w_rel = reliability_weight(reliability, n_releases, min_n)
                score_weighted = score_raw * w_rel
                impact_weighted = p80_shrunk * hit_shrunk * w_rel
                
                # Direction term: use kernel learned weights, but
                # (a) reliability-weighted
                # (b) divided by number of keys in the release to avoid bundle multiplication
                # (c) defaults to 0 if not found
                w_key_dir = float(w_dir.get(key, 0.0)) if w_dir else 0.0
                dir_term = (w_key_dir * w_rel) / max(1, len(release_keys))
                
                key_rows.append({
                    "score_weighted": score_weighted,
                    "impact_weighted": impact_weighted,
                    "dir_term": dir_term,
                    "score_raw": score_raw,
                    "key": key
                })
            
            # Aggregate at release level (max to avoid duplication)
            if key_rows:
                release_score = aggregate_release_score(key_rows)
                release_impact = max(r["impact_weighted"] for r in key_rows)
                release_scores.append(release_score)
                release_impacts.append(release_impact)
                # sum dir terms within release (already normalized by n_keys)
                release_dir_terms.append(sum(r["dir_term"] for r in key_rows))
        
        # Global "raw" score = sum of release scores (NOT bounded)
        score_raw_sum = sum(release_scores) if release_scores else 0.0
        global_impact = sum(release_impacts) if release_impacts else 0.0
        
        # Direction probability: dedup at release level + reliability weighting.
        # Also apply temperature + logit clipping to avoid saturation.
        if w_dir and release_dir_terms:
            s_dir = float(b_dir) + float(sum(release_dir_terms))
            # temperature scaling
            s_dir = s_dir / max(eps, float(temp))
            # clip
            if clip_logit is not None:
                s_dir = max(-float(clip_logit), min(float(clip_logit), s_dir))
            p_up = sigmoid(s_dir)
            # avoid exact 0/1
            p_up = min(1.0 - eps, max(eps, float(p_up)))
        else:
            p_up = 0.5  # neutral if no weights or no releases
        p_down = 1.0 - p_up
        
        rows.append({
            "date_local": d,
            "kernel_size": len(keys),
            "kernel_releases": len(releases),
            "kernel_keys_json": json.dumps(keys),
            "score_raw_sum": float(score_raw_sum),
            "prob_up": float(p_up),
            "prob_down": float(p_down),
            "impact_pred_pips": float(global_impact)
        })
    
    df_out = pd.DataFrame(rows)
    
    # Build bounded score_0_100 as percentile rank of score_raw_sum on this panel
    if not df_out.empty:
        s = df_out["score_raw_sum"].astype(float)
        # percentile rank in [0,1]
        pct = s.rank(method="average", pct=True)
        df_out["score_0_100"] = (pct * 100.0).astype(float)
        # hard clamp invariant
        df_out["score_0_100"] = df_out["score_0_100"].clip(0.0, 100.0)
    else:
        df_out["score_0_100"] = []
    
    # Reorder columns nicely
    cols = [
        "date_local", "kernel_size", "kernel_releases", "kernel_keys_json",
        "score_raw_sum", "score_0_100", "prob_up", "prob_down", "impact_pred_pips"
    ]
    df_out = df_out[cols]
    
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"v4_scores_panel_{ts}.csv"
    df_out.to_csv(out_path, index=False)
    return out_path


# -----------------------------
# Self-test / Validation
# -----------------------------
def run_self_tests(
    conn,
    dates: List[str],
    out_dir: Path,
    min_n: int = 20,
    temp: float = 1.6,
    clip_logit: float = 8.0,
    eps: float = 1e-12,
    export_csv: bool = True
) -> bool:
    """
    Run self-tests on score_dates output to verify invariants.
    
    Returns True if all tests pass, False otherwise.
    """
    print("\n" + "=" * 80)
    print("V4 SELF-TEST: Validating score_dates() invariants")
    print("=" * 80)
    
    # Generate scores
    out_path = score_dates(conn, dates, out_dir, min_n, temp, clip_logit, eps)
    df = pd.read_csv(out_path)
    
    if df.empty:
        print("❌ ERROR: Empty DataFrame")
        return False
    
    print(f"📊 Testing {len(df)} dates from: {out_path}")
    print()
    
    errors = []
    warnings = []
    
    # Test 1: score_0_100 bounds
    s100 = df["score_0_100"].astype(float)
    if (s100 < 0).any() or (s100 > 100).any():
        errors.append(f"score_0_100 out of bounds: min={s100.min():.2f}, max={s100.max():.2f}")
    else:
        print(f"✅ score_0_100 ∈ [0, 100]: min={s100.min():.2f}, max={s100.max():.2f}")
    
    # Test 2: prob_up bounds
    p_up = df["prob_up"].astype(float)
    if (p_up <= 0).any() or (p_up >= 1).any():
        errors.append(f"prob_up not in (0,1): min={p_up.min():.6f}, max={p_up.max():.6f}")
    else:
        print(f"✅ prob_up ∈ (0,1): min={p_up.min():.6f}, max={p_up.max():.6f}")
    
    # Test 3: prob_up + prob_down = 1
    p_down = df["prob_down"].astype(float)
    diff = (p_up + p_down - 1.0).abs()
    max_diff = diff.max()
    if max_diff > 1e-9:
        errors.append(f"prob_up + prob_down ≠ 1: max_diff={max_diff:.2e}")
    else:
        print(f"✅ prob_up + prob_down = 1: max_diff={max_diff:.2e}")
    
    # Test 4: impact_pred_pips >= 0
    impact = df["impact_pred_pips"].astype(float)
    if (impact < 0).any():
        errors.append(f"impact_pred_pips < 0: min={impact.min():.2f}")
    else:
        print(f"✅ impact_pred_pips >= 0: min={impact.min():.2f}, max={impact.max():.2f}")
    
    # Test 5: kernel_releases >= 0, kernel_size >= 0
    n_rel = df["kernel_releases"].astype(int)
    n_size = df["kernel_size"].astype(int)
    if (n_rel < 0).any() or (n_size < 0).any():
        errors.append(f"kernel_releases or kernel_size < 0")
    else:
        print(f"✅ kernel_releases >= 0, kernel_size >= 0")
    
    # Test 6: If kernel_releases == 0, then score_raw_sum == 0, impact == 0, prob_up == 0.5
    zero_releases = df[n_rel == 0]
    if not zero_releases.empty:
        for _, row in zero_releases.iterrows():
            date = row["date_local"]
            if abs(float(row["score_raw_sum"])) > eps:
                errors.append(f"date {date}: kernel_releases=0 but score_raw_sum={row['score_raw_sum']} != 0")
            if abs(float(row["impact_pred_pips"])) > eps:
                errors.append(f"date {date}: kernel_releases=0 but impact_pred_pips={row['impact_pred_pips']} != 0")
            if abs(float(row["prob_up"]) - 0.5) > eps:
                warnings.append(f"date {date}: kernel_releases=0 but prob_up={row['prob_up']:.4f} != 0.5")
        if not errors:
            print(f"✅ kernel_releases=0 → score_raw_sum=0, impact=0, prob_up≈0.5 ({len(zero_releases)} dates)")
    
    # Test 7: score_raw_sum vs score_0_100 relationship
    s_raw = df["score_raw_sum"].astype(float)
    if len(s_raw) > 1:
        # score_0_100 should be monotonic with score_raw_sum
        corr = s_raw.corr(s100)
        if corr < 0.9:
            warnings.append(f"score_0_100 correlation with score_raw_sum: {corr:.3f} (< 0.9)")
        else:
            print(f"✅ score_0_100 monotonic with score_raw_sum: corr={corr:.3f}")
    
    # Summary
    print()
    print("=" * 80)
    if errors:
        print(f"❌ FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"   • {e}")
        if warnings:
            print(f"\n⚠️  WARNINGS: {len(warnings)}")
            for w in warnings:
                print(f"   • {w}")
        return False
    else:
        print(f"✅ ALL TESTS PASSED")
        if warnings:
            print(f"\n⚠️  WARNINGS: {len(warnings)}")
            for w in warnings:
                print(f"   • {w}")
        if export_csv:
            test_path = out_dir / f"v4_self_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(test_path, index=False)
            print(f"\n📄 Test results exported: {test_path}")
        return True


# -----------------------------
# Main CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=str, default="data/warehouse.duckdb")
    ap.add_argument("--years", type=int, default=3, help="Rolling window (years) for training/event scores")
    ap.add_argument("--after-min", type=int, default=120, help="Price window after t0 in minutes (event scores)")
    ap.add_argument("--build-event-scores", action="store_true")
    ap.add_argument("--fit-kernel-weights", action="store_true")
    ap.add_argument("--score-dates", action="store_true")

    ap.add_argument("--dates", type=str, help='Dates "YYYY-MM-DD,YYYY-MM-DD,..."')
    ap.add_argument("--panel-file", type=str, help="CSV with date_local column")

    ap.add_argument("--readonly", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="Run self-tests on score_dates output (requires --score-dates)")

    args = ap.parse_args()

    read_only_mode = bool(args.readonly or args.dry_run)

    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    print("=" * 80)
    print("V4 SCORING BUILDER")
    print("=" * 80)
    print(f"📁 DB: {db_path}")
    print(f"🧷 DB mode: {'READONLY' if read_only_mode else 'WRITE'}")
    print(f"🪟 Window years: {args.years}")
    print(f"⏱️  after-min: {args.after_min}")
    print("=" * 80)

    conn = duckdb.connect(str(db_path), read_only=read_only_mode)

    try:
        ensure_tables(conn, read_only_mode)

        if args.build_event_scores:
            print("\n[1/3] Building event empirical scores...")
            df_scores = build_event_scores(conn, args.years, args.after_min, read_only_mode)
            print(f"✅ event_scores_empirical_v4 rows: {len(df_scores)}")
            if len(df_scores) > 0:
                print(df_scores.head(10).to_string(index=False))

        if args.fit_kernel_weights:
            print("\n[2/3] Fitting kernel weights...")
            df_w = fit_kernel_weights(conn, args.years, read_only_mode, min_n=20)
            print(f"✅ kernel_weights_v4 rows: {len(df_w)}")
            if len(df_w) > 0:
                print(df_w.head(10)[["event_key","w_dir","w_impact"]].to_string(index=False))

        if args.score_dates:
            if args.dates:
                dates = parse_dates_string(args.dates)
            elif args.panel_file:
                dates = read_panel_file(args.panel_file)
            else:
                raise ValueError("--score-dates requires --dates or --panel-file")

            print("\n[3/3] Scoring dates...")
            out_path = score_dates(conn, dates, Path("outputs"), min_n=20)
            print(f"✅ CSV exported: {out_path}")
            
            # Self-test if requested
            if args.self_test:
                success = run_self_tests(conn, dates, Path("outputs"), min_n=20, export_csv=True)
                if not success:
                    print("\n❌ Self-tests failed. Please review the errors above.")
                    import sys
                    sys.exit(1)

        if read_only_mode:
            print("\n🧪 Mode read-only: aucune écriture effectuée")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
