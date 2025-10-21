# Feature: Multi-field Expansion System

**Status:** future
**Priority:** 7
**Depends on:** Advanced Variation Selectors, Character Templates

## Description

Système permettant à un fichier de variations de définir plusieurs champs qui s'étendent ensemble de manière cohérente. Une seule sélection peut affecter multiple champs du character ou du prompt.

## Motivation

### Problème
Certaines caractéristiques sont liées et doivent varier ensemble :
- **Ethnicité** → affecte skin tone, facial features, eyes
- **Outfit** → affecte top, bottom, accessories
- **Weather** → affecte lighting, atmosphere, details

### Sans multi-field
```yaml
# Incohérent : african + pale skin !
ethnicity: "(African:1.3)"
skin_tone: "(pale skin:0.2)"  # Oups, pas changé
```

Il faut :
1. Changer manuellement chaque champ lié
2. Maintenir la cohérence manuellement
3. Risque d'incohérences

### Avec multi-field
```yaml
# ethnicities.yaml
variations:
  - key: african
    ethnicity: "(African:1.3)"
    skin_tone: "(black skin:1.3)"
    typical_features: "full lips, wide nose"

# Prompt
{CHARACTER with ethnicity=ETHNICITIES[african]}
```

**Résultat :** Tous les champs liés sont mis à jour automatiquement et de manière cohérente.

## Format des fichiers multi-field

### Structure de base
```yaml
# variations/ethnicities.yaml
version: "1.0"
type: multi_field_variation

metadata:
  name: "Ethnic Variations"
  description: "Complete ethnic characteristics with coherent features"
  fields_affected: [ethnicity, skin_tone, typical_features]

variations:
  - key: african
    ethnicity: "(African:1.3)"
    skin_tone: "(black skin:1.3)"
    typical_features: "full lips, wide nose"

  - key: asian
    ethnicity: "(Asian:1.2)"
    skin_tone: "(pale skin)"
    typical_features: "almond eyes, straight black hair"

  - key: caucasian
    ethnicity: "caucasian"
    skin_tone: "(pale skin:0.2)"
    typical_features: "varied features"

  - key: latina
    ethnicity: "(cuban venezuelan latina)"
    skin_tone: "(dark brown skin:1.3)"
    typical_features: "warm skin, expressive eyes"
```

### Format avec champs optionnels
```yaml
# variations/outfits.yaml
variations:
  - key: summer_casual
    top: "tank top"
    bottom: "denim shorts"
    shoes: "sandals"
    accessories: "sunglasses"  # Optionnel

  - key: formal
    top: "white blouse"
    bottom: "pencil skirt"
    shoes: "high heels"
    # accessories non défini = pas rendu

  - key: swimwear
    outfit: "bikini"  # Single field quand tout est une pièce
    accessories: "beach hat"
```

### Format avec poids/probabilités
```yaml
# variations/lighting.yaml
variations:
  - key: dramatic
    weight: 1.0  # Poids normal
    type: "dramatic lighting"
    intensity: "high contrast"
    direction: "side lighting"

  - key: soft
    weight: 2.0  # 2x plus probable en random
    type: "soft lighting"
    intensity: "low contrast"
    direction: "diffused"

  - key: golden_hour
    weight: 1.5
    type: "golden hour lighting"
    intensity: "warm, glowing"
    direction: "backlit"
```

## Utilisation

### Dans character override
```yaml
imports:
  CHARACTER: characters/athlete_portrait.char.yaml
  ETHNICITIES: variations/ethnicities.yaml

prompt: |
  {CHARACTER with ethnicity=ETHNICITIES[african]}
```

**Expansion :**
1. Charge `ETHNICITIES[african]`
2. Trouve : `{ethnicity: "...", skin_tone: "...", typical_features: "..."}`
3. Override tous ces champs dans CHARACTER
4. Render

**Résultat :**
```
(African:1.3), (black skin:1.3), full lips, wide nose,
[autres champs de athlete_portrait.char.yaml inchangés]
```

### Dans prompt direct
```yaml
imports:
  OUTFITS: variations/outfits.yaml

prompt: |
  1girl, {OUTFITS[summer_casual]}, beach background
```

**Expansion :**
```
1girl, tank top, denim shorts, sandals, sunglasses, beach background
```

### Accès aux champs individuels
```yaml
imports:
  WEATHER: variations/weather.yaml

prompt: |
  landscape, {WEATHER[stormy].type}, {WEATHER[stormy].intensity},
  dramatic sky
```

**Résultat :**
```
landscape, storm clouds, heavy rain, dramatic sky
```

## Règles d'expansion

### 1. Expansion automatique complète
```yaml
# Fichier définit : ethnicity, skin_tone, features
{CHARACTER with ethnicity=ETHNICITIES[african]}
```

**Résultat :** Tous les champs (ethnicity, skin_tone, features) sont étendus.

### 2. Override inline prioritaire
```yaml
{CHARACTER with
  ethnicity=ETHNICITIES[african],
  skin_tone="(red skin:1.2)"  # Override
}
```

**Résultat :**
- `ethnicity`: depuis ETHNICITIES[african]
- `skin_tone`: "(red skin:1.2)" (inline gagne)
- `features`: depuis ETHNICITIES[african]

### 3. Champs manquants
```yaml
# outfits.yaml variation "formal" ne définit pas accessories
{OUTFIT[formal]}
```

**Résultat :** Champs `accessories` n'est pas rendu (skip).

### 4. Champs en conflit

**Priorité (de la plus haute à la plus basse) :**
1. Override inline dans `with`
2. Valeurs multi-field expansion
3. Valeurs du character de base
4. Valeurs par défaut du template

**Exemple :**
```yaml
# Template : skin_tone.default = "normal skin"
# Character : skin_tone = "pale skin"
# Multi-field : skin_tone = "(black skin:1.3)"
# Inline : skin_tone = "(red skin)"
# → Résultat : "(red skin)"
```

### 5. Expansion partielle
```yaml
# Sélectionne seulement certains champs
{CHARACTER with
  ethnicity=ETHNICITIES[african].ethnicity,
  eyes=ETHNICITIES[asian].eyes
}
```

Mix de champs de différentes variations (pour créations hybrides).

## Validation

### Au chargement
```python
def validate_multifield_variation(variation: dict, template: CharacterTemplate):
    """Valide qu'une variation multi-field est cohérente"""

    # Vérifie que les champs définis existent dans le template
    for field in variation.keys():
        if field not in ['key', 'weight', 'metadata']:
            if not template.has_field(field):
                raise ValidationError(
                    f"Field '{field}' in variation '{variation['key']}' "
                    f"not defined in template"
                )

    # Warning si variation n'affecte qu'un seul champ
    affected_fields = [k for k in variation.keys()
                       if k not in ['key', 'weight', 'metadata']]
    if len(affected_fields) == 1:
        warnings.warn(
            f"Variation '{variation['key']}' only affects one field. "
            f"Consider using single-field variation instead."
        )
```

### Erreurs possibles

**Champ inexistant :**
```yaml
# Character template ne définit pas 'unknown_field'
variations:
  - key: test
    ethnicity: "asian"
    unknown_field: "value"
```
**Erreur :** `Field 'unknown_field' not defined in character template`

**Conflit de types :**
```yaml
# Template définit 'age' comme text
variations:
  - key: test
    age: 25  # Number au lieu de text
```
**Warning :** `Field 'age' expected type 'text', got 'int'`

## Exemples avancés

### Exemple 1 : Ethnicités complètes
```yaml
# variations/ethnicities_complete.yaml
variations:
  - key: west_african
    ethnicity: "(West African:1.3), Nigerian"
    skin_tone: "(dark brown skin:1.4), ebony"
    eyes: "dark brown eyes"
    hair: "black afro hair, kinky texture"
    facial_features: "full lips, wide nose, high cheekbones"
    body_type: "curvy, athletic"

  - key: east_asian
    ethnicity: "(Japanese:1.2), East Asian"
    skin_tone: "(pale skin), porcelain"
    eyes: "(almond eyes), dark brown eyes"
    hair: "straight black hair, silky"
    facial_features: "small nose, defined jawline"
    body_type: "petite, slender"

  - key: scandinavian
    ethnicity: "Swedish, Nordic"
    skin_tone: "(very pale skin:1.2), fair"
    eyes: "(blue eyes:1.3), light eyes"
    hair: "blonde hair, fine texture"
    facial_features: "sharp features, high nose bridge"
    body_type: "tall, athletic"
```

### Exemple 2 : Outfits complets
```yaml
# variations/complete_outfits.yaml
variations:
  - key: beach_day
    top: "striped bikini top"
    bottom: "bikini bottoms"
    outerwear: "sheer beach cover-up"
    accessories: "sunglasses, beach hat, flip-flops"
    setting_hint: "beach, sunny day"

  - key: office_professional
    top: "white silk blouse"
    bottom: "grey pencil skirt"
    outerwear: "black blazer"
    accessories: "pearl earrings, watch, leather bag"
    footwear: "black high heels"
    setting_hint: "office, professional"

  - key: winter_cozy
    top: "thick wool sweater"
    bottom: "dark jeans"
    outerwear: "long coat, scarf"
    accessories: "beanie, gloves"
    footwear: "winter boots"
    setting_hint: "winter, cold weather, snow"
```

### Exemple 3 : Lighting setups
```yaml
# variations/lighting_setups.yaml
variations:
  - key: golden_hour_portrait
    time: "golden hour"
    direction: "backlit, rim lighting"
    intensity: "soft, warm"
    color_temp: "warm tones, orange glow"
    atmosphere: "dreamy, romantic"
    shadows: "long shadows, soft"

  - key: studio_dramatic
    time: "studio"
    direction: "side lighting, Rembrandt lighting"
    intensity: "high contrast"
    color_temp: "neutral, cool"
    atmosphere: "dramatic, moody"
    shadows: "deep shadows, sharp"

  - key: overcast_natural
    time: "daytime, overcast"
    direction: "diffused, ambient"
    intensity: "low contrast, even"
    color_temp: "cool, neutral"
    atmosphere: "soft, natural"
    shadows: "minimal shadows"
```

## Nested access (aperçu)

*Cette feature sera détaillée dans 04-nested-variations.md*

Aperçu de la syntaxe :
```yaml
# outfit référence accessories
variations:
  - key: summer
    top: "tank top"
    accessories: ACCESSORIES[beach]  # Référence imbriquée
```

## Weighted random selection

Lorsque `random` est utilisé, les poids influencent la probabilité.

```yaml
variations:
  - key: common
    weight: 2.0
    field: "value"

  - key: rare
    weight: 0.5
    field: "special value"
```

**Probabilités :**
- common: 2.0 / (2.0 + 0.5) = 80%
- rare: 0.5 / (2.0 + 0.5) = 20%

**Usage :**
```yaml
{ITEMS[random:10]}  # Utilise les poids pour la sélection
```

## Performance

### Optimisations
- **Lazy expansion** : N'étendre que les champs utilisés
- **Caching** : Cache les variations expandues
- **Index** : Index par clé pour O(1) lookup

### Benchmarks attendus
- Expansion d'une variation multi-field (5 champs) : < 1ms
- Résolution avec 100 variations : < 20ms

## Tests

### Test 1 : Expansion complète
```python
def test_multifield_expansion():
    ethnicities = load_variations("ethnicities.yaml")
    african = ethnicities.get("african")

    result = expand_multifield(african)
    assert result["ethnicity"] == "(African:1.3)"
    assert result["skin_tone"] == "(black skin:1.3)"
    assert result["typical_features"] == "full lips, wide nose"
```

### Test 2 : Override inline
```python
def test_inline_override():
    char = load_character("athlete_portrait.char.yaml")
    ethnicities = load_variations("ethnicities.yaml")

    char.override_with_multifield(
        ethnicities.get("african"),
        inline_overrides={"skin_tone": "(red skin:1.2)"}
    )

    assert char.get("ethnicity") == "(African:1.3)"
    assert char.get("skin_tone") == "(red skin:1.2)"  # Override
```

### Test 3 : Champs optionnels
```python
def test_optional_fields():
    outfits = load_variations("outfits.yaml")
    formal = outfits.get("formal")

    result = expand_multifield(formal)
    assert "top" in result
    assert "bottom" in result
    assert "accessories" not in result  # Optionnel, non défini
```

### Test 4 : Validation
```python
def test_invalid_field():
    with pytest.raises(ValidationError):
        variation = {
            "key": "test",
            "unknown_field": "value"
        }
        validate_multifield_variation(variation, template)
```

### Test 5 : Weighted random
```python
def test_weighted_random():
    variations = load_variations("weighted.yaml")
    # variation1: weight 2.0, variation2: weight 0.5

    results = []
    for _ in range(1000):
        selected = variations.select_random(1)
        results.append(selected[0].key)

    # variation1 devrait apparaître ~80% du temps
    count1 = results.count("variation1")
    assert 750 < count1 < 850  # ~80% avec marge
```

## Documentation auto-générée

```bash
sdgen docs variations variations/ethnicities.yaml
```

**Sortie :**
```markdown
# Ethnic Variations

**Type:** Multi-field variation
**Fields affected:** ethnicity, skin_tone, typical_features

## Variations

### african
- **ethnicity:** (African:1.3)
- **skin_tone:** (black skin:1.3)
- **typical_features:** full lips, wide nose

### asian
- **ethnicity:** (Asian:1.2)
- **skin_tone:** (pale skin)
- **typical_features:** almond eyes, straight black hair

## Usage

Complete expansion:
\`{CHARACTER with ethnicity=ETHNICITIES[african]}\`

Partial expansion:
\`{CHARACTER with ethnicity=ETHNICITIES[african].ethnicity}\`

Multiple variations:
\`{CHARACTER with ethnicity=ETHNICITIES[african,asian]}\`
```

## Success Criteria

- [ ] Charger fichier multi-field variation
- [ ] Expansion complète de tous les champs
- [ ] Override inline prioritaire
- [ ] Champs optionnels gérés correctement
- [ ] Validation des champs vs template
- [ ] Weighted random selection
- [ ] Partial field access (`.field`)
- [ ] Documentation auto-générée
- [ ] Performance acceptable (< 1ms/expansion)
- [ ] Tests complets (>90% coverage)
