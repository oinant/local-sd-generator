# Next-Gen Templating System

**Status:** future
**Priority:** 8
**Component:** cli
**Created:** 2025-10-02

## Vision

Système de templating hiérarchique et composable pour la génération de prompts Stable Diffusion, permettant la réutilisation de configurations, l'héritage de caractéristiques, et la variation ciblée de paramètres.

## Problèmes actuels

1. **Duplication de configuration** : Chaque prompt doit définir l'intégralité de sa configuration
2. **Difficultés de maintenance** : Modifier un pattern commun nécessite de toucher plusieurs fichiers
3. **Manque de réutilisabilité** : Impossible de partager des définitions de personnages ou de styles
4. **Variations limitées** : Système de placeholders actuel limité et verbeux
5. **Debugging complexe** : Difficile de comprendre comment un prompt final est construit

## Solution proposée

Un système de templating en YAML avec :

- **Templates hiérarchiques** : Héritage et composition de configurations
- **Sélecteurs de variations avancés** : Syntaxe riche pour sélectionner des variations
- **Expansion multi-champs** : Un placeholder peut étendre plusieurs champs à la fois
- **Variations imbriquées** : Support de références entre fichiers de variations
- **Système d'explication** : Outil de debugging et documentation auto-générée

## Architecture

```
templates/
├── base/
│   ├── portrait_subject.char.template.yaml  # Template de portrait
│   ├── space_marine.char.template.yaml      # Template Warhammer 40K
│   ├── photorealistic_tech.txt              # Bloc technique réutilisable
│   └── styles/
│       └── grimdark.style.yaml              # Style Warhammer
│
├── characters/
│   ├── athlete_portrait.char.yaml           # Portrait sportif
│   ├── musician.char.yaml                   # Portrait musicien
│   ├── ultramarine.char.yaml                # Space Marine Ultramarine
│   └── random_warrior.char.yaml             # Character avec variations
│
├── variations/
│   ├── ethnic_features.yaml                 # Multi-field variations
│   ├── expressions.yaml
│   ├── combat_poses.yaml
│   ├── 40k_chapters.yaml                    # Chapters Space Marines
│   ├── band_equipment.yaml                  # Avec nesting
│   └── environments.yaml
│
└── prompts/
    ├── portrait.prompt.yaml                 # Prompt portrait
    ├── space_marine_battle.prompt.yaml      # Scene 40K
    └── rock_concert.prompt.yaml             # Scene musicale
```

## Features principales

### 1. Hierarchical Character Templates
Système d'implémentation de templates pour définir des personnages réutilisables.

**Détails** : [01-hierarchical-character-templates.md](./01-hierarchical-character-templates.md)

### 2. Advanced Variation Selectors
Syntaxe riche pour sélectionner des variations par clé, index, range, ou aléatoirement.

**Détails** : [02-advanced-variation-selectors.md](./02-advanced-variation-selectors.md)

### 3. Multi-field Expansion System
Un fichier de variation peut définir plusieurs champs qui s'étendent ensemble.

**Détails** : [03-multi-field-expansion.md](./03-multi-field-expansion.md)

### 4. Nested Variations
Support de références entre fichiers de variations pour des compositions complexes.

**Détails** : [04-nested-variations.md](./04-nested-variations.md)

### 5. Explain & Debug System
Outil pour comprendre la résolution des prompts et générer de la documentation.

**Détails** : [05-explain-debug-system.md](./05-explain-debug-system.md)

## Exemples complets

### Exemple 1: Portrait avec variations ethniques

**`prompts/athlete_portrait.prompt.yaml`**
```yaml
name: "Athlete Portrait Variations"

imports:
  TECHNIQUE: base/photorealistic_tech.txt
  CHARACTER: characters/athlete_portrait.char.yaml
  ETHNICITIES: variations/ethnic_features.yaml
  POSES: variations/athletic_poses.yaml
  EXPRESSIONS: variations/expressions.yaml
  ENVIRONMENTS: variations/sports_environments.yaml

prompt: |
  {TECHNIQUE}
  BREAK
  {CHARACTER with ethnicity=ETHNICITIES[african,asian,caucasian]}
  BREAK
  {POSES[range:1-10,random:5]}, {EXPRESSIONS[determined,focused]},
  {ENVIRONMENTS[stadium,gym]}
  BREAK
  action shot, dramatic lighting

negative_prompt: |
  low quality, blurry, deformed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
```

### Exemple 2: Warhammer 40K Space Marine

**`prompts/space_marine_battle.prompt.yaml`**
```yaml
name: "Space Marine Chapter Variants"

imports:
  TECHNIQUE: base/grimdark_tech.txt
  CHARACTER: characters/space_marine.char.yaml
  CHAPTERS: variations/40k_chapters.yaml
  POSES: variations/combat_poses.yaml
  WEAPONS: variations/40k_weapons.yaml
  BATTLEFIELDS: variations/40k_environments.yaml

prompt: |
  {TECHNIQUE}
  BREAK
  {CHARACTER with chapter=CHAPTERS[ultramarines,blood_angels,space_wolves]}
  BREAK
  {POSES[heroic_stance,combat_ready]}, {WEAPONS[bolter,chainsword]},
  {BATTLEFIELDS[war_torn_city,fortress]}
  BREAK
  epic composition, grimdark atmosphere, dramatic lighting

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 1000
```

**Génération :**
```bash
sdgen generate prompts/space_marine_battle.prompt.yaml
```

**Debugging :**
```bash
sdgen explain prompts/space_marine_battle.prompt.yaml \
  "Pourquoi mon Ultramarine a le schéma de couleur des Blood Angels ?" \
  > debug_output.yaml
```

## Bénéfices

1. **DRY (Don't Repeat Yourself)** : Réutilisation maximale des configurations
2. **Maintenabilité** : Modifications centralisées
3. **Flexibilité** : Mix & match de caractéristiques
4. **Partageabilité** : Bibliothèques de personnages/styles
5. **Debuggabilité** : Compréhension claire du processus
6. **Évolutivité** : Ajout facile de nouveaux templates/variations

## Migration depuis l'ancien système

- **Backward compatible** : Support des anciens fichiers `.txt`
- **Conversion automatique** : `sdgen convert old.txt → new.yaml`
- **Migration progressive** : Possibilité de mixer ancien et nouveau format

## Roadmap d'implémentation

### Phase 1 : Fondations (Priority 5-6)
- Loader YAML avec backward compatibility
- Parser de sélecteurs de variations
- Système d'imports basique

### Phase 2 : Character System (Priority 6-7)
- Templates de personnages
- Implémentation avec overrides
- Multi-field expansion

### Phase 3 : Advanced Features (Priority 7-8)
- Nested variations
- Validation et schémas
- Explain system

### Phase 4 : Tooling (Priority 8-9)
- CLI complète
- Conversion tools
- Documentation auto-générée

## Success Criteria

- [ ] Réduction de 80% de la duplication de code dans les prompts
- [ ] Support de bibliothèques partagées de personnages
- [ ] Temps de debugging divisé par 3 grâce au système explain
- [ ] 100% backward compatible avec l'ancien système
- [ ] Documentation complète auto-générée

## Notes

Ce système est particulièrement adapté pour :
- Génération de datasets cohérents pour entraînement LoRA
- Exploration systématique de variations
- Maintenance de bibliothèques de personnages
- Workflows de production avec réutilisabilité

## References

- Inspirations : Jinja2, Ansible templating, CSS preprocessors
- Similar systems : ComfyUI workflows, A1111 wildcards (mais limités)
