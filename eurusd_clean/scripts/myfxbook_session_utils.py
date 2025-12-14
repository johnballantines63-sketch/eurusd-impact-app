#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfxbook_session_utils.py
-------------------------
Utilitaires de gestion de session Myfxbook :
- Validation d'un session id
- Login (email/password) pour récupérer un nouveau session id
- Persistance dans un fichier (par défaut data/myfxbook_session.txt)
- Fonction unique `get_or_refresh_session(...)` à importer depuis d'autres scripts.

Dépendances : requests
"""

from typing import Optional, Tuple
from pathlib import Path
import requests

DEFAULT_SESSION_FILENAME = "myfxbook_session.txt"

def _session_file_path(data_dir: str) -> Path:
    p = Path(data_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p / DEFAULT_SESSION_FILENAME

def myfxbook_login(email: str, password: str) -> Optional[str]:
    url = "https://www.myfxbook.com/api/login.json"
    try:
        r = requests.get(url, params={"email": email, "password": password}, timeout=20)
        js = r.json()
    except Exception:
        return None
    if js and (not js.get("error", True)) and js.get("session"):
        return js["session"]
    return None

def myfxbook_session_valid(session_id: str) -> bool:
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    try:
        r = requests.get(url, params={"session": session_id}, timeout=20)
        js = r.json()
        if js is None:
            return False
        if isinstance(js, dict) and js.get("error") is False:
            return True
    except Exception:
        return False
    return False

def read_session_from_file(data_dir: str) -> Optional[str]:
    fp = _session_file_path(data_dir)
    if not fp.exists():
        return None
    try:
        return fp.read_text(encoding="utf-8").strip()
    except Exception:
        return None

def write_session_to_file(session_id: str, data_dir: str) -> bool:
    fp = _session_file_path(data_dir)
    try:
        fp.write_text(session_id, encoding="utf-8")
        return True
    except Exception:
        return False

def get_or_refresh_session(
    data_dir: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    current_session: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Renvoie (session_id, status) où status ∈ {"from_arg_valid","from_file_valid","refreshed","login_failed","not_available"}
    Logique :
      1) Si current_session fourni et valide → return (current_session, "from_arg_valid")
      2) Sinon, lire fichier data/myfxbook_session.txt et valider → "from_file_valid"
      3) Sinon, si email/password fournis → login, sauver fichier → "refreshed"
      4) Sinon → "not_available"
    """
    # 1) Check current_session
    if current_session and myfxbook_session_valid(current_session):
        return current_session, "from_arg_valid"

    # 2) Check file
    file_session = read_session_from_file(data_dir)
    if file_session and myfxbook_session_valid(file_session):
        return file_session, "from_file_valid"

    # 3) Refresh via login
    if email and password:
        new_sess = myfxbook_login(email, password)
        if new_sess and myfxbook_session_valid(new_sess):
            write_session_to_file(new_sess, data_dir)
            return new_sess, "refreshed"
        return None, "login_failed"

    # 4) Not available
    return None, "not_available"
