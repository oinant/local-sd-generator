# Feature: Numeric Slider Placeholders

**Status:** next
**Priority:** 4
**Component:** cli
**Created:** 2025-10-01

## Description

Ajouter un type de placeholder spécial pour générer des séquences de valeurs numériques discrètes. Utile pour tester différentes valeurs de LoRA sliders.

## Use Case

Tester un LoRA de type "detail slider" avec différentes intensités:

```json
{
  "prompt": {
    "template": "masterpiece, beautiful girl, <lora:DetailSlider:{DetailLevel}>"
  },
  "variations": {}
}
```

Le placeholder `{DetailLevel:Unit:-1:3}` génèrerait automatiquement les valeurs: `-1, 0, 1, 2, 3`

## Syntax

### Format général
```
{PlaceholderName:Type:Min:Max}
```

### Types supportés

**1. Unit (entiers par pas de 1)**
```
{DetailLevel:Unit:-1:3}
→ [-1, 0, 1, 2, 3]  # 5 valeurs
```

**2. Decimal (décimaux par pas de 1.0)**
```
{Strength:Decimal:-2.5:2.5}
→ [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]  # 6 valeurs
```

**3. Centimal (centièmes par pas de 0.1)**
```
{Fine:Centimal:-1.26:3.57}
→ [-1.26, -1.16, -1.06, ..., 3.47, 3.57]  # 49 valeurs
```

**4. Step (custom step) - BONUS**
```
{Weight:Step:-2:2:0.25}
→ [-2.0, -1.75, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]  # 17 valeurs
```

## Current Behavior

Les placeholders ne peuvent référencer que des fichiers de variations texte.

## Expected Behavior

1. Détecter placeholders de type numérique avec syntaxe `:Type:Min:Max`
2. Générer automatiquement les valeurs discrètes
3. Ces valeurs participent aux combinaisons comme les variations normales
4. Support de tous les sélecteurs: `{Detail:Unit:-1:3:#|0|2}` → [-1, 1] seulement

## Implementation

### 1. Parse Numeric Placeholders

Extension de `extract_placeholders_with_limits()` dans `variation_loader.py`:

```python
def parse_placeholder_options(placeholder_text: str) -> dict:
    """
    Parse: {Name:Unit:-1:3:#|1|2$5}

    Returns: {
        'name': 'Name',
        'type': 'numeric',
        'numeric_type': 'unit',
        'min': -1,
        'max': 3,
        'selected_indices': [1, 2],
        'priority': 5
    }
    """
    # Patterns:
    # {Name:Unit:min:max}
    # {Name:Decimal:min:max}
    # {Name:Centimal:min:max}
    # {Name:Step:min:max:step}

    pattern = r'\{([^}:]+):(?:(Unit|Decimal|Centimal|Step):([^:}]+):([^:}]+)(?::([^:}]+))?)?([#$:].*?)?\}'
```

### 2. Generate Numeric Variations

Nouvelle fonction dans `variation_loader.py`:

```python
def generate_numeric_variations(numeric_type: str, min_val: float, max_val: float,
                                step: float = None) -> Dict[str, str]:
    """
    Génère les variations numériques.

    Returns: {'0': '-1.0', '1': '0.0', '2': '1.0', ...}
    """
    if numeric_type == "Unit":
        step = 1.0
        values = range(int(min_val), int(max_val) + 1)
    elif numeric_type == "Decimal":
        step = 1.0
        values = [min_val + i * step for i in range(int((max_val - min_val) / step) + 1)]
    elif numeric_type == "Centimal":
        step = 0.1
        values = [round(min_val + i * step, 2) for i in range(int((max_val - min_val) / step) + 1)]
    elif numeric_type == "Step":
        values = [round(min_val + i * step, 3) for i in range(int((max_val - min_val) / step) + 1)]

    return {str(i): str(v) for i, v in enumerate(values)}
```

### 3. Integration

Dans `load_variations_for_placeholders()`:

```python
def load_variations_for_placeholders(prompt_template, variation_files, verbose=False):
    placeholders_with_options = extract_placeholders_with_limits(prompt_template)

    variations = {}

    for placeholder_name, options in placeholders_with_options.items():
        if options.get('type') == 'numeric':
            # Générer variations numériques
            variations[placeholder_name] = generate_numeric_variations(
                options['numeric_type'],
                options['min'],
                options['max'],
                options.get('step')
            )
        else:
            # Charger depuis fichier (comportement existant)
            file_path = variation_files.get(placeholder_name)
            variations[placeholder_name] = load_variations_from_file(file_path)

    return variations
```

### 4. Clean Template

Le template doit être nettoyé pour enlever les specs numériques:

```python
# {DetailLevel:Unit:-1:3} → {DetailLevel}
clean_template = re.sub(
    r'\{([^}:]+):(?:Unit|Decimal|Centimal|Step):[^}]+\}',
    r'{\1}',
    template
)
```

## Examples

### Example 1: Single LoRA testing
```json
{
  "prompt": {
    "template": "girl, <lora:DetailSlider:{Detail:Unit:-2:2}>"
  }
}
```
Génère 5 images avec detail = -2, -1, 0, 1, 2

### Example 2: Multiple LoRA testing
```json
{
  "prompt": {
    "template": "girl, <lora:DetailSlider:{Detail:Unit:-1:1}> <lora:ColorSlider:{Color:Decimal:-1.5:1.5}>"
  }
}
```
Génère 3×4 = 12 images avec toutes combinaisons

### Example 3: With selection
```json
{
  "prompt": {
    "template": "girl, <lora:DetailSlider:{Detail:Unit:-2:2:#|0|4}>"
  }
}
```
Génère seulement 2 images avec detail = -2 et 2 (indices 0 et 4)

### Example 4: Combined with file variations
```json
{
  "prompt": {
    "template": "{Expression}, <lora:DetailSlider:{Detail:Unit:-1:1}>"
  },
  "variations": {
    "Expression": "./expressions.txt"
  }
}
```
Combinaisons: chaque expression × chaque niveau de detail

## Tasks

- [ ] Parser les placeholders numériques (Unit/Decimal/Centimal/Step)
- [ ] Fonction `generate_numeric_variations()`
- [ ] Intégrer dans `load_variations_for_placeholders()`
- [ ] Nettoyer le template (enlever specs numériques)
- [ ] Support sélecteurs avec numériques (#|, :N, $X)
- [ ] Tests: génération Unit
- [ ] Tests: génération Decimal
- [ ] Tests: génération Centimal
- [ ] Tests: génération Step
- [ ] Tests: combinaisons numeric + file variations
- [ ] Tests: sélecteurs sur numeric
- [ ] Documentation: exemples LoRA testing

## Success Criteria

- ✓ Les 4 types numériques fonctionnent (Unit/Decimal/Centimal/Step)
- ✓ Génération correcte des valeurs discrètes
- ✓ Sélecteurs fonctionnent sur valeurs numériques
- ✓ Combinaisons avec variations fichier fonctionnent
- ✓ Métadonnées contiennent les valeurs numériques
- ✓ Noms de fichiers incluent valeurs numériques si dans filename_keys
- ✓ Tests passent

## Documentation

- Usage: `docs/cli/usage/numeric-placeholders.md` (à créer)
- Technical: `docs/cli/technical/placeholder-system.md` (à mettre à jour)

## Notes

- Valeurs arrondies pour éviter erreurs float (0.1 + 0.1 + 0.1 ≠ 0.3)
- Format dans fichier output: "Detail=-1.0" ou "Detail_-1.0"
- Caractère spécial `-` dans filename → remplacer par "m" ou "minus"?
  - Exemple: `Detail_m1` au lieu de `Detail_-1`
