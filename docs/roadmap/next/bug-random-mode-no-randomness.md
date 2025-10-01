# [BUG] Random mode loses randomness with lazy generation

**Status:** next
**Priority:** 1
**Component:** cli
**Created:** 2025-10-01

## Description

Avec l'implémentation de la génération lazy (perf fix), le mode `random` ne génère plus de combinaisons aléatoires. Les variations sont générées on-the-fly dans l'ordre séquentiel au lieu d'être d'abord préparées puis shufflées.

## Current Behavior

En mode `generation_mode: "random"`:
- Les combinaisons sont générées séquentiellement via `generate_combinations_lazy()`
- On prend les N premières avec `islice(generator, N)`
- **Résultat:** Toujours les mêmes N premières combinaisons (pas aléatoire!)

## Expected Behavior

En mode `random`, le générateur devrait:
1. Calculer le nombre total de combinaisons possibles
2. Générer N combinaisons aléatoires UNIQUES parmi toutes les possibles
3. Ces combinaisons doivent être différentes à chaque exécution (ou selon seed)

## Reference Implementation

L'ancien code dans `CLI/private_generators/facial_expression_generator.py` faisait:
```python
# Génère toutes les combinaisons
all_combinations = generate_all_combinations(variations_dict)
# Puis shuffle
random.shuffle(all_combinations)
# Puis prend N
selected = all_combinations[:n]
```

Mais cette approche ne fonctionne pas pour les très grandes combinaisons (60T+).

## Fix Approach

### Option 1: Lazy random sampling (préféré)
```python
def generate_random_combinations_lazy(variations, count, seed=None):
    """Génère count combinaisons aléatoires sans construire toutes"""
    if seed:
        random.seed(seed)

    total = calculate_total_combinations(variations)

    if count >= total:
        # Si on veut tout, shuffle l'ordre
        yield from shuffled(generate_combinations_lazy(variations))
    else:
        # Génère des indices aléatoires uniques
        indices = random.sample(range(total), count)
        indices.sort()  # Pour efficacité de génération

        # Génère seulement aux indices choisis
        for idx in indices:
            yield get_combination_at_index(variations, idx)
```

### Option 2: Smart sampling
Pour très grandes combinaisons, générer directement des combinaisons aléatoires:
```python
def generate_random_combination(variations):
    """Génère UNE combinaison aléatoire"""
    return {
        placeholder: random.choice(list(values.values()))
        for placeholder, values in variations.items()
    }

# Puis vérifier unicité avec set
seen = set()
while len(seen) < count:
    combo = generate_random_combination(variations)
    combo_tuple = tuple(sorted(combo.items()))
    seen.add(combo_tuple)
```

## Location

- `CLI/image_variation_generator.py`: _create_combinatorial_variations() ligne ~275
- `CLI/sdapi_client.py`: Ajouter generate_random_combinations_lazy()
- `CLI/variation_loader.py`: create_random_combinations() existant mais non utilisé

## Impact

**Critique pour mode random:**
- Actuellement mode random ne fonctionne pas correctement
- Les utilisateurs s'attendent à de la vraie randomisation
- Empêche l'exploration diverse de l'espace des combinaisons

## Tests

- Vérifier que 2 exécutions avec seed différent donnent combinaisons différentes
- Vérifier que mode random avec petit espace (10 combos) donne vraies variations
- Vérifier que mode random avec grand espace (1M+ combos) ne hang pas
- Vérifier unicité des combinaisons générées
