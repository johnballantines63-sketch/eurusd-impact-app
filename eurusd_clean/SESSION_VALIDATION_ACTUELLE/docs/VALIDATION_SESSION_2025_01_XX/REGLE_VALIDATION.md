# Règle de Validation - Session de Correction

**Date** : 2025-01-XX  
**Règle établie** : Validation obligatoire avant correction suivante

---

## 📋 RÈGLE FONDAMENTALE

**TOUJOURS valider les corrections avant de passer à la suivante.**

Cette règle est d'une logique implacable et doit être respectée systématiquement.

---

## 🔄 PROCESSUS DE VALIDATION

### 1. Correction
- Implémenter la correction
- Vérifier compilation (syntaxe)
- Vérifier imports

### 2. Test
- Créer test spécifique pour la correction
- Exécuter le test
- Vérifier résultats

### 3. Validation
- ✅ Si test réussi → Documenter succès
- ❌ Si test échoué → Corriger erreurs identifiées
- ⚠️ Si test partiel → Analyser et ajuster

### 4. Documentation
- Documenter résultats dans `CORRECTIONS_APPLIQUEES.md`
- Mettre à jour statut dans TODO

### 5. Passage suivant
- **SEULEMENT** après validation complète
- Ne jamais passer à la correction suivante si la précédente n'est pas validée

---

## ✅ EXEMPLES DE VALIDATION

### Correction Étape 6
1. ✅ Correction implémentée
2. ✅ Test créé (`test_corrections_etape6_8_1_8_2.py`)
3. ✅ Test exécuté
4. ✅ Résultats vérifiés (Étape 6 validée)
5. ✅ Documentation mise à jour

### Correction Étape 8.1
1. ✅ Correction implémentée
2. ✅ Test inclus dans même script
3. ✅ Test exécuté
4. ✅ Résultats vérifiés (Étape 8.1 validée)
5. ✅ Documentation mise à jour

### Correction Étape 8.2
1. ✅ Correction implémentée
2. ✅ Test inclus dans même script
3. ⏳ Test en cours d'exécution
4. ⏳ Résultats à vérifier
5. ⏳ Documentation à mettre à jour

---

## 🚫 INTERDICTIONS

- ❌ Ne jamais implémenter plusieurs corrections sans tester entre chaque
- ❌ Ne jamais passer à la correction suivante si la précédente échoue
- ❌ Ne jamais considérer une correction "terminée" sans test réussi

---

## 📊 STATUT DES CORRECTIONS

| Correction | Statut | Test | Validation |
|------------|--------|------|------------|
| Étape 6 | ✅ Corrigé | ✅ Créé | ✅ Validé |
| Étape 8.1 | ✅ Corrigé | ✅ Créé | ✅ Validé |
| Étape 8.2 | ✅ Corrigé | ✅ Créé | ⏳ En cours |

---

**Cette règle doit être appliquée systématiquement pour éviter les régressions et garantir la qualité du code.**

