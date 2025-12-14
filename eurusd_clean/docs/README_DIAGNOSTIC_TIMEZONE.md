# Diagnostic Timezone - Mode d'Emploi

**Date** : 2025-01-XX  
**Statut** : ⚠️ TOUT EST À VÉRIFIER

---

## 🎯 OBJECTIF

**Vérifier** (pas supposer) comment les timezones sont réellement stockées dans la base de données pour :
- Événements (events.ts_utc)
- Prix Dukascopy (prices_1m, prices_bern)
- Prix Finnhub (prices_finnhub_m1)

**Gérer correctement** l'heure d'hiver/été (DST).

---

## ⚠️ IMPORTANT : Hypothèses vs Réalité

### Hypothèses (À VÉRIFIER)

- ❌ **NE PAS SUPPOSER** : "Dukascopy stocke en UTC+2h"
- ❌ **NE PAS SUPPOSER** : "Event 11.09 stocké à 13h30 en hiver"
- ✅ **À VÉRIFIER** : Comment c'est réellement stocké dans la DB

### Ce qu'on sait

- ✅ Events Finnhub : API retourne en UTC (vérifié dans code)
- ✅ Table events : Colonne `ts_utc` avec `TIMESTAMP WITH TIME ZONE`
- ⚠️ **Reste à vérifier** : Quelle timezone est réellement stockée

### Ce qu'on doit vérifier

1. **Événements** :
   - Comment `events.ts_utc` est-il réellement stocké ?
   - UTC ? Bern ? Autre ?

2. **Prix Dukascopy** :
   - Comment `prices_1m.datetime` est-il réellement stocké ?
   - UTC ? UTC+2h fixe ? Autre ?

3. **Prix Finnhub** :
   - Comment `prices_finnhub_m1.datetime` est-il réellement stocké ?
   - UTC ? Bern ? Autre ?

4. **Gestion DST** :
   - Les données prennent-elles en compte DST automatiquement ?
   - Ou offset fixe qui cause des erreurs ?

---

## 🚀 LANCER LE DIAGNOSTIC

### Commande

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/diagnostic_timezone_complet.py
```

### Ce que le script fait

1. ✅ Analyse structure des tables
2. ✅ Examine échantillons de timestamps
3. ✅ Identifie les timezones réelles stockées
4. ✅ Compare événements vs prix pour même moment
5. ✅ Détecte automatiquement DST (été/hiver)
6. ✅ Teste sur dates référence (11 sept = été, 15 jan = hiver)

### Résultats attendus

Le script va afficher :
- **Structure** de chaque table
- **Échantillons** de timestamps avec timezone
- **Offset UTC** détecté
- **Comparaison** événements ↔ prix
- **Détection DST** (été/hiver)

---

## 📊 INTERPRÉTATION DES RÉSULTATS

### Exemple de sortie attendue

```
📊 Analyse de la table : events
   Colonne : ts_utc

   Échantillons :
   [1] Timestamp: 2025-09-11 12:30:00+00:00
       Date: 2025-09-11
       Heure: 12:30
       Timezone: UTC
       Offset: UTC+0
       Probable: UTC
```

### Questions à se poser

1. **Events** :
   - Offset UTC+0 ? → Stocké en UTC ✅
   - Offset UTC+1 ou +2 ? → Stocké en Bern ⚠️
   - Pas de timezone ? → Naive, problème ⚠️

2. **Prix** :
   - Même timezone que events ? → Pas de conversion nécessaire ✅
   - Timezone différente ? → Conversion nécessaire ⚠️
   - Offset fixe ? → Problème DST ⚠️

3. **Correspondance** :
   - Event 12:30 UTC → Prix 12:30 UTC ? → OK ✅
   - Event 14:30 Bern → Prix 14:30 Bern ? → OK ✅
   - Event 12:30 UTC → Prix 14:30 ? → Conversion nécessaire ⚠️

---

## ✅ PROCHAINES ÉTAPES APRÈS DIAGNOSTIC

1. **Analyser résultats** :
   - Identifier timezones réelles
   - Détecter problèmes DST
   - Comparer Dukascopy vs Finnhub

2. **Établir règle claire** :
   - Comme Session 112 pour Dukascopy
   - Documenter conversion nécessaire

3. **Créer fonctions utilitaires** :
   - Conversion standardisée
   - Gestion DST automatique

4. **Mettre à jour pipeline** :
   - Utiliser conversions correctes
   - Supprimer conversions multiples

---

## 📚 DOCUMENTS ASSOCIÉS

- `docs/GUIDE_TIMEZONE_FINNHUB_AVEC_DST.md` - Guide complet avec DST
- `docs/ANALYSE_TIMEZONES_FINNHUB_CRITIQUE.md` - Analyse détaillée
- `docs/RESUME_CRITIQUE_TIMEZONES_FINNHUB.md` - Résumé exécutif

---

**Status** : ⚠️ TOUT EST À VÉRIFIER - Lancer diagnostic pour confirmer




