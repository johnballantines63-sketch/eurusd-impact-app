# 🎨 Guide de Correction : Graphique Minute par Minute - Amplitude Réelle

**Date** : 14 Octobre 2025
**Problème** : Le graphique minute par minute affiche 231.9 pips au lieu de 52.4 pips
**Status** : Correction manuelle nécessaire

---

## 📋 Résumé du Problème

D'après le résumé de session du 14 octobre, voici la situation :

**✅ DÉJÀ CORRIGÉ** : La métrique "Impact Total" affiche correctement **52.4 pips**

**❌ PAS ENCORE CORRIGÉ** : Le graphique minute par minute affiche encore **231.9 pips**

### Cause

Le graphique utilise probablement la **somme vectorielle brute** des impacts individuels au lieu de l'**amplitude réelle** calculée depuis les prix observés.

```python
# ❌ Ce que le code fait (somme brute) :
total_impact = sum(p['predicted_pips'] for p in predictions)
# Résultat : 231.9 pips (32.5 + 54.9 + 56.0 + 31.0 + ...)

# ✅ Ce qu'il devrait faire (amplitude réelle) :
total_impact = abs(vectorial_impact)  # ou abs(observed_movement)
# Résultat : 52.4 pips (amplitude réelle du mouvement)
```

---

## 🔍 Localisation du Code

**Fichier** : `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`

**Section** : "📈 Graphique Minute par Minute" (approximativement lignes 1700-1850)

### Recherche dans le Code

1. Ouvrir le fichier dans un éditeur
2. Rechercher : `st.subheader("📈 Évolution Prédite du Cours EUR/USD (Minute par Minute)")`
3. Descendre jusqu'à la section où le graphique est créé

---

## 🔧 Correction à Appliquer

### Étape 1 : Trouver le calcul d'amplitude

Chercher cette section (approximativement ligne 1800-1850) :

```python
# ✅ Calculer mouvement dominant depuis les données générées
max_movement = (price_df['high'].max() - start_price_input) * 10000
min_movement = (price_df['low'].min() - start_price_input) * 10000
observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement
```

**✅ Cette partie est CORRECTE** - Elle calcule déjà l'amplitude réelle.

### Étape 2 : Vérifier l'utilisation dans le graphique

Juste après, chercher :

```python
# Créer graphique avec le mouvement observé
fig = create_candlestick_prediction_chart(
    price_df=price_df,
    total_impact_pips=abs(observed_movement),  # ✅ Devrait utiliser observed_movement
    direction=1 if observed_movement > 0 else -1,
    ...
)
```

**SI** vous voyez à la place :

```python
total_impact_pips=sum(p['predicted_pips'] for p in predictions)  # ❌ ERREUR
```

**ALORS remplacer par** :

```python
total_impact_pips=abs(observed_movement)  # ✅ CORRECTION
```

### Étape 3 : Vérifier les annotations/statistiques

Plus bas, dans la section "Statistiques de la Simulation", chercher si il y a des calculs qui utilisent encore `sum(...)` :

```python
# ❌ SI vous voyez ça :
amplitude = sum(p['predicted_pips'] for p in predictions)

# ✅ REMPLACER par :
amplitude = (max_price - min_price) * 10000
```

---

## 🎯 Autre Possibilité : Le Problème n'est PAS dans le Code Python

Si le code Python est déjà correct (utilise `observed_movement`), alors le problème peut être :

### 1. Cache Navigateur

**Solution** : 
- Arrêter Streamlit
- Vider cache navigateur (Ctrl+Shift+Del ou Cmd+Shift+Del)
- Relancer Streamlit
- Recharger page (Ctrl+F5 ou Cmd+Shift+R)

### 2. Annotation Hardcodée

Chercher dans `price_curve_generator.py` si une annotation affiche "231" en dur :

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
grep -n "231" fx_impact_app/src/price_curve_generator.py
```

Si trouvé, ouvrir le fichier et corriger l'annotation.

### 3. Variable Mal Nommée

Il se peut qu'il y ait deux variables différentes :
- `vectorial_impact` = 52.4 pips (✅ correct, utilisé pour la métrique)
- `total_impact_something` = 231.9 pips (❌ incorrect, utilisé pour le graphique)

**Solution** : Rechercher TOUTES les variables qui contiennent "impact" ou "amplitude" et s'assurer qu'elles utilisent l'amplitude réelle.

---

## 📝 Commandes de Recherche Utiles

```bash
# Aller dans le projet
cd ~/Desktop/eurusd_news_impact_calculator_MPC

# Chercher toutes les occurrences de somme vectorielle
grep -n "sum.*predicted_pips" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py

# Chercher utilisation de vectorial_impact
grep -n "vectorial_impact" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py

# Chercher utilisation de observed_movement
grep -n "observed_movement" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py

# Chercher la section graphique minute par minute
grep -n "📈 Évolution Prédite" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
```

---

## ✅ Validation de la Correction

Après correction, tester :

### 1. Relancer Streamlit

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
streamlit run fx_impact_app/streamlit_app/Home.py
```

### 2. Tester sur 11/09/2025

1. Aller dans "Planificateur Multi-Événements"
2. Charger date : 11/09/2025
3. Sélectionner : Jobless Claims + CPI (×3)
4. Activer mode séquentiel : ✅
5. Configurer événements
6. Descendre jusqu'à "📈 Évolution Prédite du Cours EUR/USD"
7. Paramètres :
   - Prix actuel : 1.0950
   - Spread : 1.0 pips
   - Durée : 120 min
   - Volatilité : 0.3
8. Cliquer "Générer Graphique"

### 3. Vérifier les Métriques Affichées

**✅ CORRECT** :
```
Impact Total : 52.4 pips      ← Métrique principale (déjà corrigé)
Amplitude Totale : 52-67 pips  ← Graphique (à vérifier)
```

**❌ INCORRECT** :
```
Impact Total : 52.4 pips       ← Métrique principale ✅
Amplitude Totale : 231.9 pips  ← Graphique ❌ Pas encore corrigé
```

### 4. Comparer avec Réalité

La date 11/09/2025 a un mouvement réel observé de **53-67 pips**.

Si le graphique affiche ~52-67 pips → ✅ **Correction réussie !**

Si le graphique affiche 231 pips → ❌ **Problème persiste, chercher plus loin**

---

## 🚨 Si le Problème Persiste

### Option 1 : Modification Directe du Graphique

Dans `fx_impact_app/src/price_curve_generator.py`, chercher la fonction `create_candlestick_prediction_chart()` et vérifier que le paramètre `total_impact_pips` est bien utilisé pour les annotations.

### Option 2 : Désactiver les Annotations Problématiques

Commenter temporairement toute annotation qui affiche "231" pour identifier d'où ça vient.

### Option 3 : Debugging Manuel

Ajouter des `print()` pour tracer les valeurs :

```python
print(f"🔍 DEBUG : observed_movement = {observed_movement:.1f} pips")
print(f"🔍 DEBUG : total_impact_pips passé au graphique = {abs(observed_movement):.1f} pips")
```

Relancer Streamlit et vérifier la console pour voir quelle valeur est calculée/affichée.

---

## 📚 Références

- **Résumé Session** : `Resume sessions Claude/session_14oct2025_correction_amplitude_finale.md`
- **Fichier Principal** : `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`
- **Module Graphique** : `fx_impact_app/src/price_curve_generator.py`

---

## 💡 Résumé des Actions

1. ✅ **Vérifier** que `observed_movement` est bien calculé depuis `price_df`
2. ✅ **Vérifier** que `create_candlestick_prediction_chart()` reçoit `total_impact_pips=abs(observed_movement)`
3. ✅ **Chercher** toute utilisation de `sum(p['predicted_pips']...)` après le calcul d'`observed_movement`
4. ✅ **Remplacer** par `abs(observed_movement)` ou `abs(vectorial_impact)`
5. ✅ **Tester** sur 11/09/2025 et vérifier que le graphique affiche ~52 pips

---

**Si tout est correct dans le code Python mais que le problème persiste, c'est probablement un problème de cache navigateur. Vider le cache et recharger la page.**

---

*Guide créé le 14 Octobre 2025 par Claude*
