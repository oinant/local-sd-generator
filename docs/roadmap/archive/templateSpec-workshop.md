# Template System


Exemple : 

``` yaml
# file : template/hassaku_highdef.template.yaml
# base template for hassakuXL/IllustriousXL for high def

version: '2.0'
name: 'HassakuHighDef'

parameters:
  width: 832
  height: 1216
  steps: 30
  cfg_scale: 6
  sampler: DPM++ 2M
  scheduler: "Karras"
  batch_size: 1
  batch_count: 1

  # Hires Fix configuration
  enable_hr: true
  hr_scale: 1.5
  hr_upscaler: 4x_foolhardy_Remacri
  denoising_strength: 0.4
  hr_second_pass_steps: 15
  
```

``` yaml
# file : template/hassaku_manga.template.yaml
# base template for hassakuXL/IllustriousXL for manga high def

version: '2.0'
name: 'HassakuHighDef-Manga'

implements: '../template/hassaku_highdef.template.yaml'

imports:
  chunks : 
    positive: ../chunks/managa-positive.chunk.yaml
    negative: ../chunks/managa-negative.chunk.yaml
    loras: ../chunks/managa-loras.chunk.yaml
  
   
template: |
    chunks.positves,
    {prompt}     
    chunks.loras,

negative_prompt: |
    chunks.negatives,
    {negprompt}   

```

``` yaml
# file : prompt/hassaku_manga.emma_solo.prompt.yaml
# actual prompt

version: '2.0'
name: 'HassakuHighDef-Manga'

implements: '../template/hassaku_highdef.hassaku_manga.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: random
  max_images: 1000

imports:
  Character: ../chunks/emma.chunk.yaml
  Outfit: 
    - ../varaitions/outfit.urban.yaml
    - ../varaitions/outfit.chic.yaml
  Place: 
    - "dark luxury modern living room, glass table, white sofa, modern wall art"
    - "dense tropical jungle at dawn, giant ferns and bioluminescent flowers, sunlight creating golden shafts through the foliage, vibrant parrot calls in the distance"
  Angle : ../variations/hassakuConcise/angles.yaml
  Pose: 
    - ../variations/hassaku/poses.classic.yaml 
    - ../variations/hassaku/poses.dynamic.yaml 

template : |
  {Chararcter with Angles:imports.Angle, Poses:imports.Pose },
  detailed background, {Place},
  
  {Outfit},
  
  night chiaroscuro, moonlight glow, dramatic shadows, light particles,  
  semi-realistic, black outline, sharp focus, bokeh, depth of field,

```

``` yaml
# file : chunks/girl_solo.chunk.yaml
# chunk defining a girl solo

type:character

template: |
      1girl, {Main} # => Main is taken from the implementing chunk   
      {Angle}, {Pose},
      {HairCut}, {HairColor}, {EyeColor} eyes, detailed eyes, detailed skin, subtle makeup,

defaults : 
    Main : 30, slim build, toned thighs
    HairCut : BobCut
    HairColor : Brunette
    EyeColor : Blue
    Angle : Straight
    Pose : Standing   
 
```
``` yaml 
# file : chunks/emma.chunk.yaml
# chunk defining a girl solo emma

implements: '../chunks/girl_solo.chunk.yaml'    

imports:
    Haircuts: ../variations/haircuts.yaml
    HairColors: ../variations/haircolors.yaml
    EyeColors: ../variations/eyecolors.yaml
    Angles: ../variations/angles.yaml
    Poses: ../variations/poses.yaml

chunks : 
    Main: 22, supermodel, slim curvy, large breasts, waist-to-hip 0.7, toned thighs
    HairCut : Haircuts.BobCut
    HairColor : HairColors.Ginger
    EyeColor : EyeColors.Green
    Angle : Angles.Straight
    Pose : Poses.Standing    

```

## Refinement workshop : 

## Passe 1

###  1. Syntaxe des placeholders multi-fichiers

Dans le prompt, ligne 88 :
{Chararcter with Angles:imports.Angle, Poses:imports.Pose }

Questions :
  - Est-ce que {Character with ...} signifie "injecter le chunk Character en lui passant des overrides pour Angles et Poses" ? ** => OUI ** 
  - La syntaxe Angles:imports.Angle veut dire "utiliser la variation imports.Angle pour remplir le placeholder {Angle} du chunk" ? ** => OUI, avec la variation selectionner par le generateur de variation **
  - Si le chunk girl_solo a {Angle} et {Pose}, on peut les override avec with ? => ** => OUI **

Clarification nécessaire :
 Est-ce correct ?
  {Character with Angles:imports.Angle, Poses:imports.Pose}
Signifie : 
- Injecter le chunk Character
- Remplacer {Angle} dans le chunk par imports.Angle
- Remplacer {Pose} dans le chunk par imports.Pose

** => OUI!!! par contre, il faut qu'on explore la syntaxe des selecteurs de variation **

###  2. Résolution des imports

  Ligne 75-85, vous importez des variations :
  imports:
    Outfit:
      - ../variations/outfit.urban.yaml
      - ../variations/outfit.chic.yaml

  Questions :
  - Quand on met une liste de fichiers, est-ce qu'on merge tous les choix possibles ? ** => oui **
  - Exemple : si outfit.urban.yaml a 5 tenues et outfit.chic.yaml a 8 tenues, imports.Outfit contiendra 13 choix ? ** => exactement, et idéalement, on pourrait ajouter des items inline dans la liste **
  - Ou bien on sélectionne aléatoirement un fichier puis un choix dedans ? ** => non **

###  3. Inline vs import pour variations

  Ligne 80-81, vous mixez imports et valeurs inline :
  Place:
    - "dark luxury modern living room..."
    - "dense tropical jungle..."

  Questions :
  - Les strings inline sont traitées comme des variations directes (pas besoin de fichier) ? ** => oui, check la doc de templating (/docs/cli/usage/ ) **
  - Peut-on mixer fichiers ET strings inline ? ** => en vision, oui! **
  Place:
    - ../variations/places.indoor.yaml  # fichier
    - "custom place description"         # inline

###  4. Chunks : template vs chunk

  Dans girl_solo.chunk.yaml (ligne 104), vous utilisez template: pour définir le contenu.
  Dans emma.chunk.yaml (ligne 131), vous utilisez chunk: pour définir les valeurs.

  Questions :
  - template: = le texte à injecter avec placeholders ? ** => oui **
  - chunk: = les valeurs pour remplir les placeholders ? ** => oui **
  - Est-ce que chunk: override/merge avec defaults: du parent ? ** => l'enfant (le + spécialisé), a la précedence dans les overrides, les defaults servent a injecter une valeur si rien n'est defini **

  Exemple de résolution attendue :
  - girl_solo a : Main = "30, slim build"
  - emma override : Main = "22, supermodel..."
   Résultat : Main = "22, supermodel..." (override complet) ** => oui **

###  5. Type de chunk : type:character

  Ligne 102 :
  type: character

  Questions :
  - À quoi sert le type ? Est-ce juste pour la documentation ou ça change le comportement ? ** => l'idée du type, c'est de plutot de la doc pour le moment. par contre, un chunck d'un type A ne doit être extends que par de chunk de type A **
  - Y a-t-il d'autres types prévus (scene, lighting, style, etc.) ? ** => oui, surtout pour les scenes de vie : j'aimerais pouvoir créer une histoire complete  **
  - Est-ce que ça impacte la validation ou l'ordre de résolution ? ** => non, pas que je sache **

### 6. Référence aux variations dans les chunks

  Ligne 133 :
  HairCut : Haircuts.BobCut

  Questions :
  - Haircuts.BobCut signifie "prendre le choix 'BobCut' dans le fichier importé Haircuts" ? ** => oui **
  - Le fichier haircuts.yaml doit avoir une structure spéciale avec des clés nommées ? ** => oui, un dictionnaire **
  - Ou bien BobCut est juste une des lignes/entrées dans le fichier ? ** => non **

  Format attendu de haircuts.yaml :
  - Option 1 : Dict avec clés ** => oui **
  BobCut: "bob cut, chin-length hair"
  LongHair: "long flowing hair, waist-length"

  - Option 2 : Liste simple
  - "bob cut, chin-length hair"
  - "long flowing hair, waist-length"

###  7. Ordre de résolution et héritage

  Dans hassaku_manga.template.yaml (ligne 39) :
  implements: '../template/hassaku_highdef.template.yaml'

  Questions :
  - implements hérite de tous les parameters: du parent ? ** => oui **
  - Peut-on override des paramètres spécifiques ? ** => oui **
  implements: '../template/hassaku_highdef.template.yaml'
  parameters:
    steps: 40  # override de steps: 30 du parent ** => oui, exactement **

 ### 8. Génération combinatoriale avec multi-imports

  Ligne 84-85 :
  Pose:
    - ../variations/hassaku/poses.classic.yaml
    - ../variations/hassaku/poses.dynamic.yaml

  En mode random (ligne 69), si on a 2 fichiers de poses :
  - Est-ce qu'on merge toutes les poses et on tire au hasard dedans ? ** => oui **
  - Ou on tire d'abord un fichier, puis une pose dedans ? ** => non **

###  9. Syntaxe chunks.positives

  Ligne 49 :
  template: |
    chunks.positives,
    {prompt}     

  Questions :
  - chunks.positives référence l'import positive: ../chunks/manga-positive.chunk.yaml ? ** => oui **
  - La syntaxe avec . permet de référencer les imports par leur clé ? ** => oui **
  - Est-ce que {prompt} est un placeholder réservé qui sera remplacé par le template: du prompt final ? ** => oui, c'est un placeholder reservé aux templates **

###  10. Gestion des virgules et formatage

  Les virgules finales dans le template (lignes 49, 51, 89, 91) :
  template: |
    chunks.positives,  # virgule
    {prompt}           # pas de virgule
    chunks.loras,      # virgule

  Questions :
  - Les virgules sont-elles préservées telles quelles dans le prompt final ? 
  - Ou y a-t-il un système de normalisation (trim, collapse des espaces, etc.) ?
  - Comment gérer les virgules en fin de ligne si une variation est vide ?
  ** => on a une mécanique de normalisation une fois les variation générées**

---

## Passe 2

 Points à clarifier

### 1. Syntaxe des sélecteurs de variation (vous mentionnez qu'il faut explorer ça)

  Vous avez dit "il faut qu'on explore la syntaxe des sélecteurs de variation". Actuellement, dans le système Phase 2, on a :

  {PlaceholderName:15}           # Limite à 15 choix aléatoires
  {PlaceholderName:#|1|5|22}     # Sélectionne index 1, 5, 22
  {PlaceholderName:$8}           # Poids 8 pour ordre des boucles
  {PlaceholderName:#|6|4|2$8}    # Combinaison des deux

  Questions :
  - Est-ce que cette syntaxe doit être supportée dans le nouveau système ? ** => oui **
  - Dans le contexte {Character with Angles:imports.Angle, Poses:imports.Pose}, peut-on ajouter des sélecteurs ? ** => oui **

  **Exemple hypothétique :**
  {Character with Angles:imports.Angle:15, Poses:imports.Pose:#|1|3|5}
  - Ou les sélecteurs se mettent ailleurs (dans la définition des imports) ? ** => non, ce n'est pas une piste que j'ai exploré **
  imports:
    Angle:
      source: ../variations/angles.yaml
      selector: :15  # ou limit: 15

### 2. Format des fichiers de variations : Dict vs Liste

  Vous avez dit que pour Haircuts.BobCut, le fichier doit être un dictionnaire. Mais pour les variations simples (ligne 80-81), on dirait une
  liste.

  Questions :
  - Est-ce que les fichiers .yaml peuvent avoir 2 formats différents selon l'usage ? ** => non, que des dict**
    - Format Dict : Quand on veut référencer par clé (Haircuts.BobCut)
    - Format Liste : Quand on veut juste un pool de variations

  **haircuts.yaml (format Dict pour référence par clé)**
  BobCut: "bob cut, chin-length hair"
  LongHair: "long flowing hair, waist-length"

  **poses.classic.yaml (format Liste pour pool)**
  - "standing, arms crossed"
  - "sitting elegantly"
  - "leaning against wall"
  - Peut-on mixer les deux dans un même fichier ? ** => non, que des dict **
  
  - **Mixed format ?**
  BobCut: "bob cut, chin-length hair"  # référençable par clé
  LongHair: "long flowing hair"
  - "random unnamed haircut"           # disponible en pool mais pas par clé ** => ca, c'est uniquement quand on inline des variations **

### 3. Merge de variations : ordre et priorité

  Quand on merge plusieurs sources :
  Outfit:
    - ../variations/outfit.urban.yaml    # 5 items
    - ../variations/outfit.chic.yaml     # 8 items
    - "custom red dress"                  # 1 item inline

  Questions :
  - L'ordre final des 14 items est-il préservé (urban d'abord, puis chic, puis inline) ? ** => oui **
  - Ou bien tout est mélangé aléatoirement après le merge ? ** => non, c'est la  stratégie de génération de variation qui le fait (CLI/src/templating/prompt_config.py)**
  - Si les deux fichiers ont des clés identiques, qui gagne ? ** => personne ne gagne, on a une erreur, il faut la remonter **
  
  **outfit.urban.yaml**
  Casual: "jeans and t-shirt"

  **outfit.chic.yaml**  
  Casual: "designer casual wear"  # Conflit !

### 4. Chunks : référence dans templates

  Ligne 49, vous utilisez chunks.positives pour référencer un import.

  Questions :
  - Est-ce que tous les imports peuvent être référencés avec la syntaxe à point ? ** => heu, en fait, c'est une mauvaise habitude de nommage de fichier, le point fait partie du nom de fichier, mais on ne cible pas une partie du chucnk en soit **
  imports:
    Character: ../chunks/emma.chunk.yaml

  template: |
    imports.Character,  # Est-ce valide ? ** => je veux bien qu'on reflechisse a une syntaxe plus claire, mais en l'etat, c'est valide dans mon idée **
  - Ou seulement les imports sous une clé spéciale chunks: ?
  imports:
    chunks:
      positive: ../chunks/manga-positive.chunk.yaml
    Character: ../chunks/emma.chunk.yaml  # Pas sous "chunks"

  template: |
    chunks.positive,      # OK
    imports.Character,    # OK ou erreur ?

### 5. Placeholder réservé {prompt}

  Vous avez dit que {prompt} est un placeholder réservé aux templates.

  Questions :
  - Quels sont tous les placeholders réservés ?
    - {prompt} : Le template du fichier prompt final ** => oui **
    - {negprompt} : Le negative_prompt du fichier prompt final (ligne 54) ** => oui **
    - Autres ? ({loras}, {params}, etc.) ** => les loras aussi. **
  - Que se passe-t-il si un chunk ou une variation définit un placeholder avec un nom réservé ? ** => on obtient une erreur **
  __emma.chunk.yaml__
  chunk:
    prompt: "something"  # Conflit avec {prompt} réservé ?

### 6. Type de chunk : validation de l'héritage

  Vous avez dit : "un chunk d'un type A ne doit être extends que par de chunk de type A"

  Questions :
  - Doit-on valider cette règle au runtime et rejeter avec une erreur ? ** => oui **
  **girl_solo.chunk.yaml**
  type: character

  **landscape.chunk.yaml**
  type: scene
  implements: girl_solo.chunk.yaml  # ERREUR : type mismatch
  - Ou c'est juste une convention documentée mais pas enforced ?

### 7. Normalisation des virgules et espaces

  Vous avez dit qu'il y a une "mécanique de normalisation une fois les variations générées".

  Questions :
  - Concrètement, quelles sont les règles ? 
    - Trim des espaces en début/fin de ligne ? ** => oui **
    - Collapse des virgules multiples (,, → ,) ? ** => oui **
    - Suppression des virgules orphelines en début/fin ? ** => oui **
    - Normalisation des espaces autour des virgules (word,word → word, word) ? ** => oui **
  - Exemple concret de normalisation :
  **Avant normalisation**
  template: |
    chunks.positives,
    {Outfit},

    detailed background,

  ** Si {Outfit} est vide, après normalisation :**
  "chunks.positives, detailed background" ** => oui **
  **Ou :**
  "chunks.positives,, detailed background"  # virgule orpheline ? ** => non **

### 8. Scénarios de vie (scenes)

  Vous avez mentionné vouloir "créer une histoire complète" avec des types scene. ** => c'est encore trop tot! **

  Questions :
  - Avez-vous une vision de comment ça fonctionnerait ?
    - Un fichier de scénario qui orchestre plusieurs prompts ?
    - Des chunks scene qui peuvent contenir des character chunks ?

  **story.scenario.yaml ?**
  type: story
  scenes:
    - name: "Morning routine"
      chunks: [emma, kitchen_scene, casual_outfit]
    - name: "Office work"
      chunks: [emma, office_scene, business_outfit]
  - Ou c'est pour plus tard et on se concentre d'abord sur les chunks simples ?

### 9. Résolution des chemins relatifs

  Tous vos exemples utilisent des chemins relatifs (../variations/, ../chunks/).

  Questions :
  - Relatif à quoi ? Au fichier YAML qui contient l'import ? ** => relatif à la config file sdgen_config.json, qui pointe un "Configs_dir" **
  **Si on est dans /prompts/hassaku/emma.prompt.yaml**
  imports:
    Outfit: ../variations/outfit.yaml
    **Résolu comme : /prompts/variations/outfit.yaml (relatif au fichier)**
  - Ou relatif au configs_dir de .sdgen_config.json ?
  **configs_dir = /path/to/templates**
  imports:
    Outfit: ../variations/outfit.yaml
    # Résolu comme : /path/to/variations/outfit.yaml (relatif à configs_dir)

### 10. Gestion d'erreurs et validation

  Questions :
  - Que se passe-t-il si un fichier importé est introuvable ?  ** => on obtient une erreur **
  - Que se passe-t-il si un placeholder référencé n'existe pas ? ** => on obtient une erreur **
  template: |
    {Character with Angles:imports.NonExistent}  # imports.NonExistent n'existe pas
  - Doit-on valider avant la génération (fail-fast) ou pendant (skip avec warning) ?


## ERREURS : idéalament, on ne doit pas jeter d'exceptions : on essaie de resoudre au maximum et on affiche toutes les erreurs, pour simplifer la correction des fichiers.

---

## Passe 3 - Clarifications finales

###  1. Format des fichiers variations : 100% Dict

  Vous avez dit "que des dict" (ligne 316, 328). Mais dans votre exemple initial (lignes 80-81), vous avez :
  Place:
    - "dark luxury modern living room..."
    - "dense tropical jungle..."

  Question critique :
  Si les fichiers .yaml sont uniquement des dict, comment gérer les variations sans clé nommée ?
  ** => il s'agit de variations inlines, pas de fichiers : elle sont directement utilisées. si on essaie d'y accéder par clé, alors on mets un warning à l'execution **

  Option A : Clés auto-générées
  # places.yaml (fichier)
  place_1: "dark luxury modern living room..."
  place_2: "dense tropical jungle..."

  # Mais dans le prompt, on ne veut pas référencer par clé
  {Place}  # tire parmi toutes les valeurs du dict

  Option B : Les strings inline sont une exception
  # Fichiers .yaml = TOUJOURS des dict
  # haircuts.yaml
  BobCut: "bob cut"
  LongHair: "long hair"

  # Mais les inline strings dans imports: sont traitées différemment
  imports:
    Place:
      - "inline string 1"  # Pas besoin de clé
      - "inline string 2"

  Laquelle est correcte ? Comment distinguer "variation avec clé" vs "variation sans clé" ?
** => la seconde est correcte **

---

###   2. Syntaxe de référence aux imports dans templates

  Vous avez dit (ligne 364) : "je veux bien qu'on réfléchisse à une syntaxe plus claire".

  Actuellement, vous avez :
  imports:
    chunks:
      positive: ../chunks/manga-positive.chunk.yaml
    Character: ../chunks/emma.chunk.yaml

  template: |
    chunks.positive,    # Référence nested import
    imports.Character,  # Référence top-level import ?

  Question :
  Est-ce que la syntaxe devrait être unifiée ?

  Proposition A : Préfixe imports. pour tout
  template: |
    imports.chunks.positive,  # Chemin complet
    imports.Character,         # Top-level

  Proposition B : Syntaxe sans préfixe (juste le nom de la clé)
  template: |
    chunks.positive,  # Résolution automatique dans imports
    Character,        # Résolution automatique dans imports

  Proposition C : Distinction chunk vs variation
  template: |
    @chunks.positive,  # @ pour les chunks
    {Character},       # {} pour les variations

  Laquelle préférez-vous ? Ou une autre syntaxe ?

** => la proposition C est la meilleure, elle rends l'usage plus explicite **
---

### 3. Sélecteurs dans le contexte with

  Vous avez dit "oui" pour supporter les sélecteurs dans with (ligne 300).

  Question :
  Comment parser cette syntaxe ?
  {Character with Angles:imports.Angle:15, Poses:imports.Pose:#|1|3|5}

  Parsing possible :
  - Angles = nom du placeholder à override
  - : = séparateur
  - imports.Angle = source de la variation
  - :15 = sélecteur appliqué à imports.Angle

  Mais ambiguïté :
  {Character with Angles:imports.Angle:15$3}
  #                                    ^  ^
  #                                    |  |
  #                    Est-ce :15 puis $3, ou :15$3 ?

  Proposition de syntaxe sans ambiguïté :
Option 1 : Parenthèses pour les sélecteurs
  {Character with Angles:imports.Angle(:15), Poses:imports.Pose(#|1|3|5)}

Option 2 : Syntaxe de filtre (style Jinja2)
  {Character with Angles:imports.Angle|limit:15, Poses:imports.Pose|select:#1,3,5}

Option 3 : Bracket notation
  {Character with Angles:imports.Angle[15], Poses:imports.Pose[#1,3,5]}

  Laquelle préférez-vous ?
** => l'option 3 semble etre plus versatile, on peut faire un nombre de varaition random, un set de varaitions selectionnées, utiliser des clés, donner un poids dans l'ordre de la combinatoire et informer qu'on peut pick en random mais sans intégrer dans le calcul de la combinatoire **

---

###  4. Résolution des chemins : Clarification

  Vous avez dit (ligne 449) : "relatif à la config file sdgen_config.json, qui pointe un 'Configs_dir'".

  Question :
  Si on a :
  // ~/.sdgen_config.json
  {
    "configs_dir": "/home/user/sd-templates"
  }

  Et dans /home/user/sd-templates/prompts/emma.prompt.yaml :
  imports:
    Outfit: ../variations/outfit.yaml

  Le chemin est résolu comme :
  - Option A : /home/user/sd-templates/../variations/outfit.yaml → /home/user/variations/outfit.yaml (relatif à configs_dir)
  - Option B : /home/user/sd-templates/prompts/../variations/outfit.yaml → /home/user/sd-templates/variations/outfit.yaml (relatif au fichier
  YAML)

  Laquelle est correcte ?
** =>  c'est l'option B, elle laisse moins de place a des calculs de chemins qui peuvent être particulierement pénibles**

---

### 5. Merge de variations : Gestion des clés en conflit

  Vous avez dit (ligne 346) : "personne ne gagne, on a une erreur".

  Question :
  Comment détecter le conflit ? ** => on construit un dictoinnaire au runtime, ca devrait être rapidement visible qu'on a une dup de key **

  imports:
    Outfit:
      - ../variations/outfit.urban.yaml   # {Casual: "jeans"}
      - ../variations/outfit.chic.yaml    # {Casual: "designer wear"}

  Lors du merge :
  1. On charge outfit.urban.yaml → Dict avec Casual
  2. On charge outfit.chic.yaml → Dict avec Casual
  3. Erreur immédiate : "Duplicate key 'Casual' in Outfit imports" ** => oui, on a un conflit **

  Mais que se passe-t-il si :
  imports:
    Outfit:
      - ../variations/outfit.urban.yaml   # {Casual: "jeans", Formal: "suit"}
      - "Casual: designer wear"            # String inline (pas un dict) ** => les inline sont des strings, pas des key/value, on les ajoute directement au dict avec un clé aléatoire (guid, hash de la valeur ou whatever)  ** 

  Est-ce aussi une erreur ? Ou les strings inline sont traitées différemment ?

---

### 6. Gestion des erreurs : Accumulation vs Fail-fast

  Vous avez dit (ligne 468) : "on essaie de résoudre au maximum et on affiche toutes les erreurs".

  Question :
  Concrètement, quel est le workflow ?

  Scénario :
  imports:
    Outfit: ../variations/outfit.yaml     # Fichier introuvable
    Character: ../chunks/emma.chunk.yaml  # OK
    Pose: ../variations/missing.yaml      # Fichier introuvable

  template: |
    {Character with Angles:imports.NonExistent}  # Import inexistant
    {Outfit}  # Variation manquante (fichier pas trouvé)

  Comportement attendu :
  1. Phase de validation (avant génération) :
    - Collecter toutes les erreurs :
        - imports.Outfit : fichier introuvable
      - imports.Pose : fichier introuvable
      - imports.NonExistent : import inexistant
    - Afficher toutes les erreurs ensemble (pas une par une)
    - Arrêter avant la génération
  2. Ou mode dégradé :
    - Résoudre ce qui est possible
    - Remplacer les erreurs par des placeholders vides ou des messages
    - Générer quand même avec warnings

  Lequel préférez-vous ?
** => le premier **

---

### 7. Placeholders réservés : Liste complète

  Vous avez dit (lignes 381-383) : {prompt}, {negprompt}, {loras}.

  Questions :
  - Y a-t-il d'autres placeholders réservés ? ({params}, {template}, {name}, etc.) ** => il faut qu'on puisse override les param de génération, mais sinon, non **
  - Les placeholders réservés sont-ils case-sensitive ? ({Prompt} vs {prompt}) ** => oui **
  - Peut-on avoir des placeholders réservés contextuels (uniquement dans certains types de fichiers) ? 
Dans un .template.yaml
  {prompt}  # OK, réservé

Dans un .chunk.yaml
  {prompt}  # Erreur ou OK ? ** => oui, bien vu! **

---

### 8. Chunks : template vs chunk - Résolution complète

  Dans emma.chunk.yaml, vous avez :
  implements: '../chunks/girl_solo.chunk.yaml'

  chunk:
    Main: "22, supermodel..."
    HairCut: Haircuts.BobCut
    Angle: Angles.Straight

  Question :
  Le chunk emma n'a pas de section template:. Est-ce que :
  - Option A : Il hérite du template: de girl_solo.chunk.yaml ? 
  - Option B : Il doit obligatoirement avoir un template: s'il veut être utilisé directement ?

** => Option A, vu que les chunks de base sont specifiés pour emma **

  Et si emma a un template: :
emma.chunk.yaml
  implements: '../chunks/girl_solo.chunk.yaml'

  template: |
    {Main}, beautiful woman, {HairCut}, {HairColor} hair

  chunk:
    Main: "22, supermodel..."

  Est-ce que le template: de emma remplace complètement celui de girl_solo, ou est-ce une erreur ?
  ** => ca override, mais on perd un peu l'interet du template: **

---

### 9. Référence par clé dans variations : Syntaxe exacte

  Vous avez dit (ligne 222-224) : oui, dict avec clés.

  Question :
  Dans un fichier .yaml, quelle est la syntaxe exacte ? ** => non, dans le dict python au runtime **

  Option A : YAML dict simple
  haircuts.yaml
  BobCut: "bob cut, chin-length hair"
  LongHair: "long flowing hair, waist-length"
  Pixie: "pixie cut, short spiky hair"

  Option B : Structure avec métadonnées
  haircuts.yaml
  variations:
    BobCut: "bob cut, chin-length hair"
    LongHair: "long flowing hair, waist-length"

  Option C : Liste de dicts (comme le format actuel Phase 2)
  haircuts.yaml
  - key: BobCut
    value: "bob cut, chin-length hair"
  - key: LongHair
    value: "long flowing hair, waist-length"

  Laquelle est correcte ?

---

### 10. Type de chunk : Validation stricte

  Vous avez dit (ligne 394) : oui, valider avec erreur.

  Question :
  Que se passe-t-il dans ce cas ?

  **base.chunk.yaml**
  **PAS de type défini**

  **emma.chunk.yaml**
  type: character
  implements: base.chunk.yaml  # base n'a pas de type

  Comportement :
  - Option A : Erreur : "base.chunk.yaml must have type 'character'"
  - Option B : Warning : "base.chunk.yaml has no type, assuming 'character'"
  - Option C : OK : Les chunks sans type peuvent être hérités par n'importe quel type

  Laquelle préférez-vous ?
** => option B **

  ---

 ---
  Passe 4 - Dernières clarifications critiques

 ### 1. Syntaxe bracket [] - Détails complets

  Vous avez choisi l'option 3 (bracket notation) pour les sélecteurs (ligne 582). Vous avez dit : "on peut faire un nombre de variation random, un set de
   variations sélectionnées, utiliser des clés, donner un poids dans l'ordre de la combinatoire et informer qu'on peut pick en random mais sans intégrer
  dans le calcul de la combinatoire".

  Questions critiques :

  Quelle est la syntaxe exacte pour chaque cas ?

  A. Limite aléatoire (ancien :15) :
  {Angle[15]}              # Tire 15 variations aléatoires  ** => oui  **

  B. Sélection par index (ancien #|1|3|5) :
  {Angle[#1,3,5]}          # Sélectionne index 1, 3, 5 ** => oui, moin d'ambiguité **
  _ Ou :
  {Angle[1,3,5]}           # Sans le # ?

  C. Sélection par clé :
  {Haircut[BobCut,LongHair]}   # Sélectionne par nom de clé ** => oui **

  D. Poids combinatoire (ancien $8) :
  {Angle[$8]}              # Poids 8 
  _ Ou combiné avec limite :
  {Angle[15,$8]}           # 15 variations, poids 8 
** => les 2 syntaxes sont correctes **


  E. Random sans combinatoire :
  Vous avez mentionné "pick en random mais sans intégrer dans le calcul de la combinatoire". Qu'est-ce que ça signifie exactement ?
  {Angle[random]}          # Une variation random, pas dans la combinatoire ?
  {Angle[?15]}             # 15 variations mais en mode "non-combinatorial" ?
** => mieux : un poids à 0 exclu de la combinatoire (le poids par defaut est 1) **


  Pouvez-vous donner la syntaxe exacte pour tous ces cas ?

  ---
### 2. Nouvelle syntaxe avec @ pour chunks

  Vous avez choisi la Proposition C (ligne 548) :
  template: |
    @chunks.positive,  # @ pour les chunks
    {Character},       # {} pour les variations

  Questions :

  A. Utilisation de @ partout ?
  _ Dans un .template.yaml :
  template: |
    @chunks.positive,     # OK
    {prompt},             # Placeholder réservé
    {Place},              # Variation
    @Character,           # Import direct d'un chunk ?

** => yes! **


  B. Syntaxe @ avec with ?
  _ Avant (ligne 88) :
  {Character with Angles:imports.Angle, Poses:imports.Pose}

  _ Nouvelle syntaxe avec @ ?
  @Character with Angles:{Angle}, Poses:{Pose}
  _ Ou :
  @{Character with Angles:{Angle}, Poses:{Pose}} ** => c'est plus clair comme ca **

  C. Différence chunk vs variation au runtime ?
  Si on importe un chunk et une variation avec le même nom :
  imports:
    Character: ../chunks/emma.chunk.yaml     # Chunk
    Haircut: ../variations/haircuts.yaml     # Variation

  template: |
    @Character,   # Injecte le chunk (son template résolu)
    {Haircut},    # Tire une variation

  Est-ce correct ? ** => oui **

  ---
### 3. Format YAML des fichiers variations - Confirmation

  Ligne 726, vous avez répondu "non, dans le dict python au runtime" à la question sur la syntaxe YAML.

  Mais vous n'avez pas précisé quelle option (A, B ou C) est correcte !

  Question critique :

  Dans le fichier haircuts.yaml sur disque, quelle est la syntaxe ?

  _ Option A : YAML dict simple (recommandé pour clarté)
  BobCut: "bob cut, chin-length hair"
  LongHair: "long flowing hair, waist-length"
  Pixie: "pixie cut, short spiky hair"

  _ Option B : Structure avec wrapper
  variations:
    BobCut: "bob cut, chin-length hair"
    LongHair: "long flowing hair, waist-length"

  _ Option C : Liste de dicts
  - key: BobCut
    value: "bob cut, chin-length hair"
  - key: LongHair
    value: "long flowing hair, waist-length"

  Laquelle est correcte pour les fichiers .yaml sur disque ?
** => option A, le yaml dict simple **
  ---
### 4. Inline strings : Clé auto-générée

  Vous avez dit (ligne 632) : "les inline sont des strings, pas des key/value, on les ajoute directement au dict avec une clé aléatoire (guid, hash de la
   valeur ou whatever)".

  Questions :

  A. Format de la clé auto-générée ?
  _ GUID ?
  {"f47ac10b-58cc-4372-a567-0e02b2c3d479": "inline string"}

  _ Hash ?
  {"7d8e3a2f": "inline string"}  # Hash court

  _ Index numérique ?
  {"_inline_0": "inline string"}
  {"_inline_1": "another inline"}

** =>  le hash court est mieux, car il garde un minimum de reproductibilité **  

  B. Peut-on référencer une inline par sa clé auto-générée ?
  imports:
    Outfit:
      - "red dress"
      - "blue suit"

  chunks:
    Main: Outfit._inline_0  # Référence directe à "red dress" ?

  Ou c'est impossible/non recommandé ?
** => non, pas de ref directe  **
  ---
### 5. Section chunks vs chunk dans les fichiers

  J'ai remarqué une incohérence dans vos exemples :

  Ligne 131 de la spec originale :
  _ emma.chunk.yaml
  chunk:  # Singulier
    Main: "22, supermodel..."

  Ligne 131 du fichier actuel (modifié) :
  _ emma.chunk.yaml
  chunks:  # Pluriel
    Main: 22, supermodel...

  Question :
  Quelle est la syntaxe correcte ? chunk: ou chunks: ?
** => au pluriel, comme pour les imports **
  ---
### 6. Override de template: dans un chunk enfant

  Vous avez dit (ligne 717) : "ça override, mais on perd un peu l'interet du template".

  Question :
  Est-ce que c'est autorisé mais déconseillé, ou est-ce qu'on doit valider et rejeter avec erreur ?

  # emma.chunk.yaml
  implements: girl_solo.chunk.yaml

  template: |
    # Override complet du template parent
    {Main}, beautiful, {HairCut}

  _ Comportement ?
  _ A. OK, mais warning : "Overriding parent template, consider creating a new base chunk"
  _ B. Erreur : "Cannot override template from parent chunk"
  _ C. OK sans warning (totalement autorisé)
** => OK mais warning **
  ---
### 7. Placeholders réservés contextuels - Liste exacte

  Vous avez dit (ligne 685) : "oui, bien vu!" pour les placeholders contextuels.

  Question :
  Pouvez-vous donner la liste exacte des placeholders réservés par type de fichier ?

  _ .template.yaml
  Réservés : {prompt}, {negprompt}, {loras} ** => oui **

  _ .chunk.yaml
  Réservés : ??? (Aucun ? Ou certains autorisés ?) ** => pas encore d'idée la dessus **

  _ .prompt.yaml
  Réservés : {prompt}, {negprompt}, {loras} ** => ouis **

  _ .yaml (variations)
  Réservés : ??? (Aucun ?) ** => aucun **

  ---
### 8. Override de parameters: - Merge ou Replace ?

  Vous avez dit (ligne 244) : oui, on peut override des paramètres spécifiques.

  Question :
  Est-ce un merge (on garde les autres paramètres) ou un replace (on écrase tout) ?

  _ hassaku_highdef.template.yaml (parent)
  parameters:
    width: 832
    height: 1216
    steps: 30
    cfg_scale: 6

  _ hassaku_manga.template.yaml (enfant)
  implements: hassaku_highdef.template.yaml
  parameters:
    steps: 40

  _ Résultat final ?
  _ Option A (MERGE) :
  parameters:
    width: 832      # Hérité
    height: 1216    # Hérité
    steps: 40       # Overridé
    cfg_scale: 6    # Hérité

  _ Option B (REPLACE) :
  parameters:
    steps: 40       # Seul paramètre

  Laquelle est correcte ?

** => option a, on override le parametre, pas toute la section **

  ---
### 9. Gestion d'erreurs : Format du rapport

  Vous avez dit (ligne 669) : "Phase de validation (avant génération), afficher toutes les erreurs ensemble, arrêter avant la génération".

  Question :
  Quel est le format attendu du rapport d'erreurs ?

  Option A : Liste simple
  Validation errors found:
  - imports.Outfit : file not found '../variations/outfit.yaml'
  - imports.Pose : file not found '../variations/missing.yaml'
  - template line 1 : import 'NonExistent' not defined
  Total: 3 errors. Generation aborted.

  Option B : Structuré par catégorie
  === Validation Errors ===

  File Imports (2 errors):
    - Outfit: ../variations/outfit.yaml (not found)
    - Pose: ../variations/missing.yaml (not found)

  Template Resolution (1 error):
    - Line 1: import 'NonExistent' not defined

  Total: 3 errors. Generation aborted.

  Option C : JSON pour parsing
  {
    "errors": [
      {"type": "import", "name": "Outfit", "file": "...", "message": "not found"},
      {"type": "import", "name": "Pose", "file": "...", "message": "not found"},
      {"type": "template", "line": 1, "message": "..."}
    ],
    "count": 3
  }

  Laquelle préférez-vous ?

** => c'est en 2 etapes : on génère le json, pouis on l'exploite (on l'affiche en pretty dans la console et on le met dans un fichier de log du run)  ** 


  ---
### 10. Résolution des chemins : Edge cases

  Vous avez dit (ligne 607) : Option B, relatif au fichier YAML.

  Questions sur edge cases :

  A. Imports imbriqués :
  _ /templates/prompts/emma.prompt.yaml
  imports:
    Character: ../chunks/emma.chunk.yaml

  _ /templates/chunks/emma.chunk.yaml
  imports:
    Haircuts: ../variations/haircuts.yaml

  _ haircuts.yaml est résolu comme :
  _ /templates/chunks/../variations/haircuts.yaml
  _ → /templates/variations/haircuts.yaml

  Est-ce correct ? ** => oui **

  B. Chemin absolu :
  imports:
    Outfit: /home/user/custom/outfit.yaml  # Chemin absolu
** => non, sinon on va galéré entre linux et windows **

  Est-ce supporté ?

  C. Symlinks :
  Si configs_dir pointe vers un symlink, on suit le symlink ou on reste sur le chemin symbolique ?
** => aucune idée de ca, on peut le voir plus tard? **

  ---

 ---
  Passe 5 - Micro-clarifications finales (dernière passe !)

### 1. Sélecteurs bracket : Combinaisons complexes

  Vous avez validé plusieurs syntaxes. Comment les combiner ?

  # Cas simples (validés) :
  {Angle[15]}              # 15 random
  {Angle[#1,3,5]}          # Index 1,3,5
  {Angle[$8]}              # Poids 8
  {Angle[BobCut,LongHair]} # Par clé

  # Combinaisons ?
  {Angle[#1,3,5,$8]}       # Index + poids
  {Angle[15,$0]}           # 15 random, poids 0 (hors combinatoire)
  {Angle[BobCut,LongHair,$5]} # Par clé + poids

  Question : L'ordre des éléments dans [] est-il libre ou fixe ?
  - Libre : {Angle[$8,15]} ou {Angle[15,$8]} (équivalents)
  - Fixe : Toujours [sélecteur,poids] (ordre obligatoire)

** => combinaisons : c'est libre, séparé par des points virgules **

### 2. Syntaxe @{...} avec with - Parsing

  Vous avez validé :
  @{Character with Angles:{Angle}, Poses:{Pose}}

  Question : Dans Angles:{Angle}, est-ce que :
  - Angles = nom du placeholder dans le chunk à override
  - {Angle} = référence à l'import Angle (variation) ** => c'est ca! **

  Donc cette syntaxe signifie :
  _ Résolution :
  _ 1. Charger le chunk Character
  _ 2. Dans son template, remplacer {Angles} par une variation tirée de {Angle}
  _ 3. Dans son template, remplacer {Poses} par une variation tirée de {Pose}

  C'est correct ?
** => oui, c'est bien ca! **

  Et pour les sélecteurs :
  @{Character with Angles:{Angle[15]}, Poses:{Pose[$5]}}
  Est-ce que {Angle[15]} signifie "tirer 15 variations de Angle pour ce placeholder" ?
** => oui **

### 3. Hash court pour inline - Algorithme

  Vous avez choisi le hash court (ligne 905).

  Question : Quel algorithme ?
  - MD5 court : md5("red dress")[:8] → "7d8e3a2f" ** => le MD5 **
  - SHA256 court : sha256("red dress")[:8] → "a1b2c3d4"
  - Hash simple : hash("red dress") % 100000000 → numérique

  Ou peu importe (à décider à l'implémentation) ?
** => le MD5, leger et sans trop de conséquences **

### 4. Placeholders réservés dans chunks - Proposition

  Vous avez dit (ligne 968) : "pas encore d'idée là-dessus".

  Proposition :
  Dans les .chunk.yaml, interdire tous les placeholders réservés aux templates :
  - {prompt} → Erreur
  - {negprompt} → Erreur
  - {loras} → Erreur

  Raison : Un chunk est réutilisable, il ne doit pas dépendre du contexte template.

  Êtes-vous d'accord ? ** => completement d'accord**

### 5. Erreurs : Logging du JSON

  Vous avez dit (ligne 1051) : "on génère le json, puis on l'exploite (affiche pretty + fichier log)".

  Question : Format du fichier de log ?
  _ Option A : Fichier par run
  ~/.sdgen/logs/run_2025-10-09_14-23-45_errors.json

  _ Option B : Fichier unique rotatif
  ~/.sdgen/logs/validation_errors.log (append)

  _ Option C : Dans le output_dir du run
  /output/session_name/errors.json

  Laquelle préférez-vous ?
** => Option C **

### 6. Chemins absolus Windows - Alternative

  Vous avez dit (ligne 1079) : "non, sinon on va galérer entre linux et windows".

  Question : Et si on supporte une syntaxe spéciale pour les chemins "externes" ?

  imports:
    _ Relatif (normal)
    Outfit: ../variations/outfit.yaml

    # Externe avec préfixe (optionnel)
    CustomData: file:///home/user/custom/data.yaml  # Linux
    CustomData: file:///C:/Users/user/custom.yaml   # Windows

  Ou c'est trop complexe et on reste sur "relatif uniquement" ?
** => pour l'instant, juste relatif, on a une classe loader qui pourra etre enrichie plus tard **

### 7. Normalisation : Lignes vides

  Vous avez validé la normalisation des virgules, espaces, etc. (lignes 409-414).

  Question : Et les lignes vides dans les templates ?

  template: |
    1girl, {Main},

    detailed background, {Place},


    {Outfit}, beautiful

  Après normalisation :
  - Option A : Tout sur une ligne : "1girl, {Main}, detailed background, {Place}, {Outfit}, beautiful"
  - Option B : Préserver 1 ligne vide max : Garder les paragraphes logiques
  - Option C : Préserver toutes les lignes vides

  Laquelle ? ** => il me semble que stable diffusion ne se soucie pas de lignes vides, donc la B pourrait etre pas mal**

### 8. Merge de chunks: parent/enfant

  Dans les .chunk.yaml, comment fonctionne le merge de la section chunks: ?

  _ girl_solo.chunk.yaml
  defaults:
    Main: "30, slim build"
    HairCut: BobCut

  chunks:
    Angle: Angles.Straight  # Défini dans le parent

  _ emma.chunk.yaml  
  implements: girl_solo.chunk.yaml

  chunks:
    Main: "22, supermodel..."  # Override
    HairCut: Haircuts.BobCut   # Override
    # Angle pas redéfini

  Question : Est-ce que emma hérite de Angle: Angles.Straight du parent ?
  - Oui (merge) : emma.chunks = {Main: "22...", HairCut: ..., Angle: Angles.Straight}
  - Non (replace) : emma.chunks = {Main: "22...", HairCut: ...} (Angle perdu)

** => oui, l'enfant hérite **

### 9. Validation : Ordre d'exécution

  Vous avez dit : collecter toutes les erreurs avant de générer.

  Question : Dans quel ordre valider ?

  Proposition :
  1. Validation structurelle : YAML bien formé, champs requis présents
  2. Validation des chemins : Tous les fichiers existent
  3. Validation de l'héritage : implements corrects, types compatibles
  4. Validation des imports : Pas de clés dupliquées, imports référencés existent
  5. Validation du template : Placeholders résolus, pas de réservés interdits

  Si erreur à l'étape N, on continue quand même les étapes N+1 à 5 ?
  Ou on arrête dès qu'une étape a des erreurs ?

** => on essaie de valider au plus loin, ca evite 50 aller retour **

### 10. Version du format - Migration

  Vous avez version: '2.0' dans tous vos exemples (ligne 10).

  Questions :
  - Est-ce que la version est obligatoire dans tous les fichiers ? ** => oui **
  - Que se passe-t-il si on charge un fichier sans version: ?
    - Erreur : "version field required"
    - Assume v2.0 : Warning + assume latest
    - Assume v1.0 : Rétro-compatibilité ** => ca **
    - Y a-t-il un plan de migration entre versions ? 
    sdgen migrate config.v1.yaml --to=2.0
    ** => non **


  ---