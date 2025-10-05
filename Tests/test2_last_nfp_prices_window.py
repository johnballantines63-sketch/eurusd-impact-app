import duckdb, pandas as pd
from fx_impact_app.src.config import get_db_path

def main():
    con = duckdb.connect(get_db_path())

    # Vue prix normalisée + max couverture
    con.execute("""
      CREATE OR REPLACE VIEW prices_1m_v AS
      SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
      FROM prices_1m
      WHERE datetime IS NOT NULL
      ORDER BY datetime
    """)
    px_max = con.execute("SELECT max(ts_utc) FROM prices_1m_v").fetchone()[0]
    if px_max is None:
        print("Aucune donnée prix.")
        return
    px_max = pd.Timestamp(px_max)

    # Dernier NFP COUVERT par les prix (<= px_max)
    ev = con.execute("""
      SELECT CAST(ts_utc AS TIMESTAMP) AS ts
      FROM events
      WHERE country='US'
        AND regexp_matches(
              lower(coalesce(event_key,'') || ' ' || coalesce(event_title,'')),
              '(nonfarm|non-farm|nfp|payrolls|employment)'
            )
        AND CAST(ts_utc AS TIMESTAMP) <= ?
      ORDER BY ts_utc DESC
      LIMIT 1
    """, [px_max.to_pydatetime()]).df()

    if ev.empty:
        print("Aucun NFP trouvé avant", px_max)
        return

    ts = ev.loc[0, "ts"]
    print("Dernier NFP couvert par les prix:", ts)
    for v in ["prices_1m_v","prices_5m_v","prices_m15_v","prices_m30_v","prices_1h_v","prices_h4_v"]:
        try:
            n = con.execute(f"""
                SELECT count(*) FROM {v}
                WHERE ts_utc BETWEEN ? - INTERVAL 2 HOUR AND ? + INTERVAL 2 HOUR
            """, [ts, ts]).fetchone()[0]
            print(f"{v}: {n} bougies dans ±2h")
        except Exception as e:
            print(f"{v}: vue absente ({e})")
    con.close()

if __name__ == "__main__":
    main()
