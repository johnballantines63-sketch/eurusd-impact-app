# 📋 GESTION DE PROJET SCIENTIFIQUE - OPTIMISATION AMPLIFICATION EUR/USD

**Titre projet :** Optimisation du facteur d'amplification pour prédiction impacts EUR/USD  
**Date création :** 31 octobre 2025 - Session 104  
**Version :** 2.1 - Mise à jour Session 105  
**Dernière MAJ :** 2 novembre 2025  
**Responsable :** André Valentin  
**Méthode :** Validation scientifique par clusters récurrents  
**Status :** ⏸️ **PAUSE TECHNIQUE** - Formule score_adjusted à créer (Session 106)

**État avancement Phase 1 (Cluster #3) :**
- ✅ Phase 3.1.1 : Validation mesure 11.09 → **56.8 pips exact**
- ✅ Phase 3.2 : Mesures 6 dates → Impacts + métriques OK
- ⚠️ Phase 3.2.6 : **BLOQUÉ** - score_adjusted manquant (formule non implémentée)
- ⏳ Phase 3.3 : En attente formule
- ⏳ Phase 3.4-3.5 : En attente

---

## 🌐 CONTEXTE PROJET GLOBAL

### Vision système complet

**OBJECTIF PRINCIPAL :** Système de prédiction temps réel EUR/USD pour aide au trading

**Le système doit pouvoir prédire pour un événement simple ou un cluster d'événements :**
- 📈 **DIRECTION** : Mouvement UP ou DOWN
- 📊 **AMPLITUDE** : Niveau maximum en pips
- ⏱️ **DURÉE** : Time To Reversal (minutes jusqu'au pic)
- 📉 **GRAPHIQUE** : Pattern (Single Wave, Double Wave, Triple Wave, Pullback)
- 🎯 **LATENCE** : Délai avant réaction marché

### Workflow trader opérationnel

**1. Scanner proactif (fonction future)**
- Identifier dates futures avec clusters high-impact
- Alertes sur compositions récurrentes validées
- Préparation fiches événements à venir

**2. Chargement événements**
- Page affichant événements pour date/heure précise
- Liste événements du cluster
- Champs de saisie valeurs actuelles

**3. Saisie temps réel (critère : rapidité)**
- Au moment publication : renseigner actual values
- Système calcule surprise automatiquement
- Validation données saisies

**4. Prédiction instantanée (critère : précision)**
- Calcul prédiction le plus rapidement possible
- Génération graphique prévisionnel
- Affichage métriques (impact, TTR, pullback)

**5. Décision trading**
- Adopter stratégie (Long/Short)
- Définir Stop Loss / Take Profit
- Exécution trade MT5 Swissquote

### Composantes système développées

**1. Formules validées (Sessions 51-55)** ✅ **COMPLÉTÉ**

| Formule | Fonction | Précision | Usage |
|---------|----------|-----------|-------|
| Impact | `calculate_impact_d()` | 98.6% | Amplitude pips |
| TTR | `calculate_ttr_c()` | 94.4% | Durée jusqu'au pic |
| Pullback | `calculate_pullback_v2()` | 99.3% | Retracements |
| Score ajusté | `calculate_adjusted_empirical_score()` | 99.9% | Ajustement surprise |

**Status :** Production, validé empiriquement

**2. Optimisation amplification (Sessions 103-109)** 🟡 **EN COURS** ← **CE DOCUMENT**

- Baseline amp=2.5 validée pour certains cas
- Observation : amp non optimal sur autres dates
- **Hypothèse :** amp dépend du CONTEXTE (tendance pré-event, durée, amplitude, surprise)
- **Objectif :** Baseline par cluster OU formule dynamique
- **Méthode :** Validation empirique sur clusters récurrents

**Status :** Recherche, Phase 1 (Cluster #3) en cours Session 105

**3. Détection patterns graphiques** ⏳ **FUTUR**

- Single Wave : Mouvement simple jusqu'au pic
- Double Wave : Pullback intermédiaire puis reprise (cas 11.09)
- Triple Wave : Multiples retracements
- Prédiction pattern selon contexte

**Status :** Planifié après optimisation amp

**4. Scanner événements futurs** ⏳ **FUTUR**

- Identification automatique dates high-impact
- Matching clusters récurrents validés
- Génération alertes trader

**Status :** Planifié

**5. Interface temps réel (Planificateur V2.x)** 🟡 **ÉVOLUTION**

- V2.4 : Actuel, baseline fixe amp=2.5
- V2.7 : Futur, baselines par cluster + formules dynamiques
- Saisie valeurs temps réel
- Prédiction instantanée
- Graphique prévisionnel

**Status :** V2.4 production, V2.7 développement après validation

### Cas référence : 11.09.2025 (Double Wave)

**Événements :**
- 14h30 : 11 événements CPI annoncés simultanément
- 14h45 : 1 événement additionnel (Core CPI révisé)

**Prédiction avec amp=2.5 :**
- Impact prédit : 56.3 pips UP ✅
- Impact réel : 56.8 pips UP ✅
- Erreur : 0.5 pips (0.9%) ✅
- TTR prédit : 109 minutes ✅
- Pullback prédit : -12 pips à 14h35 ✅

**Pattern graphique observé (Double Wave) :**
```
14h30 → 14h35 : UP +44 pips (Wave 1)
14h35 → 14h45 : Pullback -12 pips (profit-taking)
14h45 → 15h19 : UP +25 pips (Wave 2, annonce 14h45)
Résultat total : +56.8 pips
```

**Observation critique :**
- ✅ Formules prédisent correctement avec amp=2.5
- ✅ Pattern Double Wave identifié et expliqué
- ❓ amp=2.5 optimal aussi pour AUTRES dates Cluster #3 ?
- ❓ amp=2.5 optimal pour Cluster #2 (NFP) et Cluster #1 (Manufacturing) ?

**→ Raison de ce projet : Valider amp optimal par cluster et tester formule dynamique**

### Méthodologie validation

**Principe fondamental :**
> Tester sur PASSÉ (résultats connus) pour valider capacité prédictive

**Questions validation :**
- ✅ Aurait-on prédit la direction correcte ?
- ✅ Aurait-on prédit l'amplitude à ±5 pips ?
- ✅ Aurait-on prédit la durée à ±10 minutes ?
- ✅ Aurait-on prédit le pattern graphique (waves, pullback) ?

**Critères succès :**
- Précision direction : >85%
- MAE amplitude : <10 pips
- Précision TTR : ±15 minutes
- Identification pattern : >70%

**Validation empirique stricte :**
- Méthode Session 92.5 (timestamps corrects)
- Double-check MT5 + DB Dukascopy
- Écart acceptable : ±2 pips entre sources
- Exclusion cas avec anomalies

### Exclusions analyse

**Cas exclus (non mesurables/imprévisibles) :**

❌ **Événements politiques non programmés**
- Discours surprise Jerome Powell (Fed)
- Décisions imprévisibles Trump, UE
- Tweets influençant marché

❌ **Événements géopolitiques**
- Conflits militaires
- Crises bancaires
- Événements majeurs (attentats, catastrophes)

❌ **Anomalies techniques**
- Bugs plateforme trading
- Trading halts
- Flash crashes

**Raison :** Focus sur données objectives, répétables, vérifiables, mesurables

**Scope analyse :** Événements économiques US programmés avec données historiques (CPI, NFP, Manufacturing, etc.)

### Prochaines phases projet

**Phase actuelle : Optimisation amplification (Sessions 103-109)**
- Validation Cluster #3 (CPI) - Session 105 🟡
- Validation Cluster #1 (Manufacturing) - Session 106 ⏳
- Validation Cluster #2 (NFP) - Session 107 ⏳
- Synthèse et décision globale - Session 108-109 ⏳

**Phases suivantes (2025-2026) :**

1. **Détection patterns automatique**
   - Algorithme Single/Double/Triple Wave
   - Prédiction pattern selon métriques
   - Intégration Planificateur V3.0

2. **Scanner événements futurs**
   - Calendrier économique intégré
   - Matching clusters validés
   - Système alertes trader

3. **Optimisation interface temps réel**
   - Réduction latence saisie → prédiction
   - Graphiques interactifs
   - Recommandations stratégie automatiques

4. **Backtesting complet 2024-2025**
   - Test système sur 100+ événements passés
   - Calcul rentabilité théorique
   - Identification cas limites

5. **Trading simulation (Paper Trading)**
   - Exécution virtuelle 3 mois
   - Validation stratégies SL/TP
   - Calibration tailles positions

6. **Trading réel (Production)**
   - Déploiement MT5 Swissquote
   - Positions réelles contrôlées
   - Monitoring performance

### Positionnement de ce document

**CE DOCUMENT COUVRE : Composante #2 (Optimisation facteur amplification)**

**Parties 1-6 ci-dessous détaillent :**
- Fondations et problématique scientifique
- Méthodologie clusters récurrents
- Validation empirique par cluster (Phases 1-3)
- Synthèse et décision globale
- Intégration Planificateur V2.7

**Ce document est une BRIQUE du projet global, pas le projet complet.**

**Objectif final du projet :** Système prédiction temps réel EUR/USD avec précision >85% pour aide au trading profitable.

---

## 📚 TABLE DES MATIÈRES

[... le reste du contenu identique ...]
