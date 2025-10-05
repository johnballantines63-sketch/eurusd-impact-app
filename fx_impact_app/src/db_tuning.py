# fx_impact_app/src/db_tuning.py
from __future__ import annotations
from pathlib import Path
from typing import Dict

def _try_pragma(con, stmt: str) -> str:
    try:
        return str(con.execute(stmt).fetchone()[0])
    except Exception:
        return "N/A"

def show_settings(con) -> Dict[str, str]:
    return {
        "threads": _try_pragma(con, "PRAGMA threads"),
        "memory_limit": _try_pragma(con, "PRAGMA memory_limit"),
        "temp_directory": _try_pragma(con, "PRAGMA temp_directory"),
        "max_temp_directory_size": _try_pragma(con, "PRAGMA max_temp_directory_size"),
        "preserve_insertion_order": _try_pragma(con, "PRAGMA preserve_insertion_order"),
    }

def tune(con, mem_gb: int = 2, threads: int = 2, max_temp_gb: int = 40, temp_dir: str | None = None) -> None:
    # Réduit le risque OOM
    try:
        con.execute(f"PRAGMA threads={int(threads)}")
    except Exception:
        pass
    try:
        # Sur DuckDB 1.4, la lecture mémoire peut renvoyer N/A mais le set reste accepté
        con.execute(f"PRAGMA memory_limit='{int(mem_gb)}GB'")
    except Exception:
        pass

    if temp_dir:
        tdir = Path(temp_dir)
    else:
        # temp à côté de la DB si possible
        dbpath = None
        try:
            dbpath = con.execute("PRAGMA database_list").df().iloc[0]["file"]
        except Exception:
            pass
        if dbpath:
            tdir = Path(dbpath).with_suffix(".duckdb.tmp")
        else:
            tdir = Path.cwd() / "duckdb.tmp"

    tdir.mkdir(parents=True, exist_ok=True)
    try:
        con.execute(f"PRAGMA temp_directory='{tdir.as_posix()}'")
    except Exception:
        pass
    try:
        con.execute(f"PRAGMA max_temp_directory_size='{int(max_temp_gb)}GiB'")
    except Exception:
        pass
