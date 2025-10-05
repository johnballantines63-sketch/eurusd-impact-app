# fx_impact_app/streamlit_app/pages/0_Live_Calendar_Forecast.py
from __future__ import annotations
import pandas as pd
import streamlit as st
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
import duckdb

# --- imports modèle
from fx_impact_app.src.forecaster_mvp import (
    ForecastRequest, forecast, HORIZONS, compute_surprise
)
from fx_impact_app.src.config import get_db_path

st.set_page_config(page_title="Live Calendar Forecast (jour)", layout="wide")
st.title("🟢 Live Calendar Forecast — jour")
st.caption(f"Loaded from: {__file__}")

# ---------- helpers ----------
FAM_RX = {
    "NFP":  r"(?i)(nonfarm|non-farm|nfp|payrolls|employment)",
    "CPI":  r"(?i)\\bcpi\\b|consumer price",
    "FOMC": r"(?i)(fomc|fed funds|federal funds|target rate|rate decision|interest rate|policy statement|press conference|dot plot|economic projections|summary of economic projections|sep|minutes)",
}

def guess_family(event_key: str|None, event_title: str|None) -> str|None:
    s = f"{event_key or ''} {event_title or ''}".lower()
    if any(k in s for k in ["nonfarm","non-farm","nfp","payroll","employment"]):
        return "NFP"
    if "cpi" in s or "consumer price" in s:
        return "CPI"
    if any(k in s for k in ["fomc","rate decision","interest rate","fed funds","federal funds","policy statement","press conference","minutes"]):
        return "FOMC"
    return None

def utc_day_bounds(d: date):
    s = pd.Timestamp(datetime.combine(d, time(0,0)), tz="UTC").tz_convert("UTC").tz_localize(None)
    e = pd.Timestamp(datetime.combine(d, time(23,59,59)), tz="UTC").tz_convert("UTC").tz_localize(None)
    return s, e

def localize(ts_utc: pd.Timestamp, tz: str) -> str:
    if ts_utc is None or pd.isna(ts_utc): return ""
    return pd.Timestamp(ts_utc).tz_localize("UTC").tz_convert(ZoneInfo(tz)).strftime("%Y-%m-%d %H:%M:%S %Z")

# ---------- UI haut ----------
c0, c1, c2, c3 = st.columns([1.5, 1.2, 1.2, 2])
with c0:
    tz_name = st.selectbox("Fuseau", ["Europe/Zurich","UTC","Europe/Paris","America/New_York","Europe/London"], index=0)
with c1:
    jour = st.date_input("Jour (UTC)", value=date.today())
with c2:
    before = st.slider("Fenêtre before (min)", 0, 180, 60, 5)
with c3:
    after = st.slider("Fenêtre after (min)", 0, 180, 15, 5)

st.markdown("---")

# ---------- Charger events du jour ----------
db = get_db_path()
start_utc, end_utc = utc_day_bounds(jour)

try:
    with duckdb.connect(db) as con:
        # petite tune safe
        try:
            con.execute("PRAGMA threads=2")
        except Exception:
            pass
        try:
            tmp = pd.Series([db]).astype("string")[0]  # no-op pour garder un objet
            # on laisse db_tuning faire le reste si appelé
        except Exception:
            pass

        cols = {r[1].lower() for r in con.execute("PRAGMA table_info('events')").fetchall()}
        if "ts_utc" not in cols:
            st.error("Table `events` absente ou sans `ts_utc`."); st.stop()

        base_sel = ["CAST(ts_utc AS TIMESTAMP) AS ts_utc"]
        for c in ["country","event_title","event_key","previous","estimate","forecast","unit","actual"]:
            if c in cols:
                base_sel.append(c)
        q = f"""
          SELECT {", ".join(base_sel)}
          FROM events
          WHERE ts_utc BETWEEN ? AND ?
          ORDER BY ts_utc
        """
        df = con.execute(q, [start_utc, end_utc]).df()

except Exception as e:
    st.error("Erreur lecture des événements.")
    st.exception(e)
    st.stop()

if df.empty:
    st.info("Aucun événement ce jour (dans `events`).")
    st.stop()

# enrichir pour édition
df["ts_local"] = df["ts_utc"].apply(lambda t: localize(t, tz_name))
if "estimate" in df and "forecast" in df:
    df["consensus"] = df[["estimate","forecast"]].mean(axis=1, skipna=True)
elif "estimate" in df:
    df["consensus"] = df["estimate"]
elif "forecast" in df:
    df["consensus"] = df["forecast"]
else:
    df["consensus"] = pd.NA

df["family"] = [guess_family(r.get("event_key"), r.get("event_title")) for r in df.to_dict("records")]
df["Actual (live)"] = df["actual"] if "actual" in df else pd.NA
df["✔︎"] = False

view_cols = ["✔︎","ts_local","country","event_title","event_key","previous","consensus","Actual (live)","family","unit"]
view_cols = [c for c in view_cols if c in df.columns]
st.subheader("Événements du jour")
edited = st.data_editor(
    df[view_cols],
    use_container_width=True,
    num_rows="fixed",
    key="live_editor",
    column_config={
        "✔︎": st.column_config.CheckboxColumn("Inclure", default=False),
        "consensus": st.column_config.NumberColumn("Consensus", step=0.1, format="%.2f"),
        "Actual (live)": st.column_config.NumberColumn("Actual (live)", step=0.1, format="%.2f"),
        "family": st.column_config.SelectboxColumn("Famille", options=["NFP","CPI","FOMC",None], required=False),
    },
    hide_index=True,
)

st.caption(f"Total lignes: {len(edited)} — cochées: {(edited['✔︎'] == True).sum()}")

st.markdown("---")
cA, cB = st.columns([1,2])
with cA:
    horizons = st.multiselect("Horizons (min)", HORIZONS, default=[15,30,60])
with cB:
    st.write("")

if st.button("Calculer les forecasts des lignes cochées", type="primary"):
    try:
        rows = []
        for i, r in edited[edited["✔︎"] == True].reset_index(drop=True).iterrows():
            fam = r.get("family") or guess_family(r.get("event_key"), r.get("event_title"))
            if not fam:
                continue
            cons = r.get("consensus")
            act  = r.get("Actual (live)")
            if pd.isna(cons) or pd.isna(act):
                continue

            req = ForecastRequest(
                event_family=fam,
                actual=float(act),
                consensus=float(cons),
                country=str(r.get("country") or "US"),
                window_before_min=int(before),
                window_after_min=int(after),
                horizons=[int(h) for h in horizons] or [15,30,60],
            )

            stats, diags = forecast(req)  # on laisse le modèle choisir regex par famille
            for s in stats:
                rows.append({
                    "ts_local": r.get("ts_local"),
                    "country": r.get("country"),
                    "event_title": r.get("event_title"),
                    "family": fam,
                    "horizon_min": s.horizon,
                    "n": s.n,
                    "p_up": s.p_up,
                    "mfe_med": s.mfe_med,
                    "mfe_p80": s.mfe_p80,
                    "surprise_%": compute_surprise(float(act), float(cons)),
                })

        if not rows:
            st.warning("Aucune ligne exploitable : coche au moins une ligne et renseigne Actual & Consensus.")
        else:
            out = pd.DataFrame(rows)
            st.subheader("Résultats")
            st.dataframe(out, use_container_width=True, hide_index=True)

            with st.expander("Export & diagnostics"):
                st.download_button(
                    "Exporter CSV",
                    data=out.to_csv(index=False).encode("utf-8"),
                    file_name=f"live_forecasts_{jour}.csv",
                    mime="text/csv",
                )
                st.json({"db_path": db, "jour_utc": [str(start_utc), str(end_utc)], "horizons": horizons})

    except Exception as e:
        st.error("Erreur pendant le calcul.")
        st.exception(e)
