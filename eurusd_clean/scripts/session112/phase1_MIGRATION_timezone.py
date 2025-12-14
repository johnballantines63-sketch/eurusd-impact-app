#!/usr/bin/env python3
"""
MIGRATION TIMEZONE - Unifier events et prices
==============================================

OBJECTIF: Éliminer le décalage -2h entre events et prices

MÉTHODE:
- Events stockés à 14:30+02:00 (heure affichée)
- Prices cherchables à 12:30 (décalage -2h)
- SOLUTION: Ne RIEN modifier, mais clarifier la règle

APRÈS ANALYSE:
- Les deux tables sont déjà correctes
- Events: timestamp d'affichage (14:30)
- Prices: timestamp système (12:30 pour event 14:30)
- Pas de migration nécessaire, juste une règle claire

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import duckdb
from pathlib import Path
import pandas as pd

print("="*80)
print("🔧 MIGRATION TIMEZONE - DÉCISION")
print("="*80)

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

# ══════════════════════════════════════════════════════════════════════
# QUESTION: Faut-il migrer ?
# ══════════════════════════════════════════════════════════════════════

print("\n🤔 ANALYSE: Faut-il modifier la DB ?")
print("-"*80)

print("\n📋 OPTION A: Migrer events (+2h)")
print("   Avantage: Event 14:30 → chercher prix 14:30 (simple)")
print("   Inconvénient: Perd info heure réelle affichée")
print("   Impact: Modifie 60,000+ enregistrements")

print("\n📋 OPTION B: Migrer prices (-2h)")  
print("   Avantage: Alignement théorique")
print("   Inconvénient: Décale tous les prix, complexe")
print("   Impact: Modifie millions d'enregistrements")

print("\n📋 OPTION C: Ne rien migrer")
print("   Avantage: Garde cohérence actuelle")
print("   Inconvénient: Règle -2h obligatoire dans scripts")
print("   Impact: Aucune modification DB")

# ══════════════════════════════════════════════════════════════════════
# DÉCISION RECOMMANDÉE
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💡 RECOMMANDATION")
print("="*80)

print("\n✅ OPTION C: NE RIEN MIGRER")

print("\nRaisons:")
print("1. Les données sont cohérentes dans leur contexte actuel")
print("2. Events garde l'heure d'affichage MT5 (14:30)")
print("3. Prices garde l'heure système réelle")
print("4. Règle -2h simple à implémenter dans code")
print("5. Pas de risque de corruption de 60,000+ events")

print("\n💻 SOLUTION:")
print("   - Garder DB telle quelle")
print("   - Implémenter règle -2h dans modules Python")
print("   - Documenter clairement la règle")
print("   - Créer fonctions helper pour conversion")

# ══════════════════════════════════════════════════════════════════════
# ALTERNATIVE: Si André veut vraiment migrer
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("⚠️ SI MIGRATION SOUHAITÉE")
print("="*80)

print("\nVeux-tu vraiment migrer les events ?")
print("\n[1] OUI - Migrer events pour simplifier scripts")
print("[2] NON - Garder DB actuelle et utiliser règle -2h")

choice = input("\nChoix (1 ou 2): ").strip()

if choice == "1":
    print("\n⚠️ ATTENTION: Migration irréversible !")
    print("   Vérifie qu'un backup existe !")
    
    confirm = input("\nTaper 'MIGRER' pour confirmer: ").strip()
    
    if confirm == "MIGRER":
        print("\n🔄 Migration en cours...")
        
        con = duckdb.connect(str(db_path), read_only=False)
        
        try:
            # Compter events à migrer
            count = con.execute("""
                SELECT COUNT(*) FROM events
                WHERE country = 'US'
            """).fetchone()[0]
            
            print(f"\n📊 {count:,} events US à migrer")
            
            # MIGRATION: Ajouter 2h aux timestamps
            # Cela alignera events 14:30 avec prices 14:30
            # (au lieu de prices 12:30 actuellement)
            
            # NOTE: Cette migration change la sémantique !
            # Events ne représente plus l'heure affichée mais l'heure système
            
            print(f"\n⚠️ STOP: Migration désactivée par sécurité")
            print(f"   Si vraiment nécessaire, décommenter le code ci-dessous")
            print(f"   et relancer le script")
            
            # DÉCOMMENTER POUR ACTIVER:
            # con.execute("""
            #     UPDATE events
            #     SET ts_utc = ts_utc + INTERVAL '2 hours'
            #     WHERE country = 'US'
            # """)
            # 
            # print(f"\n✅ Migration terminée !")
            # print(f"   {count:,} events migrés")
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            con.rollback()
        finally:
            con.close()
    else:
        print("\n✅ Migration annulée")

else:
    print("\n✅ Pas de migration - Règle -2h conservée")
    print("\n📖 Documentation:")
    print("   Voir: docs/REGLE_TIMEZONE_DEFINITIVE.md")
    print("   Module: fx_impact_app/src/impact_measurement.py")

print("\n" + "="*80)
print("FIN")
print("="*80)
