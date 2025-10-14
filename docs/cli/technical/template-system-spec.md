# Template System V2.0 - Spécification Technique (Version Corrigée)

**Version:** 2.0.0 (corrected)
**Date:** 2025-10-10
**Status:** 🔧 Correction in progress

---

## 0. Glossaire

### Concepts fondamentaux

**Template** (`.template.yaml`)
: Structure de base définissant les paramètres de génération SD et un squelette de prompt avec des points d'injection (`{prompt}`, `{negprompt}`). Les templates fonctionnent par **héritage** (`implements:`).

**Chunk** (`.chunk.yaml`)
: Bloc de prompt réutilisable et composable (personnage, scène, style, etc.). Les chunks fonctionnent par **composition** (injection via `@Chunk`).

**Definition** (chunk)
: Chunk générique avec valeurs par défaut, destiné à être réutilisé.
: Exemple : `young_heroine.chunk.yaml`

**Implementation** (chunk)
: Spécialisation d'une definition avec valeurs personnalisées.
: Exemple : `young_heroine.chloe.chunk.yaml`

**Prompt** (`.prompt.yaml`)
: Configuration finale assemblant templates et chunks pour la génération d'images. Définit le contenu concret à injecter dans les placeholders du template parent.

**Variation** (`.yaml`)
: Fichier de dictionnaire clé-valeur contenant des alternatives pour un placeholder.
: Exemple : `haircolors.yaml` → `{Blonde: "blonde hair", Brunette: "brown hair"}`

### Patterns architecturaux

**Héritage** (`implements:`)
: Mécanisme de réutilisation pour templates et chunks. L'enfant hérite des propriétés du parent et peut les overrider.

**Composition** (`@Chunk`)
: Mécanisme d'assemblage pour construire des prompts complexes à partir de chunks réutilisables.

**Injection** (`{prompt}`, `{negprompt}`)
: Placeholders réservés permettant au parent de définir des points d'insertion pour le contenu de l'enfant (Template Method Pattern).

---

## 1. Architecture conceptuelle

### 1.1 Vue d'ensemble

Le Template System V2.0 utilise **deux patterns complémentaires** :

1. **Héritage (Templates)** : Réutilisation par spécialisation
2. **Composition (Chunks)** : Réutilisation par assemblage

```
┌─────────────────────────────────────────────────────────────┐
│                        TEMPLATES                            │
│                    (Héritage vertical)                      │
│                                                             │
│  base.template.yaml                                         │
│    ↓ implements                                             │
│  manga.template.yaml                                        │
│    ↓ implements                                             │
│  portrait.prompt.yaml ──┐                                   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          │ injecte
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                        CHUNKS                               │
│                  (Composition horizontale)                  │
│                                                             │
│  young_heroine.chunk.yaml (definition)                      │
│    ↓ implements                                             │
│  young_heroine.chloe.chunk.yaml (implementation)            │
│                                                             │
│  landscape.chunk.yaml                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Distinctions clés

| Aspect | Template | Chunk |
|--------|----------|-------|
| **Extension** | `.template.yaml` | `.chunk.yaml` |
| **Pattern** | Héritage | Composition |
| **Contenu** | Structure + placeholders | Contenu réutilisable |
| **Placeholders réservés** | ✅ `{prompt}`, `{negprompt}` | ❌ Interdits |
| **Injection** | Via `{prompt}` placeholder | Via `@Chunk` syntax |
| **Héritage** | Multi-niveaux | 1 niveau (definition → implementation) |

---

## 2. Structure des fichiers

### 2.1 `.template.yaml` - Structure réutilisable

**Rôle** : Définir une structure de prompt avec points d'injection pour les enfants.

```yaml
version: '2.0'                  # OBLIGATOIRE
name: 'TemplateName'            # OBLIGATOIRE

implements: '../parent.template.yaml'  # OPTIONNEL - Héritage

parameters:                     # OPTIONNEL - Paramètres SD WebUI
  width: 832
  height: 1216
  steps: 30
  cfg_scale: 6
  sampler: 'DPM++ 2M'
  scheduler: 'Karras'
  enable_hr: true
  hr_scale: 1.5
  hr_upscaler: '4x_foolhardy_Remacri'
  denoising_strength: 0.4
  hr_second_pass_steps: 15

imports:                        # OPTIONNEL - Imports de chunks/variations
  chunks:
    positive: ../chunks/positive.chunk.yaml
  Character: ../chunks/young_heroine.chunk.yaml

template: |                     # OBLIGATOIRE - Doit contenir {prompt}
  @chunks.positive,
  masterpiece, detailed,
  {prompt}

negative_prompt: |              # OPTIONNEL - Peut contenir {negprompt}
  low quality, {negprompt}
```

**Champs obligatoires :** `version`, `name`, `template`

**Validation :**
- ✅ `template:` **doit** contenir le placeholder `{prompt}`
- ✅ `negative_prompt:` **peut** contenir le placeholder `{negprompt}` (optionnel)

**Sémantique du `{prompt}` placeholder :**
Le placeholder `{prompt}` est un **point d'injection** (Template Method Pattern). Le contenu du champ `prompt:` de l'enfant (`.prompt.yaml`) sera injecté à cet emplacement.

### 2.2 `.chunk.yaml` - Bloc réutilisable

**Rôle** : Définir un bloc de prompt composable (personnage, scène, style).

#### 2.2.1 Chunk Definition (générique)

```yaml
# young_heroine.chunk.yaml
version: '2.0'                  # OBLIGATOIRE
type: 'character'               # OBLIGATOIRE

imports:                        # OPTIONNEL
  Haircuts: ../variations/haircuts.yaml
  Poses: ../variations/poses.yaml

template: |                     # OBLIGATOIRE
  1girl, {Age}, {HairColor} hair,
  {Haircut}, {Pose},
  detailed eyes, detailed skin

defaults:                       # OPTIONNEL - Valeurs par défaut
  Age: '20'
  HairColor: 'brown'
  Haircut: 'BobCut'
  Pose: 'Standing'
```

**Champs obligatoires :** `version`, `type`, `template`

#### 2.2.2 Chunk Implementation (spécialisée)

```yaml
# young_heroine.chloe.chunk.yaml
version: '2.0'
type: 'character'
implements: 'young_heroine.chunk.yaml'  # OBLIGATOIRE - Référence la definition

imports:
  Haircuts: ../variations/haircuts.yaml

chunks:                         # OPTIONNEL - Valeurs spécifiques
  Age: '22'
  HairColor: 'blonde'
  Haircut: 'Haircuts.LongHair'
  # Pose héritée de defaults: "Standing"
```

**Convention de nommage :**
```
<type>.<specialization>.chunk.yaml

Exemples :
  young_heroine.chunk.yaml                    # Definition
  young_heroine.chloe.chunk.yaml              # Implementation
  young_heroine.chloe_at_prime.chunk.yaml     # Implementation spécifique
  young_heroine.emma.chunk.yaml               # Autre implementation
```

**Avantages :**
- ✅ Ordonnancement alphabétique (definition en premier)
- ✅ Groupement visuel (toutes les variations ensemble)
- ✅ Lisible et intuitif

**Validation :**
- ❌ `template:` **ne doit PAS** contenir `{prompt}`, `{negprompt}`, `{loras}`
- ✅ Si `implements:` défini, le parent doit avoir le même `type:`
- ✅ Un seul niveau d'héritage autorisé (definition → implementation)

**Ordre de priorité des valeurs :**
```
1. Prompt override (avec "with" syntax) ← Plus haute priorité
2. Implementation chunks (chunks: dans l'implem)
3. Definition defaults (defaults: dans la definition)
```

### 2.3 `.prompt.yaml` - Configuration finale

**Rôle** : Assembler templates et chunks pour générer des images.

```yaml
version: '2.0'                  # OBLIGATOIRE
name: 'PromptName'              # OBLIGATOIRE

implements: '../template.yaml'  # OBLIGATOIRE - Template parent

generation:                     # OBLIGATOIRE
  mode: 'random'                # 'random' | 'combinatorial'
  seed: 42
  seed_mode: 'progressive'      # 'fixed' | 'progressive' | 'random'
  max_images: 100

imports:                        # OPTIONNEL
  Character: ../chunks/young_heroine.chloe.chunk.yaml
  HairColors: ../variations/haircolors.yaml
  Place:
    - "luxury living room"
    - "tropical jungle"

prompt: |                       # OBLIGATOIRE - Contenu à injecter dans {prompt}
  @{Character with HairColor:{HairColors[Blonde,Brunette]}},
  {Place}, detailed background,
  dramatic lighting

negative_prompt: |              # OPTIONNEL - Contenu à injecter dans {negprompt}
  extra legs, bad anatomy

output:
  session_name: my_session
```

**Champs obligatoires :** `version`, `name`, `implements`, `generation`, `prompt`

**Différences clés avec V2.0 original :**
- ✅ Utilise `prompt:` au lieu de `template:`
- ✅ Le `prompt:` est **injecté** dans le `{prompt}` du template parent
- ✅ Le `negative_prompt:` (optionnel) est **injecté** dans le `{negprompt}` du parent

### 2.4 `.yaml` - Fichier de variations

**Rôle** : Dictionnaire de valeurs alternatives pour un placeholder.

```yaml
# haircolors.yaml
Blonde: "blonde hair, golden highlights"
Brunette: "brown hair, chestnut tones"
RedHead: "red hair, fiery copper"
BlackHair: "black hair, raven dark"
```

**Format :** Dictionnaire YAML simple (clé → valeur)

---

## 3. Résolution et injection

### 3.1 Template Method Pattern - Injection de `{prompt}`

**Principe :** Le template parent définit un squelette avec `{prompt}`, l'enfant fournit le contenu.

#### Exemple complet

```yaml
# base.template.yaml
template: |
  masterpiece, detailed,
  {prompt}

# manga.template.yaml
implements: base.template.yaml
template: |
  s1_dram, {Angle}, ultra-HD,
  {prompt},
  <lora:manga>

# portrait.prompt.yaml
implements: manga.template.yaml
prompt: |
  mysterious girl, in a galactic place
```

**Résolution (de bas en haut) :**

1. **Étape 1 : Résoudre `manga.template.yaml`**
   ```
   Injecter manga.template dans {prompt} de base.template:

   "masterpiece, detailed,
    s1_dram, {Angle}, ultra-HD,
    {prompt},
    <lora:manga>"
   ```

2. **Étape 2 : Résoudre `portrait.prompt.yaml`**
   ```
   Injecter portrait.prompt dans {prompt} résolu:

   "masterpiece, detailed,
    s1_dram, {Angle}, ultra-HD,
    mysterious girl, in a galactic place,
    <lora:manga>"
   ```

**Résultat final :**
```
masterpiece, detailed,
s1_dram, {Angle}, ultra-HD,
mysterious girl, in a galactic place,
<lora:manga>
```

### 3.2 Chunk Injection - `@Chunk` syntax

#### Cas 1 : Chunk simple

```yaml
# portrait.prompt.yaml
imports:
  Character: ../chunks/young_heroine.chloe.chunk.yaml

prompt: |
  @Character, beautiful landscape
```

**Résolution :**
1. Charger `young_heroine.chloe.chunk.yaml`
2. Résoudre son héritage (`young_heroine.chunk.yaml`)
3. Appliquer les valeurs (implementation chunks > definition defaults)
4. Résoudre le template du chunk
5. Injecter le résultat

#### Cas 2 : Chunk avec override

```yaml
# portrait.prompt.yaml
imports:
  Character: ../chunks/young_heroine.chunk.yaml
  HairColors: ../variations/haircolors.yaml

prompt: |
  @{Character with HairColor:{HairColors[Blonde]}}
```

**Résolution :**
1. Charger le chunk `Character`
2. Le placeholder `{HairColor}` dans le template du chunk sera overridé
3. Sélectionner la variation `Blonde` depuis `HairColors`
4. Résoudre le template du chunk avec cette valeur
5. Injecter le résultat

**Ordre de priorité :**
```
Prompt override (with) > Implementation chunks > Definition defaults
```

#### Cas 3 : Chunk défini dans template + override dans prompt

```yaml
# manga.template.yaml
imports:
  Character: ../chunks/young_heroine.chunk.yaml
template: |
  @Character, {prompt}, manga style

# portrait.prompt.yaml
implements: manga.template.yaml
imports:
  HairColors: ../variations/haircolors.yaml

prompt: |
  @{Character with HairColor:{HairColors[Blonde]}},
  in a mysterious forest
```

**Résolution :**
1. Le `@Character` dans manga.template utilise les defaults
2. Le `@{Character with ...}` dans portrait.prompt override les valeurs
3. Les deux sont résolus et injectés à leurs emplacements respectifs

**Résultat :** Les deux chunks (du template et du prompt) sont injectés.

### 3.3 Negative prompt injection - `{negprompt}`

**Même principe que `{prompt}` :**

```yaml
# base.template.yaml
negative_prompt: |
  low quality, {negprompt}

# portrait.prompt.yaml
implements: base.template.yaml
negative_prompt: |
  extra legs, bad anatomy
```

**Résultat :**
```
low quality, extra legs, bad anatomy
```

**Si le prompt n'a pas de `negative_prompt:` :**
```
low quality
```
(Le `{negprompt}` devient une chaîne vide)

---

## 4. Règles de merge (héritage)

### 4.1 `parameters:` - MERGE

```yaml
# parent.template.yaml
parameters:
  width: 832
  height: 1216
  steps: 30

# child.template.yaml
implements: parent.template.yaml
parameters:
  steps: 40  # Override

# Résultat :
# parameters:
#   width: 832      ← Hérité
#   height: 1216    ← Hérité
#   steps: 40       ← Overridé
```

### 4.2 `imports:` - MERGE

```yaml
# parent.template.yaml
imports:
  Character: ../chunks/char.chunk.yaml

# child.template.yaml
imports:
  Outfit: ../variations/outfit.yaml

# Résultat :
# imports:
#   Character: ../chunks/char.chunk.yaml  ← Hérité
#   Outfit: ../variations/outfit.yaml     ← Ajouté
```

### 4.3 `defaults:` et `chunks:` (dans chunks) - MERGE

Même comportement que `parameters:`

### 4.4 `template:` - INJECTION (Template Method Pattern)

**Nouvelle sémantique (V2.0 corrigée) :**

Si le parent contient `{prompt}` :
- ✅ **INJECTION** : Le template enfant est injecté dans `{prompt}`

Si le parent ne contient PAS `{prompt}` :
- ⚠️ **REPLACE** : Le template enfant remplace celui du parent (avec WARNING)

```yaml
# parent.template.yaml
template: |
  masterpiece, {prompt}, detailed

# child.prompt.yaml
prompt: |
  1girl, beautiful

# Résultat : INJECTION
# "masterpiece, 1girl, beautiful, detailed"
```

### 4.5 `negative_prompt:` - INJECTION (si `{negprompt}` présent)

Même comportement que `template:`

---

## 5. Validation

### 5.1 Validation structurelle

**Templates (`.template.yaml`):**
- ✅ `template:` doit être une string
- ✅ `template:` doit contenir `{prompt}`
- ✅ Si `negative_prompt:` défini, peut contenir `{negprompt}` (optionnel)

**Chunks (`.chunk.yaml`):**
- ✅ `template:` doit être une string
- ❌ `template:` ne doit PAS contenir `{prompt}`, `{negprompt}`, `{loras}`
- ✅ Si `implements:`, le parent doit avoir le même `type:`
- ✅ Maximum 1 niveau d'héritage (definition → implementation)

**Prompts (`.prompt.yaml`):**
- ✅ `prompt:` doit être une string (pas `template:`)
- ✅ `implements:` obligatoire
- ✅ `generation:` obligatoire

### 5.2 Messages d'erreur

```python
# Template sans {prompt}
"Template 'base.template.yaml' must contain {prompt} placeholder"

# Chunk avec {prompt}
"Chunk 'character.chunk.yaml' cannot use reserved placeholder {prompt}"

# Type mismatch
"Type mismatch: young_heroine.emma.chunk.yaml (type='character') cannot implement landscape.chunk.yaml (type='scene')"

# Multi-niveau héritage chunk
"Chunk inheritance limited to 1 level: young_heroine.chloe.at_prime.chunk.yaml cannot implement young_heroine.chloe.chunk.yaml (already an implementation)"

# Prompt.yaml sans prompt:
"Prompt 'portrait.prompt.yaml' must define 'prompt:' field (not 'template:')"
```

---

## 6. Exemples complets

### Exemple 1 : Template simple + Prompt

```yaml
# base.template.yaml
version: '2.0'
name: 'Base Template'

parameters:
  width: 832
  height: 1216
  steps: 30

template: |
  masterpiece, {prompt}, detailed

negative_prompt: |
  low quality, {negprompt}
```

```yaml
# portrait.prompt.yaml
version: '2.0'
name: 'Simple Portrait'
implements: 'base.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 10

prompt: |
  1girl, beautiful, smiling

negative_prompt: |
  bad anatomy
```

**Résultat :**
```
Prompt: "masterpiece, 1girl, beautiful, smiling, detailed"
Negative: "low quality, bad anatomy"
```

### Exemple 2 : Chunk definition + implementation

```yaml
# young_heroine.chunk.yaml
version: '2.0'
type: 'character'

imports:
  Haircuts: ../variations/haircuts.yaml

template: |
  1girl, {Age}, {HairColor} hair, {Haircut}

defaults:
  Age: '20'
  HairColor: 'brown'
  Haircut: 'BobCut'
```

```yaml
# young_heroine.chloe.chunk.yaml
version: '2.0'
type: 'character'
implements: 'young_heroine.chunk.yaml'

chunks:
  Age: '22'
  HairColor: 'blonde'
  Haircut: 'Haircuts.LongHair'
```

```yaml
# portrait.prompt.yaml
version: '2.0'
name: 'Chloe Portrait'
implements: '../base.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 10

imports:
  Chloe: ../chunks/young_heroine.chloe.chunk.yaml

prompt: |
  @Chloe, beautiful landscape
```

**Résultat :**
```
Prompt: "masterpiece, 1girl, 22, blonde hair, long flowing hair, beautiful landscape, detailed"
```

### Exemple 3 : Chunk dans template + override dans prompt

```yaml
# manga.template.yaml
version: '2.0'
name: 'Manga Template'
implements: 'base.template.yaml'

imports:
  Character: ../chunks/young_heroine.chunk.yaml

template: |
  s1_dram, @Character, {prompt}, <lora:manga>
```

```yaml
# portrait.prompt.yaml
version: '2.0'
name: 'Custom Manga Portrait'
implements: 'manga.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 10

imports:
  HairColors: ../variations/haircolors.yaml

prompt: |
  @{Character with HairColor:{HairColors[RedHead]}},
  in a mysterious forest
```

**Résolution :**
1. `@Character` dans manga.template → Utilise les defaults
2. `@{Character with HairColor:...}` dans portrait.prompt → Override HairColor
3. Les deux chunks sont injectés

**Résultat :**
```
masterpiece,
s1_dram, 1girl, 20, brown hair, bob cut,
1girl, 20, red hair, fiery copper, bob cut, in a mysterious forest,
<lora:manga>,
detailed
```

### Exemple 4 : Multi-niveaux template + chunk

```yaml
# base.template.yaml
version: '2.0'
name: 'Base'

parameters:
  width: 832
  height: 1216

template: |
  masterpiece, {prompt}, detailed
```

```yaml
# manga.template.yaml
version: '2.0'
name: 'Manga Style'
implements: 'base.template.yaml'

template: |
  s1_dram, manga style, {prompt}, <lora:manga>
```

```yaml
# portrait.prompt.yaml
version: '2.0'
name: 'Portrait Chloe'
implements: 'manga.template.yaml'

generation:
  mode: combinatorial
  seed: 42
  seed_mode: progressive
  max_images: 50

imports:
  Chloe: ../chunks/young_heroine.chloe.chunk.yaml
  Places: ../variations/places.yaml

prompt: |
  @Chloe, {Places}, dramatic lighting
```

**Résolution (injection récursive) :**

1. **Résoudre manga.template dans base :**
   ```
   "masterpiece,
    s1_dram, manga style, {prompt}, <lora:manga>,
    detailed"
   ```

2. **Résoudre portrait.prompt dans le résultat :**
   ```
   "masterpiece,
    s1_dram, manga style,
    @Chloe, {Places}, dramatic lighting,
    <lora:manga>,
    detailed"
   ```

3. **Résoudre @Chloe chunk :**
   ```
   "masterpiece,
    s1_dram, manga style,
    1girl, 22, blonde hair, long flowing hair,
    {Places}, dramatic lighting,
    <lora:manga>,
    detailed"
   ```

**Résultat final :**
```
masterpiece,
s1_dram, manga style,
1girl, 22, blonde hair, long flowing hair,
luxury living room,
dramatic lighting,
<lora:manga>,
detailed
```

---

## 7. Migration V2.0 original → V2.0 corrigée

### 7.1 Changements dans les fichiers

#### `.template.yaml`
```diff
  version: '2.0'
  name: 'MyTemplate'

  template: |
-   some prompt text
+   some prompt text, {prompt}
+   # {prompt} est maintenant OBLIGATOIRE
```

#### `.prompt.yaml`
```diff
  version: '2.0'
  name: 'MyPrompt'
  implements: 'template.yaml'

  generation:
    mode: random
    seed: 42
    seed_mode: progressive
    max_images: 10

- template: |
+ prompt: |
    1girl, beautiful
+   # Champ renommé : template → prompt
```

### 7.2 Changements dans le code

**Models (`config_models.py`):**
```python
@dataclass
class TemplateConfig:
    template: str  # Doit contenir {prompt}
    negative_prompt: str  # Peut contenir {negprompt}

@dataclass
class PromptConfig:
    prompt: str  # Nouveau champ (anciennement template)
    negative_prompt: Optional[str]
```

**Parser (`parser.py`):**
```python
def parse_prompt(self, data: Dict[str, Any], source_file: Path) -> PromptConfig:
    # Validation
    if 'template' in data:
        raise ValueError(
            f"Prompt files use 'prompt:' field, not 'template:'. "
            f"Please rename 'template:' to 'prompt:' in {source_file.name}"
        )

    prompt = data['prompt']  # Nouveau champ
```

**Inheritance Resolver (`inheritance_resolver.py`):**
```python
def _merge_configs(self, parent: ConfigType, child: ConfigType) -> ConfigType:
    # Template injection (Template Method Pattern)
    if isinstance(child, PromptConfig):
        # Injecter child.prompt dans parent.template {prompt}
        merged.template = parent.template.replace('{prompt}', child.prompt)

        # Injecter child.negative_prompt dans parent.negative_prompt {negprompt}
        if child.negative_prompt:
            merged.negative_prompt = parent.negative_prompt.replace(
                '{negprompt}', child.negative_prompt
            )
        else:
            # Supprimer {negprompt} si pas de contenu
            merged.negative_prompt = parent.negative_prompt.replace('{negprompt}', '')
```

---

## 8. Récapitulatif des changements

| Aspect | V2.0 original | V2.0 corrigée |
|--------|---------------|---------------|
| **Template placeholder** | Optionnel | ✅ **Obligatoire** `{prompt}` |
| **Prompt field** | `template:` | ✅ `prompt:` |
| **Merge strategy** | REPLACE | ✅ **INJECTION** (Template Method) |
| **Chunk naming** | Libre | ✅ Convention `type.specialization.chunk.yaml` |
| **Chunk inheritance** | Multi-niveaux | ✅ **1 niveau** (definition → implementation) |
| **Validation** | Partielle | ✅ Stricte (`{prompt}` obligatoire) |

---

## 9. Glossaire technique (développeurs)

**Template Method Pattern**
: Pattern de conception où une classe parente définit la structure (skeleton) d'un algorithme avec des points d'extension (hooks). Les sous-classes implémentent ces hooks pour personnaliser le comportement.

**Injection de dépendances**
: Le parent définit des points d'injection (`{prompt}`), l'enfant fournit le contenu à injecter.

**Composition over inheritance**
: Les chunks utilisent la composition (`@Chunk`) plutôt que l'héritage profond pour favoriser la réutilisabilité.

**Single Responsibility Principle**
: Chaque fichier a une responsabilité unique :
  - Templates : Structure et paramètres
  - Chunks : Blocs réutilisables
  - Prompts : Assemblage final

---

**Fin de la spécification V2.0 corrigée**

**Status :** 🔧 Correction en cours
**Prochaines étapes :**
1. Validation de la spec avec l'utilisateur
2. Implémentation des changements
3. Migration des tests
4. Mise à jour de la documentation utilisateur
