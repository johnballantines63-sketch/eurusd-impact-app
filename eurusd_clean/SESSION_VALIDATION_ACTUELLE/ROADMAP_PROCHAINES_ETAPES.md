# Roadmap - Prochaines Étapes

**Date** : 2025-12-07  
**Status actuel** : Pipeline validé sur 50 dates significatives

---

## 🎯 Prochaines Étapes par Priorité

### 1. 🚀 Intégration Streamlit (HAUTE PRIORITÉ)

#### A. Fonction d'Import Automatique
- **Fichier** : `streamlit_app/utils/data_refresh.py`
- **Fonctionnalités** :
  - Bouton "Mettre à jour les données"
  - Import automatique prix + événements Finnhub
  - Indicateur de progression
  - Messages de statut
- **Référence** : Voir `TODO_STREAMLIT_IMPORT.md`

#### B. Intégration Formule Linéaire dans Planificateur
- Modifier `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py`
- Utiliser `calculate_impact_linear` au lieu de l'ancienne formule
- Ajouter filtre automatique pour mouvements significatifs (>= 20 pips)

#### C. Interface Utilisateur
- Afficher classification mouvement (MOYEN/FORT/TRÈS_FORT)
- Indicateur visuel pour mouvements significatifs
- Stratégie de sortie recommandée (85% pour MOYEN)

---

### 2. 📊 Optimisation Stratégie de Sortie (MOYENNE PRIORITÉ)

#### Objectif
Tester différents pourcentages de sortie pour optimiser win rate et gain moyen.

#### Tests à Effectuer
- Sortie à 80%, 85%, 90% de la prédiction
- Analyser impact sur win rate
- Analyser impact sur gain moyen
- Déterminer stratégie optimale par classe

#### Scripts à Créer
- `scripts/test_exit_strategies.py` - Tester différents % de sortie
- Analyser résultats sur les 50 dates validées

---

### 3. 🔍 Analyse Approfondie (BASSE PRIORITÉ)

#### A. Investigation Corrélation Négative
- Analyser pourquoi corrélation = -0.102
- Identifier cas problématiques
- Comprendre patterns

#### B. Analyse Meilleures vs Pires Prédictions
- Identifier patterns communs dans meilleures prédictions
- Identifier patterns communs dans pires prédictions
- Ajuster formule si nécessaire

---

### 4. 🧪 Tests en Conditions Réelles (CONTINU)

#### Objectif
Valider le pipeline sur événements futurs en temps réel.

#### Actions
- Utiliser pipeline sur événements à venir
- Comparer prédictions avec résultats réels
- Ajuster si nécessaire

---

## 📋 Checklist Intégration Streamlit

### Fonction Import Automatique
- [ ] Créer `streamlit_app/utils/data_refresh.py`
- [ ] Implémenter `check_data_freshness()`
- [ ] Implémenter `refresh_prices()`
- [ ] Implémenter `refresh_events()`
- [ ] Créer page/bouton dans Streamlit
- [ ] Tester import automatique

### Intégration Formule
- [ ] Modifier Planificateur pour utiliser formule linéaire
- [ ] Ajouter filtre mouvements significatifs
- [ ] Tester prédictions dans interface
- [ ] Valider affichage résultats

### Interface Utilisateur
- [ ] Afficher classification mouvement
- [ ] Indicateur mouvements significatifs
- [ ] Stratégie de sortie recommandée
- [ ] Documentation utilisateur

---

## 🎯 Objectifs à Court Terme

1. ✅ Pipeline validé (TERMINÉ)
2. ⏳ Intégration Streamlit (EN ATTENTE)
3. ⏳ Tests en conditions réelles (CONTINU)

---

## 💡 Notes

- **Focus trading** : Ne trader que MOYEN, FORT, TRÈS_FORT (>= 20 pips)
- **Formule** : Fonctionne très bien pour FORT (ratio 1.297)
- **Stratégie** : Sortie à 85% pour MOYEN, ajuster pour FORT selon résultats

---

**Prochaine session** : Commencer intégration Streamlit


