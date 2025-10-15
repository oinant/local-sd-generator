# Feature: Advanced Variation Selectors

**Status:** future
**Priority:** 6
**Depends on:** YAML loader, Variation file parser

## Description

Syntaxe riche et expressive pour sélectionner des variations depuis des fichiers, permettant de cibler précisément quelles variations utiliser par clé, index, range, ou sélection aléatoire.

## Motivation

### Problème actuel
```python
# Système actuel : limité et verbeux
"{FacialExpression:15}"  # Seulement : limiter à N aléatoires
"{FacialExpression:#|1|5|22}"  # Sélection d'index, syntaxe obscure
```

Limitations :
- Syntaxe peu intuitive
- Impossible de combiner plusieurs modes
- Pas de sélection par clé nommée
- Pas de ranges

### Avec ce système
```yaml
{EXPRESSIONS[happy,sad,surprised]}           # Clés nommées
{EXPRESSIONS[1,5,8]}                         # Index spécifiques
{EXPRESSIONS[range:1-10]}                    # Range d'index
{EXPRESSIONS[random:5]}                      # 5 aléatoires
{EXPRESSIONS[happy,sad,random:3]}            # Mix : clés + aléatoires
{EXPRESSIONS[range:10-50,random:20]}         # 20 aléatoires du range 10-50
```

## Syntaxe complète

### Format général
```
{SOURCE[selector1,selector2,...]}
```

Où `SOURCE` est une clé dans le bloc `imports:` et les sélecteurs peuvent être combinés.

### Types de sélecteurs

#### 1. Sélection par clé nommée
```yaml
{EXPRESSIONS[happy]}
{EXPRESSIONS[happy,sad,surprised]}
```

Sélectionne les variations dont la clé correspond.

**Fichier de variations :**
```yaml
# expressions.yaml
variations:
  - key: happy
    value: "smiling, cheerful"
  - key: sad
    value: "crying, tears"
  - key: surprised
    value: "eyes wide, mouth open"
```

**Résultat :** Utilise uniquement happy, sad, surprised

#### 2. Sélection par index
```yaml
{POSES[1]}
{POSES[1,5,8,12]}
```

Sélectionne les variations par leur position (0-indexed ou 1-indexed selon config).

**Fichier de variations :**
```yaml
variations:
  - standing     # Index 0 (ou 1)
  - sitting      # Index 1 (ou 2)
  - lying down   # Index 2 (ou 3)
  - kneeling     # Index 3 (ou 4)
  - crouching    # Index 4 (ou 5)
```

**Résultat avec `[1,3]` (0-indexed) :** sitting, kneeling

#### 3. Range d'index
```yaml
{POSES[range:1-10]}
{POSES[range:5-20]}
```

Sélectionne toutes les variations dans le range (inclusif).

**Résultat avec `[range:1-3]` :** Index 1, 2, 3

#### 4. Sélection aléatoire
```yaml
{EXPRESSIONS[random:5]}
{EXPRESSIONS[random:10]}
```

Sélectionne N variations aléatoires parmi toutes les variations disponibles.

#### 5. Combinaisons

**Clés + aléatoires**
```yaml
{EXPRESSIONS[happy,sad,random:3]}
```
Résultat : happy, sad, + 3 autres variations aléatoires

**Range + aléatoires**
```yaml
{POSES[range:10-50,random:20]}
```
Résultat : 20 variations aléatoires choisies dans le range 10-50

**Clés + index + aléatoires**
```yaml
{ITEMS[sword,shield,5,8,random:2]}
```
Résultat : clés "sword" et "shield", index 5 et 8, + 2 aléatoires

#### 6. Tous (par défaut)
```yaml
{EXPRESSIONS}
{EXPRESSIONS[all]}
```

Utilise toutes les variations du fichier.

## Format des fichiers de variations

### Format simple (liste)
```yaml
# poses.yaml
variations:
  - standing
  - sitting
  - lying down
  - kneeling
```

### Format avec clés
```yaml
# expressions.yaml
variations:
  - key: happy
    value: "smiling, cheerful, joyful"

  - key: sad
    value: "crying, tears, melancholic"

  - key: angry
    value: "frowning, clenched jaw, intense"
```

### Format backward compatible (.txt)
```
# expressions.txt
happy→smiling, cheerful, joyful
sad→crying, tears, melancholic
angry→frowning, clenched jaw, intense
```

Converti automatiquement en :
```yaml
variations:
  - key: happy
    value: "smiling, cheerful, joyful"
  # ...
```

## Exemples d'utilisation

### Exemple 1 : Portrait avec expressions ciblées
```yaml
imports:
  EXPRESSIONS: variations/facial_expressions.yaml

prompt: |
  beautiful girl, {EXPRESSIONS[happy,content,peaceful]}, detailed
```

Génère 3 images avec seulement ces 3 expressions.

### Exemple 2 : Test rapide avec range
```yaml
imports:
  POSES: variations/poses.yaml  # 100 poses

prompt: |
  1girl, {POSES[range:1-10]}, outdoor
```

Teste les 10 premières poses rapidement.

### Exemple 3 : Exploration aléatoire
```yaml
imports:
  EVERYTHING: variations/mega_pack.yaml  # 500 variations

prompt: |
  character, {EVERYTHING[random:25]}, scenery
```

Explore 25 variations aléatoires sur les 500 disponibles.

### Exemple 4 : Mix précis
```yaml
imports:
  OUTFITS: variations/clothing.yaml

prompt: |
  1girl, {OUTFITS[dress,suit,random:5]}, portrait
```

Génère : dress, suit, + 5 tenues aléatoires = 7 images

### Exemple 5 : Dans character override
```yaml
imports:
  CHARACTER: characters/athlete_portrait.char.yaml
  ETHNICITIES: variations/ethnicities.yaml

prompt: |
  {CHARACTER with ethnicity=ETHNICITIES[african,asian,latina]}
```

Emma avec 3 ethnies spécifiques.

## Validation et erreurs

### Erreur : Clé inexistante
```yaml
{EXPRESSIONS[unknown_key]}
```
**Erreur :** `Key 'unknown_key' not found in variations/expressions.yaml`

**Options de gestion :**
- `strict: true` → Erreur fatale
- `strict: false` → Warning + skip la clé

### Erreur : Index hors limites
```yaml
# expressions.yaml a 10 variations
{EXPRESSIONS[50]}
```
**Erreur :** `Index 50 out of range [0-9] in variations/expressions.yaml`

### Erreur : Range invalide
```yaml
{EXPRESSIONS[range:50-10]}  # Start > end
```
**Erreur :** `Invalid range 50-10: start must be <= end`

### Warning : Random > disponible
```yaml
# expressions.yaml a 10 variations
{EXPRESSIONS[random:50]}
```
**Warning :** `Requested 50 random variations but only 10 available, using all 10`

### Erreur : Syntaxe invalide
```yaml
{EXPRESSIONS[random]}  # Manque le nombre
```
**Erreur :** `Invalid selector 'random': expected 'random:N'`

## Configuration

### Dans le fichier de prompt
```yaml
selector_config:
  index_base: 1              # 0-indexed ou 1-indexed (défaut: 0)
  strict_mode: true          # Erreur sur clé/index invalide (défaut: true)
  allow_duplicates: false    # Permettre les doublons (défaut: false)
  random_seed: 42            # Seed pour random (défaut: null)
```

### Exemples avec config

**Index 1-based :**
```yaml
selector_config:
  index_base: 1

prompt: |
  {POSES[1]}  # Sélectionne la 1ère pose (pas la 2ème)
```

**Loose mode :**
```yaml
selector_config:
  strict_mode: false

prompt: |
  {EXPRESSIONS[happy,unknown,sad]}  # Warning sur 'unknown', continue
```

**Random déterministe :**
```yaml
selector_config:
  random_seed: 42

prompt: |
  {EXPRESSIONS[random:5]}  # Toujours les mêmes 5 avec ce seed
```

## Parser

### Grammaire
```
selector      ::= '[' selector_list ']'
selector_list ::= selector_item (',' selector_item)*
selector_item ::= key_selector | index_selector | range_selector | random_selector | all_selector

key_selector    ::= identifier
index_selector  ::= integer
range_selector  ::= 'range:' integer '-' integer
random_selector ::= 'random:' integer
all_selector    ::= 'all'
```

### Exemples de parsing

**Input :** `[happy,sad,random:3]`
**AST :**
```python
[
  KeySelector("happy"),
  KeySelector("sad"),
  RandomSelector(3)
]
```

**Input :** `[range:10-20,5,random:2]`
**AST :**
```python
[
  RangeSelector(10, 20),
  IndexSelector(5),
  RandomSelector(2)
]
```

## Résolution

### Algorithme
```python
def resolve_selectors(source: VariationFile, selectors: List[Selector]) -> List[Variation]:
    result = []
    all_variations = source.load_all()

    for selector in selectors:
        if isinstance(selector, KeySelector):
            variation = source.get_by_key(selector.key)
            if variation:
                result.append(variation)
            elif strict_mode:
                raise KeyError(f"Key {selector.key} not found")

        elif isinstance(selector, IndexSelector):
            if 0 <= selector.index < len(all_variations):
                result.append(all_variations[selector.index])
            elif strict_mode:
                raise IndexError(f"Index {selector.index} out of range")

        elif isinstance(selector, RangeSelector):
            if selector.start > selector.end:
                raise ValueError(f"Invalid range {selector.start}-{selector.end}")
            result.extend(all_variations[selector.start:selector.end+1])

        elif isinstance(selector, RandomSelector):
            available = [v for v in all_variations if v not in result]
            count = min(selector.count, len(available))
            result.extend(random.sample(available, count))

        elif isinstance(selector, AllSelector):
            result.extend(all_variations)

    # Dédupliquer si nécessaire
    if not allow_duplicates:
        result = list(dict.fromkeys(result))  # Preserve order

    return result
```

## Tests

### Test 1 : Sélection par clé
```python
def test_key_selector():
    variations = load_variations("expressions.yaml")
    selected = resolve("{EXPRESSIONS[happy,sad]}", {"EXPRESSIONS": variations})
    assert len(selected) == 2
    assert selected[0].key == "happy"
    assert selected[1].key == "sad"
```

### Test 2 : Sélection par index
```python
def test_index_selector():
    variations = load_variations("poses.yaml")
    selected = resolve("{POSES[0,2,4]}", {"POSES": variations})
    assert len(selected) == 3
```

### Test 3 : Range
```python
def test_range_selector():
    variations = load_variations("items.yaml")
    selected = resolve("{ITEMS[range:5-10]}", {"ITEMS": variations})
    assert len(selected) == 6  # 5,6,7,8,9,10
```

### Test 4 : Random
```python
def test_random_selector():
    variations = load_variations("expressions.yaml")  # 100 expressions
    selected = resolve("{EXPRESSIONS[random:10]}", {"EXPRESSIONS": variations})
    assert len(selected) == 10
```

### Test 5 : Combinaisons
```python
def test_combined_selectors():
    variations = load_variations("all.yaml")
    selected = resolve(
        "{ALL[happy,5,range:10-15,random:3]}",
        {"ALL": variations}
    )
    # happy + index5 + range(6 items) + random(3) = au moins 10, au plus 11 si pas de doublons
```

### Test 6 : Erreurs
```python
def test_invalid_key():
    with pytest.raises(KeyError):
        resolve("{EXPR[unknown]}", {"EXPR": variations})

def test_invalid_range():
    with pytest.raises(ValueError):
        resolve("{EXPR[range:10-5]}", {"EXPR": variations})
```

## Performance

### Optimisations
- **Lazy loading** : Ne charger que les variations sélectionnées si possible
- **Caching** : Cache les fichiers de variations parsés
- **Index** : Créer un index clé→variation pour O(1) lookup

### Benchmarks attendus
- Parse de sélecteur : < 1ms
- Résolution de 100 variations : < 10ms
- Chargement de fichier (avec cache) : < 5ms

## Documentation auto-générée

```bash
sdgen docs variations variations/expressions.yaml
```

**Sortie :**
```markdown
# Facial Expressions Variations

**File:** variations/expressions.yaml
**Total variations:** 50

## Available keys
- happy: "smiling, cheerful"
- sad: "crying, tears"
- angry: "frowning, intense"
...

## Usage examples

Select by key:
\`{EXPRESSIONS[happy,sad]}\`

Select by index:
\`{EXPRESSIONS[1,5,10]}\`

Select range:
\`{EXPRESSIONS[range:1-10]}\`

Random selection:
\`{EXPRESSIONS[random:5]}\`
```

## Migration

### Depuis l'ancien système
```python
# Ancien
"{Expression:15}"  → "{Expression[random:15]}"
"{Expression:#|1|5|22}"  → "{Expression[1,5,22]}"
```

Outil de conversion :
```bash
sdgen migrate-selectors old_prompt.py
```

## Success Criteria

- [ ] Parser tous les types de sélecteurs
- [ ] Résolution correcte avec combinaisons
- [ ] Validation et erreurs claires
- [ ] Support de tous les formats de fichiers
- [ ] Performance acceptable (< 10ms par résolution)
- [ ] Documentation auto-générée
- [ ] Migration depuis ancien système
- [ ] Tests unitaires complets (>90% coverage)
