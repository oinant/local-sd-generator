# Phase 2 Implementation - Part 2: Resolver Integration

## État actuel (ce qui a été fait)

✅ **Fondations Phase 2 complètes** :

```
CLI/templating/
├── chunk.py              ✅ Load templates/chunks, résolution, rendering
├── multi_field.py        ✅ Multi-field expansion avec priorités
├── selectors.py          ✅ Parser syntaxe {CHUNK with field=SOURCE[selector]}
└── types.py              ✅ ChunkTemplate, Chunk, MultiFieldVariation

CLI/tests/templating/
├── test_chunk.py                ✅ 8 tests
├── test_multi_field.py          ✅ 8 tests
├── test_selectors_chunk.py      ✅ 6 tests
└── fixtures/
    ├── base/
    │   └── portrait_subject.char.template.yaml  ✅
    ├── characters/
    │   └── emma.char.yaml                       ✅
    ├── variations/
    │   ├── ethnic_features.yaml (multi-field)   ✅
    │   └── poses.yaml                           ✅
    └── prompts/
        └── emma_variations.prompt.yaml          ✅
```

**22 tests Phase 2 passent** ✅

## Ce qu'il reste à faire

### 1. Intégrer dans `resolver.py`

Le resolver doit maintenant supporter les chunks avec multi-field expansion.

**Changements nécessaires dans `resolver.py` :**

1. **Détecter les chunks dans les imports**
   ```python
   # Dans load_imports()
   if filepath.endswith('.char.yaml') or filepath.endswith('.chunk.yaml'):
       # Load chunk au lieu de variations
       chunk = load_chunk(filepath, base_path)
       template = load_chunk_template(chunk.implements, base_path)
       imports[name] = {'type': 'chunk', 'chunk': chunk, 'template': template}
   ```

2. **Détecter la syntaxe `{CHUNK with ...}`**
   ```python
   # Dans resolve_prompt()
   for placeholder_name, selector_str in placeholders.items():
       # Check if it's chunk with syntax
       full_content = f"{placeholder_name}..."  # Extract full {CHUNK with...}
       chunk_name, overrides = parse_chunk_with_syntax(full_content)

       if chunk_name:
           # Handle chunk resolution with overrides
       else:
           # Handle normal variation resolution
   ```

3. **Résoudre les chunks avec multi-field**
   ```python
   def resolve_chunk_placeholder(chunk_name, overrides, imports):
       """
       Résout un placeholder de type {CHUNK with field=SOURCE[selector]}.

       Steps:
       1. Load chunk + template
       2. For each override (field=SOURCE[selector]):
          - Load SOURCE variations (peut être multi-field)
          - Parse selector
          - Resolve variations sélectionnées
       3. Generate combinations:
          - Pour chaque variation de chaque override
          - Apply multi-field expansion
          - Resolve chunk fields
          - Render chunk
       4. Return list of rendered chunks
       """
   ```

4. **Générer les combinaisons**
   ```python
   # Mode combinatorial
   # Si {CHUNK with ethnicity=ETH[african,asian], pose=POSES[standing,sitting]}
   # → 2 ethnies × 2 poses = 4 chunks rendus

   # Mode random
   # Générer N combinaisons aléatoires
   ```

### 2. Test d'intégration end-to-end

**Créer `tests/templating/test_phase2_integration.py` :**

```python
def test_emma_variations_full_resolution():
    """
    Test complet avec le fixture emma_variations.prompt.yaml.

    Expected:
    - 2 ethnies (african, asian) × 2 poses (standing, sitting) = 4 variations
    - Chaque variation doit avoir:
      - Emma's base fields (name, age, body_type)
      - Ethnicity fields (skin, hair, eyes) from multi-field
      - Pose value
      - Technical quality from template defaults
    """
    config = load_prompt_config("fixtures/prompts/emma_variations.prompt.yaml")
    variations = resolve_prompt(config)

    assert len(variations) == 4

    # Variation 0: african + standing
    assert "Emma" in variations[0].final_prompt
    assert "dark skin" in variations[0].final_prompt
    assert "standing" in variations[0].final_prompt

    # Variation 1: african + sitting
    assert "dark skin" in variations[1].final_prompt
    assert "sitting" in variations[1].final_prompt

    # Variation 2: asian + standing
    assert "light skin" in variations[2].final_prompt
    assert "standing" in variations[2].final_prompt

    # Variation 3: asian + sitting
    assert "light skin" in variations[3].final_prompt
    assert "sitting" in variations[3].final_prompt
```

### 3. Demo fonctionnelle

**Créer `CLI/example_phase2_demo.py` :**

```python
from templating import load_prompt_config, resolve_prompt

# Load Emma variations prompt
config = load_prompt_config("tests/templating/fixtures/prompts/emma_variations.prompt.yaml")

# Resolve
variations = resolve_prompt(config)

print(f"Generated {len(variations)} variations:\n")

for i, var in enumerate(variations):
    print(f"=== Variation {i} (seed {var.seed}) ===")
    print(var.final_prompt)
    print()
```

**Output attendu :**
```
Generated 4 variations:

=== Variation 0 (seed 100) ===
Emma, 23 years old, athletic build
dark skin, ebony complexion, coily black hair, dark brown eyes
masterpiece, best quality
standing, upright posture

=== Variation 1 (seed 101) ===
Emma, 23 years old, athletic build
dark skin, ebony complexion, coily black hair, dark brown eyes
masterpiece, best quality
sitting, relaxed pose

=== Variation 2 (seed 102) ===
Emma, 23 years old, athletic build
light skin, porcelain complexion, straight black hair, almond-shaped dark eyes
masterpiece, best quality
standing, upright posture

=== Variation 3 (seed 103) ===
Emma, 23 years old, athletic build
light skin, porcelain complexion, straight black hair, almond-shaped dark eyes
masterpiece, best quality
sitting, relaxed pose
```

## Architecture suggérée pour resolver.py

### Nouvelles fonctions à ajouter

```python
def detect_chunk_import(filepath: str) -> bool:
    """Check if import is a chunk file."""
    return filepath.endswith('.char.yaml') or filepath.endswith('.chunk.yaml')


def load_chunk_import(filepath: Path, base_path: Path) -> dict:
    """Load chunk + template, return dict with both."""
    from .chunk import load_chunk, load_chunk_template

    chunk = load_chunk(filepath, base_path)
    template_path = base_path / chunk.implements
    template = load_chunk_template(template_path)

    return {
        'type': 'chunk',
        'chunk': chunk,
        'template': template
    }


def resolve_chunk_with_overrides(
    chunk_name: str,
    overrides: Dict[str, Tuple[str, str]],  # {field: (SOURCE, selector)}
    imports: Dict,
    config: PromptConfig
) -> List[str]:
    """
    Resolve chunk with multi-field overrides.

    Returns list of rendered chunk strings for each combination.
    """
    chunk_data = imports[chunk_name]
    chunk = chunk_data['chunk']
    template = chunk_data['template']

    # Resolve each override field
    override_variations = {}
    for field_name, (source_name, selector_str) in overrides.items():
        source_data = imports[source_name]

        # Check if multi-field
        if source_data.get('is_multi_field'):
            variations = source_data['variations']  # MultiFieldVariation objects
        else:
            variations = source_data  # Normal Variation objects

        # Parse and resolve selector
        selectors = parse_selector(selector_str) if selector_str else [Selector(type="all")]
        selected = resolve_selectors(variations, selectors, ...)

        override_variations[field_name] = selected

    # Generate combinations
    from itertools import product

    if config.generation_mode == "combinatorial":
        # All combinations
        field_names = list(override_variations.keys())
        field_values = [override_variations[f] for f in field_names]

        results = []
        for combo in product(*field_values):
            # combo is tuple of variations, one per field
            # Apply multi-field expansion if needed
            additional_fields = {}
            for field_name, variation in zip(field_names, combo):
                if isinstance(variation, MultiFieldVariation):
                    # Expand multi-field
                    additional_fields = merge_multi_field_into_chunk(
                        [variation],
                        chunk.fields,
                        additional_fields
                    )

            # Resolve and render
            resolved = resolve_chunk_fields(chunk, template, additional_fields)
            rendered = render_chunk(template, resolved)
            results.append(rendered)

        return results

    elif config.generation_mode == "random":
        # Generate N random combinations
        ...
```

### Modification de `resolve_prompt()`

```python
def resolve_prompt(config: PromptConfig) -> List[ResolvedVariation]:
    # Load imports
    imports = {}
    for name, filepath in config.imports.items():
        if detect_chunk_import(filepath):
            imports[name] = load_chunk_import(filepath, base_path)
        else:
            imports[name] = load_variations(filepath, base_path)

    # Extract placeholders from template
    # Check each placeholder for chunk "with" syntax
    chunks_to_resolve = {}
    variations_to_resolve = {}

    for placeholder_name in placeholders:
        full_content = extract_full_placeholder(config.prompt_template, placeholder_name)
        chunk_name, overrides = parse_chunk_with_syntax(full_content)

        if chunk_name:
            chunks_to_resolve[placeholder_name] = (chunk_name, overrides)
        else:
            variations_to_resolve[placeholder_name] = ...

    # Resolve chunks
    resolved_chunks = {}
    for placeholder_name, (chunk_name, overrides) in chunks_to_resolve.items():
        resolved_chunks[placeholder_name] = resolve_chunk_with_overrides(
            chunk_name, overrides, imports, config
        )

    # Resolve normal variations (existing code)
    ...

    # Generate combinations (mix chunks + variations)
    ...
```

## Ordre d'implémentation

1. **Modifier `resolver.py`**
   - Ajouter `detect_chunk_import()`, `load_chunk_import()`
   - Ajouter `resolve_chunk_with_overrides()`
   - Modifier `resolve_prompt()` pour détecter et résoudre les chunks

2. **Test d'intégration**
   - Créer `test_phase2_integration.py`
   - Valider que les 4 variations sont générées correctement

3. **Demo**
   - Créer `example_phase2_demo.py`
   - Vérifier l'output

4. **Documentation**
   - Mettre à jour `docs/roadmap/next/templating-phase2-characters.md`
   - Déplacer vers `docs/roadmap/done/` si tout est terminé

## Notes importantes

- **Backward compatibility** : Phase 1 doit continuer de fonctionner
- **Pattern extraction** : Besoin d'extraire le contenu complet `{...}` pour parser "with" syntax
- **Multi-field priority** : additional_fields > chunk.fields > template.defaults
- **Combinatorial** : Produit cartésien de tous les overrides

## Success Criteria pour Part 2

- [x] `resolver.py` modifié et fonctionnel ✅
- [x] Test d'intégration passe (4 variations Emma) ✅
- [x] 27 tests Phase 2 passent (22 + 5 intégration) ✅
- [x] Phase 1 reste compatible (imports `CLI.templating.*`) ✅

---

## ✅ PART 2 TERMINÉE

**Date de complétion:** 2025-10-03

### Résumé des modifications

**Fichiers modifiés:**
- `CLI/templating/resolver.py` - Intégration complète chunks + multi-field
  - `_is_chunk_file()` - Détection fichiers .char.yaml / .chunk.yaml
  - `_load_import()` - Chargement unifié variations/multi-field/chunks
  - `_resolve_chunk_with_overrides()` - Résolution chunks avec overrides multi-field
  - `_generate_combinatorial_mixed()` / `_generate_random_mixed()` - Combinaisons mixtes
  - `resolve_prompt()` - Parser "with" syntax et génération finale

**Fichiers créés:**
- `CLI/tests/templating/test_phase2_integration.py` - 5 tests end-to-end
- `CLI/example_phase2_demo.py` - Démonstration fonctionnelle

**Documentation:**
- `CLAUDE.md` mis à jour (python3, pas pytest-cov)

### Tests

```bash
cd /mnt/d/StableDiffusion/local-sd-generator/CLI
../venv/bin/python3 -m pytest tests/templating/test_chunk.py tests/templating/test_multi_field.py tests/templating/test_selectors_chunk.py tests/templating/test_phase2_integration.py -v
```

**Résultat:** 27 passed in 1.01s ✅

### Fonctionnalités validées

1. ✅ Chunk loading avec multi-field expansion
2. ✅ Parsing `{CHUNK with field=SOURCE[selector]}`
3. ✅ Résolution combinatoire (2 ethnies × 2 poses = 4 variations)
4. ✅ Résolution random mode avec chunks
5. ✅ Mix chunks + variations normales
6. ✅ Progressive seeds (100, 101, 102, 103)
7. ✅ Multi-field priority (additional > chunk > template defaults)

### Prochaines étapes

Phase 2 est maintenant **COMPLÈTE** et **FONCTIONNELLE** !

**Pour utiliser:**
```python
from CLI.templating import load_prompt_config, resolve_prompt

config = load_prompt_config("path/to/config.prompt.yaml")
variations = resolve_prompt(config, base_path=fixtures_path)

for var in variations:
    print(var.final_prompt)
```

**Architecture finale:**
- `chunk.py` - Templates et résolution de chunks
- `multi_field.py` - Expansion multi-champs
- `selectors.py` - Parsing syntaxe "with"
- `resolver.py` - Orchestration complète ✅
