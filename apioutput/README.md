# API Output Directory

Ce répertoire contient les images générées partagées entre le CLI et le backend web.

## Structure

```
apioutput/
├── images/          # Images haute résolution générées
├── thumbnails/      # Miniatures WebP générées automatiquement
└── metadata/        # Métadonnées des générations (JSON)
```

## Notes

- Les images sont organisées par session/job ID
- Les miniatures sont générées automatiquement par le worker Celery
- Les métadonnées incluent les prompts, seeds, et paramètres utilisés