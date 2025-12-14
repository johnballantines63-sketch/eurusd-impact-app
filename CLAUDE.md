# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EUR/USD News Impact Calculator - A Streamlit application that analyzes the impact of macroeconomic news events on the EUR/USD forex pair. The system calculates tradability scores, latency metrics, and provides event classification across 26+ event families.

**Version**: 3.1
**Language**: Python 3.13
**Database**: DuckDB (89MB, 31,988+ events, 1.1M+ price records)

## Running the Application

```bash
# Start Streamlit app (from project root)
streamlit run fx_impact_app/streamlit_app/Home.py

# Alternative: Run from streamlit_app directory
cd fx_impact_app/streamlit_app
streamlit run Home.py
```

## Development Setup

```bash
# Install dependencies
pip install -r Divers/requirements.txt

# Required packages
streamlit==1.50.0
duckdb==1.4.0
pandas==2.3.3
numpy==2.3.3
requests==2.32.5
python-dotenv==1.1.1
gdown==5.1.0
plotly>=5.18.0
```

## Environment Variables

Configure in `.env` file at project root or Streamlit Cloud secrets:

```env
EODHD_API_KEY=your_eodhd_api_key
TE_API_KEY=your_trading_economics_api_key
GDRIVE_DB_FILE_ID=1Kr4t_X-D12rex48s-FfdxR4UhxR7h-g-  # For Google Drive DB download
```

## Architecture

### Core Data Flow

```
EODHD API → events table → event classification (26 families)
                    ↓
            prices_1m table (1-minute EUR/USD prices)
                    ↓
        Latency Analysis + MFE Calculation
                    ↓
            event_families table (precomputed stats)
                    ↓
            Scoring Engine → Tradability Score (0-100)
```

### Key Directories

```
fx_impact_app/
├── src/                          # Core Python modules
│   ├── config.py                 # Env vars, DB path, API keys
│   ├── event_families.py         # 26 event families with regex patterns
│   ├── forecaster_mvp.py         # ForecastEngine - calculates MFE, latency, TTR
│   ├── scoring_engine.py         # ScoringEngine - composite score 0-100
│   ├── latency_analyzer.py       # Market reaction latency analysis
│   ├── eodhd_client.py           # EODHD API client for calendar events
│   ├── te_client.py              # Trading Economics API client
│   └── download_database.py      # Google Drive DB download logic
├── streamlit_app/
│   ├── Home.py                   # Entry point dashboard
│   └── pages/
│       ├── 1_Calendrier-Trading.py          # Future events with scores
│       ├── 2_Backtest-Strategie.py          # Historical strategy backtest
│       ├── 3_Analyseur-Surprise.py          # Impact prediction from actual vs forecast
│       ├── 4_Planificateur-Multi-Evenements.py  # Multi-event timeline planner
│       ├── 5_Analyse-Latence.py             # Latency analysis page
│       └── 99_API_Status.py                 # API health check
├── data/
│   └── warehouse.duckdb          # Main database (89MB)
└── scripts/                      # Maintenance scripts
    ├── ingest_eodhd_calendar.py
    ├── ingest_prices_eodhd.py
    └── check_price_coverage.py
```

### Database Schema

**Primary Tables:**
- `events` - Economic calendar events (31,988+ rows)
  - Key columns: `ts_utc`, `event_key`, `country`, `importance_n`, `actual`, `forecast`, `previous`
- `prices_1m` - 1-minute EUR/USD prices (1.1M+ rows)
  - Key columns: `datetime`, `open`, `high`, `low`, `close`
- `event_families` - Precomputed statistics per event family
  - Key columns: `event_key`, `country`, `family`, `empirical_score`, `latency_median`, `ttr_median`, `mfe_p80`, `n_events_latency`
- `prices_5m`, `prices_15m`, `prices_30m`, `prices_1h`, `prices_4h` - Aggregated timeframes

**Note**: Database is downloaded from Google Drive on first run if `GDRIVE_DB_FILE_ID` is set.

## Core Concepts

### Event Families

26 event families defined in `event_families.py`:
- **High Impact**: NFP, CPI, FOMC, ECB, GDP (importance=3)
- **Medium Impact**: Jobless Claims, PPI, PMI, Retail Sales (importance=2)
- **Low Impact**: Housing data, Durable Goods, Factory Orders (importance=1)

Each family has:
- Regex pattern for classification (`FAMILY_PATTERNS`)
- Default importance (1-3) (`FAMILY_IMPORTANCE`)
- Calibrated sensitivity in pips (`FAMILY_SENSITIVITIES`)

### Metrics Calculation

**MFE (Maximum Favorable Excursion)**: Peak price movement within horizon (default 30min)

**Latency**: Time to initial reaction (>5 pips threshold)

**TTR (Time To Return)**: Time for price to return near baseline after peak

**Composite Score (0-100)**: Weighted average of:
- Impact (40%): Based on MFE P80
- Persistence (30%): Average of latency + TTR scores
- Reliability (20%): Based on sample size (n_events)
- Importance (10%): Event family importance (1-3)

### Precomputed Statistics

The `event_families` table contains precomputed stats stored in `warehouse.duckdb` for instant lookups:
- Avoids real-time calculation on every page load
- TTL cache: 3600s (1 hour)
- Stats calculated via `ForecastEngine.calculate_family_stats()`

### Scoring System Grades

- **A+** (85-100): Elite tradability
- **A** (75-84): Excellent
- **B+** (65-74): Very good
- **B** (55-64): Good
- **C+** (45-54): Acceptable
- **C** (35-44): Fair
- **D** (25-34): Poor
- **F** (<25): Not tradable

## Common Operations

### Query Future Events

```python
from config import get_db_path
import duckdb

conn = duckdb.connect(get_db_path())
events = conn.execute("""
    SELECT ts_utc, event_key, country, importance_n
    FROM events
    WHERE ts_utc > CURRENT_TIMESTAMP
      AND country IN ('US', 'EU', 'GB')
    ORDER BY ts_utc
""").fetchdf()
```

### Calculate Event Impact

```python
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine

engine = ForecastEngine(get_db_path())
scorer = ScoringEngine()

# Calculate stats for NFP events (last 3 years)
stats = engine.calculate_family_stats(
    family_pattern='(?i)(non farm payrolls|nonfarm)',
    horizon_minutes=30,
    hist_years=3,
    countries=['US']
)

# Get tradability score
score = scorer.calculate_score(stats, importance=3)
print(f"Score: {score['score']}/100 (Grade: {score['grade']})")
```

### Classify Event Family

```python
from event_families import FAMILY_PATTERNS
import re

def classify_event(event_key: str) -> str:
    for family, pattern in FAMILY_PATTERNS.items():
        if re.search(pattern, event_key, re.IGNORECASE):
            return family
    return 'Other'

family = classify_event("US Nonfarm Payrolls")  # Returns 'NFP'
```

## Testing & Scripts

```bash
# Check database integrity
python3 fx_impact_app/scripts/check_price_coverage.py

# Fetch latest calendar events (requires EODHD_API_KEY)
python3 fx_impact_app/scripts/ingest_eodhd_calendar.py

# Update EUR/USD prices from EODHD
python3 fx_impact_app/scripts/ingest_prices_eodhd.py

# Analyze simultaneous events
python3 fx_impact_app/scripts/analyze_simultaneous_events.py
```

## Diagnostic & Correction Scripts

Located in `eurusd_correction_scripts/` (external to project):

1. **01_diagnostic_complet.py** - Full diagnostic (no changes)
2. **02_correction_automatique.py** - Auto-fix with backups
3. **03_validation_corrections.py** - Validate fixes
4. **04_rollback_backup.py** - Restore from backup

These scripts handle common issues like incorrect impact formulas, missing scores, etc.

## Page-Specific Notes

### 1_Calendrier-Trading.py
- Shows future events sorted by tradability score
- Uses cached precomputed stats from `event_families` table
- Real-time filtering by country, importance, date range

### 4_Planificateur-Multi-Evenements.py
- Multi-event timeline visualization using `unified_chart.py`
- Handles overlapping events with vectorial price curve synthesis
- Complex state management - see backup versions in `pages/Backups/` if issues occur
- **STABLE VERSION**: `4_Planificateur_STABLE_0159_PERFECT.py` (known working version)

### 3_Analyseur-Surprise.py
- Predicts impact from actual vs forecast deviation
- Formula: `impact = (mfe_p80 / 100) * abs(surprise)`
- Surprise = (actual - forecast) standardized by family

## Known Issues & Solutions

### Missing Scores Display
- **Symptom**: Scores show 0.0 or NULL
- **Cause**: Missing precomputed stats in `event_families` table
- **Fix**: Run `calculate_missing_empirical_scores.py` or recalculate via ForecastEngine

### Database Corruption
- **Symptom**: DuckDB errors, missing columns
- **Fix**: Re-download from Google Drive or restore from backup in `fx_impact_app/src/backups/`

### Streamlit Rerun Loops
- **Symptom**: Infinite reloading on 4_Planificateur
- **Cause**: State management issues with checkboxes/multiselect
- **Fix**: Use unique widget keys with event IDs, avoid st.rerun() after widget interactions

### Latency Columns Missing
- **Symptom**: `Column 'latency_median' not found`
- **Fix**: Database migration already handled in code with graceful fallbacks

## Git Workflow

```bash
# Update calendar (automated via cron/GitHub Actions)
bash fx_impact_app/update_calendar.sh

# Current branch
git branch  # main

# Recent changes are often in many diagnostic/fix scripts in root
# Core app logic is stable in fx_impact_app/
```

## Deployment

**Streamlit Cloud**: Configured with Google Drive database download
- Database auto-downloads on first run via `download_database.py`
- Secrets: `EODHD_API_KEY`, `TE_API_KEY`, `GDRIVE_DB_FILE_ID`
- Memory: Requires ~500MB+ for DuckDB operations

## Critical Files - Backup Before Editing

- `fx_impact_app/src/event_families.py` - Family definitions (has backups/ dir)
- `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py` - Complex state logic
- `fx_impact_app/data/warehouse.duckdb` - Database (redownloadable from Google Drive)

**Backup pattern**: Files create timestamped backups before major changes (e.g., `*_backup_YYYYMMDD_HHMMSS.py`)

## Performance Considerations

- **Cache aggressively**: Use `@st.cache_data(ttl=3600)` for DB queries
- **Precompute stats**: Store in `event_families` table, don't recalculate on every page load
- **DuckDB read-only**: Use `read_only=True` when possible to avoid locks
- **Limit query horizons**: Default 3 years history, 30min forward window

## Regex Pattern Syntax

Event classification uses Python regex with DuckDB's `~` operator:
- DuckDB uses POSIX regex, not PCRE
- Use `event_key ~ 'pattern'` not `REGEXP(event_key, 'pattern')`
- Case-insensitive: Include `(?i)` prefix in patterns

Example:
```sql
WHERE event_key ~ '(?i)(non farm payrolls|nonfarm)'
```
