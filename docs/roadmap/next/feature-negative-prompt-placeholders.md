# Feature: Negative Prompt Placeholders

**Status:** next
**Priority:** 3
**Component:** cli
**Created:** 2025-10-01

## Description

Permettre l'utilisation de placeholders dans le negative prompt pour pouvoir varier facilement entre différents styles de negative prompts (SDXL, Illustrious, Pony, etc.).

## Use Case

Actuellement, le negative prompt est statique. Mais différents modèles SD nécessitent des negative prompts différents:

```json
{
  "prompt": {
    "template": "masterpiece, {Subject}, {Style}",
    "negative": "{NegStyle}"
  },
  "variations": {
    "Subject": "./subjects.txt",
    "Style": "./styles.txt",
    "NegStyle": "./negative_styles.txt"
  }
}
```

Fichier `negative_styles.txt`:
```
sdxl→low quality, bad anatomy, blurry, watermark
illustrious→worst quality, low quality, displeasing, very displeasing
pony→3d, worst quality, low quality, bad anatomy, text
none→
```

## Current Behavior

Le negative prompt est une string statique définie dans `prompt.negative`.

## Expected Behavior

1. Le negative prompt peut contenir des placeholders `{PlaceholderName}`
2. Ces placeholders sont résolus comme ceux du prompt principal
3. Les fichiers de variations pour neg prompt suivent le même format (clé→valeur)
4. En mode combinatorial, les variations de negative s'ajoutent aux combinaisons
5. Support de tous les sélecteurs: `{NegStyle:#|1|3}`, `{NegStyle:2}`, etc.

## Implementation

### Changes Required

**1. Config Schema** (`CLI/config/config_schema.py`)
- Le champ `prompt.negative` reste string (peut contenir placeholders)
- Pas de changement structurel

**2. Variation Loader** (`CLI/variation_loader.py`)
- `extract_placeholders()` doit analyser AUSSI le negative prompt
- `load_variations_for_placeholders()` doit accepter le negative en paramètre

**3. Image Variation Generator** (`CLI/image_variation_generator.py`)
- Analyser placeholders dans `self.negative_prompt`
- Charger variations nécessaires pour le negative
- Lors de `_apply_variations_to_prompt()`, appliquer aussi au negative
- Retourner `(prompt, negative_prompt, keys)` au lieu de `(prompt, keys)`

**4. PromptConfig** (`CLI/sdapi_client.py`)
- Déjà supporte `negative_prompt` ✓
- Pas de changement nécessaire

### Example Implementation

```python
# Dans ImageVariationGenerator._create_variations()

# Extraire placeholders du prompt ET negative
prompt_placeholders = extract_placeholders(self.prompt_template)
negative_placeholders = extract_placeholders(self.negative_prompt)
all_placeholders = prompt_placeholders | negative_placeholders

# Charger variations pour tous
variations_dict = load_variations_for_placeholders(
    self.prompt_template,
    self.negative_prompt,  # Nouveau paramètre
    self.variation_files,
    verbose=True
)

# Appliquer variations aux deux
def _apply_variations_to_prompt(self, prompt, negative, combination):
    final_prompt = prompt
    final_negative = negative

    for placeholder, value in combination.items():
        final_prompt = final_prompt.replace(f"{{{placeholder}}}", value)
        final_negative = final_negative.replace(f"{{{placeholder}}}", value)

    # Générer keys pour filename
    keys = [self._format_key(k, v) for k, v in combination.items()
            if k in self.filename_keys]

    return final_prompt, final_negative, keys
```

## Tasks

- [ ] Modifier `extract_placeholders()` pour accepter multiple strings
- [ ] Modifier `load_variations_for_placeholders()` pour negative prompt
- [ ] Modifier `_apply_variations_to_prompt()` pour retourner negative aussi
- [ ] Mettre à jour tous les appels de cette fonction
- [ ] Mettre à jour PromptConfig création avec nouveau negative
- [ ] Tests: negative avec placeholders
- [ ] Tests: negative avec sélecteurs (#|, :N, $X)
- [ ] Tests: combinaisons prompt + negative
- [ ] Documentation: exemples d'usage

## Success Criteria

- ✓ Placeholders dans negative prompt fonctionnent
- ✓ Tous les sélecteurs supportés (#|, :N, $X)
- ✓ Combinaisons incluent variations de negative
- ✓ Fichiers de variations partagés entre prompt et negative
- ✓ Métadonnées sauvent le negative utilisé
- ✓ Tests passent

## Documentation

- Usage: `docs/cli/usage/negative-prompt-variations.md` (à créer)
- Technical: `docs/cli/technical/placeholder-system.md` (à mettre à jour)

## Notes

- Cette feature est orthogonale aux autres (sliders, etc.)
- Peut réutiliser le même fichier de variations pour prompt et negative
- Exemple: `{Style}` dans prompt et `{Style}` dans negative → même valeur
