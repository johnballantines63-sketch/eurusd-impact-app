# 🚧 PLANIFICATEUR - MIGRATION TODO

**Date :** 22 octobre 2025  
**Session :** 37  
**Statut :** En cours

## 🎯 Objectif

Migrer le Planificateur Multi-Événements vers `eurusd_clean/ui/planificateur.py` en utilisant UNIQUEMENT les modules depuis `eurusd_clean/app/`.

## ❌ Erreur Critique Identifiée

**Fichier :** `fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py`  
**Ligne :** 732  
**Erreur :** Colonne `empirical_impact` n'existe pas dans la table `event_families`

**Query actuelle (INCORRECTE) :**
```sql
SELECT 
    e.ts_utc, e.event_key, e.country, e.importance_n,
    e.actual, e.forecast, e.previous,
    ef.empirical_score, ef.empirical_impact, ef.impact_level,  -- ❌ empirical_impact n'existe pas
    ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key AND e.country = ef.country
WHERE...
```

**Query corrigée (CORRECTE) :**
```sql
SELECT 
    e.ts_utc, e.event_key, e.country, e.importance_n,
    e.actual, e.forecast, e.previous,
    ef.empirical_score, ef.impact_level,  -- ✅ empirical_impact supprimé
    ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key AND e.country = ef.country
WHERE...
```

## 📋 Étapes Migration

### Phase 1 : Correction Urgente (Session 37)
- [ ] Créer script de correction SQL pour fx_impact_app/
- [ ] Tester que l'application fonctionne après correction
- [ ] Backup de la version corrigée

### Phase 2 : Migration vers eurusd_clean/ (Session 38+)
- [ ] Adapter imports legacy → clean
- [ ] Remplacer modules legacy par modules clean
- [ ] Tests progressifs

## 🔧 Script Correction Urgente

Créer fichier : `fix_planificateur_sql_error.py`

```python
#!/usr/bin/env python3
"""
Correction urgente erreur SQL ligne 732 - Planificateur
"""

import sys
from pathlib import Path

# Chemin fichier à corriger
planificateur_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py")

def fix_sql_query():
    """Corriger la ligne 732 - supprimer empirical_impact"""
    
    with open(planificateur_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher et remplacer
    old_query = "ef.empirical_score, ef.empirical_impact, ef.impact_level,"
    new_query = "ef.empirical_score, ef.impact_level,"
    
    if old_query in content:
        content_fixed = content.replace(old_query, new_query)
        
        # Backup
        backup_path = planificateur_path.with_suffix('.py.backup_before_sql_fix')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup créé : {backup_path}")
        
        # Écrire version corrigée
        with open(planificateur_path, 'w', encoding='utf-8') as f:
            f.write(content_fixed)
        print(f"✅ Correction appliquée : {planificateur_path}")
        print(f"   Ligne 732 corrigée : empirical_impact supprimé")
        
        return True
    else:
        print("❌ Pattern non trouvé dans le fichier")
        return False

if __name__ == "__main__":
    print("🔧 Correction erreur SQL Planificateur...")
    success = fix_sql_query()
    sys.exit(0 if success else 1)
```

## 🚀 Utilisation

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 fix_planificateur_sql_error.py
```

Puis tester :
```bash
cd fx_impact_app
streamlit run streamlit_app/Home.py
```

## 📝 Notes

- Le fichier original STABLE contient ~2200 lignes
- Dépendances legacy complexes (sequence_multi_event_timeline, etc.)
- Migration complète vers eurusd_clean/ nécessite plusieurs sessions
- **PRIORITÉ :** Corriger l'erreur SQL d'abord, migrer ensuite

## 🔗 Références

- Fichier source : `fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py`
- Erreur identifiée : Session 37 - User feedback
- Structure DB : `docs/DB_STRUCTURE_REFERENCE.md`
