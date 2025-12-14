# Plan de Migration Dukascopy → Finnhub

## Réponse à votre Question

**OUI, les données Dukascopy seront supprimées intégralement après validation, et il n'y aura AUCUNE redondance.**

### Pourquoi Pas de Redondance ?

1. **Tables séparées** :
   - Dukascopy : `prices_bern`, `prices_1m`, `prices_1h`, etc.
   - Finnhub : `prices_finnhub_m1`, `prices_finnhub_h1`, etc.
   - **Aucun conflit de noms**

2. **Migration progressive** :
   - Phase 1 : Import Finnhub en parallèle (EN COURS)
   - Phase 2 : Validation et comparaison
   - Phase 3 : Migration complète vers Finnhub
   - Phase 4 : **Suppression totale de Dukascopy**

3. **Source unique finale** :
   - Après migration : **UNIQUEMENT** Finnhub
   - Toutes les références à Dukascopy supprimées
   - Scripts Dukascopy archivés ou supprimés

## Tables Dukascopy à Supprimer

### Tables Principales
```sql
DROP TABLE IF EXISTS prices_1m;           -- Prix M1 Dukascopy
DROP VIEW IF EXISTS prices_bern;          -- Vue Dukascopy
DROP VIEW IF EXISTS prices_1h;            -- Ancienne vue H1
DROP VIEW IF EXISTS prices_15m;           -- Vue M15 (si existe)
```

### Backups Dukascopy
```sql
-- Tous les backups avec préfixe prices_*_backup_*
DROP TABLE IF EXISTS prices_1m_backup_*;
DROP TABLE IF EXISTS prices_1m_backup_tz_*;
```

### Scripts Dukascopy
- `scripts/session113/update_dukascopy_prices.py` → **Archiver**
- `scripts/download_verify_prices_09sept.py` → **Supprimer** (temporaire)

## Plan de Migration Détaillé

### Phase 1 : Import Finnhub (EN COURS)
- ✅ Import de tous les timeframes
- ✅ 10 ans d'historique
- ✅ Tables préfixées `prices_finnhub_*`
- ✅ **Pas de suppression Dukascopy** (validation nécessaire)

### Phase 2 : Validation (À FAIRE)
- Comparer données sur période test (09.09.2025)
- Valider cohérence des prix
- Valider détection de tendances
- **Si OK → Phase 3**

### Phase 3 : Migration Complète
- Mettre à jour `detect_trend_pre_event` pour utiliser `prices_finnhub_*`
- Mettre à jour `Planificateur_V3_CLEAN` pour utiliser Finnhub
- Tester toutes les fonctionnalités
- **Si OK → Phase 4**

### Phase 4 : Suppression Dukascopy
- **BACKUP COMPLET** de la DB avant suppression
- Supprimer toutes les tables Dukascopy
- Supprimer/archiver scripts Dukascopy
- Mettre à jour documentation

## Script de Suppression (à exécuter après validation)

```sql
-- Script de nettoyage Dukascopy
-- À EXÉCUTER SEULEMENT APRÈS VALIDATION COMPLÈTE

-- 1. Tables principales
DROP TABLE IF EXISTS prices_1m;
DROP VIEW IF EXISTS prices_bern;
DROP VIEW IF EXISTS prices_1h;
DROP VIEW IF EXISTS prices_15m;
DROP VIEW IF EXISTS prices_5m;
DROP VIEW IF EXISTS prices_m15;
DROP VIEW IF EXISTS prices_m30;
DROP VIEW IF EXISTS prices_h4;

-- 2. Vues associées
DROP VIEW IF EXISTS prices_1m_v;
DROP VIEW IF EXISTS prices_1h_v;
DROP VIEW IF EXISTS prices_5m_v;
DROP VIEW IF EXISTS prices_m15_v;
DROP VIEW IF EXISTS prices_m30_v;
DROP VIEW IF EXISTS prices_h4_v;

-- 3. Tables de compatibilité
DROP TABLE IF EXISTS prices_1m_compat;
DROP TABLE IF EXISTS prices_1m_2c;

-- 4. Backups (optionnel, garder si besoin)
-- DROP TABLE IF EXISTS prices_1m_backup_*;
```

## Vérification Post-Migration

Après suppression, vérifier que :
1. ✅ Toutes les tables `prices_finnhub_*` existent
2. ✅ Le Planificateur fonctionne avec Finnhub
3. ✅ La détection de tendance fonctionne
4. ✅ Aucune référence à Dukascopy dans le code

## Avantages de la Migration

1. **Source unique** : Plus de confusion entre sources
2. **Données cohérentes** : Même source pour prix et événements
3. **Historique étendu** : 10 ans vs 3 ans
4. **Outils intégrés** : Patterns, Support/Résistance, Indicateurs
5. **Maintenance simplifiée** : Une seule API à gérer

## Timeline Estimée

- **Phase 1** : 1-2 jours (import en cours)
- **Phase 2** : 1 jour (validation)
- **Phase 3** : 2-3 jours (migration code)
- **Phase 4** : 1 jour (nettoyage)

**Total : ~1 semaine** pour migration complète


