# Feature: Nested Variations

**Status:** future
**Priority:** 7
**Depends on:** Multi-field Expansion, Advanced Variation Selectors

## Description

Support de références entre fichiers de variations, permettant à une variation de composer d'autres variations. Une variation peut référencer d'autres fichiers de variations pour créer des compositions complexes et modulaires.

## Motivation

### Problème
Certaines variations sont des compositions d'autres variations :
- **Outfit complet** = top + bottom + shoes + accessories
- **Scene** = environment + lighting + weather + props
- **Character complet** = ethnicity + body + face + style

Sans nesting, il faut :
1. Dupliquer les valeurs
2. Maintenir la cohérence manuellement
3. Pas de réutilisabilité

### Avec nesting
```yaml
# outfits.yaml
variations:
  - key: beach_outfit
    top: "bikini top"
    bottom: "bikini bottom"
    accessories: ACCESSORIES[beach]  # Référence imbriquée
    footwear: FOOTWEAR[summer]       # Référence imbriquée
```

**Avantages :**
- Réutilisation des bibliothèques d'accessories/footwear
- Modifications centralisées
- Compositions modulaires

## Format

### Syntaxe de référence
```yaml
field_name: SOURCE[selectors]
```

Où `SOURCE` est défini dans :
- Les imports du prompt parent
- Un bloc `imports:` local au fichier de variation

### Exemple basique
```yaml
# variations/outfits.yaml
version: "1.0"

# Imports locaux (optionnel)
imports:
  ACCESSORIES: variations/accessories.yaml
  FOOTWEAR: variations/footwear.yaml

variations:
  - key: beach_casual
    top: "white tank top"
    bottom: "denim shorts"
    accessories: ACCESSORIES[beach]
    footwear: FOOTWEAR[sandals]

  - key: formal_evening
    top: "silk blouse"
    bottom: "pencil skirt"
    accessories: ACCESSORIES[formal,random:1]
    footwear: FOOTWEAR[heels]
```

**Fichiers référencés :**
```yaml
# variations/accessories.yaml
variations:
  - key: beach
    value: "sunglasses, beach hat, tote bag"

  - key: formal
    value: "pearl necklace, diamond earrings"

# variations/footwear.yaml
variations:
  - key: sandals
    value: "leather sandals"

  - key: heels
    value: "black stiletto heels"
```

## Résolution

### Algorithme récursif
```python
def resolve_nested(variation: dict, imports: dict, depth: int = 0) -> dict:
    """Résout récursivement les références imbriquées"""

    if depth > MAX_DEPTH:  # Éviter récursion infinie
        raise RecursionError(f"Max nesting depth {MAX_DEPTH} exceeded")

    result = {}

    for field, value in variation.items():
        if isinstance(value, str) and is_reference(value):
            # C'est une référence : SOURCE[selectors]
            source_name, selectors = parse_reference(value)

            if source_name not in imports:
                raise ImportError(f"Source '{source_name}' not found in imports")

            # Charge et résout la source
            source_variations = load_variations(imports[source_name])
            selected = apply_selectors(source_variations, selectors)

            # Résolution récursive si la variation sélectionnée a aussi des refs
            if len(selected) == 1:
                resolved = resolve_nested(selected[0], imports, depth + 1)
                result[field] = resolved.get('value', resolved)
            else:
                # Multiple sélections → liste
                result[field] = [
                    resolve_nested(s, imports, depth + 1)
                    for s in selected
                ]

        else:
            # Valeur simple
            result[field] = value

    return result
```

### Ordre de résolution
1. Parse la variation
2. Détecte les références `SOURCE[...]`
3. Charge le fichier source
4. Applique les sélecteurs
5. Résout récursivement les références dans les variations sélectionnées
6. Assemble le résultat final

## Exemples

### Exemple 1 : Outfit complet
```yaml
# variations/complete_outfits.yaml
imports:
  TOPS: variations/clothing/tops.yaml
  BOTTOMS: variations/clothing/bottoms.yaml
  ACCESSORIES: variations/accessories.yaml
  FOOTWEAR: variations/footwear.yaml

variations:
  - key: casual_summer
    top: TOPS[tank_top]
    bottom: BOTTOMS[shorts]
    accessories: ACCESSORIES[beach]
    footwear: FOOTWEAR[sandals]

  - key: business_formal
    top: TOPS[blouse]
    bottom: BOTTOMS[pencil_skirt]
    accessories: ACCESSORIES[professional]
    footwear: FOOTWEAR[heels]

  - key: random_casual
    top: TOPS[random:1]
    bottom: BOTTOMS[casual,random:2]
    accessories: ACCESSORIES[random:1]
```

**Résolution de `casual_summer` :**
1. `top`: charge TOPS, sélectionne `tank_top` → "white tank top"
2. `bottom`: charge BOTTOMS, sélectionne `shorts` → "denim shorts"
3. `accessories`: charge ACCESSORIES, sélectionne `beach` → "sunglasses, beach hat"
4. `footwear`: charge FOOTWEAR, sélectionne `sandals` → "leather sandals"

**Résultat final :**
```yaml
top: "white tank top"
bottom: "denim shorts"
accessories: "sunglasses, beach hat"
footwear: "leather sandals"
```

### Exemple 2 : Scene composition
```yaml
# variations/scenes.yaml
imports:
  ENVIRONMENTS: variations/environments.yaml
  LIGHTING: variations/lighting.yaml
  WEATHER: variations/weather.yaml
  PROPS: variations/props.yaml

variations:
  - key: beach_sunset
    environment: ENVIRONMENTS[beach]
    lighting: LIGHTING[golden_hour]
    weather: WEATHER[clear]
    props: PROPS[beach,random:2]

  - key: studio_portrait
    environment: ENVIRONMENTS[studio]
    lighting: LIGHTING[professional]
    weather: ""  # N/A pour studio
    props: PROPS[studio]

  - key: urban_night
    environment: ENVIRONMENTS[city_street]
    lighting: LIGHTING[neon]
    weather: WEATHER[rain]
    props: PROPS[urban,random:3]
```

### Exemple 3 : Multi-level nesting
```yaml
# Level 1: variations/full_scene.yaml
imports:
  SCENES: variations/scenes.yaml
  POSES: variations/poses.yaml

variations:
  - key: beach_portrait
    scene: SCENES[beach_sunset]  # Niveau 2
    pose: POSES[standing]

# Level 2: variations/scenes.yaml (de l'exemple précédent)
# Contient déjà des références (niveau 3)

# Résolution : 3 niveaux
# full_scene → scenes → environments/lighting/weather/props
```

## Multi-field nested expansion

Une référence peut aussi retourner multiple champs :

```yaml
# variations/character_presets.yaml
imports:
  ETHNICITIES: variations/ethnicities.yaml
  BODY_TYPES: variations/body_types.yaml

variations:
  - key: african_athletic
    # ETHNICITIES[african] expande : ethnicity, skin_tone, features
    ethnicity_bundle: ETHNICITIES[west_african]
    # BODY_TYPES[athletic] expande : height, build, muscle_tone
    body_bundle: BODY_TYPES[athletic]
```

**Résolution :**
```yaml
# Après expansion
ethnicity: "(West African:1.3)"
skin_tone: "(dark brown skin:1.4)"
features: "full lips, wide nose"
height: "tall"
build: "athletic, toned"
muscle_tone: "defined muscles"
```

## Imports locaux vs globaux

### Imports globaux (dans le prompt)
```yaml
# prompt.yaml
imports:
  ACCESSORIES: variations/accessories.yaml

prompt: |
  {OUTFIT}  # Peut utiliser ACCESSORIES
```

### Imports locaux (dans le fichier de variation)
```yaml
# outfits.yaml
imports:
  ACCESSORIES: variations/accessories.yaml

variations:
  - key: beach
    accessories: ACCESSORIES[beach]
```

### Scope resolution
1. Cherche dans les imports locaux du fichier
2. Si non trouvé, cherche dans les imports globaux du prompt
3. Si non trouvé, erreur

## Circular references

### Détection
```yaml
# outfits.yaml
imports:
  ACCESSORIES: accessories.yaml

variations:
  - key: beach
    acc: ACCESSORIES[beach_set]

# accessories.yaml
imports:
  OUTFITS: outfits.yaml  # ⚠️ Circular !

variations:
  - key: beach_set
    outfit: OUTFITS[beach]  # ⚠️ Circular !
```

**Erreur :**
```
CircularReferenceError: Detected circular reference:
  outfits.yaml → accessories.yaml → outfits.yaml
```

### Prevention
- Track la stack de résolution
- Détecter si on revisite un fichier déjà en cours de résolution
- Lever une erreur explicite

```python
def resolve_nested(variation, imports, depth=0, stack=None):
    if stack is None:
        stack = []

    current_file = get_current_file(variation)

    if current_file in stack:
        raise CircularReferenceError(
            f"Circular reference: {' → '.join(stack + [current_file])}"
        )

    stack.append(current_file)
    # ... résolution ...
    stack.pop()
```

## Depth limit

Limite la profondeur de nesting pour éviter :
- Performances dégradées
- Stack overflow
- Configurations trop complexes

```python
MAX_NESTING_DEPTH = 5  # Configurable

def resolve_nested(variation, imports, depth=0):
    if depth > MAX_NESTING_DEPTH:
        raise MaxDepthError(
            f"Max nesting depth {MAX_NESTING_DEPTH} exceeded at level {depth}"
        )
    # ...
```

## Caching

Pour éviter de recharger les mêmes fichiers :

```python
class VariationCache:
    def __init__(self):
        self._cache = {}
        self._resolved_cache = {}

    def load_variations(self, path: str):
        """Cache le fichier chargé"""
        if path not in self._cache:
            self._cache[path] = _load_yaml(path)
        return self._cache[path]

    def resolve_reference(self, ref: str, imports: dict):
        """Cache les résolutions"""
        cache_key = f"{ref}:{hash(frozenset(imports.items()))}"
        if cache_key not in self._resolved_cache:
            self._resolved_cache[cache_key] = _resolve(ref, imports)
        return self._resolved_cache[cache_key]
```

## Validation

### Au chargement
- Vérifier que les imports référencés existent
- Vérifier la syntaxe des références
- Détecter les circular references
- Warning si depth > 3 (complexité élevée)

### Erreurs possibles

**Import manquant :**
```yaml
variations:
  - key: test
    field: UNKNOWN[selector]
```
**Erreur :** `ImportError: Source 'UNKNOWN' not found in imports`

**Référence invalide :**
```yaml
variations:
  - key: test
    field: "INVALID[no_closing_bracket"
```
**Erreur :** `SyntaxError: Invalid reference syntax`

**Max depth :**
```yaml
# Nesting trop profond (> 5 niveaux)
```
**Erreur :** `MaxDepthError: Max nesting depth 5 exceeded at level 6`

## Tests

### Test 1 : Référence simple
```python
def test_simple_reference():
    accessories = {"beach": "sunglasses, hat"}
    outfit = {
        "top": "tank top",
        "accessories": "ACCESSORIES[beach]"
    }

    result = resolve_nested(outfit, {"ACCESSORIES": accessories})
    assert result["accessories"] == "sunglasses, hat"
```

### Test 2 : Multi-level nesting
```python
def test_multilevel_nesting():
    props = {"umbrella": "beach umbrella"}
    scenes = {
        "beach": {
            "env": "beach",
            "props": "PROPS[umbrella]"
        }
    }
    full = {
        "scene": "SCENES[beach]"
    }

    result = resolve_nested(
        full,
        {"SCENES": scenes, "PROPS": props}
    )
    assert result["scene"]["props"] == "beach umbrella"
```

### Test 3 : Circular reference detection
```python
def test_circular_reference():
    a = {"field": "B[ref]"}
    b = {"field": "A[ref]"}

    with pytest.raises(CircularReferenceError):
        resolve_nested(a, {"A": a, "B": b})
```

### Test 4 : Max depth
```python
def test_max_depth():
    # Créer une chaîne de 10 niveaux
    variations = create_nested_chain(depth=10)

    with pytest.raises(MaxDepthError):
        resolve_nested(variations, MAX_DEPTH=5)
```

### Test 5 : Cache
```python
def test_caching():
    cache = VariationCache()

    # Premier load
    cache.load_variations("test.yaml")
    load_count_1 = cache.load_count

    # Deuxième load (devrait être caché)
    cache.load_variations("test.yaml")
    load_count_2 = cache.load_count

    assert load_count_1 == load_count_2  # Pas de reload
```

## Performance

### Optimisations
- **Caching agressif** : Cache fichiers et résolutions
- **Lazy loading** : Ne charge que les fichiers nécessaires
- **Parallel resolution** : Résout les références indépendantes en parallèle

### Benchmarks attendus
- Résolution simple (1 niveau) : < 5ms
- Résolution complexe (3 niveaux, 10 refs) : < 50ms
- Avec cache : < 1ms

## Documentation auto-générée

```bash
sdgen explain-nesting variations/complete_outfits.yaml beach_casual
```

**Sortie :**
```markdown
# Nesting resolution for: beach_casual

## Resolution tree

beach_casual
├─ top: TOPS[tank_top]
│  └─ Resolved to: "white tank top"
│
├─ bottom: BOTTOMS[shorts]
│  └─ Resolved to: "denim shorts"
│
├─ accessories: ACCESSORIES[beach]
│  └─ Resolved to: "sunglasses, beach hat"
│     ├─ sunglasses (from accessories.yaml)
│     └─ beach hat (from accessories.yaml)
│
└─ footwear: FOOTWEAR[sandals]
   └─ Resolved to: "leather sandals"

## Final result
{
  "top": "white tank top",
  "bottom": "denim shorts",
  "accessories": "sunglasses, beach hat",
  "footwear": "leather sandals"
}

## Files involved
- variations/complete_outfits.yaml
- variations/clothing/tops.yaml
- variations/clothing/bottoms.yaml
- variations/accessories.yaml
- variations/footwear.yaml
```

## Success Criteria

- [ ] Parser les références `SOURCE[selectors]`
- [ ] Résolution récursive des références
- [ ] Support multi-level nesting (≥3 niveaux)
- [ ] Détection de circular references
- [ ] Max depth enforcement
- [ ] Caching efficace
- [ ] Imports locaux + globaux
- [ ] Multi-field nested expansion
- [ ] Validation et erreurs claires
- [ ] Documentation de résolution
- [ ] Performance acceptable (< 50ms pour 3 niveaux)
- [ ] Tests complets (>90% coverage)
