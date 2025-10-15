# Wizard UX - Interactive Prompt Creation

**Status:** future
**Priority:** 7
**Component:** cli
**Created:** 2025-10-08
**Depends on:** Phase 2 Character Templates (in progress)

## Description

Interface wizard interactive pour créer rapidement de nouveaux fichiers `.prompt.yaml` en réutilisant des templates, chunks et variations existants. Élimine le besoin de copier/modifier manuellement des prompts existants.

## Motivation

**Problème actuel :**
- L'utilisateur copie un fichier `.prompt.yaml` existant
- Modifie manuellement les imports, le prompt, les variations
- Perd du temps à retrouver les bons fichiers de variations
- Risque d'erreurs de syntaxe YAML
- Difficile de découvrir quels chunks/variations sont disponibles

**Avec le wizard :**
```bash
sdgen wizard
# 🧙 Interface interactive guide l'utilisateur
# ✅ Génère un .prompt.yaml valide en 30 secondes
# 📁 Découvre automatiquement chunks/variations disponibles
# 🎯 Prévisualise les combinaisons avant génération
```

## User Stories

### US1: Création rapide de prompt depuis un template
```
En tant qu'utilisateur,
Je veux créer un nouveau prompt en choisissant un template de base,
Pour ne pas partir de zéro à chaque fois.
```

### US2: Sélection interactive de variations
```
En tant qu'utilisateur,
Je veux voir la liste des variations disponibles avec leur nombre d'options,
Pour décider rapidement lesquelles tester.
```

### US3: Prévisualisation des combinaisons
```
En tant qu'utilisateur,
Je veux voir combien de combinaisons seront générées,
Pour éviter de lancer 10000 images par erreur.
```

### US4: Sauvegarde et lancement immédiat
```
En tant qu'utilisateur,
Je veux pouvoir lancer la génération immédiatement après création,
Pour tester rapidement mon prompt.
```

## Implementation

### Architecture

```
CLI/src/wizard/
├── __init__.py
├── wizard.py           # Main wizard orchestrator
├── prompts.py          # Prompt builder
├── discovery.py        # Auto-discover chunks/variations
└── preview.py          # Preview combinations

CLI/template_cli_typer.py
└── @app.command("wizard")  # Entry point
```

### Flow du Wizard

```
┌─────────────────────────────────────────┐
│ 1. Nom du prompt                        │
│    > emma_beach_photoshoot              │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 2. Template de base (optionnel)         │
│    [ ] portrait_standard                │
│    [ ] landscape_scenic                 │
│    [ ] concept_art                      │
│    [x] None (start from scratch)        │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 3. Character/Chunk (optionnel)          │
│    Discovered chunks:                   │
│    [x] emma.chunk.yaml                  │
│    [ ] athlete.chunk.yaml               │
│    [ ] None                             │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 4. Variations à inclure                 │
│    Discovered variations:               │
│    [x] ethnicity (3 options)            │
│    [x] poses (10 options)               │
│    [ ] lighting (5 options)             │
│    [ ] weather (4 options)              │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 5. Configuration génération             │
│    Mode: [combinatorial / random]       │
│    Seed mode: [progressive / fixed]     │
│    Seed: 42                             │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 6. Preview                              │
│    Prompt: emma_beach_photoshoot        │
│    Character: Emma (23yo, athletic)     │
│    Variations: 3 ethnicity × 10 poses   │
│    = 30 combinations                    │
│                                         │
│    Generated prompt preview:            │
│    "masterpiece, Emma, 23 years old,    │
│     athletic build, {ethnicity},        │
│     {pose}, beach background"           │
│                                         │
│    Continue? [Y/n]                      │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 7. Save & Launch                        │
│    ✅ Saved to: emma_beach.prompt.yaml  │
│                                         │
│    Launch generation now? [Y/n]         │
└─────────────────────────────────────────┘
```

### Discovery System

**Auto-découverte des ressources disponibles :**

```python
def discover_resources(configs_dir: Path) -> Resources:
    """
    Scan configs_dir for available templates, chunks, and variations.

    Returns:
        Resources object with:
        - templates: List[PromptTemplate]
        - chunks: List[ChunkInfo]
        - variations: Dict[str, VariationInfo]
    """
    resources = Resources()

    # Find all .chunk.yaml files
    for chunk_file in configs_dir.rglob("*.chunk.yaml"):
        chunk = load_chunk(chunk_file)
        resources.chunks.append(ChunkInfo(
            name=chunk.name,
            path=chunk_file,
            fields=list(chunk.fields.keys()),
            description=chunk.metadata.get('description', '')
        ))

    # Find all variation files
    for var_file in configs_dir.rglob("variations/*.yaml"):
        variations = load_variations(var_file)
        resources.variations[var_file.stem] = VariationInfo(
            name=var_file.stem,
            path=var_file,
            count=len(variations),
            type='multi_field' if is_multi_field_variation(var_file) else 'simple'
        )

    return resources
```

### Interactive Prompt Builder

```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

def run_wizard(configs_dir: Path, output_dir: Path):
    """Run interactive wizard to create a new prompt."""

    # 1. Name
    name = inquirer.text(
        message="Prompt name:",
        validate=lambda x: len(x) > 0,
        default="my_prompt"
    ).execute()

    # 2. Discover resources
    resources = discover_resources(configs_dir)

    # 3. Select template (optional)
    template_choices = [Choice(None, "None (start from scratch)")]
    template_choices.extend([
        Choice(t, f"{t.name} - {t.description}")
        for t in resources.templates
    ])
    template = inquirer.select(
        message="Base template:",
        choices=template_choices
    ).execute()

    # 4. Select chunk (optional)
    chunk_choices = [Choice(None, "None")]
    chunk_choices.extend([
        Choice(c, f"{c.name} ({len(c.fields)} fields)")
        for c in resources.chunks
    ])
    chunk = inquirer.select(
        message="Character/Chunk:",
        choices=chunk_choices
    ).execute()

    # 5. Select variations (multi-select)
    var_choices = [
        Choice(v, f"{v.name} ({v.count} options, {v.type})")
        for v in resources.variations.values()
    ]
    variations = inquirer.checkbox(
        message="Variations to include:",
        choices=var_choices
    ).execute()

    # 6. Generation config
    gen_mode = inquirer.select(
        message="Generation mode:",
        choices=["combinatorial", "random"]
    ).execute()

    seed_mode = inquirer.select(
        message="Seed mode:",
        choices=["progressive", "fixed", "random"]
    ).execute()

    seed = inquirer.number(
        message="Base seed:",
        default=42,
        validate=lambda x: x >= 0
    ).execute()

    # 7. Preview
    preview = build_preview(name, template, chunk, variations, gen_mode)
    print("\n" + "="*50)
    print("PREVIEW")
    print("="*50)
    print(preview)

    confirm = inquirer.confirm(
        message="Create this prompt?",
        default=True
    ).execute()

    if not confirm:
        print("Cancelled.")
        return

    # 8. Generate YAML
    prompt_yaml = build_prompt_yaml(
        name, template, chunk, variations, gen_mode, seed_mode, seed
    )

    # 9. Save
    output_path = configs_dir / f"{name}.prompt.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(prompt_yaml, f, sort_keys=False)

    print(f"✅ Saved to: {output_path}")

    # 10. Launch now?
    launch = inquirer.confirm(
        message="Launch generation now?",
        default=True
    ).execute()

    if launch:
        from .execution.orchestrator import Orchestrator
        orchestrator = Orchestrator(output_path, output_dir)
        orchestrator.run()
```

## Tasks

- [ ] Installer `InquirerPy` (librairie interactive moderne pour Python)
- [ ] Implémenter `discovery.py` - Auto-découverte des chunks/variations
- [ ] Implémenter `preview.py` - Prévisualisation des combinaisons
- [ ] Implémenter `prompts.py` - Builder de fichier .prompt.yaml
- [ ] Implémenter `wizard.py` - Orchestrateur principal
- [ ] Ajouter commande `sdgen wizard` dans template_cli_typer.py
- [ ] Tests unitaires pour discovery/preview/builder
- [ ] Test d'intégration end-to-end du wizard
- [ ] Documentation usage dans `docs/cli/usage/wizard.md`

## Success Criteria

- [ ] `sdgen wizard` lance l'interface interactive
- [ ] Découvre automatiquement tous les chunks/variations dans configs_dir
- [ ] Génère un fichier .prompt.yaml syntaxiquement valide
- [ ] Preview affiche le nombre exact de combinaisons
- [ ] Peut lancer la génération immédiatement après création
- [ ] Tests couvrent les cas d'usage principaux
- [ ] Documentation avec screenshots/exemples

## Dependencies

**Librairies Python :**
- `InquirerPy` - Interface interactive moderne (remplace `inquirer`)
  ```bash
  pip install InquirerPy
  ```

**Features requises :**
- ✅ Phase 1 templating (done)
- 🔄 Phase 2 character templates (in progress)
- Optional: Phase 3 nested variations (future)

## User Experience Examples

### Exemple 1: Création rapide avec defaults

```bash
$ sdgen wizard

? Prompt name: test_emma
? Base template: None (start from scratch)
? Character/Chunk: emma.chunk.yaml
? Variations to include:
  ❯ ◉ ethnicity (3 options, multi_field)
    ◉ poses (10 options, simple)
? Generation mode: combinatorial
? Seed mode: progressive
? Base seed: 42

========================================
PREVIEW
========================================
Prompt: test_emma
Character: Emma (23yo, athletic build)
Variations: 3 × 10 = 30 combinations
Mode: combinatorial, progressive seeds

Generated prompt preview:
  masterpiece, best quality
  {CHARACTER}, {ETHNICITY}, {POSE}

? Create this prompt? Yes
✅ Saved to: /configs/test_emma.prompt.yaml

? Launch generation now? Yes
[Génération lance...]
```

### Exemple 2: Découverte interactive

```bash
$ sdgen wizard

? Prompt name: landscape_test
? Base template: landscape_scenic.template.yaml
? Character/Chunk: None
? Variations to include:
  ❯ ◉ weather (4 options)
    ◉ time_of_day (6 options)
    ◯ season (4 options)
    ◯ lighting_mood (8 options)

4 × 6 = 24 combinations

? Generation mode: random
? How many images: 10
? Seed mode: random

✅ Will generate 10 random combinations
```

## Future Enhancements

**Phase 1 (MVP):**
- Discovery basique (chunks, variations)
- Sélection interactive
- Preview simple
- Génération YAML

**Phase 2:**
- Templates wizard (templates de wizards pour différents use cases)
- Édition inline de variations
- Preview avec rendu du premier prompt
- Historique des prompts créés

**Phase 3:**
- Wizard avancé avec conditions ("if chunk = emma then show ethnicity")
- Validation avancée (détection de conflits)
- Suggestions intelligentes basées sur l'historique
- Export vers d'autres formats (A1111, ComfyUI)

## Documentation

- Usage: `docs/cli/usage/wizard.md` (à créer)
- Technical: `docs/cli/technical/wizard-architecture.md` (à créer)
- Examples: Screenshots dans la doc

## Notes

**Choix de InquirerPy vs inquirer :**
- `InquirerPy` est plus moderne, mieux maintenu
- Support meilleur de Windows/WSL
- Plus de types de questions (fuzzy search, autocomplete)
- API plus simple

**Limitations connues :**
- Pas d'éditeur de prompt inline (utiliser éditeur externe après)
- Pas de preview des images générées (juste le texte)
- Découverte basée sur fichiers seulement (pas de DB)

## Related Issues

- Dépend de: Phase 2 Character Templates (#TODO)
- Bloqué par: Aucun
- Lié à: Interactive Metadata (#TODO future)
