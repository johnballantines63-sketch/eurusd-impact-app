-- ============================================================================
-- EVENTS_ENRICHED_V1 - Source Canonique des Événements
-- ============================================================================
-- Version: V1
-- Date: 2025-12-13
-- Objectif: Créer une VIEW canonique qui unifie events_with_ts_local_v1
--           et economic_events avec consensus robuste (priorité economic_events)
-- ============================================================================

-- DROP VIEW IF EXISTS events_enriched_v1;

CREATE OR REPLACE VIEW events_enriched_v1 AS
WITH base_events AS (
    -- Source principale: events_with_ts_local_v1
    SELECT
        ts_utc,
        ts_local,
        DATE(ts_local) AS date_local,
        country,
        COALESCE(event_key, 
                 -- Fallback: créer event_key déterministe
                 LOWER(REGEXP_REPLACE(event_title, '[^a-zA-Z0-9]', '')) || '_' || 
                 CAST(EXTRACT(EPOCH FROM ts_utc) AS VARCHAR) || '_' || country
        ) AS event_key,
        event_title,
        actual,
        estimate AS estimate_base,
        forecast AS forecast_base,
        previous AS previous_base,
        importance_n,
        -- Normaliser event_title pour matching
        LOWER(REGEXP_REPLACE(event_title, '[^a-zA-Z0-9 ]', '')) AS normalized_title
    FROM events_with_ts_local_v1
),

-- Enrichissement depuis economic_events (prioritaire pour consensus)
econ_enrichment AS (
    SELECT
        datetime_utc AS ts_utc_econ,
        country AS country_econ,
        event_name,
        forecast AS forecast_econ,
        previous AS previous_econ,
        LOWER(REGEXP_REPLACE(event_name, '[^a-zA-Z0-9 ]', '')) AS normalized_event_name
    FROM economic_events
),

-- Join sur (ts_utc arrondi minute + country) pour matching temporel
matched_econ AS (
    SELECT
        b.*,
        e.forecast_econ,
        e.previous_econ,
        'economic_events' AS debug_source_consensus_temp
    FROM base_events b
    LEFT JOIN econ_enrichment e
        ON DATE_TRUNC('minute', b.ts_utc) = DATE_TRUNC('minute', e.ts_utc_econ)
        AND b.country = e.country_econ
),

-- Fallback: join texte normalisé pour ceux sans match temporel
matched_econ_text AS (
    SELECT
        m.*,
        COALESCE(
            m.debug_source_consensus_temp,
            CASE 
                WHEN e2.forecast_econ IS NOT NULL THEN 'economic_events_text'
                ELSE NULL
            END
        ) AS debug_source_consensus_text,
        COALESCE(m.forecast_econ, e2.forecast_econ) AS forecast_final,
        COALESCE(m.previous_econ, e2.previous_econ) AS previous_final
    FROM matched_econ m
    LEFT JOIN econ_enrichment e2
        ON m.normalized_title = e2.normalized_event_name
        AND m.country = e2.country_econ
        AND m.debug_source_consensus_temp IS NULL
),

-- Consensus final: priorité economic_events, puis fallback base
final_consensus AS (
    SELECT
        *,
        -- Consensus: priorité forecast_econ, puis estimate_base, puis forecast_base
        COALESCE(forecast_final, estimate_base, forecast_base) AS consensus,
        -- Previous: priorité previous_econ, puis previous_base
        COALESCE(previous_final, previous_base) AS previous,
        -- Source debug
        COALESCE(debug_source_consensus_text, 
                 CASE 
                     WHEN estimate_base IS NOT NULL THEN 'events_with_ts_local_v1_estimate'
                     WHEN forecast_base IS NOT NULL THEN 'events_with_ts_local_v1_forecast'
                     ELSE 'missing'
                 END
        ) AS debug_source_consensus,
        -- Flags
        (actual IS NOT NULL) AS has_actual,
        (COALESCE(forecast_final, estimate_base, forecast_base) IS NOT NULL) AS has_consensus
    FROM matched_econ_text
)

-- Colonnes finales
SELECT
    fc.ts_utc,
    fc.ts_local,
    fc.date_local,
    fc.country,
    fc.event_key,
    fc.event_title,
    fc.normalized_title,
    fc.actual,
    fc.consensus,
    fc.previous,
    fc.importance_n,
    fc.has_actual,
    fc.has_consensus,
    fc.debug_source_consensus,
    -- Join event_impacts_v2 pour impact_prior_pips
    ei.phase1_pips AS impact_prior_pips,
    -- Join event_families pour family
    ef.family,
    -- Unit (si disponible dans base, sinon NULL)
    NULL AS unit  -- TODO: ajouter unit si disponible
FROM final_consensus fc
LEFT JOIN event_impacts_v2 ei
    ON fc.ts_utc = ei.ts_utc
    AND fc.country = ei.country
    AND (fc.event_key = ei.event_key OR fc.event_title = ei.event_title)
LEFT JOIN event_families ef
    ON fc.event_key = ef.event_key
    AND fc.country = ef.country
ORDER BY fc.ts_local, fc.country, fc.event_key;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- PRIORITÉ CONSENSUS:
-- 1. economic_events.forecast (via join temporel minute)
-- 2. economic_events.forecast (via join texte normalisé)
-- 3. events_with_ts_local_v1.estimate
-- 4. events_with_ts_local_v1.forecast
-- 5. NULL (marqué 'missing' dans debug_source_consensus)
--
-- EVENT_KEY:
-- - Utilise event_key si présent
-- - Sinon: normalized_title + epoch + country (déterministe)
--
-- NORMALISATION TEXTE:
-- - Lowercase
-- - Suppression caractères non alphanumériques
-- - Espaces préservés pour matching flexible
--
-- ============================================================================

