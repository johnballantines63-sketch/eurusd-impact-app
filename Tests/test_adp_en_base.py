import duckdb, pandas as pd
from fx_impact_app.src.config import get_db_path

# ajuste la date si besoin
jour = "2025-09-30"
start = pd.to_datetime(jour + " 00:00:00").tz_localize("UTC").tz_convert("UTC").tz_localize(None)
end   = (pd.to_datetime(jour) + pd.Timedelta(days=1)).tz_localize("UTC").tz_convert("UTC").tz_localize(None)

con = duckdb.connect(get_db_path())
df = con.execute("""
  SELECT CAST(ts_utc AS TIMESTAMP) AS ts_utc, country, event_title, event_key, label, type, estimate, forecast, previous
  FROM events
  WHERE ts_utc >= ? AND ts_utc < ?
    AND (
      lower(coalesce(event_title,'')) LIKE '%adp%'
      OR lower(coalesce(event_key,'')) LIKE '%adp%'
      OR lower(coalesce(label,''))     LIKE '%adp%'
      OR lower(coalesce(type,''))      LIKE '%adp%'
      OR lower(coalesce(type,''))      LIKE '%employment%'
    )
  ORDER BY ts_utc
""", [start.to_pydatetime(), end.to_pydatetime()]).df()
con.close()

print(df.to_string(index=False) if not df.empty else "❌ Aucune ligne ADP ce jour dans `events`")
PY
