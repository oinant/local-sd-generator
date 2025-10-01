# Product Ideas & Future Improvements

## 1. Session Configuration Metadata Improvements

### 1.1 Ajouter les options du menu interactif dans session_config.txt

**Problème actuel :**
Le fichier `session_config.txt` généré après chaque run ne contient pas les choix faits dans le menu interactif (mode de génération, mode de seed, nombre d'images, etc.).

**Solution proposée :**
Inclure dans `session_config.txt` :
- Mode de génération choisi (`combinatorial` / `random`)
- Mode de seed choisi (`fixed` / `progressive` / `random`)
- Nombre d'images demandé
- Seed de base utilisé
- Toutes les options configurables du run

**Bénéfices :**
- Reproductibilité complète des sessions
- Documentation automatique des choix effectués
- Facilite le debugging et l'analyse des runs

---

## 2. Format JSON Pretty-Print pour session_config.txt

### 2.1 Améliorer la lisibilité du fichier de configuration

**Problème actuel :**
- La ligne `fichiers_variations` contient du JSON sur une seule ligne, difficile à lire
- Le format global du fichier n'est pas structuré

**Solution proposée :**
Transformer `session_config.txt` en un véritable fichier JSON structuré avec indentation :

```json
{
  "session_name": "my_generation_session",
  "timestamp": "2025-09-30_14-30-45",
  "prompt_template": "masterpiece, {Expression}, {Angle}",
  "negative_prompt": "low quality",
  "generation_mode": "random",
  "seed_mode": "progressive",
  "base_seed": 42,
  "max_images": 100,
  "variation_files": {
    "Expression": "variations/expressions.txt",
    "Angle": "variations/angles.txt"
  },
  "variations_loaded": {
    "Expression": ["happy", "sad", "angry", "surprised"],
    "Angle": ["front view", "side view", "3/4 view"]
  },
  "total_combinations": 12,
  "actual_images_generated": 100
}
```

**Bénéfices :**
- Lisibilité améliorée
- Facilité de parsing pour scripts automatisés
- Structure extensible pour futures fonctionnalités

---

## 3. Configuration Run Directement depuis JSON

### 3.1 Support de fichiers de configuration JSON en entrée

**Extension de la solution 2 :**
Une fois le format JSON en place, permettre de lancer une génération directement avec un fichier de config :

```bash
python my_generator.py --config session_config.json
```

ou via l'API du générateur :

```python
generator = ImageVariationGenerator.from_config_file("session_config.json")
generator.run()
```

**Bénéfices :**
- Réutilisation facile de configurations précédentes
- Automatisation de workflows de génération
- Partage de configurations entre utilisateurs
- Batch processing de multiples configurations

---

## 4. Sélection Manuelle d'Index de Variations

### 4.1 Syntaxe pour spécifier des index précis

**Fonctionnalité actuelle :**
`{Hair:2}` → sélectionne 2 variations aléatoires parmi toutes les variations de Hair

**Nouvelle syntaxe proposée :**
`{Hair:#|1|5|22}` → sélectionne spécifiquement les variations aux index 1, 5 et 22

**Exemples d'utilisation :**

```python
# Mélange des deux syntaxes
prompt = "beautiful girl, {Hair:#|1|5|22}, {Expression:10}, {Angle:#|0|2}"

# Cas d'usage 1: Tester des combinaisons spécifiques connues
# Vous savez que les coupes 1, 5, 22 fonctionnent bien ensemble
prompt = "{Hair:#|1|5|22}, {Outfit:#|3|7}"

# Cas d'usage 2: Exclure certaines variations problématiques
# Au lieu de lister toutes celles qu'on veut, on pourrait avoir une syntaxe d'exclusion
# (future extension)
prompt = "{Hair:!|4|8|15}"  # Exclut les index 4, 8, 15
```

**Comportement attendu :**
- `{Hair:2}` → 2 variations aléatoires (comportement actuel)
- `{Hair:#|1|5|22}` → variations aux index 1, 5, 22 exactement
- `{Hair}` → toutes les variations (comportement actuel)
- `{Hair:0}` → placeholder supprimé du prompt ou remplacé par "" (voir section 4.2)

**Extensions futures possibles :**
- `{Hair:!|4|8}` → toutes sauf index 4 et 8
- `{Hair:#|1-5|10-15}` → ranges d'index (1 à 5 et 10 à 15)
- `{Hair:#|even}` ou `{Hair:#|odd}` → index pairs/impairs

### 4.2 Placeholder optionnel avec valeur 0

**Nouvelle fonctionnalité : Désactivation de placeholder**

Permet de désactiver dynamiquement un placeholder lors de la génération en utilisant la valeur `0`.

**Syntaxe :**
```python
prompt_template = "beautiful girl, {Hair:0}, {Expression}, detailed portrait"
```

**Comportement :**
- `{Hair:0}` → Le placeholder est complètement retiré du prompt final
- Équivalent à ne pas avoir le placeholder du tout
- Le prompt devient : `"beautiful girl, , detailed portrait"` puis nettoyé en `"beautiful girl, detailed portrait"`

**Cas d'usage :**

1. **Prompts conditionnels selon le contexte :**
```python
# Version avec cheveux
prompt = "portrait, {Hair}, {Expression}, beautiful"
# Génère: "portrait, long blonde hair, smiling, beautiful"

# Version sans cheveux (chauve, casque, etc.)
prompt = "portrait, {Hair:0}, {Expression}, beautiful"
# Génère: "portrait, smiling, beautiful"
```

2. **Tests A/B sur l'impact d'une variation :**
```python
# Run 1 : Avec l'élément
generator = create_generator("masterpiece, {Lighting}, {Pose}", ...)

# Run 2 : Sans l'élément pour comparer
generator = create_generator("masterpiece, {Lighting:0}, {Pose}", ...)
```

3. **Génération combinatoire avec option "aucun" :**
```python
# Fichier: accessories.txt
0→  # Ligne vide ou absente = pas d'accessoire
1→wearing glasses
2→wearing hat
3→wearing necklace

# Prompt
prompt = "portrait, {Accessories}, beautiful"
# Génère des variations avec ET sans accessoires
```

4. **Prompts flexibles selon le nombre de variations :**
```python
# Si on veut parfois désactiver un élément
prompt = "anime girl, {Background:0}, {Outfit}, centered"
# Génère sans background spécifique
```

**Implémentation suggérée :**

```python
def process_placeholder_with_zero(prompt_template, variations):
    """
    Traite les placeholders avec :0 en les supprimant du prompt
    """
    for placeholder, values in variations.items():
        if len(values) == 0 or (len(values) == 1 and values[0] == ""):
            # Supprimer le placeholder du prompt
            patterns = [
                f", {{{placeholder}}},",  # Au milieu
                f", {{{placeholder}}}",   # À la fin
                f"{{{placeholder}}}, ",   # Au début
                f"{{{placeholder}}}"      # Seul
            ]
            for pattern in patterns:
                prompt_template = prompt_template.replace(pattern, "")

    # Nettoyer les virgules doubles et espaces multiples
    prompt_template = re.sub(r',\s*,', ',', prompt_template)
    prompt_template = re.sub(r'\s+', ' ', prompt_template)
    prompt_template = prompt_template.strip(', ')

    return prompt_template
```

**Alternative : Support dans les fichiers de variations :**

```
# accessories.txt
0→none    # Ou ligne vide, ou mot-clé spécial
1→glasses
2→hat
```

Quand "none" est sélectionné, le placeholder est supprimé.

**Bénéfices :**
- **Flexibilité** : Prompts adaptatifs selon le besoin
- **Tests** : Facilite les comparaisons avec/sans éléments
- **Combinatoire enrichi** : Inclut naturellement l'option "sans cet élément"
- **Simplicité** : Syntaxe intuitive (0 = rien)
- **Compatibilité** : N'affecte pas le comportement existant

**Bénéfices :**
- Contrôle précis sur les variations utilisées
- Utile pour:
  - Tester des combinaisons spécifiques problématiques
  - Reproduire des résultats avec variations exactes
  - Créer des sets cohérents avec variations choisies
  - Affiner progressivement les variations utilisées
- Complément parfait au mode aléatoire existant

---

## 5. Simplification Architecture Webapp + Génération Thumbnails

### 5.1 Problème actuel : Complexité multi-dossiers

**Architecture actuelle :**
```
/CLI/apioutput/           # Images générées par les scripts CLI
/backend/app/...          # Backend FastAPI
/backend/frontend/...     # Frontend Vue.js
/backend/uploads/         # Dossier séparé pour images webapp
```

**Problèmes :**
- Double gestion des dossiers d'images
- Confusion entre images CLI et webapp
- Duplication potentielle de fichiers
- Configuration complexe des chemins

### 5.2 Solution proposée : Source unique de vérité

**Nouvelle architecture :**
```
/CLI/apioutput/                    # Source unique de vérité (images PNG originales)
├── session_2025-09-30_14-30-45/
│   ├── session_config.json
│   ├── image_0001.png
│   ├── image_0002.png
│   └── ...

/backend/static/thumbnails/        # Réplique en thumbnails WebP
├── session_2025-09-30_14-30-45/
│   ├── image_0001.webp
│   ├── image_0002.webp
│   └── ...

/backend/database.sqlite           # Métadonnées centralisées
```

### 5.3 Génération automatique de thumbnails

**Workflow lors de la génération d'image :**

1. Image PNG générée dans `/CLI/apioutput/session_xxx/`
2. **En background** : génération d'un thumbnail WebP
3. Thumbnail placé dans `/backend/static/thumbnails/session_xxx/`
4. Métadonnées enregistrées dans SQLite

**Configuration suggérée pour thumbnails :**
```python
THUMBNAIL_CONFIG = {
    "format": "webp",
    "quality": 85,
    "max_width": 512,
    "max_height": 512,
    "maintain_aspect_ratio": True
}
```

**Bénéfices :**
- **Performance webapp** : Chargement rapide avec WebP optimisés
- **Économie de bande passante** : WebP ~30% plus léger que JPEG
- **Préservation des originaux** : PNG haute qualité intacts dans apioutput
- **Génération asynchrone** : Pas de ralentissement du workflow principal
- **Structure miroir** : Facile de retrouver l'original depuis le thumbnail

### 5.4 Base de données SQLite centralisée

**Schema proposé :**

```sql
-- Table des sessions de génération
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,
    prompt_template TEXT,
    negative_prompt TEXT,
    generation_mode TEXT,
    seed_mode TEXT,
    base_seed INTEGER,
    max_images INTEGER,
    total_combinations INTEGER,
    actual_images_generated INTEGER,
    config_json TEXT,  -- JSON complet de la config
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des images générées
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    image_number INTEGER NOT NULL,
    original_path TEXT NOT NULL,      -- /CLI/apioutput/session_xxx/image_0001.png
    thumbnail_path TEXT,               -- /backend/static/thumbnails/session_xxx/image_0001.webp
    prompt_used TEXT,
    seed INTEGER,
    variations_used TEXT,              -- JSON: {"Hair": "long blonde", "Expression": "smiling"}
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Table des variations utilisées (pour analytics)
CREATE TABLE variation_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    placeholder_name TEXT NOT NULL,
    variation_value TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

-- Index pour performances
CREATE INDEX idx_images_session ON images(session_id);
CREATE INDEX idx_images_filename ON images(filename);
CREATE INDEX idx_variation_usage_image ON variation_usage(image_id);
```

**API Backend simplifiée :**

```python
# GET /api/sessions
# Retourne la liste de toutes les sessions

# GET /api/sessions/{session_name}
# Retourne détails session + liste images

# GET /api/images/{image_id}
# Retourne métadonnées image complètes

# GET /api/images/{image_id}/original
# Sert le PNG original haute qualité

# GET /static/thumbnails/session_xxx/image_0001.webp
# Sert le thumbnail WebP (statique)

# GET /api/search?variation=Hair:blonde&expression=smiling
# Recherche images par variations utilisées
```

### 5.5 Avantages de cette architecture

**Pour le développement :**
- Source unique de vérité (CLI/apioutput)
- Backend devient une couche de lecture/présentation
- Plus de synchronisation manuelle de dossiers

**Pour les performances :**
- Thumbnails WebP légers pour navigation rapide
- SQLite rapide pour queries et filtres
- Originaux servis uniquement sur demande

**Pour l'utilisateur :**
- Vue unifiée de toutes les générations (CLI + webapp)
- Recherche puissante par métadonnées
- Navigation rapide dans les images
- Accès aux originaux haute qualité

**Pour la maintenance :**
- Moins de duplication de code
- Configuration simplifiée
- Backup simple (apioutput + sqlite)
- Régénération des thumbnails possible à tout moment

### 5.6 Implémentation progressive

**Phase 1 : Génération thumbnails**
- Hook dans ImageVariationGenerator pour créer thumbnail après chaque image
- Utiliser Pillow pour conversion PNG → WebP
- Structure miroir dans /backend/static/thumbnails/

**Phase 2 : Base de données SQLite**
- Créer schema et migrations
- Peupler base depuis session_config.json existants
- API de lecture pour webapp

**Phase 3 : Refactor backend**
- Supprimer logique upload
- Pointer vers CLI/apioutput comme source
- Servir thumbnails en statique
- API de lecture depuis SQLite

**Phase 4 : Features avancées**
- Recherche par variations
- Analytics sur variations populaires
- Régénération sélective de thumbnails
- Cleanup d'anciennes sessions

---

## 6. Idées Connexes (À Développer)

### 6.1 Prévisualisation des variations
Interface pour voir toutes les variations disponibles avant de lancer une génération.

### 6.2 Variations conditionnelles
Certaines variations ne s'appliquent que si d'autres sont présentes.
Exemple: `{OpenMouth}` seulement si `{Expression}` = "surprised" ou "laughing"

### 6.3 Poids de variations
Certaines variations apparaissent plus souvent que d'autres en mode random.
Format: `{Hair:weighted|1:0.5|2:1.0|3:0.3}`

### 6.4 Historique et favoris
- Marquer certaines images générées comme favorites
- Système de rating pour identifier les meilleures combinaisons
- Générer plus de variations autour des favoris

### 6.5 Templates de configuration réutilisables
Bibliothèque de configurations prêtes à l'emploi pour différents cas d'usage :
- Portrait standard
- Character design
- Expression sheet
- Angle study
- etc.

---

## Notes d'Implémentation

### Priorités suggérées :
1. **P1 - Haute priorité**:
   - Section 2: Format JSON pretty-print (fondation pour le reste)
   - Section 1: Inclusion des options interactives
   - Section 5: Architecture webapp simplifiée + thumbnails WebP

2. **P2 - Priorité moyenne**:
   - Section 3: Support de fichiers config JSON en entrée
   - Section 4: Sélection manuelle d'index
   - Section 5.4: Base de données SQLite

3. **P3 - Basse priorité**:
   - Section 6: Idées connexes (à raffiner)

### Compatibilité :
- Toutes les propositions doivent maintenir la compatibilité avec le code existant
- Les nouvelles fonctionnalités doivent être opt-in (ne pas casser les scripts existants)
- Garder la simplicité d'utilisation pour les cas basiques