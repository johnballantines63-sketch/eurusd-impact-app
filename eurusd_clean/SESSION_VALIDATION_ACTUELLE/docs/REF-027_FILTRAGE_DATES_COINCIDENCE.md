# REF-027 : Filtrage des Dates avec Événement Coïncidant

**Date :** 2025-12-06  
**Objectif :** Éliminer les dates sans événement coïncidant avec le début du mouvement

---

## 🎯 PRINCIPE

En trading réel, on ne s'intéresse qu'aux mouvements qui commencent **directement** après un événement économique. Si le mouvement commence sans événement coïncidant, on ne serait pas investi à cette heure précise.

**Critères de coïncidence :**
- Fenêtre : ±15 minutes autour du début du mouvement
- Seuil mouvement : 5 pips minimum
- Détection : Mouvement FORT principal (pas juste le premier mouvement de 5 pips)

---

## 📊 RÉSULTATS

### Dates à ÉLIMINER (pas de coïncidence)

| Date | Début Mouvement | Amplitude | Direction | Raison |
|------|-----------------|-----------|-----------|--------|
| **2025-10-10** | 17:00 | 23.5 pips | UP | Aucun événement à 17:00 (±15 min) |

**Analyse 2025-10-10 :**
- Mouvement principal : 17:00-17:30 (69.90 pips au pic 17:36)
- Événements à 16:00 : Michigan Consumer Sentiment (US)
- **Problème :** Délai de réaction de 1h, pas de coïncidence directe
- **Conclusion :** En trading réel, on ne serait pas investi à 17:00 sans événement

---

### Dates à CONSERVER (avec coïncidence)

**22 dates valides :**

1. **2025-11-20** : mouvement à 14:30 → 24 événements (US Average Hourly Earnings, etc.)
2. **2025-09-11** : mouvement à 14:52 → 9 événements (DE Current Account, ECB Press Conference)
3. **2025-08-01** : mouvement à 14:31 → 12 événements (US Average Hourly Earnings, etc.)
4. **2025-05-29** : mouvement à 14:30 → 1 événement (CA Average Weekly Earnings)
5. **2025-06-23** : mouvement à 16:00 → 4 événements (US PMI Flash)
6. **2025-04-10** : mouvement à 15:39 → 3 événements (XK Inflation, EG Core Inflation)
7. **2025-03-12** : mouvement à 15:40 → 11 événements (CA BOC Press Conference, etc.)
8. **2025-02-07** : mouvement à 16:53 → 4 événements (RU GDP)
9. **2025-01-10** : mouvement à 14:30 → 22 événements (SN Inflation, etc.)
10. **2024-12-13** : mouvement à 15:00 → 2 événements (SN Industrial Production, PE Trade Balance)
11. **2024-11-08** : mouvement à 17:02 → 1 événement (US Fed Bowman Speech)
12. **2024-10-11** : mouvement à 16:11 → 4 événements (US Michigan Consumer Expectations)
13. **2024-09-06** : mouvement à 14:30 → 16 événements (US Average Hourly Earnings, etc.)
14. **2024-08-02** : mouvement à 14:41 → 9 événements (US Average Hourly Earnings, etc.)
15. **2024-07-11** : mouvement à 14:30 → 8 événements (US Continuing Jobless Claims, etc.)
16. **2024-06-07** : mouvement à 14:30 → 29 événements (US Average Hourly Earnings, etc.)
17. **2024-05-10** : mouvement à 16:15 → 6 événements (US Fed Kashkari Speech, Michigan)
18. **2024-04-05** : mouvement à 14:30 → 17 événements (US Average Hourly Earnings, etc.)
19. **2024-03-08** : mouvement à 14:30 → 21 événements (UA Inflation, etc.)
20. **2024-02-13** : mouvement à 14:30 → 6 événements (US Core Inflation)
21. **2024-01-12** : mouvement à 14:54 → 1 événement (XK Inflation)

---

## 📋 LISTE DES DATES VALIDES POUR TESTS

```python
VALID_TEST_DATES = [
    '2025-11-20',
    '2025-09-11',
    '2025-08-01',
    '2025-05-29',
    '2025-06-23',
    '2025-04-10',
    '2025-03-12',
    '2025-02-07',
    '2025-01-10',
    '2024-12-13',
    '2024-11-08',
    '2024-10-11',
    '2024-09-06',
    '2024-08-02',
    '2024-07-11',
    '2024-06-07',
    '2024-05-10',
    '2024-04-05',
    '2024-03-08',
    '2024-02-13',
    '2024-01-12',
]
```

**Total : 21 dates valides** (au lieu de 22)

---

## 🔍 MÉTHODE DE DÉTECTION

### 1. Identification du Mouvement Principal

**Stratégie :**
1. Identifier le pic maximum (mouvement le plus fort dans la fenêtre 14:00-20:00)
2. Remonter dans le temps pour trouver le début de ce mouvement
3. Le début est la première bougie qui s'écarte significativement (30% du mouvement max) de la baseline

**Avantages :**
- Détecte le VRAI mouvement fort, pas juste le premier mouvement de 5 pips
- Évite les faux positifs (petits mouvements avant le mouvement principal)

### 2. Vérification de Coïncidence

**Fenêtre :** ±15 minutes autour du début du mouvement

**Critères :**
- Événement dans la fenêtre : ✅ Coïncidence
- Pas d'événement : ❌ Pas de coïncidence → Date éliminée

---

## 📈 IMPACT SUR LES TESTS

### Avant Filtrage

- **22 dates** testées
- **2025-10-10** incluse (mouvement à 17:00 sans événement)

### Après Filtrage

- **21 dates** valides
- **2025-10-10** éliminée (pas de coïncidence)

**Bénéfice :**
- Tests plus réalistes (seulement dates où on serait investi en trading réel)
- Meilleure validation du pipeline (événements coïncidants)

---

## ✅ RECOMMANDATION

**Utiliser uniquement les 21 dates valides pour tous les tests futurs.**

**Fichier de référence :**
- `SESSION_VALIDATION_ACTUELLE/outputs/dates_coincidence_analysis.csv`

**Script de filtrage :**
- `SESSION_VALIDATION_ACTUELLE/scripts/filter_dates_with_event_coincidence.py`

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




