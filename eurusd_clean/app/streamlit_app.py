#!/usr/bin/env python3
# app/streamlit_app.py

"""
UI Streamlit — EURUSD Trading Assistant (V3.2.1)
================================================

Principe "sécurité ++" :
- UI THIN : aucune logique de modèle ici (juste lecture DB + saisie actuals + rendu).
- Les invariants et validations doivent vivre côté scripts/contracts et moteur.
- L'UI ne fait que produire/afficher un "DayPayload" compatible avec DayPrediction.

Entrées attendues (DB DuckDB):
- data/warehouse.duckdb
- table: daily_risk_signal_v3_2_1 (date, pred_vol_pips, ... éventuellement direction/pattern/risk_score si dispo)
- view/table: events_with_ts_local_v1 (ts_local, country, event_name, previous, forecast, importance, ...)
- (optionnel) une table/vues des clusters/patterns si déjà existantes

Sorties garanties:
- Affichage calendar + day detail
- Formulaire actuals (core) + recalcul bouton (placeholder) + graphique pattern (placeholder)

Invariants UI:
- N'affiche "TRADE" que si au moins 1 core event est présent
- Core events affichés par défaut, non-core via checkbox
- Toutes les saisies actuals restent locales à la session (pas d'écriture DB dans V1 UI)
"""

import sys
from pathlib import Path

# Fix import path (avant tout import de app.*)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
from dataclasses import dataclass
from typing import Optional, List, Dict

import duckdb
import pandas as pd
import numpy as np
import streamlit as st

# Plotly (très lisible dans Streamlit)
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ----------------------------
# Config
# ----------------------------
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

RISK_MIN_DEFAULT = 0.60
IMPACT_MIN_PIPS_DEFAULT = 40

# "Core" = événements à renseigner impérativement (V1)
# => on prend une règle simple: importance >= 4 OU country == 'US' (à ajuster)
CORE_IMPORTANCE_MIN = 4


@dataclass
class DaySelection:
    date: str


def get_conn(db_path: str):
    return duckdb.connect(str(db_path), read_only=True)


def load_calendar(conn: duckdb.DuckDBPyConnection, mode: str = "latest", limit: int = 30) -> pd.DataFrame:
    """
    Charge une liste de dates.
    mode:
      - latest: dernières dates dispo
      - future: dates >= current_date si la table en contient (souvent non)
    """
    if mode == "future":
        q = f"""
        SELECT date, pred_vol_pips
        FROM daily_risk_signal_v3_2_1
        WHERE date >= CURRENT_DATE
        ORDER BY date ASC
        LIMIT {int(limit)}
        """
    else:
        q = f"""
        SELECT date, pred_vol_pips
        FROM daily_risk_signal_v3_2_1
        ORDER BY date DESC
        LIMIT {int(limit)}
        """
    df = conn.execute(q).df()
    if not df.empty:
        df["date"] = df["date"].astype(str)
    return df


def load_day_events(conn: duckdb.DuckDBPyConnection, date_str: str) -> pd.DataFrame:
    """
    Events de la journée (heure locale) avec actuals.
    """
    q = """
    SELECT
      ts_local,
      country,
      event_key,
      event_title,
      importance_n,
      previous,
      forecast,
      actual
    FROM events_with_ts_local_v1
    WHERE DATE(ts_local) = CAST(? AS DATE)
    ORDER BY ts_local ASC
    """
    df = conn.execute(q, [date_str]).df()
    if df.empty:
        return df
    df["ts_local"] = pd.to_datetime(df["ts_local"])
    return df


def load_actuals_from_db(conn: duckdb.DuckDBPyConnection, date_str: str) -> Dict[str, float]:
    """
    Charge les actuals depuis la DB pour une date donnée.
    Retourne un dict {event_uid: actual_value}
    """
    q = """
    SELECT
      ts_local,
      event_key,
      event_title,
      actual
    FROM events_with_ts_local_v1
    WHERE DATE(ts_local) = CAST(? AS DATE)
      AND actual IS NOT NULL
    ORDER BY ts_local ASC
    """
    df = conn.execute(q, [date_str]).df()
    
    actuals_dict = {}
    for idx, row in df.iterrows():
        ts_iso = pd.to_datetime(row["ts_local"]).isoformat()
        event_key = str(row.get("event_key") or row.get("event_title") or "UNKNOWN")
        actual_val = row["actual"]
        
        if pd.notna(actual_val):
            # Construire event_uid (sans row= pour chercher toutes les variantes possibles)
            # On cherchera dans le form avec row=idx
            actuals_dict[f"{event_key}|{ts_iso}|row={idx}"] = float(actual_val)
            # Fallback: aussi stocker sans row= pour compatibilité
            actuals_dict[f"{event_key}|{ts_iso}"] = float(actual_val)
    
    return actuals_dict


def mark_core_events(df_events: pd.DataFrame) -> pd.DataFrame:
    if df_events.empty:
        return df_events
    df = df_events.copy()
    df["is_core"] = (df["importance_n"].fillna(0) >= CORE_IMPORTANCE_MIN) | (df["country"] == "US")
    return df


def compute_placeholder_prediction(date_str: str, pred_vol_pips: float, df_events: pd.DataFrame, actuals: Dict[str, float]) -> dict:
    """
    Placeholder V1 : l'UI n'entraîne ni ne recalcule le modèle.
    Ici on simule une "direction/pattern/impact" pour rendre l'UI utilisable,
    en attendant de brancher le vrai moteur (script apply + logique cluster/pattern).
    """
    # Heuristique simple : plus la vol prédite est haute, plus "impact" est haut.
    impact = float(np.clip(pred_vol_pips, 20, 200))

    # Direction placeholder : si beaucoup d'events US, on met "BUY" sinon "SELL" (exemple)
    n_us = int((df_events["country"] == "US").sum()) if not df_events.empty else 0
    direction = "BUY" if n_us >= 3 else "SELL"

    # Pattern placeholder basé sur impact
    if impact < 60:
        pattern = "single_wave"
    elif impact < 110:
        pattern = "double_wave"
    else:
        pattern = "zigzag"

    # risk_score placeholder normalisé
    risk_score = float(np.clip((impact - 30) / 120, 0, 1))

    # Fenêtres par défaut (minutes autour du 1er core event)
    if not df_events.empty and (df_events["is_core"].any() if "is_core" in df_events.columns else False):
        t0 = df_events.loc[df_events["is_core"], "ts_local"].min()
    else:
        # fallback
        t0 = pd.Timestamp(date_str + " 13:30:00")

    entry = {"start": (t0 + pd.Timedelta(minutes=15)), "end": (t0 + pd.Timedelta(minutes=45))}
    if pattern == "single_wave":
        exit_w = {"start": (t0 + pd.Timedelta(minutes=60)), "end": (t0 + pd.Timedelta(minutes=180))}
    elif pattern == "double_wave":
        exit_w = {"start": (t0 + pd.Timedelta(minutes=90)), "end": (t0 + pd.Timedelta(minutes=240))}
    else:
        exit_w = {"start": (t0 + pd.Timedelta(minutes=120)), "end": (t0 + pd.Timedelta(minutes=300))}

    # Targets conservateurs
    pips_target = float(np.clip(0.55 * impact, 20, 80))
    stop_loss = float(np.clip(0.35 * impact, 15, 60))

    return {
        "date": date_str,
        "pred_vol_pips": float(pred_vol_pips),
        "direction": direction,
        "pattern": pattern,
        "impact_pred_pips": impact,
        "risk_score": risk_score,
        "entry_window": entry,
        "exit_window": exit_w,
        "pips_target": pips_target,
        "stop_loss_pips": stop_loss,
    }


def plot_prediction_timeline(pred: dict, df_events: pd.DataFrame) -> Optional[go.Figure]:
    """
    Graphique lisible:
    - points verticaux = events
    - zones = entry/exit windows
    - courbe "pattern attendu" (placeholder)
    """
    if not HAS_PLOTLY:
        return None
    
    fig = go.Figure()

    # base timeline
    t0 = pred["entry_window"]["start"]
    t_end = pred["exit_window"]["end"]
    t_range = pd.date_range(t0 - pd.Timedelta(minutes=30), t_end + pd.Timedelta(minutes=30), freq="5min")

    # Pattern attendu (placeholder) : une sinusoïde écrêtée selon le pattern
    amp = pred["impact_pred_pips"]
    x = t_range
    if pred["pattern"] == "single_wave":
        y = amp * np.sin(np.linspace(0, np.pi, len(x)))
    elif pred["pattern"] == "double_wave":
        y = amp * np.sin(np.linspace(0, 2*np.pi, len(x))) * 0.7
        y = np.maximum(y, 0)  # on affiche une forme "pics"
    else:  # zigzag
        y = amp * np.sin(np.linspace(0, 3*np.pi, len(x))) * 0.6

    if pred["direction"] == "SELL":
        y = -y

    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Pattern attendu (placeholder)"))

    # Events verticaux
    if not df_events.empty:
        for _, r in df_events.iterrows():
            fig.add_vline(
                x=r["ts_local"],
                line_width=1,
                line_dash="dot",
                opacity=0.5,
            )

    # Entry/Exit windows (shaded)
    fig.add_vrect(
        x0=pred["entry_window"]["start"],
        x1=pred["entry_window"]["end"],
        opacity=0.15,
        line_width=0,
        annotation_text="ENTRY",
        annotation_position="top left",
    )
    fig.add_vrect(
        x0=pred["exit_window"]["start"],
        x1=pred["exit_window"]["end"],
        opacity=0.12,
        line_width=0,
        annotation_text="EXIT",
        annotation_position="top left",
    )

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Heure locale",
        yaxis_title="Pips (pattern attendu)",
        legend_orientation="h",
    )
    return fig


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="EURUSD Trading Assistant — V3.2.1", layout="wide")

st.title("EURUSD Trading Assistant — V3.2.1 (sécurité ++)")

# Badge statut moteur sera mis à jour après sélection de la date

with st.sidebar:
    st.header("Configuration")
    db_path = st.text_input("DuckDB path", value=str(DEFAULT_DB_PATH))
    calendar_mode = st.selectbox("Calendar mode", ["latest", "future"], index=0)
    calendar_limit = st.slider("Nb dates", 10, 1500, 200, step=10)

    st.divider()
    st.header("Trading gates (V1)")
    risk_min = st.slider("RISK_MIN", 0.0, 1.0, float(RISK_MIN_DEFAULT), 0.05)
    impact_min = st.slider("IMPACT_MIN_PIPS", 0, 200, int(IMPACT_MIN_PIPS_DEFAULT), 5)

# connect
try:
    conn = get_conn(db_path)
except Exception as e:
    st.error(f"Impossible d'ouvrir DuckDB: {e}")
    st.stop()

# Calendar
df_cal = load_calendar(conn, mode=calendar_mode, limit=calendar_limit)
if df_cal.empty:
    st.warning("Aucune date dans daily_risk_signal_v3_2_1 (ou filtre future sans dates).")
    st.stop()

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Calendar")
    st.dataframe(df_cal, use_container_width=True, hide_index=True)

    mode_pick = st.radio("Mode sélection date", ["Liste", "Saisie"], horizontal=True)

    if mode_pick == "Liste":
        selected_date = st.selectbox("Choisir une date", df_cal["date"].tolist(), index=0)
    else:
        d = st.date_input("Entrer une date", value=pd.to_datetime(df_cal["date"].iloc[0]).date())
        selected_date = d.strftime("%Y-%m-%d")

    # Toujours charger pred_vol depuis DB pour la date choisie (liste OU saisie)
    df_one = conn.execute("""
        SELECT pred_vol_pips
        FROM daily_risk_signal_v3_2_1
        WHERE date = CAST(? AS DATE)
    """, [selected_date]).df()

    if df_one.empty:
        st.error(f"Aucune prédiction dans daily_risk_signal_v3_2_1 pour {selected_date}")
        st.stop()

    selected_pred_vol = float(df_one.iloc[0]["pred_vol_pips"])

with right:
    st.subheader(f"Day Detail — {selected_date}")
    
    # Badge statut moteur (dynamique selon checkbox de cette date)
    use_real_engine_key = f"use_real_{selected_date}"
    use_real_engine = st.session_state.get(use_real_engine_key, False)
    if use_real_engine:
        st.info("🟢 **Moteur réel V3.2.1 activé** — Calcul basé sur clusters + actuals")
    else:
        st.warning("🟡 **Placeholder actif** — Cocher 'Utiliser moteur réel' pour activer")

    # Load events
    df_events = load_day_events(conn, selected_date)
    df_events = mark_core_events(df_events)

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        show_non_core = st.checkbox("Afficher non-essentiels", value=False)
    with c2:
        st.metric("Pred vol (pips)", f"{selected_pred_vol:.1f}")
    with c3:
        st.write("")
    with c4:
        st.write("")

    if df_events.empty:
        st.info("Aucun event dans events_with_ts_local_v1 pour cette date.")
        df_show = df_events
    else:
        df_show = df_events.copy()
        if not show_non_core:
            df_show = df_show[df_show["is_core"]].copy()

    st.markdown("### Timeline des events (heure locale)")
    if df_show.empty:
        st.warning("Aucun event CORE à afficher (active 'Afficher non-essentiels' si besoin).")
    else:
        # Afficher les colonnes disponibles
        display_cols = ["ts_local", "country", "event_key", "importance_n", "previous", "forecast", "is_core"]
        available_cols = [c for c in display_cols if c in df_show.columns]
        st.dataframe(
            df_show[available_cols],
            use_container_width=True,
            hide_index=True,
        )

    # Actuals form (core first)
    st.markdown("### Actuals (core events)")
    actuals_key = f"actuals_{selected_date}"
    
    # Initialiser ou charger depuis DB si date passée
    if actuals_key not in st.session_state:
        st.session_state[actuals_key] = {}
    
    # Charger actuals depuis DB si date passée
    selected_date_obj = pd.to_datetime(selected_date).date()
    today = pd.Timestamp.now().date()
    
    if selected_date_obj < today:
        # Date passée : charger depuis DB
        db_actuals = load_actuals_from_db(conn, selected_date)
        # Fusionner avec session_state (DB prioritaire, mais session_state peut override)
        for uid, val in db_actuals.items():
            if uid not in st.session_state[actuals_key]:
                st.session_state[actuals_key][uid] = val
        if db_actuals:
            st.info(f"📥 {len(db_actuals)} actual(s) chargé(s) depuis la base de données (date passée)")

    core_df = df_events[df_events["is_core"]].copy() if not df_events.empty and "is_core" in df_events.columns else pd.DataFrame()
    if core_df.empty:
        st.info("Aucun core event détecté (importance>=4 ou US). Impossible de proposer BUY/SELL en sécurité ++.")
    else:
        # Build form avec event_uid stable et unique (ajout row=idx pour éviter collisions)
        for idx, r in core_df.iterrows():
            label = f"{r['ts_local'].strftime('%H:%M')} — {r['country']} — {r.get('event_key', r.get('event_title', 'Unknown'))}"
            cols = st.columns([2, 1, 1, 1])
            with cols[0]:
                st.write(label)
            with cols[1]:
                st.caption("Previous")
                st.write(r.get("previous", "N/A"))
            with cols[2]:
                st.caption("Forecast")
                st.write(r.get("forecast", "N/A"))
            with cols[3]:
                st.caption("Actual")
                # Construire event_uid unique (event_key|ts_local_iso|row=idx)
                ts_iso = pd.to_datetime(r["ts_local"]).isoformat()
                event_key = str(r.get("event_key") or r.get("event_title") or "UNKNOWN")
                event_uid = f"{event_key}|{ts_iso}|row={idx}"
                # Clé Streamlit unique (simplifiée)
                streamlit_key = f"actual_{selected_date}_{idx}"
                
                # Récupérer valeur : session_state > DB actual > empty
                default_val = st.session_state[actuals_key].get(event_uid)
                if default_val is None:
                    # Fallback: chercher aussi dans DB actual directement
                    db_actual_val = r.get("actual")
                    if pd.notna(db_actual_val):
                        default_val = float(db_actual_val)
                
                # Mode lecture seule si date passée ET actual en DB
                is_readonly = (selected_date_obj < today) and (r.get("actual") is not None and pd.notna(r.get("actual")))
                
                if is_readonly:
                    # Afficher en lecture seule
                    st.write(f"**{default_val if default_val is not None else 'N/A'}**")
                    # Stocker quand même dans session_state pour le moteur
                    if default_val is not None:
                        st.session_state[actuals_key][event_uid] = default_val
                else:
                    # Mode édition
                    val = st.text_input("", value="" if default_val is None else str(default_val), key=streamlit_key)
                    if val.strip() == "":
                        st.session_state[actuals_key].pop(event_uid, None)
                    else:
                        try:
                            st.session_state[actuals_key][event_uid] = float(val)
                        except ValueError:
                            st.warning("Actual doit être numérique (float).")

    st.divider()

    # Recompute (réel ou placeholder)
    st.markdown("### Calcul de prédiction")
    use_real_engine = st.checkbox(
        "🟢 Utiliser moteur réel V3.2.1", 
        value=st.session_state.get(f"use_real_{selected_date}", False), 
        key=f"use_real_{selected_date}",
        help="Active le moteur réel avec détection de clusters, calcul d'impact basé sur actuals, et validation Pydantic"
    )
    
    if st.button("Recalculer prédiction", type="primary"):
        if use_real_engine:
            try:
                from app.compute_real_prediction import compute_real_prediction
                
                # Appel du moteur réel avec actuals (format event_uid)
                # actuals = {"event_key|ts_local_iso": float_value, ...}
                pred = compute_real_prediction(
                    date_str=selected_date,
                    actuals=st.session_state[actuals_key],  # Dict avec clés event_uid
                    conn=conn,
                    model_path=None  # Utilise le modèle par défaut depuis daily_risk_signal_v3_2_1
                )
                st.session_state[f"pred_{selected_date}"] = pred
                st.success("✅ Prédiction calculée avec moteur réel V3.2.1")
                
                # Afficher info debug si impact=0
                if pred.get("impact_pred_pips", 0) == 0 and len(st.session_state[actuals_key]) > 0:
                    st.warning("⚠️ Impact=0 malgré actuals saisis. Vérifier que les actuals correspondent aux events core.")
                
            except Exception as e:
                st.error(f"❌ Erreur moteur réel: {e}")
                import traceback
                with st.expander("🔍 Détails de l'erreur"):
                    st.code(traceback.format_exc())
                st.info("Fallback vers placeholder")
                pred = compute_placeholder_prediction(
                    selected_date,
                    selected_pred_vol,
                    df_events,
                    st.session_state[actuals_key],
                )
                st.session_state[f"pred_{selected_date}"] = pred
        else:
            st.session_state[f"pred_{selected_date}"] = compute_placeholder_prediction(
                selected_date,
                selected_pred_vol,
                df_events,
                st.session_state[actuals_key],
            )

    # Charger prédiction (réelle si disponible, sinon placeholder)
    if use_real_engine and f"pred_{selected_date}" in st.session_state:
        pred = st.session_state[f"pred_{selected_date}"]
    else:
        pred = st.session_state.get(f"pred_{selected_date}", compute_placeholder_prediction(
            selected_date, selected_pred_vol, df_events, st.session_state[actuals_key]
        ))

    # Gates
    st.markdown("### Trading Plan")
    gates_ok = (
        pred["direction"] in ("BUY", "SELL")
        and pred["impact_pred_pips"] >= impact_min
        and pred["risk_score"] >= risk_min
        and (not df_events.empty and df_events["is_core"].any() if "is_core" in df_events.columns else False)
    )

    badge = "✅ TRADE OK" if gates_ok else "⛔ NO_TRADE"
    st.write(f"**{badge}**")
    
    # Raison NO_TRADE
    if not gates_ok:
        reasons = []
        if pred["direction"] not in ("BUY", "SELL"):
            reasons.append(f"Direction: {pred['direction']}")
        if pred["impact_pred_pips"] < impact_min:
            reasons.append(f"Impact ({pred['impact_pred_pips']:.1f}) < {impact_min}")
        if pred["risk_score"] < risk_min:
            reasons.append(f"Risk score ({pred['risk_score']:.2f}) < {risk_min}")
        if df_events.empty or not df_events["is_core"].any():
            reasons.append("Aucun core event")
        st.caption(f"Raison: {', '.join(reasons) if reasons else 'Gates non respectés'}")
    
    # Journal de trading (optionnel)
    with st.expander("📝 Journal de Trading"):
        try:
            from app.trading_journal import TradingJournal
            journal = TradingJournal()
            
            if st.button("Enregistrer cette décision", key=f"journal_{selected_date}"):
                reason_no_trade = None if gates_ok else ", ".join(reasons) if 'reasons' in locals() else "Gates non respectés"
                entry = journal.add_decision(
                    date_str=selected_date,
                    direction=pred["direction"],
                    pattern=pred["pattern"],
                    impact_pred_pips=pred["impact_pred_pips"],
                    risk_score=pred["risk_score"],
                    gates_ok=gates_ok,
                    reason_no_trade=reason_no_trade,
                    actuals=st.session_state.get(actuals_key, {}),
                )
                st.success(f"✅ Décision enregistrée: {entry['decision']}")
            
            # Stats
            stats = journal.get_stats()
            st.markdown("**Statistiques:**")
            st.json(stats)
            
        except ImportError:
            st.info("Journal de trading non disponible (module non importé)")

    cols = st.columns(6)
    cols[0].metric("Direction", pred["direction"])
    cols[1].metric("Pattern", pred["pattern"])
    cols[2].metric("Impact (pips)", f"{pred['impact_pred_pips']:.1f}")
    cols[3].metric("Risk score", f"{pred['risk_score']:.2f}")
    cols[4].metric("Target (pips)", f"{pred['pips_target']:.1f}")
    cols[5].metric("Stop (pips)", f"{pred['stop_loss_pips']:.1f}")

    st.write(
        f"- **Entry window:** {pred['entry_window']['start']} → {pred['entry_window']['end']}\n"
        f"- **Exit window:** {pred['exit_window']['start']} → {pred['exit_window']['end']}\n"
        f"- **Mode:** HYBRID (pips_target OU fenêtre de sortie)"
    )

    st.markdown("### Graphique (pattern attendu + fenêtres)")
    st.info("⚠️ **Note importante :** Ce graphique n'est pas une prévision de prix, c'est une représentation du scénario attendu (pattern + fenêtres entry/exit).")
    if HAS_PLOTLY:
        fig = plot_prediction_timeline(pred, df_events)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Plotly non disponible. Installer avec: pip install plotly")

st.caption("Note: V1 UI utilise un placeholder pour pattern/direction. À brancher ensuite au moteur réel (contracts + cluster/pattern + recalcul).")

