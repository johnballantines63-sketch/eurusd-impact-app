# ⚡ MIGRATION TIMEZONE - PROCÉDURE COMPLÈTE

**Session 112 - Phase 1 - Option A**

---

## 🎯 OBJECTIF

Unifier timezones pour que:
```
Event 14:30 → Prix 14:30 (DIRECT, sans -2h)
```

---

## 🚀 EXÉCUTION (3 étapes)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# ÉTAPE 1: BACKUP (OBLIGATOIRE - 30s)
python scripts/session112/STEP1_backup_avant_migration.py

# ÉTAPE 2: MIGRATION (CRITIQUE - 1 min)
python scripts/session112/STEP2_migration_timezone.py
# → Choisir option 2 (SOUSTRAIRE 2h)
# → Taper 'MIGRER' pour confirmer

# ÉTAPE 3: TEST (30s)
python scripts/session112/STEP3_test_apres_migration.py
```

---

## ⚠️ CHOIX DANS STEP2

**Question:** Quel changement ?

**→ Choisis OPTION 2 (SOUSTRAIRE 2h)**

**Pourquoi ?**
- Event actuel: 14:30+02:00
- Prix correspondant: 12:30
- Soustraire 2h: 14:30 → 12:30
- Résultat: Event 12:30 = Prix 12:30 ✅

---

## ✅ RÉSULTAT ATTENDU

**STEP1:**
```
✅ BACKUP RÉUSSI !
   Taille: 205.XX MB
   Emplacement: .../backups/warehouse_AVANT_MIGRATION_TIMEZONE_...
```

**STEP2:**
```
✅ MIGRATION RÉUSSIE !
   58,449 events migrés
   
Vérification:
   Ancien: 2025-09-11 14:30:00+02:00
   Nouveau: 2025-09-11 12:30:00+02:00
```

**STEP3:**
```
✅ ALIGNEMENT CORRECT !
   Event et prix correspondent directement

🎉 MIGRATION RÉUSSIE !
   Impact correct sans règle -2h
   Impact: 57.1 pips (attendu ~57)
```

---

## 🔧 APRÈS MIGRATION

Mettre à jour `impact_measurement.py`:
```python
# AVANT (avec -2h)
hour_db = hour_bern - 2

# APRÈS (direct)
hour_db = hour_bern
```

---

## 🆘 SI PROBLÈME

**Restaurer backup:**
```bash
cp app/data/backups/warehouse_AVANT_MIGRATION_TIMEZONE_*.duckdb app/data/warehouse.duckdb
```

---

## 📊 Token Status

**Utilisés:** 77,700 / 190,000 (41%)  
**Restants:** 112,300 (59%)

→ Assez pour Phase 2 après !
