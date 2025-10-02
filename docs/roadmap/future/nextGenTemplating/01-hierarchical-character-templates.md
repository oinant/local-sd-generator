# Feature: Hierarchical Character Templates

**Status:** future
**Priority:** 6
**Depends on:** YAML loader, Template parser

## Description

Système permettant de définir des templates de personnages réutilisables avec implémentation et overrides. Un template définit la structure de sortie et les champs disponibles, tandis qu'une implémentation fournit les valeurs concrètes.

## Motivation

### Problème actuel
Pour générer des variations d'un personnage (un athlète avec différents sports, un musicien avec différents styles), il faut :
1. Dupliquer tout le prompt
2. Modifier manuellement les variations
3. Maintenir la cohérence entre fichiers
4. Pas de réutilisation possible

### Avec ce système
```yaml
# athlete_portrait.char.yaml
implements: portrait_subject.char.template.yaml
values:
  eyes: "focused eyes, determined gaze"
  height: "tall, athletic build"
  body_type: "muscular, athletic"
  # ethnicity varie selon le prompt
```

## Format des fichiers

### Character Template (`.char.template.yaml`)

Définit la structure de sortie et les champs disponibles.

**`templates/portrait_subject.char.template.yaml`**
```yaml
version: "1.0"
type: character_template
name: "Portrait Subject Template"
description: "Template for portrait subject definition"

# Définit comment assembler les champs en prompt
output: |
  {ethnicity}, {skin_tone},
  {eyes},
  {hair_style}, {hair_color},
  {facial_hair},
  {age}, {body_type}, {height},
  {distinctive_features},
  {clothing_style},
  {expression}

# Définit les champs disponibles
fields:
  ethnicity:
    type: text
    description: "Ethnic characteristics"
    example: "ginger, (pale skin:0.2)"

  skin_tone:
    type: text
    description: "Skin color and tone"
    example: "(pale skin:0.2)"

  eyes:
    type: text
    description: "Eye characteristics"
    example: "(blue eyes:0.3)"

  hair_style:
    type: text
    description: "Hair style"
    example: "bob hair"

  hair_color:
    type: text
    description: "Hair color"
    example: "blonde"

  facial_hair:
    type: text
    description: "Facial hair if any"
    example: "clean shaven, full beard, goatee"

  age:
    type: text
    description: "Age descriptor"
    example: "young adult, middle-aged, 25 year old"
    required: true  # Ce champ doit toujours être défini

  body_type:
    type: text
    description: "Body type"
    example: "athletic, average, muscular, slender"

  height:
    type: text
    description: "Height descriptor"
    example: "short, tall"

  distinctive_features:
    type: text
    description: "Distinguishing physical characteristics"
    example: "scar across eyebrow, tattoo on forearm, freckles"

  skin_details:
    type: text
    description: "Skin texture and details"
    example: "realistic skin, weathered skin, smooth complexion"
    default: "realistic skin"  # Valeur par défaut

  clothing_style:
    type: text
    description: "Clothing and outfit"
    example: "leather jacket, sports jersey, casual wear"

  expression:
    type: text
    description: "Facial expression"
    example: "determined, focused, relaxed, intense"

# Métadonnées
metadata:
  compatible_models: [SDXL, Pony, SD1.5]
  tags: [portrait, character, realistic]
  author: "..."
  version: "1.0"
```

### Character Implementation (`.char.yaml`)

Implémente un template avec des valeurs concrètes.

**`characters/athlete_portrait.char.yaml`**
```yaml
version: "1.0"
type: character
name: "Professional Athlete"
implements: templates/portrait_subject.char.template.yaml

# Valeurs fixes pour ce portrait
values:
  ethnicity: "caucasian"
  skin_tone: "tanned skin"
  eyes: "focused eyes, determined gaze"
  hair_style: "short athletic cut"
  hair_color: "dark brown"
  facial_hair: "clean shaven"
  age: "25 year old"
  body_type: "athletic, muscular"
  height: "tall"
  distinctive_features: "defined jawline, athletic build"
  skin_details: "realistic skin"
  clothing_style: "sports jersey, athletic wear"
  expression: "determined, focused"

metadata:
  description: "Professional athlete portrait for sports photography"
  tags: [athlete, sports, portrait, dynamic]
```

**`characters/random_portrait.char.yaml`**
```yaml
version: "1.0"
type: character
name: "Random Girl"
implements: templates/portrait_subject.char.template.yaml

# Valeurs avec variations
values:
  ethnicity:
    vary: variations/ethnicities.yaml  # Varie selon le fichier
  eyes:
    vary: variations/eye_colors.yaml
  hair_style:
    vary: variations/hair_styles.yaml
  age: "young"  # Fixe
  height:
    vary: [short, average, tall]  # Variations inline
  breasts:
    vary: variations/breast_types.yaml
  skin_details: "real skin, face freckles"
  # Autres champs vides = non rendus

metadata:
  description: "Randomized girl with varying characteristics"
```

## Utilisation dans les prompts

### Basique
```yaml
# portrait.prompt.yaml
imports:
  CHARACTER: characters/athlete_portrait.char.yaml

prompt: |
  {TECHNIQUE}
  BREAK
  {CHARACTER}
  BREAK
  {POSE}, {ENVIRONMENT}
```

### Avec overrides
```yaml
imports:
  CHARACTER: characters/athlete_portrait.char.yaml
  ETHNICITIES: variations/ethnicities.yaml

prompt: |
  {TECHNIQUE}
  BREAK
  {CHARACTER with ethnicity=ETHNICITIES[african,asian]}
  BREAK
  {POSE}, {ENVIRONMENT}
```

### Accès aux champs individuels
```yaml
prompt: |
  masterpiece, {CHARACTER.eyes}, {CHARACTER.hair_style},
  1girl, {CHARACTER.age}, {CHARACTER.height}
```

## Règles de résolution

### 1. Champs vides
Les champs vides ou non définis ne sont pas rendus dans la sortie.

**Input:**
```yaml
ethnicity: "ginger"
skin_tone: ""
eyes: "(blue eyes)"
hair_style: ""
```

**Output avec nettoyage:**
```
ginger,
(blue eyes),
,
```

**Output après cleanup regex:**
```
ginger, (blue eyes),
```

### 2. Champs requis
Si un champ marqué `required: true` n'est pas défini, erreur de validation.

```yaml
# Erreur : age est requis mais non défini
values:
  ethnicity: "asian"
  # age: manquant !
```

### 3. Valeurs par défaut
Si un champ a un `default` et n'est pas défini, utilise la valeur par défaut.

```yaml
# Template
fields:
  skin_details:
    default: "real skin"

# Character (ne définit pas skin_details)
values:
  ethnicity: "asian"
  # skin_details non défini

# Résultat : utilise "real skin"
```

### 4. Priorité d'override

1. **Override inline dans prompt** (priorité max)
2. **Valeurs dans character file**
3. **Valeurs par défaut du template**

```yaml
# Template : skin_details.default = "real skin"
# Character : skin_details = "face freckles"
# Prompt : {CHARACTER with skin_details="smooth skin"}
# → Résultat : "smooth skin"
```

## Validation

### Au chargement du character
- Vérifie que le template référencé existe
- Vérifie que tous les champs requis sont définis
- Vérifie que les champs définis existent dans le template
- Warning si un champ du template n'est pas utilisé

### Exemple d'erreurs
```yaml
# Erreur : champ inexistant
values:
  unknown_field: "value"
# → Error: Field 'unknown_field' not defined in template 'portrait_subject.char.template.yaml'

# Erreur : champ requis manquant
# age est requis
values:
  ethnicity: "asian"
# → Error: Required field 'age' not defined

# Warning : champ inutilisé
# Template définit 'extras' mais character ne l'utilise pas
# → Warning: Field 'extras' defined in template but not used
```

## Exemples d'utilisation

### Cas 1 : Personnage fixe
```yaml
# sophia.char.yaml
implements: portrait_subject.char.template.yaml
values:
  ethnicity: "(Asian:1.2)"
  eyes: "brown eyes"
  hair_style: "long straight hair"
  age: "young"
  height: "tall"
  breasts: "(medium breasts, perky breasts)"
```

### Cas 2 : Personnage avec quelques variations
```yaml
# emma_flex.char.yaml
implements: portrait_subject.char.template.yaml
values:
  # Fixe
  eyes: "(blue eyes:0.3)"
  age: "young"
  height: "short"

  # Varie
  ethnicity:
    vary: variations/ethnicities.yaml
  hair_style:
    vary: variations/hair_styles.yaml
```

### Cas 3 : Override au runtime
```yaml
# Prompt
{CHARACTER=characters/athlete_portrait.char.yaml with
  ethnicity=ETHNICITIES[african],
  hair_color="(pink hair:1.2)"
}
```

## Tests

### Test 1 : Template valide
```python
def test_valid_template():
    template = load_template("portrait_subject.char.template.yaml")
    assert template.has_field("ethnicity")
    assert template.has_field("age")
    assert template.field("age").required == True
```

### Test 2 : Character valide
```python
def test_valid_character():
    char = load_character("athlete_portrait.char.yaml")
    assert char.template == "portrait_subject.char.template.yaml"
    assert char.get_value("eyes") == "(blue eyes:0.3)"
```

### Test 3 : Validation erreurs
```python
def test_missing_required_field():
    with pytest.raises(ValidationError):
        char = Character(
            implements="portrait_subject.char.template.yaml",
            values={"ethnicity": "asian"}  # age manquant
        )
```

### Test 4 : Override
```python
def test_override():
    char = load_character("athlete_portrait.char.yaml")
    char.override("ethnicity", "african")
    prompt = char.render()
    assert "african" in prompt
    assert "ginger" not in prompt
```

### Test 5 : Cleanup virgules
```python
def test_empty_field_cleanup():
    char = Character(
        values={
            "ethnicity": "asian",
            "skin_tone": "",  # Vide
            "eyes": "brown eyes"
        }
    )
    output = char.render()
    assert ", ," not in output  # Pas de double virgule
```

## Documentation auto-générée

Le système doit pouvoir générer :

```bash
sdgen docs character templates/portrait_subject.char.template.yaml
```

**Sortie:**
```markdown
# Girl Character Template

## Description
Template for female character definition

## Fields

### ethnicity
- **Type:** text
- **Required:** No
- **Description:** Ethnic characteristics
- **Example:** `ginger, (pale skin:0.2)`

### age
- **Type:** text
- **Required:** Yes
- **Description:** Age descriptor
- **Example:** `young, 25 year old`

...

## Characters using this template
- athlete_portrait.char.yaml
- sophia.char.yaml
- random_girl.char.yaml

## Example usage
\`\`\`yaml
{CHARACTER=characters/athlete_portrait.char.yaml}
\`\`\`
```

## Migration

### Depuis l'ancien système
Conversion automatique des prompts existants :

```bash
sdgen convert-to-character \
  --prompt "ginger, (pale skin:0.2), (blue eyes:0.3), ..." \
  --template portrait_subject.char.template.yaml \
  --output athlete_portrait.char.yaml
```

## Implementation notes

### Structures de données
```python
@dataclass
class CharacterTemplate:
    name: str
    output_format: str
    fields: Dict[str, FieldDefinition]
    metadata: Dict

@dataclass
class FieldDefinition:
    name: str
    type: str
    description: str
    required: bool = False
    default: Optional[str] = None
    example: Optional[str] = None

@dataclass
class Character:
    name: str
    template: str  # Path to template
    values: Dict[str, Union[str, VariationRef]]
    metadata: Dict

    def render(self) -> str:
        """Render character to prompt string"""

    def override(self, field: str, value: str):
        """Override a field value"""

    def validate(self):
        """Validate against template"""
```

### Parser l'output format
```python
def parse_output_format(format_str: str) -> List[Token]:
    """
    Parse: "{ethnicity}, {skin_tone},\n{eyes}"
    Returns: [
        Placeholder("ethnicity"),
        Literal(", "),
        Placeholder("skin_tone"),
        Literal(",\n"),
        Placeholder("eyes")
    ]
    """
```

## Success Criteria

- [ ] Charger un template .char.template.yaml
- [ ] Charger un character .char.yaml
- [ ] Valider qu'un character implémente correctement son template
- [ ] Render un character en prompt string
- [ ] Support des champs vides (cleanup)
- [ ] Support des champs requis (validation)
- [ ] Support des valeurs par défaut
- [ ] Override de champs au runtime
- [ ] Documentation auto-générée
- [ ] Tests unitaires complets
