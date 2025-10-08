# WebApp: Architecture simplifiée

**Priorité** : P1 (Haute)
**Cible** : WebApp
**Statut** : 🔜 À venir

---

## Problème actuel

Architecture multi-dossiers complexe avec duplication :

```
/CLI/apioutput/           # Images générées par scripts CLI
/api/app/             # Backend FastAPI
/api/frontend/        # Frontend Vue.js
/api/uploads/         # Dossier séparé pour images webapp
```

**Problèmes :**
- Double gestion des dossiers d'images
- Confusion entre images CLI et webapp
- Duplication potentielle de fichiers
- Configuration complexe des chemins

---

## Solution proposée

**Source unique de vérité** : CLI/apioutput devient la source unique.

### Nouvelle architecture

```
/CLI/apioutput/                    # Source unique (PNG originaux)
├── session_2025-09-30_14-30-45/
│   ├── session_config.json
│   ├── image_0001.png
│   ├── image_0002.png
│   └── ...

/api/static/thumbnails/        # Réplique WebP optimisée
├── session_2025-09-30_14-30-45/
│   ├── image_0001.webp
│   ├── image_0002.webp
│   └── ...

/api/database.sqlite           # Métadonnées centralisées
```

---

## Bénéfices

### Pour le développement
- ✅ Source unique de vérité (CLI/apioutput)
- ✅ Backend devient une couche de lecture/présentation
- ✅ Plus de synchronisation manuelle

### Pour les performances
- ✅ Thumbnails WebP légers (~30% plus léger)
- ✅ SQLite rapide pour queries
- ✅ Originaux servis uniquement sur demande

### Pour l'utilisateur
- ✅ Vue unifiée de toutes les générations (CLI + webapp)
- ✅ Recherche puissante par métadonnées
- ✅ Navigation rapide
- ✅ Accès aux originaux haute qualité

### Pour la maintenance
- ✅ Moins de duplication de code
- ✅ Configuration simplifiée
- ✅ Backup simple (apioutput + sqlite)
- ✅ Régénération des thumbnails possible à tout moment

---

## Implémentation progressive

### Phase 1 : Génération thumbnails
- Hook dans ImageVariationGenerator
- Conversion PNG → WebP avec Pillow
- Structure miroir dans /api/static/thumbnails/

### Phase 2 : Base de données SQLite
- Créer schema et migrations
- Peupler base depuis session_config.json existants
- API de lecture pour webapp

### Phase 3 : Refactor backend
- Supprimer logique upload
- Pointer vers CLI/apioutput comme source
- Servir thumbnails en statique
- API de lecture depuis SQLite

### Phase 4 : Features avancées
- Recherche par variations
- Analytics sur variations populaires
- Régénération sélective de thumbnails
- Cleanup d'anciennes sessions

---

## Impact

Refonte majeure de l'architecture qui simplifie le projet et améliore les performances.

**Dépendances :**
- Génération automatique de thumbnails WebP
- Base de données SQLite centralisée
