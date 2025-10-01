# [BUG] Random mode loses randomness with lazy generation

**Status:** done (false positive)
**Priority:** 1
**Component:** cli
**Created:** 2025-10-01
**Closed:** 2025-10-01
**Resolution:** Not a bug - expected behavior

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

## Resolution

**Conclusion:** False positive - le comportement actuel est correct.

### Clarification:

1. **Mode combinatorial** (utilisé dans le test initial): génère les combinaisons dans un ordre déterministe (toujours les mêmes dans le même ordre). C'est le comportement attendu.

2. **Mode random**: utilise `create_random_combinations()` qui génère des combinaisons aléatoires uniques via `random.seed(time.time())`. Fonctionne correctement.

3. **La "seed"** mentionnée dans ImageVariationGenerator fait référence au **noise seed de Stable Diffusion**, pas au seed de randomisation des variations.

### Vérification du code:

- `CLI/image_variation_generator.py:221`: Mode random appelle `_create_random_variations()`
- `CLI/image_variation_generator.py:228`: Utilise `create_random_combinations()` de variation_loader
- `CLI/variation_loader.py:289`: Utilise `random.seed(time.time())` pour vraie randomisation

Le système fonctionne comme prévu:
- **Combinatorial**: déterministe, reproductible
- **Random**: aléatoire, différent à chaque run
