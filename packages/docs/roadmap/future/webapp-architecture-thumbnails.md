# Webapp Architecture Simplification + Thumbnail Generation

**Status:** future
**Priority:** 6
**Component:** webapp
**Created:** 2025-10-08

## Description

Simplifier l'architecture webapp en utilisant une source unique de vérité pour les images (CLI/apioutput) avec génération automatique de thumbnails WebP pour la performance.

## Current Architecture Problems

```
/CLI/apioutput/           # Images générées par les scripts CLI
/api/app/...          # Backend FastAPI
/api/frontend/...     # Frontend Vue.js
/api/uploads/         # Dossier séparé pour images webapp
```

**Problèmes :**
- Double gestion des dossiers d'images
- Confusion entre images CLI et webapp
- Duplication potentielle de fichiers
- Configuration complexe des chemins

## Proposed Architecture

```
/CLI/apioutput/                    # Source unique de vérité (images PNG originales)
├── session_2025-09-30_14-30-45/
│   ├── session_config.yaml
│   ├── image_0001.png
│   ├── image_0002.png
│   └── ...

/api/static/thumbnails/        # Réplique en thumbnails WebP
├── session_2025-09-30_14-30-45/
│   ├── image_0001.webp
│   ├── image_0002.webp
│   └── ...

/api/database.sqlite           # Métadonnées centralisées
```

## Thumbnail Generation

**Workflow lors de la génération d'image :**

1. Image PNG générée dans `/CLI/apioutput/session_xxx/`
2. **En background** : génération d'un thumbnail WebP
3. Thumbnail placé dans `/api/static/thumbnails/session_xxx/`
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

## SQLite Database Schema

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
    config_yaml TEXT,  -- YAML complet de la config
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des images générées
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    image_number INTEGER NOT NULL,
    original_path TEXT NOT NULL,      -- /CLI/apioutput/session_xxx/image_0001.png
    thumbnail_path TEXT,               -- /api/static/thumbnails/session_xxx/image_0001.webp
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

## API Backend

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

## Benefits

**Pour le développement :**
- Source unique de vérité (CLI/apioutput)
- Backend devient une couche de lecture/présentation
- Plus de synchronisation manuelle de dossiers

**Pour les performances :**
- Thumbnails WebP légers pour navigation rapide (~30% plus léger que JPEG)
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

## Implementation Plan

**Phase 1 : Génération thumbnails**
- Hook dans les générateurs pour créer thumbnail après chaque image
- Utiliser Pillow pour conversion PNG → WebP
- Structure miroir dans /api/static/thumbnails/

**Phase 2 : Base de données SQLite**
- Créer schema et migrations
- Peupler base depuis session_config.yaml existants
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

## Success Criteria

- [ ] Thumbnails WebP générés automatiquement
- [ ] SQLite database fonctionnelle
- [ ] API backend lisant depuis apioutput
- [ ] Webapp affichant thumbnails rapidement
- [ ] Recherche par variations fonctionnelle
- [ ] Plus de duplication uploads/apioutput

## Tests

- Tests de génération thumbnails
- Tests schema SQLite
- Tests API endpoints
- Tests performance chargement webapp
