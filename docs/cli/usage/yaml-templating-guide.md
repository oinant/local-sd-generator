# Guide du Système de Templating YAML

**Guide utilisateur complet pour créer des prompts avec le système de templating Phase 2**

---

## Vue d'ensemble

Le système de templating YAML vous permet de créer des prompts réutilisables et modulaires pour Stable Diffusion. Au lieu d'écrire 100 prompts différents manuellement, vous définissez :
- Un **template** avec des placeholders
- Des **fichiers de variations** qui remplissent ces placeholders
- Des **modes de génération** pour créer toutes les combinaisons ou des sélections aléatoires

---

## Concepts de base illustrés

```mermaid
graph LR
    A[Template avec<br/>placeholders] --> B[Chargement des<br/>variations]
    B --> C[Génération des<br/>combinaisons]
    C --> D[Images générées<br/>avec métadonnées]

    style A fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style B fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style C fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style D fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

### Exemple simple

**Template**
```yaml
template: beautiful portrait, {Expression}, {Outfit}
```

**Variations**
```
expressions.yaml:
  happy: smiling, cheerful
  sad: crying, tears

outfits.yaml:
  dress: red dress
  suit: formal suit
```

**Résultat** (mode combinatorial)
```
Image 1: beautiful portrait, smiling, cheerful, red dress
Image 2: beautiful portrait, smiling, cheerful, formal suit
Image 3: beautiful portrait, crying, tears, red dress
Image 4: beautiful portrait, crying, tears, formal suit
```

---

## Structure de projet

```mermaid
graph TB
    subgraph "Votre projet"
        Root[📁 mon-projet/]

        Prompts[📁 prompts/]
        Root --> Prompts

        Portrait[📄 portrait.prompt.yaml]
        Landscape[📄 landscape.prompt.yaml]
        Prompts --> Portrait
        Prompts --> Landscape

        Variations[📁 variations/]
        Root --> Variations

        Expressions[📄 expressions.yaml]
        Outfits[📄 outfits.yaml]
        Backgrounds[📄 backgrounds.yaml]
        Variations --> Expressions
        Variations --> Outfits
        Variations --> Backgrounds

        Results[📁 results/]
        Root --> Results

        Session1[📁 20251006_143052_portrait/]
        Session2[📁 20251006_150234_landscape/]
        Results --> Session1
        Results --> Session2
    end

    style Root fill:#e3f2fd,stroke:#333,stroke-width:2px,color:#000
    style Prompts fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Variations fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style Results fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

---

## Progression des concepts

```mermaid
flowchart TD
    Start([Débutant]) --> Simple[Niveau 1: Template simple<br/>1 template + 2-3 variations]

    Simple --> Multi[Niveau 2: Multi-variations<br/>Plusieurs placeholders<br/>Modes combinatorial/random]

    Multi --> Selectors[Niveau 3: Sélecteurs<br/>Choisir des variations spécifiques<br/>random:N, indices, ranges]

    Multi --> Lists[Niveau 3: Listes d'imports<br/>Combiner plusieurs fichiers<br/>sans fichier intermédiaire]

    Selectors --> Inheritance[Niveau 4: Héritage<br/>Réutiliser des templates<br/>extends, modes]

    Lists --> Inheritance

    Inheritance --> Advanced[Niveau 5: Avancé<br/>Characters/Chunks<br/>Multi-field variations]

    Advanced --> Expert([Expert])

    style Start fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style Simple fill:#e8f5e9,stroke:#333,stroke-width:2px,color:#000
    style Multi fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Selectors fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style Lists fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style Inheritance fill:#d1c4e9,stroke:#333,stroke-width:2px,color:#000
    style Advanced fill:#ffccbc,stroke:#333,stroke-width:2px,color:#000
    style Expert fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

---

## Niveau 1 : Template simple

### Fichier minimal

```yaml
version: '2.0'
name: 'Mon Premier Portrait'

imports:
  Expression: ../variations/expressions.yaml

template: |
  beautiful portrait, {Expression}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 1000
  max_images: 10

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

### Ce qui se passe

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant S as Système
    participant SD as Stable Diffusion

    U->>S: Charge portrait.prompt.yaml
    S->>S: Lit expressions.yaml (3 variations)
    S->>S: Génère 3 combinaisons

    loop Pour chaque combinaison
        S->>S: Remplace {Expression}
        S->>S: Calcule seed (1000, 1001, 1002)
        S->>SD: Génère image
        SD-->>S: Image PNG
        S->>U: Sauvegarde + métadonnées
    end

    U->>U: 3 images dans results/
```

---

## Niveau 2 : Multi-variations

### Template avec plusieurs placeholders

```yaml
version: '2.0'
name: 'Portrait Complet'

imports:
  Expression: ../variations/expressions.yaml      # 5 variations
  Outfit: ../variations/outfits.yaml             # 4 variations
  Background: ../variations/backgrounds.yaml      # 3 variations

template: |
  masterpiece, beautiful woman, {Expression}, {Outfit}, {Background}

generation:
  mode: combinatorial
  max_images: 60  # 5 × 4 × 3 = 60 combinaisons
```

### Visualisation des combinaisons

```mermaid
graph TB
    subgraph "Mode Combinatorial"
        Root[Template]

        Root --> E1[Expression 1]
        Root --> E2[Expression 2]

        E1 --> O1[Outfit 1]
        E1 --> O2[Outfit 2]

        E2 --> O3[Outfit 1]
        E2 --> O4[Outfit 2]

        O1 --> B1[Bg 1]
        O1 --> B2[Bg 2]
        O2 --> B3[Bg 1]
        O2 --> B4[Bg 2]
        O3 --> B5[Bg 1]
        O3 --> B6[Bg 2]
        O4 --> B7[Bg 1]
        O4 --> B8[Bg 2]
    end

    B1 --> Img1[Image 1]
    B2 --> Img2[Image 2]
    B3 --> Img3[Image 3]
    B4 --> Img4[Image 4]
    B5 --> Img5[Image 5]
    B6 --> Img6[Image 6]
    B7 --> Img7[Image 7]
    B8 --> Img8[Image 8]

    style Root fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style Img1 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img2 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img3 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img4 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img5 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img6 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img7 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Img8 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

### Mode Random vs Combinatorial

```mermaid
graph LR
    subgraph "Mode Combinatorial"
        C1[Expression 1<br/>Outfit 1<br/>Bg 1]
        C2[Expression 1<br/>Outfit 1<br/>Bg 2]
        C3[Expression 1<br/>Outfit 1<br/>Bg 3]
        C4[Expression 1<br/>Outfit 2<br/>Bg 1]
        Cdots[...]
        C60[Expression 5<br/>Outfit 4<br/>Bg 3]
    end

    subgraph "Mode Random max_images: 20"
        R1[Expression 3<br/>Outfit 1<br/>Bg 2]
        R2[Expression 1<br/>Outfit 4<br/>Bg 3]
        R3[Expression 5<br/>Outfit 2<br/>Bg 1]
        Rdots[...]
        R20[Expression 2<br/>Outfit 3<br/>Bg 2]
    end

    style C1 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style C2 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style C3 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style C60 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000

    style R1 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R2 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R3 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R20 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
```

---

## Niveau 3a : Sélecteurs

### Syntaxe des sélecteurs

```yaml
template: |
  {Expression}              # Toutes les variations
  {Expression[random:5]}    # 5 variations aléatoires
  {Expression[0,2,4]}       # Indices 0, 2, 4 uniquement
  {Expression[happy,sad]}   # Variations nommées "happy" et "sad"
  {Expression[#0-10]}       # Range d'indices 0 à 10
```

### Exemple concret

```yaml
version: '2.0'
name: 'Test Expressions Spécifiques'

imports:
  Expression: ../variations/expressions.yaml  # 50 expressions disponibles
  Angle: ../variations/angles.yaml           # 20 angles disponibles

template: |
  portrait, {Expression[random:5]}, {Angle[front,side,back]}

generation:
  mode: combinatorial
  # Résultat: 5 expressions × 3 angles = 15 images
```

### Visualisation

```mermaid
graph LR
    subgraph "50 Expressions disponibles"
        E1[happy]
        E2[sad]
        E3[angry]
        Edots1[...]
        E50[surprised]
    end

    Select[random:5<br/>sélectionne 5]

    E1 -.-> Select
    E2 -.-> Select
    E15[neutral] --> Select
    E28[smiling] --> Select
    E35[laughing] --> Select
    E42[crying] --> Select
    E47[thinking] --> Select

    subgraph "20 Angles disponibles"
        A1[front]
        A2[side]
        A3[back]
        Adots[...]
        A20[top]
    end

    Select2[Sélecteur<br/>front,side,back]

    A1 --> Select2
    A2 --> Select2
    A3 --> Select2

    Select --> Combo[5 × 3 = 15<br/>combinaisons]
    Select2 --> Combo

    style Select fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Select2 fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Combo fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

---

## Niveau 3b : Listes d'imports

### Avant (Phase 1)

```yaml
# Fallait créer un fichier intermédiaire
# haircolors_combined.yaml:
type: multi-field
sources:
  - haircolors.realist.yaml
  - haircolors.fantasy.yaml

# Puis l'importer
imports:
  HairColor: ../variations/haircolors_combined.yaml
```

### Maintenant (Phase 2)

```yaml
# Import direct d'une liste !
imports:
  HairColor:
    - ../variations/haircolors.realist.yaml
    - ../variations/haircolors.fantasy.yaml
    - ../variations/haircolors.gradient.yaml
```

### Visualisation

```mermaid
graph LR
    subgraph "Fichiers sources"
        F1[haircolors.realist.yaml<br/>• brown<br/>• blonde<br/>• black]
        F2[haircolors.fantasy.yaml<br/>• pink<br/>• blue<br/>• purple]
        F3[haircolors.gradient.yaml<br/>• ombre<br/>• highlights]
    end

    F1 --> Merge[Merge automatique]
    F2 --> Merge
    F3 --> Merge

    Merge --> Result[HairColor<br/>8 variations totales]

    style Merge fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Result fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

---

## Niveau 4 : Héritage de templates

### Use case typique

Vous avez un setup technique que vous aimez (résolution, steps, sampler, etc.) et vous voulez créer plusieurs prompts qui partagent cette base.

### Template de base

```yaml
# base_portrait.prompt.yaml
version: '2.0'
name: 'Base Portrait Setup'
base_path: ../..

imports:
  HairColor: variations/haircolors.yaml
  Outfit: variations/outfits.yaml

template: |
  masterpiece, ultra-HD, high detail, depth of field,
  beautiful woman, {HairColor} hair, {Outfit},
  cinematic lighting, HDR

parameters:
  width: 832
  height: 1216
  steps: 24
  cfg_scale: 3
  sampler: DPM++ 2M Karras
  enable_hr: true
  hr_scale: 1.5
  hr_upscaler: 4x_foolhardy_Remacri
  denoising_strength: 0.4
```

### Templates enfants

```yaml
# portrait_smiling.prompt.yaml
version: '2.0'
name: 'Portrait Souriant'
extends: base_portrait.prompt.yaml
extends_mode: append

template: |
  smiling, happy, looking at viewer

generation:
  mode: random
  seed_mode: progressive
  seed: 1000
  max_images: 50

output:
  session_name: portrait_happy
```

```yaml
# portrait_action.prompt.yaml
version: '2.0'
name: 'Portrait Action'
extends: base_portrait.prompt.yaml
extends_mode: append

template: |
  dynamic pose, action shot, motion blur

imports:
  Action: variations/actions.yaml

generation:
  mode: combinatorial
  max_images: 100

output:
  session_name: portrait_action
```

### Visualisation de l'héritage

```mermaid
graph TB
    Base[📄 base_portrait.prompt.yaml<br/>━━━━━━━━━━━━━━━━<br/>Template de base<br/>Parameters complets<br/>Imports de base]

    Base --> Child1[📄 portrait_smiling.prompt.yaml<br/>━━━━━━━━━━━━━━━━<br/>+ smiling, happy<br/>+ generation config<br/>✅ Hérite tout de base]

    Base --> Child2[📄 portrait_action.prompt.yaml<br/>━━━━━━━━━━━━━━━━<br/>+ dynamic pose, action<br/>+ Import Action<br/>✅ Hérite tout de base]

    Base --> Child3[📄 portrait_night.prompt.yaml<br/>━━━━━━━━━━━━━━━━<br/>+ night scene, stars<br/>+ Override parameters<br/>✅ Hérite + override]

    style Base fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style Child1 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Child2 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style Child3 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

### Modes d'extension

```mermaid
graph TB
    subgraph "Base Template"
        BT["masterpiece, beautiful woman,<br/>{Outfit}"]
    end

    subgraph "Child Template"
        CT[smiling, looking at viewer]
    end

    subgraph "extends_mode: append (défaut)"
        A["masterpiece, beautiful woman, {Outfit}<br/>smiling, looking at viewer"]
    end

    subgraph "extends_mode: prepend"
        P["smiling, looking at viewer<br/>masterpiece, beautiful woman, {Outfit}"]
    end

    subgraph "extends_mode: replace"
        R[smiling, looking at viewer]
    end

    BT -.-> A
    CT -.-> A

    BT -.-> P
    CT -.-> P

    CT -.-> R

    style A fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style P fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style R fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
```

---

## Modes de seed

```mermaid
graph TB
    subgraph "seed_mode: fixed"
        F1[Combo 1<br/>seed: 1000]
        F2[Combo 2<br/>seed: 1000]
        F3[Combo 3<br/>seed: 1000]
        F4[Combo 4<br/>seed: 1000]
    end

    subgraph "seed_mode: progressive"
        P1[Combo 1<br/>seed: 1000]
        P2[Combo 2<br/>seed: 1001]
        P3[Combo 3<br/>seed: 1002]
        P4[Combo 4<br/>seed: 1003]
    end

    subgraph "seed_mode: random"
        R1[Combo 1<br/>seed: -1 aléatoire]
        R2[Combo 2<br/>seed: -1 aléatoire]
        R3[Combo 3<br/>seed: -1 aléatoire]
        R4[Combo 4<br/>seed: -1 aléatoire]
    end

    style F1 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style F2 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style F3 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000
    style F4 fill:#bbdefb,stroke:#333,stroke-width:2px,color:#000

    style P1 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style P2 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style P3 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style P4 fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000

    style R1 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R2 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R3 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style R4 fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
```

### Cas spécial : Génération sans variations

```yaml
version: '2.0'
name: 'Même prompt, seeds différentes'

# Aucun import !

template: |
  masterpiece, beautiful sunset landscape, mountains, lake

generation:
  mode: random
  seed_mode: progressive
  seed: 5000
  max_images: 40

# Résultat: 40 images identiques en prompt, seeds 5000-5039
```

---

## Workflow utilisateur complet

```mermaid
flowchart TD
    Start([Idée d'image]) --> Check{Template existe?}

    Check -->|Oui| Reuse[Utiliser template existant<br/>ou extend]
    Check -->|Non| CreateBase[Créer nouveau template]

    Reuse --> EditChild[Créer/modifier<br/>fichier .prompt.yaml]
    CreateBase --> CreateVars{Variations existent?}

    CreateVars -->|Oui| EditChild
    CreateVars -->|Non| CreateVarFiles[Créer fichiers<br/>.yaml de variations]

    CreateVarFiles --> EditChild

    EditChild --> TestSmall[Test avec max_images: 5]

    TestSmall --> Review{Résultat OK?}

    Review -->|Non| TweakPrompt[Ajuster template<br/>ou variations]
    Review -->|Partiel| TweakParams[Ajuster parameters<br/>steps, cfg, etc.]

    TweakPrompt --> TestSmall
    TweakParams --> TestSmall

    Review -->|Oui| Production[Lancer génération<br/>complète max_images: N]

    Production --> Organize[Organiser/trier<br/>les résultats]

    Organize --> Archive[Archiver<br/>ou réutiliser base]

    Archive --> End([Terminé])

    style Start fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style TestSmall fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style Production fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style End fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

---

## Cas d'usage réels

### Cas 1 : Entraînement de LoRA

**Objectif** : Générer 500 images d'un personnage avec variations maximales

```yaml
version: '2.0'
name: 'Dataset LoRA - Character Name'

imports:
  Expression:
    - expressions.happy.yaml
    - expressions.neutral.yaml
    - expressions.sad.yaml
  Angle:
    - angles.portrait.yaml
    - angles.fullbody.yaml
  Outfit:
    - outfits.casual.yaml
    - outfits.formal.yaml
    - outfits.fantasy.yaml
  Background: backgrounds.varied.yaml

template: |
  masterpiece, 1girl, [character description],
  {Expression}, {Angle}, {Outfit}, {Background}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 10000
  max_images: 500
```

### Cas 2 : Exploration créative

**Objectif** : Explorer rapidement des idées avec randomisation

```yaml
version: '2.0'
name: 'Creative Exploration'

imports:
  Style: styles.artistic.yaml
  Mood: moods.varied.yaml
  Color: colorpalettes.yaml

template: |
  {Style}, {Mood}, {Color} color scheme, abstract art

generation:
  mode: random
  seed_mode: random
  max_images: 100
```

### Cas 3 : Production de variantes

**Objectif** : Générer des variantes d'un concept approuvé

```yaml
version: '2.0'
name: 'Approved Concept Variants'
extends: base_approved_concept.prompt.yaml

template: |
  [concept de base déjà approuvé]
  {LightingVariation[random:10]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 10
```

---

## Organisation recommandée

### Structure pour un projet

```
mon-projet/
├── .sdgen_config.json          # Config globale
│
├── templates/                   # Templates réutilisables
│   ├── base_portrait.prompt.yaml
│   ├── base_landscape.prompt.yaml
│   └── base_fantasy.prompt.yaml
│
├── prompts/                     # Prompts spécifiques (extend templates)
│   ├── character_alice/
│   │   ├── alice_portrait.prompt.yaml
│   │   ├── alice_action.prompt.yaml
│   │   └── alice_expressions.prompt.yaml
│   │
│   └── scenes/
│       ├── forest_scene.prompt.yaml
│       └── city_scene.prompt.yaml
│
├── variations/                  # Variations réutilisables
│   ├── shared/                  # Variations communes
│   │   ├── expressions.yaml
│   │   ├── angles.yaml
│   │   └── backgrounds.yaml
│   │
│   ├── character_alice/         # Variations spécifiques
│   │   ├── alice_outfits.yaml
│   │   └── alice_poses.yaml
│   │
│   └── styles/
│       ├── artistic_styles.yaml
│       └── photo_styles.yaml
│
└── results/                     # Images générées
    ├── 20251006_alice_portrait/
    ├── 20251006_alice_action/
    └── 20251006_forest_scene/
```

---

## Astuces et bonnes pratiques

### 1. Commencer petit

```mermaid
graph LR
    A[1 template<br/>2 variations<br/>= 2 images] --> B[Ajouter 1 variation<br/>= 4 images]
    B --> C[Ajouter 1 placeholder<br/>= 12 images]
    C --> D[Affiner sélecteurs<br/>= images optimisées]

    style A fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
    style B fill:#fff9c4,stroke:#333,stroke-width:2px,color:#000
    style C fill:#f8bbd0,stroke:#333,stroke-width:2px,color:#000
    style D fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
```

### 2. Tester avant production

```yaml
# Version test
generation:
  mode: random
  max_images: 5  # Quick test

# Version production (après validation)
generation:
  mode: combinatorial
  max_images: 500
```

### 3. Nommer clairement

```yaml
# ❌ Mauvais
name: 'test1'

# ✅ Bon
name: 'Character Alice - Portrait Expressions Test'
```

### 4. Documenter les templates

```yaml
version: '2.0'
name: 'Portrait Setup - High Quality'
description: |
  Template de base pour portraits haute qualité.

  Résolution: 832x1216 upscalée à 1248x1824
  Utilise Hires Fix avec 4x_foolhardy_Remacri

  Optimisé pour:
  - Portraits de personnages féminins
  - Style semi-réaliste
  - Lighting dramatique
```

### 5. Réutiliser avec extends

Au lieu de copier-coller, extend !

```yaml
# Nouveau prompt
extends: ../templates/base_portrait.prompt.yaml
template: |
  [juste les modifications spécifiques]
```

---

## Exemples de fichiers de variations

### expressions.yaml
```yaml
version: '1.0'
variations:
  happy: smiling, cheerful expression, bright eyes
  sad: sad expression, tears, melancholic
  angry: angry expression, frowning, intense gaze
  neutral: neutral expression, calm face
  surprised: surprised expression, wide eyes, open mouth
  thinking: thoughtful expression, hand on chin
```

### outfits.casual.yaml
```yaml
version: '1.0'
variations:
  jeans_tshirt: blue jeans, white t-shirt, casual sneakers
  hoodie: gray hoodie, black pants, comfortable shoes
  dress_casual: casual summer dress, sandals
  sportswear: athletic wear, running shoes, sporty look
```

### angles.portrait.yaml
```yaml
version: '1.0'
variations:
  front: front view, looking at camera, centered composition
  side: side profile, 90 degree angle
  three_quarter: three-quarter view, slight angle
  close_up: close-up shot, tight framing, focus on face
  upper_body: upper body shot, from chest up
```

---

## Dépannage courant

### Problème : Trop d'images générées

```yaml
# Vous avez:
Expression: 50 variations
Outfit: 30 variations
Angle: 20 variations
# = 50 × 30 × 20 = 30,000 combinaisons !

# Solution 1: Sélecteurs
template: |
  {Expression[random:5]}, {Outfit[random:3]}, {Angle[random:4]}
  # = 5 × 3 × 4 = 60 combinaisons

# Solution 2: Mode random
generation:
  mode: random
  max_images: 100
```

### Problème : Pas assez de variété

```yaml
# Au lieu de:
generation:
  seed_mode: fixed  # Toutes les images avec même seed

# Utiliser:
generation:
  seed_mode: progressive  # Seeds différentes
  # ou
  seed_mode: random
```

### Problème : Template trop répétitif

```yaml
# Au lieu de dupliquer:
# portrait1.prompt.yaml, portrait2.prompt.yaml, portrait3.prompt.yaml

# Créer une base:
# base_portrait.prompt.yaml

# Puis extend:
extends: base_portrait.prompt.yaml
template: |
  [juste ce qui change]
```

---

## Référence rapide

| Concept | Syntaxe | Exemple |
|---------|---------|---------|
| Placeholder | `{Nom}` | `{Expression}` |
| Random N | `{Nom[random:N]}` | `{Expression[random:5]}` |
| Indices | `{Nom[i,j,k]}` | `{Expression[0,2,4]}` |
| Noms | `{Nom[key1,key2]}` | `{Expression[happy,sad]}` |
| Range | `{Nom[#0-N]}` | `{Expression[#0-10]}` |
| Liste imports | Liste YAML | `HairColor:\n  - file1.yaml\n  - file2.yaml` |
| Héritage | `extends: base.yaml` | `extends: base_portrait.prompt.yaml` |
| Mode extend | `extends_mode: append` | `append / prepend / replace` |

---

## Prochaines étapes

```mermaid
graph LR
    A[Lire ce guide] --> B[Créer 1er template simple]
    B --> C[Tester avec 5 images]
    C --> D[Ajouter variations]
    D --> E[Expérimenter sélecteurs]
    E --> F[Créer template base]
    F --> G[Utiliser extends]
    G --> H[Maîtriser le système!]

    style A fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style H fill:#c8e6c9,stroke:#333,stroke-width:2px,color:#000
```

1. **Créez votre premier template** avec 1-2 placeholders
2. **Testez** avec `max_images: 5`
3. **Itérez** : ajoutez des variations, affinez
4. **Créez un template de base** réutilisable
5. **Utilisez `extends`** pour éviter la duplication
6. **Explorez les sélecteurs** pour plus de contrôle

---

## Ressources

- **[Exemples de templates](../../../CLI/examples/prompts/)** - Templates prêts à l'emploi
- **[Exemples de variations](../../../CLI/examples/variations/)** - Fichiers de variations
- **[Architecture technique](../technical/phase2-templating-engine.md)** - Documentation technique détaillée

---

**Dernière mise à jour:** 2025-10-06
**Version du système:** Phase 2 avec extends + list imports
