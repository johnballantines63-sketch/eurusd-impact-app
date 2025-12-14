#!/usr/bin/env python3
import requests
import json
from pathlib import Path

def get_session(email: str, password: str):
    """Appelle l'API login Myfxbook et retourne la réponse JSON."""
    url = f"https://www.myfxbook.com/api/login.json?email={email}&password={password}"
    resp = requests.get(url)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError("Réponse Myfxbook non valide.")

    if data.get("error"):
        raise RuntimeError(f"Erreur Myfxbook: {data.get('message')}")

    session = data.get("session")
    if not session:
        raise RuntimeError("Aucun session_id reçu.")

    return session

def save_session(session_id: str, path="myfxbook_session.json"):
    """Enregistre le session_id dans un fichier JSON."""
    obj = {"session": session_id}
    Path(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"✅ Session sauvegardée dans {path}")

def main():
    print("=== Myfxbook Session Retriever ===")
    email = input("Email Myfxbook : ").strip()
    password = input("Password Myfxbook : ").strip()

    try:
        session_id = get_session(email, password)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    print("\n=== SESSION ID RÉCUPÉRÉ ===")
    print(session_id)

    save = input("\nVoulez-vous enregistrer ce session_id ? (y/n) : ").lower()
    if save == "y":
        save_session(session_id)

if __name__ == "__main__":
    main()
