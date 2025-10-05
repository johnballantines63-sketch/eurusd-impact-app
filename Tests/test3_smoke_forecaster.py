import pandas as pd
from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast

def main():
    # 3 ans raisonnables; clamp automatique à la couverture des prix à l'intérieur du moteur
    hist_from = (pd.Timestamp.now(tz="UTC") - pd.DateOffset(years=3)).tz_convert("UTC").tz_localize(None)
    hist_to   =  pd.Timestamp.now(tz="UTC").tz_convert("UTC").tz_localize(None)

    req = ForecastRequest(
        event_family="NFP",
        actual=0.0, consensus=0.0,
        country="US",
        window_before_min=60, window_after_min=15,
        horizons=[15,30,60],
        strict_decision=False,
    )

    stats, diags = forecast(req, time_from=hist_from, time_to=hist_to)
    print("Diagnostics:", diags)
    for s in stats:
        print({"horizon": s.horizon, "n": s.n, "p_up": s.p_up, "mfe_med": s.mfe_med, "mfe_p80": s.mfe_p80})

if __name__ == "__main__":
    main()
