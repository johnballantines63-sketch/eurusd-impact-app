# 📚 HISTORIQUE CONSOLIDÉ DES SESSIONS 1-27

**Dernière mise à jour :** 21 octobre 2025 - Session 28  
**Type :** Synthèse historique (pas besoin de lire sauf investigation)

---

## 🎯 SYNTHÈSE PAR PÉRIODE

### Phase 1 : Fondations (Sessions 1-10)

**Objectif :** Créer système de base

**Réalisations :**
- ✅ Structure base de données
- ✅ Import événements EODHD
- ✅ Formule V1 (score / 50)
- ✅ Calculs impacts groupés

**Problèmes rencontrés :**
- Confusion base de données (fx_news_impact.db vs warehouse.duckdb)
- Erreurs TIMESTAMP conversion
- Formule V1 trop simpliste (MAE 258%)

---

### Phase 2 : Amélioration formule (Sessions 11-20)

**Objectif :** Améliorer précision prédictions

**Réalisations :**
- ✅ Formule v9-CLEAN (base validée)
- ✅ Formule V2 avec amplification surprise
- ✅ Formule pullback validée
- ✅ Validation 11 septembre MT5

**Problèmes rencontrés :**
- Données prix EODHD insuffisantes
- Sous-estimation mouvements ×10

---

### Phase 3 : Reconstruction données (Sessions 21-22)

**Objectif :** Reconstruire tables après import massif

**Réalisations :**
- ✅ Import +75% événements (58,449 total)
- ✅ Reconstruction event_families (747)
- ✅ Reconstruction event_group_impacts (19,653)
- ✅ Ajout suffixes (_mom, _yoy, _qoq)

**Problèmes rencontrés :**
- Tables obsolètes après import
- Décision : Reconstruction complète plutôt que patch

---

### Phase 4 : Diagnostic sources (Sessions 23-25)

**Objectif :** Identifier pourquoi mouvements sous-estimés

**Découvertes MAJEURES :**
- ❌ EODHD prix : Sous-estime ×10
- ❌ HistData : Sous-estime ×100-300
- ✅ Dukascopy : Source institutionnelle validée
- ✅ Correction timezone -2h

**Actions :**
- Import Dukascopy complet (1.1M lignes)
- Validation 11 septembre : 33.7 pips ✅
- Recalcul 16,335 événements

---

### Phase 5 : Nettoyage et correction (Sessions 26-27)

**Objectif :** Nettoyer base et corriger erreurs

**Découvertes CRITIQUES :**
- ❌ Tables event_impacts_calculated et event_group_impacts corrompues
- ❌ EODHD utilise "estimate" pas "forecast"
- ❌ 99.98% événements n'avaient pas forecast

**Actions majeures :**
- Suppression 3 tables corrompues
- Création event_impacts_v2 (8,344 événements)
- Correction forecast/estimate (26,370 événements réparés)
- Restructuration documentation

**Résultat :**
- ✅ Base propre et validée
- ✅ Forecast corrigé
- ✅ Documentation consolidée

---

## 🔑 DÉCISIONS CLÉS PAR SESSION

### Session 21 : Principe reconstruction

**Décision :** Reconstruire depuis zéro plutôt que patcher

**Rationale :**
- Garantit cohérence totale
- Plus rapide que debug patches multiples
- Élimine bugs cachés

**Statut :** ✅ Validé, appliqué Sessions 22, 26, 27

---

### Session 24 : Approche trading André

**Décision :** Focus sur phases exploitables, pas volatilité minute

**Ce qui compte :**
- Phase 1 globale (5-15 min)
- TTR
- Pullback
- Phase 2

**Ce qui ne compte PAS :**
- Range 1ère minute (trop volatile)

**Statut :** ✅ Validé, à intégrer dans V4

---

### Session 25 : Adoption Dukascopy

**Décision :** Abandonner EODHD/HistData prix, utiliser Dukascopy

**Rationale :**
- Source institutionnelle (banque suisse)
- Tick-by-tick (précision maximale)
- Validé vs MT5 André

**Statut :** ✅ Adopté définitivement

---

### Session 26 : Restructuration documentation

**Décision :** Créer structure 3 niveaux (START_HERE / CRITIQUES / TECHNIQUES)

**Problème résolu :**
- Info fragmentée dans 50+ fichiers
- Redécouverte erreurs 6+ fois

**Statut :** ✅ En cours d'amélioration Session 28

---

### Session 27 : Correction forecast/estimate

**Décision :** Copier estimate → forecast pour 26,370 événements

**Problème résolu :**
- 99.98% événements n'avaient pas forecast
- Surprises calculées avec previous (faux)

**Impact :** ×2,397 plus d'événements utilisables

**Statut :** ✅ Corrigé définitivement

---

## 📊 ÉVOLUTION MÉTRIQUES

### Base de données

| Session | events | prices_1m | Source prix | event_impacts |
|---------|--------|-----------|-------------|---------------|
| 1-18 | ~33k | ? | Inconnue | - |
| 19 | 58,449 | ? | EODHD | - |
| 23 | 58,449 | 1.1M | EODHD | - |
| 25 | 58,449 | 1.1M | Dukascopy | - |
| 26 | 58,449 | 1.1M | Dukascopy | 16,660 |
| 27 | 58,449 | 1.1M | Dukascopy | 8,344 |

**Note Session 27 :** Moins d'événements car utilise forecast (pas previous), mais surprises VRAIES.

### Formules

| Version | MAE | Base | Amplification | Statut |
|---------|-----|------|---------------|--------|
| V1 | 258% | score/50 | Aucune | Obsolète |
| v9-CLEAN | - | -7.08 + 0.419×score | Aucune | Base V2 |
| V2 | ~24% | v9-CLEAN | ×2.5 fixe | Actuelle |
| V3d | - | v9-CLEAN | Variable | Abandonné |
| **V4** | **?** | **Empirique** | **Adaptative** | **À créer** |

---

## 🚨 ERREURS MAJEURES DÉCOUVERTES

| # | Erreur | Fréquence | Sessions | Statut |
|---|--------|-----------|----------|--------|
| 1 | previous au lieu forecast | ⭐⭐⭐ 6+ | 7,11,13,18,23,26 | Documenté |
| 2 | Timezone conversion | ⭐⭐⭐ 4+ | 23,24,25,26 | Documenté |
| 3 | Filtrer trop tôt | ⭐⭐ 3+ | 18,23,26 | Documenté |
| 4 | Tables dérivées sans validation | ⭐⭐ 2+ | 25,26 | Documenté |
| 5 | Sous-estimer cas référence | ⭐⭐⭐ Constant | Toutes | Documenté |
| 7 | EODHD estimate vs forecast | ⭐⭐⭐ 1 majeur | 27 | Corrigé |

---

## 📁 FICHIERS HISTORIQUES IMPORTANTS

### Rapports clés à consulter si besoin

| Rapport | Session | Contenu | Quand consulter |
|---------|---------|---------|-----------------|
| RAPPORT_SESSION20_FINAL.md | 20 | Validation MT5 11 sept | Cas référence |
| RAPPORT_SESSION23_FINAL.md | 23 | Diagnostic prix incorrects | Investigation données |
| RAPPORT_SESSION25_FINAL.md | 25 | Import Dukascopy | Sources données |
| RAPPORT_SESSION26_FINAL.md | 26 | Nettoyage tables | Tables corrompues |
| RAPPORT_SESSION27_FINAL.md | 27 | Correction forecast | Surprise calcul |

### Scripts historiques

**76 scripts obsolètes** dans le répertoire racine

**Ne plus utiliser** sauf investigation spécifique d'une erreur passée.

**À créer pour Session 28+ :** Scripts simples et documentés.

---

## 🎯 LEÇONS APPRISES

### 1. Toujours valider données sources

**Erreur :** Utiliser EODHD/HistData sans validation
**Coût :** Sessions 20-25 basées sur fausses données
**Leçon :** Valider avec cas référence AVANT toute analyse

### 2. Documentation fragmentée = Redécouverte erreurs

**Erreur :** Info dans 50+ fichiers
**Coût :** Même erreur commise 6+ fois
**Leçon :** Documentation consolidée avec garde-fous

### 3. Reconstruction > Patch

**Erreur :** Essayer de patcher tables corrompues
**Coût :** Temps perdu en debug
**Leçon :** Reconstruire depuis zéro = plus rapide et plus sûr

### 4. Nommage API peut tromper

**Erreur :** EODHD appelle forecast "estimate"
**Coût :** 99.98% événements sans forecast
**Leçon :** Vérifier structure API complètement

### 5. Timezone = Source d'erreurs silencieuses

**Erreur :** Ne pas convertir explicitement en UTC
**Coût :** Lectures 2h après événement réel
**Leçon :** Toujours convertir et valider

---

## 📊 TEMPS INVESTI

**Sessions totales :** 27  
**Durée estimée :** 80-100 heures  
**Scripts créés :** 100+  
**Documentation :** 50+ fichiers

**Résultat Session 28 :**
- ✅ Base propre et validée
- ✅ Documentation consolidée
- ✅ Erreurs documentées
- ✅ Prêt pour V4

---

**FIN HISTORIQUE CONSOLIDÉ**

**Note :** Ce document est pour référence historique uniquement. Pour travailler sur le projet, utiliser `00_START_HERE_V2.md` et les fichiers `CRITIQUES/`.
