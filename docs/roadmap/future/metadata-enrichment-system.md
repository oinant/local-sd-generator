# Metadata Enrichment System

**Status:** wip
**Priority:** 3 (critique - sprint actuel)
**Component:** cli + api + front
**Created:** 2025-10-17

## 🎯 Research Vision (North Star)

Ce projet n'est pas qu'un simple outil de gestion d'images. C'est un **laboratoire de recherche** sur les modèles de diffusion.

### Objectif final

Construire un système capable de :
1. **Comprendre** profondément comment les modèles de diffusion réagissent à différents prompts/variations
2. **Apprendre** des patterns d'échec et de réussite (ML/DL)
3. **Prédire** si une combinaison prompt+modèle va réussir ou échouer
4. **Optimiser** automatiquement les prompts pour un résultat donné

### Pipeline visé

```
Langage naturel (utilisateur)
    ↓
LLM (comprend l'intention)
    ↓
Générateur de prompt enrichi par ML/DL
(connaît les patterns qui marchent par modèle)
    ↓
Diffusion guidée précise
    ↓
Résultat qui marche à tous les coups
```

### Approche

**Phase 1 (maintenant) :** Foundation - Capturer TOUTES les données nécessaires
**Phase 2+ (futur) :** Research - Expérimenter avec ML/DL quand prêt

## Description

### Problème résolu (Phase 1)

Actuellement, il n'y a aucun moyen de :
- Distinguer les vraies sessions complètes des tests/échecs
- Marquer les images favorites ou celles avec des problèmes techniques
- Catégoriser les échecs de génération
- Filtrer rapidement parmi 31k+ images
- **Analyser les patterns d'échec** pour comprendre les modèles

### Solution (Phase 1)

Base de données SQLite embarquée (`./metadata.db`) avec :
- Schéma **flexible** (JSON) pour capture exhaustive des métadonnées
- Système de notation **binaire** (thumbs/like) pour volumes élevés
- **Export facile** vers CSV/Parquet pour pipelines ML
- **Analytics API** pour pattern detection

## Implementation (Phase 1)

### Architecture

**Stack :**
- SQLite (embedded, zero-dependency)
- Module `MetadataManager` (Python)
- Endpoints FastAPI enrichis
- UI filters dans WebUI
- **JSON flexible** pour évolution future

**DB Location :** `./metadata.db` (à côté de `sdgen_config.json`)

### Schéma de données (Research-Ready)

```sql
-- Sessions : capture TOUT avec JSON flexible
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT UNIQUE NOT NULL,
    created_at DATETIME NOT NULL,

    -- Flags basiques (navigation rapide)
    is_test BOOLEAN DEFAULT 0,
    is_failed BOOLEAN DEFAULT 0,
    is_archived BOOLEAN DEFAULT 0,

    -- Metadata COMPLÈTE en JSON (flexible pour ML)
    metadata JSON,
    -- Contient : {
    --   "model_name": "sd-v1.5",
    --   "model_hash": "abc123...",
    --   "template_name": "portrait.yaml",
    --   "generation_params": {
    --     "cfg_scale": 7.5,
    --     "steps": 30,
    --     "sampler": "Euler a",
    --     "scheduler": "karras",
    --     ...
    --   },
    --   "variations_config": {...},
    --   ... (tout ce qui peut être utile pour ML)
    -- }

    -- Enrichissement utilisateur
    display_name TEXT,
    notes TEXT,

    -- Audit & soft delete
    is_deleted BOOLEAN DEFAULT 0,
    created_at_real DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Images : idem, JSON flexible
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    filename TEXT NOT NULL,

    -- Status & notation (UI rapide)
    status TEXT DEFAULT 'ok',           -- 'ok' | 'ko'
    technical_quality TEXT,             -- 'perfect' (👍) | 'imperfect' (👎) | NULL
    is_liked BOOLEAN DEFAULT 0,         -- Coeur émotionnel ❤️
    failure_category TEXT,              -- 'malformed' | 'noise' | 'incomplete' | 'off_prompt'
    failure_notes TEXT,

    -- Metadata COMPLÈTE en JSON
    metadata JSON,
    -- Contient : {
    --   "seed": 42,
    --   "prompt": "...",
    --   "negative_prompt": "...",
    --   "variations": {"Expression": "happy", "Pose": "sitting"},
    --   "variation_combination_hash": "sha256(...)",  # Pour grouping
    --   "file_size": 1024000,
    --   "dimensions": [512, 512],
    --   ... (tout depuis manifest + PNG metadata)
    -- }

    -- ML predictions (pour le futur)
    ml_predictions JSON,
    -- Format libre : {
    --   "predicted_category": "malformed",
    --   "confidence": 0.85,
    --   "model_version": "v1.0",
    --   "features": {...}
    -- }

    -- Notes & audit
    notes TEXT,
    is_deleted BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    UNIQUE(session_id, filename)
);

-- Cache analytique (pré-calculs pour perf)
CREATE TABLE analytics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    cache_value JSON,
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index pour filtres fréquents
CREATE INDEX idx_sessions_test ON sessions(is_test);
CREATE INDEX idx_sessions_failed ON sessions(is_failed);
CREATE INDEX idx_sessions_archived ON sessions(is_archived);
CREATE INDEX idx_sessions_deleted ON sessions(is_deleted);

CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_liked ON images(is_liked);
CREATE INDEX idx_images_technical ON images(technical_quality);
CREATE INDEX idx_images_deleted ON images(is_deleted);
CREATE INDEX idx_images_session ON images(session_id);
```

### Modules

**CLI Package (`packages/sd-generator-cli/`) :**
```
sd_generator_cli/
├── metadata/
│   ├── __init__.py
│   ├── schema.py               # SQLite schema + migrations
│   ├── metadata_manager.py     # CRUD operations + analytics
│   ├── migration.py            # Import manifests existants
│   └── export.py               # Export vers CSV/Parquet/JSONL
```

**Backend Package (`packages/sd-generator-webui/backend/`) :**
```
sd_generator_webui/api/
├── sessions.py         # Enrichir avec filtres metadata
├── images.py           # Enrichir avec filtres metadata
├── metadata.py         # CRUD endpoints pour metadata
└── analytics.py        # Stats & pattern detection (Phase 1)
```

### API MetadataManager (Phase 1)

```python
# Sessions
manager.register_session(folder_name, manifest_data, is_test=False)
manager.update_session(session_id, display_name=..., notes=...)
manager.flag_session(session_id, is_test=..., is_failed=..., is_archived=...)
manager.get_sessions(filters={}, include_deleted=False)

# Images
manager.register_image(session_id, image_data)
manager.update_image_rating(image_id, technical_quality=..., is_liked=...)
manager.update_image_failure(image_id, failure_category, failure_notes)
manager.get_images(session_id, filters={}, include_deleted=False)

# Analytics (Phase 1 - basique)
manager.get_stats()  # Global stats
manager.get_failure_rate_by_category()
manager.get_session_stats(session_id)

# Export (Phase 1)
manager.export_to_csv(output_path, filters={})
manager.export_to_parquet(output_path, filters={})
manager.export_to_jsonl(output_path, filters={})

# Soft delete
manager.soft_delete_session(session_id)
manager.soft_delete_image(image_id)
manager.restore_session(session_id)
manager.restore_image(image_id)
```

## Tasks (Phase 1 : Foundation)

### Phase 1.1 : Infrastructure SQLite
- [x] Créer roadmap spec
- [ ] Définir schéma SQLite complet avec JSON flexible
- [ ] Créer module `metadata/schema.py`
- [ ] Créer module `metadata/metadata_manager.py`
  - CRUD sessions/images
  - Soft delete
  - Stats basiques
- [ ] Créer module `metadata/export.py`
  - Export CSV
  - Export Parquet (optionnel)
  - Export JSONL
- [ ] Tests unitaires `MetadataManager` (pytest)

### Phase 1.2 : CLI Integration
- [ ] Ajouter flag `--test` à `sdgen generate`
- [ ] Auto-register session dans metadata.db après génération
- [ ] Commande `sdgen metadata migrate` pour import existant
- [ ] Commande `sdgen metadata export` (CSV/JSONL)
- [ ] Commande `sdgen metadata stats` pour overview

### Phase 1.3 : Migration
- [ ] Créer `metadata/migration.py`
- [ ] Scanner dossiers pour tous les manifests
- [ ] Inférer données depuis anciens formats si pas de manifest
- [ ] Gérer 31k+ images efficacement (batch insert)
- [ ] Progress bar + validation post-import
- [ ] Tests migration sur subset

### Phase 1.4 : Backend API
- [ ] Enrichir `GET /api/sessions/` avec filtres metadata
- [ ] Enrichir `GET /api/sessions/{id}/images` avec filtres
- [ ] Nouveaux endpoints CRUD :
  - `PATCH /api/sessions/{id}/metadata`
  - `PATCH /api/images/{id}/metadata`
  - `POST /api/images/{id}/rating` (thumbs/like)
  - `POST /api/sessions/{id}/flags`
- [ ] Endpoint stats : `GET /api/analytics/stats`
- [ ] Endpoint export : `GET /api/export/images?format=csv`

### Phase 1.5 : Frontend (WebUI)
- [ ] Filtres sidebar sessions (test/failed/archived)
- [ ] Boutons rating sur images (👍👎❤️)
- [ ] Modale KO avec catégories + notes
- [ ] Badge counts (liked, perfect, ko)
- [ ] Page stats/analytics basique
- [ ] Bulk actions (archive/delete multiple)

### Phase 1.6 : Documentation
- [ ] Technical doc : `docs/cli/technical/metadata-system.md`
- [ ] Usage guide : `docs/cli/usage/metadata-management.md`
- [ ] API reference : `docs/backend/api/metadata-endpoints.md`
- [ ] Migration guide pour users existants
- [ ] Research vision : `docs/research/diffusion-models-analysis.md`

## Success Criteria (Phase 1)

- ✅ DB SQLite créée automatiquement dans projet
- ✅ Schéma JSON flexible accepte toutes métadonnées
- ✅ Flag `--test` fonctionne sur `sdgen generate`
- ✅ Migration importe 31k+ images en < 5min
- ✅ Export CSV/JSONL fonctionne
- ✅ Filtres sessions/images dans WebUI
- ✅ Notation (thumbs/like) persiste correctement
- ✅ Soft delete fonctionne (pas de données perdues)
- ✅ 100% des nouvelles sessions auto-registered
- ✅ Stats basiques disponibles via API
- ✅ Tous les tests passent (95%+ coverage)

## Tests (Phase 1)

**Unit tests :**
- `test_metadata_manager.py` : CRUD operations
- `test_schema.py` : DB schema creation
- `test_migration.py` : Import manifests
- `test_export.py` : Export CSV/JSONL

**Integration tests :**
- `test_cli_metadata_flag.py` : CLI flag --test
- `test_api_metadata_endpoints.py` : API CRUD
- `test_migration_full.py` : Migration 31k images
- `test_json_flexibility.py` : Ajout métadonnées custom

**Target :** 95%+ coverage sur module metadata

## Performance Requirements (Phase 1)

- Import 31k images : < 5min
- Export 31k images CSV : < 2min
- Filtrage sessions (12k) : < 200ms
- Filtrage images par session : < 100ms
- Update rating image : < 50ms
- DB size pour 31k images : < 100MB (avec JSON)

## Security Considerations

- ✅ SQLite pas exposé au network (local only)
- ✅ Pas de SQL injection (parameterized queries)
- ✅ Soft delete pour éviter pertes accidentelles
- ✅ Backup automatique avant migration
- ✅ JSON validation pour éviter corruption

## Migration Strategy

**Pour utilisateurs existants :**

1. Lancer : `sdgen metadata migrate`
2. Scanner automatiquement dossier configuré (ex: `apioutput/`)
3. Import progressif avec progress bar
4. Backup auto : `metadata.db.backup.TIMESTAMP`
5. Validation post-import (count sessions/images)
6. Rapport détaillé (réussis/échoués/skipped)

**Backward compatibility :**
- Pas de manifest.json ? → inférer depuis session_config.txt + PNG metadata
- Sessions sans metadata.db → continuent de fonctionner normalement
- Migration optionnelle mais fortement recommandée

**Rollback :**
- Backup auto avant migration
- Commande : `sdgen metadata restore --backup metadata.db.backup.TIMESTAMP`

## 🔬 Future Research Directions (Phase 2+)

**Ces fonctionnalités ne seront PAS implémentées dans Phase 1.**
Elles sont documentées ici comme "north star" pour orienter les décisions d'architecture.

### Phase 2 : Pattern Detection (ML)

**Objectif :** Identifier automatiquement les combinaisons qui échouent.

**Features :**
- Analyse des variations par modèle
- Détection de patterns d'échec
- Corrélations prompt/params/résultats
- Recommandations automatiques

**API envisagée :**
```python
manager.analyze_failure_patterns(
    model_name="sd-v1.5",
    min_occurrences=10,
    failure_threshold=0.7
)
→ [
    {
        "pattern": {"Expression": "angry", "Pose": "profile"},
        "failure_rate": 0.85,
        "sample_count": 42,
        "common_category": "malformed"
    }
]
```

**Stack potentiel :**
- pandas pour agrégation
- scikit-learn pour pattern detection
- Visualisations (matplotlib/seaborn)

### Phase 3 : Auto-Classification (Deep Learning)

**Objectif :** Classifier automatiquement les images ratées sans marquage manuel.

**Features :**
- CNN pour classification malformed/noise/incomplete
- Active learning (corrections manuelles → amélioration modèle)
- Batch classification sur sessions existantes

**API envisagée :**
```python
classifier.predict(image_path)
→ {
    "category": "malformed",
    "confidence": 0.89,
    "features": [...]
}

classifier.classify_session(session_id, auto_update=False)
→ {"classified": 87, "skipped": 13, "avg_confidence": 0.82}
```

**Stack potentiel :**
- PyTorch/TensorFlow
- Pre-trained models (CLIP, ResNet)
- HuggingFace Transformers

### Phase 4 : Prompt Optimization (LLM + ML)

**Objectif final :** Transformer langage naturel → prompt optimisé qui marche.

**Pipeline envisagé :**
```
User: "Une femme souriante de profil, éclairage doux"
    ↓
LLM (GPT-4/Claude) : Comprend intention
    ↓
ML Optimizer : Ajuste selon patterns appris
    ↓
Prompt optimisé : "portrait, happy woman, side profile, soft lighting, detailed face, 8k"
+ Variations suggérées : {"Expression": "gentle_smile", "Angle": "3_4_profile"}
+ Params suggérés : {"cfg_scale": 7.5, "sampler": "Euler a"}
    ↓
Diffusion → Succès garanti
```

**Features :**
- Embedding-based similarity search (trouver prompts similaires qui ont marché)
- Reinforcement learning pour optimisation
- A/B testing automatique

**Stack potentiel :**
- LangChain pour LLM orchestration
- Vector DB (ChromaDB, Pinecone) pour similarity search
- Ray pour distributed training

### Metrics de succès (Phase 2+)

- **Phase 2 :** Détecter 80%+ des patterns d'échec connus
- **Phase 3 :** Classifier 90%+ des images KO correctement (vs manual)
- **Phase 4 :** Générer des prompts avec 95%+ de taux de réussite

## Documentation

### Phase 1
- Technical: `docs/cli/technical/metadata-system.md`
- Usage: `docs/cli/usage/metadata-management.md`
- API: `docs/backend/api/metadata-endpoints.md`
- Migration: `docs/cli/usage/migrating-existing-sessions.md`

### Research (Future)
- Vision: `docs/research/diffusion-models-analysis.md`
- ML Pipeline: `docs/research/ml-pattern-detection.md`
- DL Classification: `docs/research/dl-auto-classification.md`
- Prompt Optimization: `docs/research/llm-prompt-optimization.md`

## Notes

### Design Principles
- **Flexible first :** JSON schema pour évolution sans migration
- **Export-friendly :** CSV/Parquet pour pipelines ML externes
- **Scalable :** Conçu pour 100k+ images
- **Research-ready :** Capture exhaustive des métadonnées
- **Pragmatic :** Notation binaire pour gestion volumes

### Trade-offs acceptés
- DB size augmentée (JSON) vs flexibilité
- Pas de normalisation stricte vs évolutivité
- Soft delete (overhead) vs sécurité données
- Analytics simples (Phase 1) vs ML complexe (Phase 2+)

### Long-term vision
Ce système n'est pas qu'un outil de gestion. C'est une **plateforme de recherche** pour :
- Comprendre profondément les modèles de diffusion
- Développer une expertise technique en ML/DL
- Expérimenter avec LLMs + diffusion
- Construire un système de génération intelligent
