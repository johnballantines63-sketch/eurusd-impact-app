#!/usr/bin/env python3
"""
Trading Journal (V3.2.1)
========================

Journal minimal pour tracker les décisions de trading.

Fonctionnalités :
- Enregistrer une décision (TRADE / NO_TRADE)
- Enregistrer résultat (si trade exécuté)
- Consulter historique
- Statistiques simples

Format : JSON simple (pas de DB pour V1)
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import date, datetime
import json

PROJECT_ROOT = Path(__file__).parent.parent
JOURNAL_PATH = PROJECT_ROOT / "data" / "trading_journal_v3_2_1.json"


class TradingJournal:
    """Journal de trading minimal."""
    
    def __init__(self, journal_path: Optional[Path] = None):
        self.journal_path = journal_path or JOURNAL_PATH
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _load(self) -> List[Dict]:
        """Charge le journal depuis JSON."""
        if self.journal_path.exists():
            with open(self.journal_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def _save(self, entries: List[Dict]):
        """Sauvegarde le journal en JSON."""
        with open(self.journal_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False, default=str)
    
    def add_decision(
        self,
        date_str: str,
        direction: str,
        pattern: str,
        impact_pred_pips: float,
        risk_score: float,
        gates_ok: bool,
        reason_no_trade: Optional[str] = None,
        actuals: Optional[Dict] = None,
    ) -> Dict:
        """
        Enregistre une décision (TRADE ou NO_TRADE).
        
        Returns:
            Dict de l'entrée créée
        """
        entry = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "pattern": pattern,
            "impact_pred_pips": impact_pred_pips,
            "risk_score": risk_score,
            "gates_ok": gates_ok,
            "decision": "TRADE" if gates_ok else "NO_TRADE",
            "reason_no_trade": reason_no_trade,
            "actuals": actuals or {},
            "result": None,  # Rempli plus tard si trade exécuté
        }
        
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        
        return entry
    
    def update_result(
        self,
        date_str: str,
        entry_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        pips_result: Optional[float] = None,
        exit_reason: Optional[str] = None,  # "take_profit", "stop_loss", "time_window", "kill_switch"
        notes: Optional[str] = None,
    ):
        """
        Met à jour le résultat d'un trade.
        
        Args:
            date_str: Date du trade
            entry_price: Prix d'entrée
            exit_price: Prix de sortie
            pips_result: Résultat en pips
            exit_reason: Raison de sortie
            notes: Notes additionnelles
        """
        entries = self._load()
        
        # Trouver la dernière entrée pour cette date avec decision=TRADE
        for entry in reversed(entries):
            if entry["date"] == date_str and entry["decision"] == "TRADE":
                entry["result"] = {
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pips_result": pips_result,
                    "exit_reason": exit_reason,
                    "notes": notes,
                    "updated_at": datetime.now().isoformat(),
                }
                self._save(entries)
                return entry
        
        raise ValueError(f"Aucun trade trouvé pour {date_str}")
    
    def get_entries(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        decision: Optional[str] = None,  # "TRADE" ou "NO_TRADE"
    ) -> List[Dict]:
        """Récupère les entrées avec filtres."""
        entries = self._load()
        
        filtered = entries
        
        if date_from:
            filtered = [e for e in filtered if e["date"] >= date_from]
        
        if date_to:
            filtered = [e for e in filtered if e["date"] <= date_to]
        
        if decision:
            filtered = [e for e in filtered if e["decision"] == decision]
        
        return filtered
    
    def get_stats(self) -> Dict:
        """Calcule statistiques simples."""
        entries = self._load()
        trades = [e for e in entries if e["decision"] == "TRADE" and e.get("result")]
        
        if not trades:
            return {
                "n_decisions": len(entries),
                "n_trades": 0,
                "n_no_trades": len([e for e in entries if e["decision"] == "NO_TRADE"]),
                "n_completed": 0,
                "win_rate": None,
                "avg_pips": None,
                "total_pips": None,
            }
        
        completed = [t for t in trades if t.get("result", {}).get("pips_result") is not None]
        wins = [t for t in completed if t["result"]["pips_result"] > 0]
        losses = [t for t in completed if t["result"]["pips_result"] < 0]
        
        pips_results = [t["result"]["pips_result"] for t in completed]
        
        return {
            "n_decisions": len(entries),
            "n_trades": len(trades),
            "n_no_trades": len([e for e in entries if e["decision"] == "NO_TRADE"]),
            "n_completed": len(completed),
            "n_wins": len(wins),
            "n_losses": len(losses),
            "win_rate": len(wins) / len(completed) if completed else None,
            "avg_pips": sum(pips_results) / len(pips_results) if pips_results else None,
            "total_pips": sum(pips_results) if pips_results else None,
        }


def main():
    """Test du journal."""
    journal = TradingJournal()
    
    # Exemple : ajouter une décision
    entry = journal.add_decision(
        date_str="2024-09-11",
        direction="BUY",
        pattern="double_wave",
        impact_pred_pips=85.0,
        risk_score=0.31,
        gates_ok=False,
        reason_no_trade="Risk score (0.31) < RISK_MIN (0.60)",
    )
    
    print("✅ Entrée ajoutée:", entry)
    
    # Stats
    stats = journal.get_stats()
    print("\n📊 Statistiques:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

