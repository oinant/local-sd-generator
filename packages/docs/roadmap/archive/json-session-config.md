# CLI: Format JSON pour session_config

**Priorité** : P1 (Haute)
**Cible** : CLI
**Statut** : 🔜 À venir

---

## Problème actuel

Le fichier `session_config.txt` utilise un format texte peu structuré :
- Ligne `fichiers_variations` contient du JSON sur une seule ligne (difficile à lire)
- Format global non structuré
- Difficile à parser programmatiquement

---

## Solution proposée

Transformer `session_config.txt` en fichier JSON structuré avec indentation.

### Exemple de format cible

```json
{
  "session_name": "my_generation_session",
  "timestamp": "2025-09-30_14-30-45",
  "prompt_template": "masterpiece, {Expression}, {Angle}",
  "negative_prompt": "low quality",
  "generation_mode": "random",
  "seed_mode": "progressive",
  "base_seed": 42,
  "max_images": 100,
  "variation_files": {
    "Expression": "variations/expressions.txt",
    "Angle": "variations/angles.txt"
  },
  "variations_loaded": {
    "Expression": ["happy", "sad", "angry", "surprised"],
    "Angle": ["front view", "side view", "3/4 view"]
  },
  "total_combinations": 12,
  "actual_images_generated": 100
}
```

---

## Bénéfices

- ✅ **Lisibilité améliorée** : Format structuré facile à lire
- ✅ **Parsing facilité** : Standard JSON pour scripts automatisés
- ✅ **Extensibilité** : Structure ouverte pour futures fonctionnalités
- ✅ **Compatibilité** : Outils JSON standard disponibles partout

---

## Impact

Fondation pour :
- Lancement depuis fichier de configuration
- Base de données SQLite
- Intégration webapp améliorée
- Scripts d'automatisation

---

## Notes d'implémentation

### Rétrocompatibilité
- Garder la possibilité de lire les anciens `session_config.txt`
- Migration automatique au format JSON lors de la première lecture

### Nom de fichier
- Renommer en `session_config.json`
- Ou garder `.txt` mais avec contenu JSON (moins standard)

### Pretty-print
- Utiliser `json.dump()` avec `indent=2`
- Assure la lisibilité humaine
