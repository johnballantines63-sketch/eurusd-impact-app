# 📊 Guide : Calcul des Métriques Empiriques

Ce guide explique comment calculer les métriques empiriques manquantes dans la base de données.

## 🎯 Objectif

Calculer les scores d'impact **vérifiés par backtest** pour les événements qui n'ont pas encore de métriques empiriques, notamment :
- ECB Interest Rate Decision
- Jobless Claims (US)
- PPI (US, EU)
- Autres événements HIGH sans score

## 📁 Scripts Disponibles

### 1. `calculate_missing_scores.py` (Recommandé)
Script simple et rapide pour calculer les scores manquants.

```bash
# Calculer seulement les événements HIGH prioritaires (rapide ~2-5 min)
python3 calculate_missing_scores.py

# Calculer TOUS les événements sans score (long ~20-30 min)
python3 calculate_missing_scores.py --all
```

### 2. `calculate_empirical_impact.py` (Complet)
Script complet qui recalcule TOUT et génère des rapports détaillés.

```bash
# Recalcule toutes les métriques empiriques (très long ~1h)
python3 calculate_empirical_impact.py
```

### 3. `check_empirical_status.py` (Diagnostic)
Vérifie l'état actuel sans rien calculer.

```bash
# Voir quels événements manquent de métriques
python3 check_empirical_status.py
```

## 🚀 Procédure Recommandée

### Étape 1 : Vérifier l'état actuel
```bash
python3 check_empirical_status.py
```

Cela affiche :
- Nombre d'événements avec/sans score
- Liste des événements HIGH prioritaires sans métriques
- Disponibilité des données pour ECB, Jobless Claims, PPI

### Étape 2 : Calculer les scores manquants
```bash
# Mode rapide : seulement les événements HIGH
python3 calculate_missing_scores.py
```

**Ce que fait le script :**
1. ✅ Identifie les événements `impact_level = 'HIGH'` sans `empirical_score`
2. ✅ Pour chaque événement :
   - Récupère l'historique depuis sept 2022 (3 ans de données)
   - Analyse les mouvements de prix après chaque occurrence
   - Calcule les métriques :
     - `avg_movement_pips` : Mouvement moyen en pips
     - `reaction_rate` : % d'événements avec réaction > 5 pips
     - `avg_latency_min` : Latence moyenne de réaction
     - `empirical_score` : Score composite 0-100
     - `empirical_impact` : Classification HIGH/MEDIUM/LOW
3. ✅ Met à jour la table `event_families` avec les nouvelles métriques

### Étape 3 : Vérifier les résultats
```bash
python3 check_empirical_status.py
```

Vous devriez voir :
- ✅ Augmentation du nombre d'événements avec score
- ✅ Métriques pour ECB, Jobless Claims, PPI

## 📊 Métriques Calculées

| Métrique | Description | Utilisation |
|----------|-------------|-------------|
| `empirical_score` | Score composite 0-100 | Filtrer les meilleurs événements |
| `empirical_impact` | HIGH/MEDIUM/LOW | Classifier par importance réelle |
| `avg_movement_pips` | Mouvement moyen en pips | Estimer le potentiel |
| `reaction_rate` | % de réaction significative | Mesurer la fiabilité |
| `avg_latency_min` | Latence moyenne en minutes | Timing d'entrée |
| `analyzed_occurrences` | Nombre d'occurrences analysées | Confiance statistique |

## 🧮 Calcul du Score Empirique

Le score est calculé sur **100 points** :

### 1. Volatilité (40 points max)
- 1 pip de mouvement = 1 point
- Plafonné à 40 points

**Exemple :**
- 25 pips → 25 points
- 50 pips → 40 points (plafonné)

### 2. Fréquence de Réaction (30 points max)
- `reaction_rate × 30`
- Mesure la fiabilité

**Exemple :**
- 90% de réaction → 27 points
- 50% de réaction → 15 points

### 3. Rapidité (30 points max)
- Inversement proportionnel à la latence
- `30 - avg_latency_min`

**Exemple :**
- Latence 2 min → 28 points
- Latence 15 min → 15 points
- Latence 30 min → 0 point

### Classification Finale

| Score | Impact | Interprétation |
|-------|--------|----------------|
| 70-100 | HIGH | Excellent - À trader en priorité |
| 40-69 | MEDIUM | Bon - Considérer selon contexte |
| 0-39 | LOW | Faible - Éviter |

## 📋 Exemples de Résultats Attendus

### CPI US (Déjà calculé)
```
empirical_score: 78.2
empirical_impact: HIGH
avg_movement_pips: 25.8
reaction_rate: 0.906 (90.6%)
avg_latency_min: 5.2
analyzed_occurrences: 200
```

### ECB Interest Rate (À calculer)
```
Avant: 
  empirical_score: NULL
  impact_level: HIGH (manuel)

Après (estimé):
  empirical_score: ~75-85
  empirical_impact: HIGH
  avg_movement_pips: ~20-30
  reaction_rate: ~85-95%
  avg_latency_min: ~3-8
```

### Jobless Claims US (À calculer)
```
Avant:
  empirical_score: NULL
  impact_level: HIGH (manuel)

Après (estimé):
  empirical_score: ~45-65
  empirical_impact: MEDIUM
  avg_movement_pips: ~10-15
  reaction_rate: ~70-80%
  avg_latency_min: ~5-10
```

## ⚠️ Points d'Attention

### 1. Données Insuffisantes
Si un événement a < 5 occurrences analysables :
- ❌ Il est sauté
- 💡 Raison : Pas assez de données pour statistiques fiables

### 2. Mapping EA ↔ EU
- Les événements ECB sont marqués 'EA' dans la DB
- Le script gère automatiquement ce mapping
- Pas d'action requise

### 3. Durée d'Exécution
- Mode rapide (HIGH seulement) : 2-5 minutes
- Mode complet (tous) : 20-30 minutes
- Recalcul total : ~1 heure

### 4. Sauvegarde
Les données sont sauvegardées automatiquement dans `event_families`.
Aucune sauvegarde manuelle nécessaire.

## 🔍 Vérification des Résultats

### Via Python
```python
import duckdb

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# Vérifier ECB
ecb = conn.execute("""
    SELECT event_key, empirical_score, empirical_impact, 
           avg_movement_pips, reaction_rate
    FROM event_families
    WHERE event_key LIKE '%ECB%Interest%'
""").fetchall()

print(ecb)
```

### Via Calendrier Trading
1. Ouvrir l'application Streamlit
2. Aller à "Calendrier Trading"
3. Activer "Mode Empirique"
4. Vérifier que les événements ECB, Jobless Claims, PPI affichent :
   - 🔴🔴🔴 avec un score (au lieu de ⚪⚪⚪)
   - Section "Métriques Backtest Vérifiées" remplie

## 🐛 Dépannage

### Erreur : "Module not found"
```bash
# Installer les dépendances
pip install duckdb pandas numpy
```

### Erreur : "Database is locked"
```bash
# Fermer l'application Streamlit
# Réessayer
```

### Événement toujours sans score après calcul
**Cause possible :** Données de prix manquantes

**Solution :**
1. Vérifier les données de prix : `prices_1m`
2. Vérifier la période : doit avoir des occurrences depuis sept 2022
3. Vérifier les actuals : doivent être non NULL

## 📚 Références

- Script principal : `fx_impact_app/src/calculate_missing_empirical_scores.py`
- Résumé session : `Resume sessions Claude/resume_session_13oct_2025_calendrier_trading.md`
- Calendrier Trading : `fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py`

## ✅ Checklist Complète

- [ ] Étape 1 : Vérifier l'état avec `check_empirical_status.py`
- [ ] Étape 2 : Calculer les scores avec `calculate_missing_scores.py`
- [ ] Étape 3 : Vérifier les résultats avec `check_empirical_status.py`
- [ ] Étape 4 : Tester dans Calendrier Trading (mode Empirique)
- [ ] Étape 5 : Vérifier que ECB, Jobless Claims, PPI ont des scores
- [ ] Étape 6 : Documenter les nouveaux scores dans un résumé

---

**Prêt à lancer ?** 🚀

```bash
# Commande simple pour tout faire
python3 calculate_missing_scores.py
```
