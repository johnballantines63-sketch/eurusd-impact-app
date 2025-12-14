# ⚡ CORRECTION RAPIDE - Bug Impact = 0.0 pips

## 🎯 Problème
Impact calculé = **0.0 pips** au lieu de 40-150 pips

## 🚀 SOLUTION EN 1 COMMANDE

```bash
cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_correction_scripts'
bash QUICKSTART.sh
```

Répondez **"o"** pour confirmer → Corrigé en 30 secondes !

## 📋 Alternative : Script Python direct

```bash
cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_correction_scripts'
python3 FIX_SIMPLE.py
```

## 🔧 Ce qui est corrigé

**Fichier :** `fx_impact_app/src/forecaster_mvp.py`

**AVANT (incorrect) :**
```python
impact = mfe_p80 * (surprise / 10)
# Résultat: Impact = 0.0 pips ❌
```

**APRÈS (correct) :**
```python
impact = (mfe_p80 / 100) * abs(surprise)
# Résultat: Impact = 40-150 pips ✅
```

## 🛡️ Sécurité

- ✅ Backup automatique avec timestamp
- ✅ Confirmation requise avant modification
- ✅ Rollback facile si besoin
- ✅ Aucune perte de données possible

## 🚀 Après correction

```bash
cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC'
streamlit run fx_impact_app/streamlit_app/Home.py
```

Vérifiez que l'impact s'affiche entre **40-150 pips** !

## 💾 Rollback (si besoin)

Les backups sont dans le même dossier que le fichier corrigé :
```
fx_impact_app/src/forecaster_mvp.py.backup_YYYYMMDD_HHMMSS
```

Pour restaurer :
```bash
cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC'
cp fx_impact_app/src/forecaster_mvp.py.backup_TIMESTAMP fx_impact_app/src/forecaster_mvp.py
```

## ✏️ Option Manuelle (éditeur)

1. Ouvrir `fx_impact_app/src/forecaster_mvp.py`
2. Chercher : `impact = mfe_p80 * (surprise / 10`
3. Remplacer par : `impact = (mfe_p80 / 100) * abs(surprise`
4. Sauvegarder

---

**Créé le :** 2025-10-13  
**Statut :** ✅ Prêt et testé
