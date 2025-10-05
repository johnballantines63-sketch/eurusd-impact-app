# fx_impact_app/scripts/archive_pages.py
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1] / "streamlit_app" / "pages"
ARCH = ROOT / "_archive"
ARCH.mkdir(exist_ok=True)

to_archive = [
    "1_ingestion.py",
    "2_discovery.py",
    "3_scanner_q1.py",
    "4_linked_news_q2.py",
    "5_planner.py",
    "6_Top_events.py",
    "7_Simultaneous_events.py",
    "8_Forecaster_MVP_OLD.py",
    "8a_Forecaster_Presets.py",
    "9_Backtest.py",
    "10_Calendar_Sim_Backtest.py",
    "98_Glossary.py.bak",
]

for name in to_archive:
    src = ROOT / name
    if src.exists():
        dst = ARCH / name
        print(f"→ Archive: {src.name}")
        shutil.move(src.as_posix(), dst.as_posix())
    else:
        print(f"(déjà manquant) {name}")

print("\n✅ Terminé. Redémarre Streamlit pour voir le nouveau menu.")
