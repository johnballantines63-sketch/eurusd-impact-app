# fx_impact_app/src/forecaster_mvp.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import pandas as pd
import duckdb

from fx_impact_app.src.config import get_db_path

# Ajout en début de fichier (après les imports)

# Horizons par défaut (minutes)
HORIZONS = [15, 30, 60]

def compute_surprise(actual: float, consensus: float) -> float:
    """
    Calcule la surprise en % : (Actual - Consensus) / |Consensus| * 100
    Retourne 0.0 si consensus est nul pour éviter division par zéro.
    """
    if consensus == 0:
        return 0.0
    return ((actual - consensus) / abs(consensus)) * 100.0


# --------- familles -> regex (case-insensitive, on matche en lower()) ----------
_FAMILY_REGEX: Dict[str, str] = {
    # NFP / emploi US
    "NFP": r"(nonfarm|non-farm|nfp|payrolls|employment)",
    # CPI / inflation
    "CPI": r"(cpi|inflation|consumer price)",
    # FOMC / Fed
    "FOMC": r"(fomc|fed (rate|interest)|policy statement|dot ?plot|press conference|powell)",
}

@dataclass
class ForecastRequest:
    event_family: str
    actual: float
    consensus: float
    country: str = "US"
    window_before_min: int = 60
    window_after_min: int = 15
    horizons: List[int] = None
    strict_decision: bool = False
    # seuils (en pips) pour latence (départ) et retour (autour du point d'entrée)
    thr_pips: float = 10.0
    rev_pips: float = 5.0

    def __post_init__(self):
        if self.horizons is None:
            self.horizons = [15, 30, 60]
        self.event_family = str(self.event_family or "").upper()
        if self.event_family not in _FAMILY_REGEX:
            raise ValueError(f"Unknown family {self.event_family}; allowed: {list(_FAMILY_REGEX)}")

@dataclass
class StatRow:
    horizon: int
    n: int
    p_up: float
    mfe_med: float
    mfe_p80: float
    latency_med: Optional[float] = None
    latency_p80: Optional[float] = None
    ttr_med: Optional[float] = None
    ttr_p80: Optional[float] = None

# ------------ helpers ---------------

def _family_to_regex(family: str) -> str:
    return _FAMILY_REGEX[family]

def _price_max_ts(con: duckdb.DuckDBPyConnection) -> Optional[pd.Timestamp]:
    df = con.execute("SELECT MAX(ts_utc) AS t FROM prices_1m_v").df()
    t = df.iloc[0]["t"]
    return pd.Timestamp(t) if pd.notna(t) else None

def _events_ts_for_family(
    con: duckdb.DuckDBPyConnection,
    family: str,
    country: Optional[str],
    time_from: Optional[pd.Timestamp],
    time_to: Optional[pd.Timestamp],
) -> pd.DataFrame:
    """
    Renvoie une colonne 'ts_utc' (TIMESTAMP naïf UTC) des événements
    filtrés par regex famille + country + fenêtre. Utilise regexp_matches().
    """
    regex = _family_to_regex(family)

    q = """
    SELECT DISTINCT CAST(ts_utc AS TIMESTAMP) AS ts_utc
    FROM events
    WHERE (? IS NULL OR country = ?)
      AND (
        regexp_matches(lower(coalesce(event_title, '')), ?)
        OR regexp_matches(lower(coalesce(type, '')), ?)
        OR regexp_matches(lower(coalesce(event_key, '')), ?)
      )
      AND (? IS NULL OR ts_utc >= ?)
      AND (? IS NULL OR ts_utc <  ?)
    ORDER BY ts_utc
    """
    params = [
        country, country,
        regex, regex, regex,
        time_from, time_from,
        time_to, time_to,
    ]
    df = con.execute(q, params).df()

    # on garde uniquement les ts qui ont une bougie d'entrée disponible
    if not df.empty:
        con.register("ev", df)
        df = con.execute("""
          SELECT ev.ts_utc
          FROM ev
          JOIN prices_1m_v p USING(ts_utc)
          ORDER BY ev.ts_utc
        """).df()
        con.unregister("ev")
    return df

def _stats_for_horizon(
    con: duckdb.DuckDBPyConnection,
    event_ts: pd.DataFrame,  # colonne ts_utc
    horizon_min: int,
    thr_pips: float,
    rev_pips: float,
) -> StatRow:
    """
    Calcule, pour un horizon (minutes):
      - p_up : proba que close(t0+h) > close(t0)
      - MFE (pips) médian / P80
      - latence (min) jusqu'au franchissement thr_pips dans le sens du MFE
      - TTR (min) time-to-reversal après le pic (retour à ±rev_pips autour de l'entrée)
    """
    if event_ts.empty:
        return StatRow(horizon=horizon_min, n=0, p_up=0.0, mfe_med=0.0, mfe_p80=0.0)

    con.register("ev", event_ts)
    pip = 1.0 / 10000.0
    thr = thr_pips * pip
    rev = rev_pips * pip

    sql = f"""
    WITH e AS (
      SELECT ev.ts_utc AS t0, p.close AS px0
      FROM ev
      JOIN prices_1m_v p ON p.ts_utc = ev.ts_utc
    ),
    h AS (  -- close à l'horizon
      SELECT e.t0, ph.close AS close_h
      FROM e
      LEFT JOIN prices_1m_v ph ON ph.ts_utc = e.t0 + INTERVAL {horizon_min} MINUTE
    ),
    w AS (  -- fenêtre minute par minute
      SELECT e.t0, e.px0, p.ts_utc, p.close
      FROM e
      JOIN prices_1m_v p
        ON p.ts_utc > e.t0 AND p.ts_utc <= e.t0 + INTERVAL {horizon_min} MINUTE
    ),
    agg AS ( -- MFE up/down et magnitude absolue
      SELECT
        t0,
        MAX(close - px0)  AS up,
        MIN(close - px0)  AS down,
        GREATEST(ABS(MAX(close - px0)), ABS(MIN(close - px0))) AS mfe_abs
      FROM w
      GROUP BY t0
    ),
    dir AS (
      SELECT t0,
             CASE WHEN ABS(up) >= ABS(down) THEN 'UP' ELSE 'DOWN' END AS side
      FROM agg
    ),
    hits AS ( -- premiers franchissements (thr)
      SELECT
        w.t0,
        MIN(CASE WHEN (w.close - w.px0) >= {thr} THEN w.ts_utc END) AS hit_up,
        MIN(CASE WHEN (w.px0 - w.close) >= {thr} THEN w.ts_utc END) AS hit_dn
      FROM w
      GROUP BY w.t0
    ),
    peak AS ( -- timestamp du pic (MFE absolu)
      SELECT t0,
             arg_max(ts_utc, ABS(close - px0)) AS t_peak
      FROM w
      GROUP BY t0
    ),
    rev AS ( -- premier retour à ±rev autour de l'entrée, après le pic
      SELECT
        w.t0,
        MIN(CASE WHEN w.ts_utc > p.t_peak AND ABS(w.close - w.px0) <= {rev} THEN w.ts_utc END) AS t_rev
      FROM w
      JOIN peak p USING(t0)
      GROUP BY w.t0
    ),
    per_event AS (
      SELECT
        e.t0,
        -- direction finale à l'horizon, proba up
        CASE WHEN h.close_h IS NULL THEN NULL
             WHEN h.close_h > e.px0 THEN 1 ELSE 0 END AS is_up,
        -- MFE (pips)
        ROUND( (SELECT mfe_abs FROM agg WHERE agg.t0 = e.t0) * 10000.0 , 6) AS mfe_pips,
        -- latence (minutes) dans le sens dominant
        CASE
          WHEN (SELECT side FROM dir WHERE dir.t0 = e.t0) = 'UP'
               THEN CASE WHEN (SELECT hit_up FROM hits WHERE hits.t0 = e.t0) IS NULL
                         THEN NULL
                         ELSE datediff('minute', e.t0, (SELECT hit_up FROM hits WHERE hits.t0=e.t0)) END
          ELSE CASE WHEN (SELECT hit_dn FROM hits WHERE hits.t0 = e.t0) IS NULL
                    THEN NULL
                    ELSE datediff('minute', e.t0, (SELECT hit_dn FROM hits WHERE hits.t0=e.t0)) END
        END AS latency_min,
        -- time-to-reversal (min) depuis le pic
        CASE
          WHEN (SELECT t_rev FROM rev WHERE rev.t0 = e.t0) IS NULL
               OR (SELECT t_peak FROM peak WHERE peak.t0 = e.t0) IS NULL
               THEN NULL
          ELSE datediff('minute',
                        (SELECT t_peak FROM peak WHERE peak.t0=e.t0),
                        (SELECT t_rev  FROM rev  WHERE rev.t0 =e.t0))
        END AS ttr_min
      FROM e
      LEFT JOIN h USING(t0)
    )
    SELECT
      COUNT(*)                                         AS n,
      AVG(is_up)::DOUBLE                               AS p_up,
      quantile(mfe_pips, 0.5)                          AS mfe_med,
      quantile(mfe_pips, 0.8)                          AS mfe_p80,
      quantile(latency_min, 0.5) FILTER (WHERE latency_min IS NOT NULL) AS latency_med,
      quantile(latency_min, 0.8) FILTER (WHERE latency_min IS NOT NULL) AS latency_p80,
      quantile(ttr_min, 0.5)     FILTER (WHERE ttr_min     IS NOT NULL) AS ttr_med,
      quantile(ttr_min, 0.8)     FILTER (WHERE ttr_min     IS NOT NULL) AS ttr_p80
    FROM per_event;
    """

    out = con.execute(sql).df().iloc[0].to_dict()
    con.unregister("ev")

    return StatRow(
        horizon=horizon_min,
        n=int(out["n"] or 0),
        p_up=float(out["p_up"] or 0.0),
        mfe_med=float(out["mfe_med"] or 0.0),
        mfe_p80=float(out["mfe_p80"] or 0.0),
        latency_med=(None if pd.isna(out["latency_med"]) else float(out["latency_med"])),
        latency_p80=(None if pd.isna(out["latency_p80"]) else float(out["latency_p80"])),
        ttr_med=(None if pd.isna(out["ttr_med"]) else float(out["ttr_med"])),
        ttr_p80=(None if pd.isna(out["ttr_p80"]) else float(out["ttr_p80"])),
    )

# ------------- API principale ----------------

def forecast(req: ForecastRequest,
             time_from: Optional[pd.Timestamp] = None,
             time_to: Optional[pd.Timestamp] = None
            ) -> Tuple[List[StatRow], Dict]:
    """
    Calcule des stats d’impact pour une famille donnée sur l’historique.
    Retourne (liste StatRow par horizon, diagnostics).
    """
    path = get_db_path()
    with duckdb.connect(path) as con:
        con.execute("PRAGMA threads=2")
        con.execute("PRAGMA preserve_insertion_order=false")

        regex = _family_to_regex(req.event_family)
        ev = _events_ts_for_family(con, req.event_family, req.country, time_from, time_to)
        hist_n = len(ev)
        hist_n_unique = ev["ts_utc"].nunique() if hist_n else 0

        # Prix max connu (utile pour cadrer l’historique de calcul dans l’UI)
        pmax = _price_max_ts(con)

        stats: List[StatRow] = []
        for h in req.horizons:
            s = _stats_for_horizon(con, ev, h, req.thr_pips, req.rev_pips)
            stats.append(s)

        diags = {
            "hist_n": hist_n,
            "hist_n_unique_ts": hist_n_unique,
            "regex": regex,
            "price_max_ts": None if pmax is None else pmax.strftime("%Y-%m-%d %H:%M:%S"),
            "db_path": path,
        }
        return stats, diags
