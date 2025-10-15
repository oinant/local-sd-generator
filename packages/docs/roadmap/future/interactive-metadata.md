# CLI: Métadonnées des choix interactifs

**Priorité** : P1 (Haute)
**Cible** : CLI
**Statut** : 🔜 À venir

---

## Problème actuel

Le fichier `session_config.txt` ne contient pas les choix faits dans le menu interactif :
- Mode de génération (`combinatorial` / `random`)
- Mode de seed (`fixed` / `progressive` / `random`)
- Nombre d'images demandé
- Seed de base utilisé

**Conséquence** : Impossible de reproduire exactement une session sans se souvenir des choix faits.

---

## Solution proposée

Inclure tous les paramètres de session dans le fichier de configuration.

### Champs à ajouter

```json
{
  "generation_mode": "random",
  "seed_mode": "progressive",
  "base_seed": 42,
  "max_images": 100,
  "actual_images_generated": 95
}
```

---

## Bénéfices

- ✅ **Reproductibilité complète** : Tous les paramètres sont sauvegardés
- ✅ **Documentation automatique** : Historique complet des choix
- ✅ **Debugging facilité** : Analyser les runs problématiques
- ✅ **Comparaison** : Comparer différentes stratégies de génération

---

## Cas d'usage

### 1. Reproduire une session réussie
```bash
# Session originale avec choix interactifs sauvegardés
python generator.py --config good_session/session_config.json
```

### 2. Analyser l'impact des modes
```bash
# Comparer les résultats entre différents modes
diff session_random/session_config.json session_combinatorial/session_config.json
```

### 3. Documentation des expérimentations
Le fichier config devient un journal automatique des tests effectués.

---

## Impact

- Prérequis pour la feature "Lancement depuis fichier de configuration"
- Améliore la traçabilité
- Facilite les workflows d'expérimentation
