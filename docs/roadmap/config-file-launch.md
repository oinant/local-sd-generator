# CLI: Lancement depuis fichier de configuration

**Priorité** : P2 (Moyenne)
**Cible** : CLI
**Statut** : 🔜 À venir

---

## Objectif

Permettre de lancer une génération directement avec un fichier de configuration JSON.

---

## Utilisation proposée

### Via CLI

```bash
python my_generator.py --config session_config.json
```

### Via API

```python
generator = ImageVariationGenerator.from_config_file("session_config.json")
generator.run()
```

---

## Bénéfices

- ✅ **Réutilisation** : Relancer facilement des configurations précédentes
- ✅ **Automatisation** : Workflows de génération scriptés
- ✅ **Partage** : Échanger des configurations entre utilisateurs
- ✅ **Batch processing** : Traiter multiples configurations en série

---

## Exemples d'utilisation

### Relancer une session exactement

```bash
python generator.py --config previous_session/session_config.json
```

### Batch processing

```bash
for config in configs/*.json; do
    python generator.py --config "$config"
done
```

### Tests A/B automatisés

```bash
# Générer avec plusieurs configs pour comparer
python generator.py --config config_seed42.json
python generator.py --config config_seed123.json
python generator.py --config config_random.json
```

---

## Implémentation

### Méthode de classe

```python
class ImageVariationGenerator:
    @classmethod
    def from_config_file(cls, config_path: str):
        """Crée un générateur depuis un fichier JSON."""
        with open(config_path, 'r') as f:
            config = json.load(f)

        return cls(
            prompt_template=config["prompt_template"],
            negative_prompt=config["negative_prompt"],
            variation_files=config["variation_files"],
            seed=config["base_seed"],
            generation_mode=config["generation_mode"],
            seed_mode=config["seed_mode"],
            max_images=config["max_images"],
            session_name=config["session_name"]
        )
```

---

## Dépendances

**Prérequis :**
- Format JSON pour session_config
- Métadonnées des choix interactifs

---

## Impact

Amélioration majeure des workflows d'automatisation et d'expérimentation.
