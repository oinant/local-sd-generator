# WebApp: Base de données SQLite centralisée

**Priorité** : P2 (Moyenne)
**Cible** : WebApp
**Statut** : 🔜 À venir

---

## Objectif

Centraliser les métadonnées de toutes les sessions et images générées dans une base SQLite.

---

## Schema proposé

### Table sessions

```sql
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
```

### Table images

```sql
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
```

### Table variation_usage

```sql
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

---

## API Backend proposée

```
GET /api/sessions
# Retourne la liste de toutes les sessions

GET /api/sessions/{session_name}
# Retourne détails session + liste images

GET /api/images/{image_id}
# Retourne métadonnées image complètes

GET /api/images/{image_id}/original
# Sert le PNG original haute qualité

GET /static/thumbnails/session_xxx/image_0001.webp
# Sert le thumbnail WebP (statique)

GET /api/search?variation=Hair:blonde&expression=smiling
# Recherche images par variations utilisées
```

---

## Bénéfices

- ✅ **Queries rapides** : SQLite optimisé pour la lecture
- ✅ **Recherche puissante** : Filtres par métadonnées
- ✅ **Analytics** : Statistiques sur variations populaires
- ✅ **Backup simple** : Un seul fichier .sqlite

---

## Cas d'usage

### Recherche avancée

```sql
-- Toutes les images avec "blonde hair" et "smiling"
SELECT i.* FROM images i
JOIN variation_usage v1 ON i.id = v1.image_id
JOIN variation_usage v2 ON i.id = v2.image_id
WHERE v1.placeholder_name = 'Hair' AND v1.variation_value LIKE '%blonde%'
  AND v2.placeholder_name = 'Expression' AND v2.variation_value LIKE '%smiling%';
```

### Analytics

```sql
-- Variations les plus utilisées
SELECT placeholder_name, variation_value, COUNT(*) as usage_count
FROM variation_usage
GROUP BY placeholder_name, variation_value
ORDER BY usage_count DESC
LIMIT 20;
```

---

## Impact

Fondation pour recherche avancée, analytics et features webapp futures.

**Dépendances :**
- Format JSON pour session_config
- Génération automatique de thumbnails WebP
