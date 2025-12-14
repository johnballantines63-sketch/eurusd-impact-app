import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ... autres imports existants ...


# ============================================================
#  Direction empirique V2/V3 (alpha · surprise_z)
# ============================================================

def load_alpha_map(alpha_csv_path="alpha_weights.csv"):
    """
    Charge les poids alpha appris walk-forward.
    Format attendu: colonnes [feature, alpha] ou [col, weight].
    Retourne dict {feature_name: alpha}.
    """
    try:
        df = pd.read_csv(alpha_csv_path)
    except FileNotFoundError:
        return {}

    # Tolérance de schéma
    col_feature = None
    col_alpha = None
    for c in df.columns:
        cl = c.lower()
        if col_feature is None and cl in ("feature", "col", "event", "event_key", "name"):
            col_feature = c
        if col_alpha is None and cl in ("alpha", "weight", "coef", "coefficient"):
            col_alpha = c
    if col_feature is None or col_alpha is None:
        # fallback: 1ère colonne = feature, 2ème = alpha
        col_feature, col_alpha = df.columns[:2]

    return dict(zip(df[col_feature].astype(str), df[col_alpha].astype(float)))


def load_surprise_stats(events_csv_path="events.csv"):
    """
    Calcule (mu, sigma) des surprises (actual-estimate) par event_key.
    Utilisé pour standardiser en z-score.

    Si le fichier n'existe pas, on renvoie dict vide.
    """
    try:
        ev = pd.read_csv(events_csv_path)
    except FileNotFoundError:
        return {}

    # colonnes attendues
    if "event_key" not in ev.columns or "actual" not in ev.columns or "estimate" not in ev.columns:
        return {}

    ev["event_key"] = (
        ev["event_key"].astype(str).str.strip().str.lower()
        .str.replace(r"\s+", " ", regex=True).str.replace("-", " ")
    )
    ev["actual"] = pd.to_numeric(ev["actual"], errors="coerce")
    ev["estimate"] = pd.to_numeric(ev["estimate"], errors="coerce")

    ev = ev.dropna(subset=["actual", "estimate"])
    ev["surprise"] = ev["actual"] - ev["estimate"]

    stats = {}
    g = ev.groupby("event_key")["surprise"]
    mu = g.mean()
    sigma = g.std(ddof=0)
    for k in mu.index:
        s = float(sigma.loc[k])
        if s == 0 or np.isnan(s):
            continue
        stats[k] = (float(mu.loc[k]), s)
    return stats


def predict_direction_empirical(events_df, alpha_map, stats_map, theta=0.0):
    """
    Direction finale basée sur:
        S = sum(alpha_e * z_e)
    où z_e est surprise standardisée par event_key,
    et alpha_e est appris sur events V2: family_surp_pos/neg

    Retour: (direction, score_S, method)
        direction in {"UP","DOWN","UNKNOWN"}
    """
    S = 0.0
    used = 0

    for _, row in events_df.iterrows():
        actual = row.get("actual")
        estimate = row.get("estimate")
        family = str(row.get("family", "Other")).strip()
        event_key = str(row.get("event_key", "")).strip().lower()

        # pas d'actual -> pas de direction finale possible
        if pd.isna(actual):
            continue

        # estimate obligatoire en V2/V3 (sinon NO_SIGNAL)
        if pd.isna(estimate):
            continue

        actual = float(actual)
        estimate = float(estimate)
        surprise = actual - estimate

        mu_sigma = stats_map.get(event_key)
        if mu_sigma is None:
            continue
        mu, sigma = mu_sigma
        if sigma == 0:
            continue

        z = (surprise - mu) / sigma
        sign = "pos" if z > 0 else "neg"

        alpha_key = f"{family}_surp_{sign}"
        alpha = float(alpha_map.get(alpha_key, 0.0))

        S += alpha * z
        used += 1

    if used == 0:
        return "UNKNOWN", 0.0, "no_signal"

    if S > theta:
        return "UP", S, "alpha_surprise"
    elif S < -theta:
        return "DOWN", S, "alpha_surprise"
    else:
        return "UNKNOWN", S, "alpha_neutral"


def calculate_prediction_pipeline(event_time, cluster_events, use_linear_formula=True):
    """
    Pipeline principal de prédiction pour une date/cluster donnée.
    Retourne un dict avec impact, direction, latence, etc.
    """

    # 1) Calcul impact (amplitude) existant
    impact_results = calculate_cluster_impact(
        event_time=event_time,
        cluster_events=cluster_events,
        use_linear_formula=use_linear_formula
    )

    # ... extraction impact_pips/base_score/etc existante ...

    # 2) Détection de tendance conservée uniquement pour info de régime
    prices_before = load_prices_for_trend(event_time)
    trend_info = detect_trend_by_inversion_s107(prices_before, scenario="default")
    trend_relaxed = detect_trend_by_inversion_s107(prices_before, scenario="relaxed")
    trend_very_relaxed = detect_trend_by_inversion_s107(prices_before, scenario="very_relaxed")

    selected_trend = select_best_trend([trend_info, trend_relaxed, trend_very_relaxed])
    regime = selected_trend["trend_direction"] if selected_trend else "UNKNOWN"
    trend_r2 = selected_trend["r2"] if selected_trend and "r2" in selected_trend else None

    # 3) Direction finale empirique (si actuals présents)
    alpha_map = load_alpha_map("alpha_weights.csv")
    stats_map = load_surprise_stats("events.csv")

    direction_predicted, direction_score, direction_method = predict_direction_empirical(
        cluster_events, alpha_map, stats_map, theta=0.0
    )

    # 4) Pré-release fallback si aucun actual
    if direction_method == "no_signal":
        # on peut garder une direction pré-release faible, basée sur historique cluster
        # (si tu as une fonction existante)
        try:
            direction_predicted, direction_method = predict_pre_release_direction(cluster_events)
            direction_score = 0.0
        except NameError:
            direction_predicted = "UNKNOWN"
            direction_method = "pre_release_none"
            direction_score = 0.0

    results = {
        # impact existant
        **impact_results,

        "direction_predicted": direction_predicted,
        "direction_score": direction_score,
        "direction_method": direction_method,

        # info contexte (non décisionnelle)
        "regime_pre_event": regime,
        "trend_r2": trend_r2,
    }

    return results
