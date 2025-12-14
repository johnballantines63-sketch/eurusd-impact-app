-- ============================================================================
-- DAILY_PATTERN_TRUTH_V4 - Vérité terrain patterns depuis prix M1
-- ============================================================================
-- Version: V4
-- Objectif: stocker (par jour) le pattern labellisé depuis EURUSD M1
--           + infos kernel (t0, kernel_keys, counts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_pattern_truth_v4 (
    date_local DATE PRIMARY KEY,

    -- Meta
    timezone VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Kernel (déclencheur)
    t0_local TIMESTAMP,
    kernel_first_ts_local TIMESTAMP,
    kernel_event_count INTEGER,
    kernel_keys_json VARCHAR,   -- JSON array des event_keys du kernel

    -- Vérité terrain pattern
    pattern VARCHAR,            -- 'single_wave', 'double_wave', 'zigzag', 'unknown'
    direction INTEGER,          -- +1 (up), -1 (down), 0 (unknown)

    -- Mesures (pips & temps)
    impact_mfe_pips DOUBLE,
    mae_pips DOUBLE,
    t_end_local TIMESTAMP,
    time_to_peak_min INTEGER,
    retracement_pips DOUBLE,
    n_swings DOUBLE,
    n_alternances DOUBLE,

    -- Reproductibilité
    config_hash VARCHAR,
    config_json VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_pattern_truth_v4_pattern
    ON daily_pattern_truth_v4(pattern);

CREATE INDEX IF NOT EXISTS idx_pattern_truth_v4_date
    ON daily_pattern_truth_v4(date_local);

