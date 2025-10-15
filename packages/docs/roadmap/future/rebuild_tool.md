# Rebuild Tool - Reconstruct Templates from Manifest

**Status:** future
**Priority:** 7
**Component:** cli
**Created:** 2025-10-13
**Depends on:** `wip/manifest_v2_snapshot.md`

## Description

Outil CLI permettant de reconstruire un template standalone et ses fichiers de variations depuis un manifest V2.

### Problème résolu
- Impossible de modifier/réutiliser une configuration passée sans les fichiers originaux
- Besoin de créer un nouveau template pour une génération qui a fonctionné
- Partage de configurations : envoyer juste le manifest sans les templates

### Solution
Commande `sdgen rebuild` qui parse le manifest V2 et génère :
- Un fichier template YAML standalone
- Les fichiers de variations (un par placeholder)
- La structure peut être regénérée et modifiée

## Implementation

### Commande CLI

```bash
# Rebuild depuis un manifest
sdgen rebuild manifest.json --output-dir ./rebuilt/

# Output:
# rebuilt/
# ├── template.yaml
# └── variations/
#     ├── Expression.txt
#     ├── Angle.txt
#     └── Defect.txt
```

### Structure générée

**template.yaml** :
```yaml
version: "2.0"

prompt: "masterpiece, {Expression}, {Angle}, beautiful girl, detailed"
negative_prompt: "low quality, {Defect}, blurry"

parameters:
  steps: 30
  cfg_scale: 7.5
  width: 512
  height: 768
  sampler_name: "DPM++ 2M Karras"
  scheduler: "karras"
  # ... tous les api_params du snapshot

generation:
  mode: "random"
  seed_mode: "progressive"
  seed: 42
  num_images: 100
```

**variations/Expression.txt** :
```
happy
sad
angry
surprised
neutral
```

### Code

**Fichier** : `CLI/src/cli.py`

```python
@app.command()
def rebuild(
    manifest_path: str = typer.Argument(..., help="Path to manifest.json"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory")
):
    """Rebuild template and variations from manifest snapshot."""
    from templating.utils.rebuild import ManifestRebuilder

    rebuilder = ManifestRebuilder(manifest_path)
    output_path = rebuilder.rebuild(output_dir)

    typer.echo(f"✅ Template rebuilt in: {output_path}")
    typer.echo(f"   - template.yaml")
    typer.echo(f"   - variations/ ({len(rebuilder.variations)} files)")
```

**Fichier** : Nouveau `CLI/src/templating/utils/rebuild.py`

```python
import json
from pathlib import Path
from typing import Dict, List, Any
import yaml

class ManifestRebuilder:
    """Reconstruit un template standalone depuis un manifest V2."""

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        with open(self.manifest_path, 'r') as f:
            self.manifest = json.load(f)

        self.snapshot = self.manifest.get("snapshot", {})
        if not self.snapshot:
            raise ValueError("Not a V2 manifest (missing snapshot)")

    def rebuild(self, output_dir: Optional[str] = None) -> Path:
        """Reconstruit le template et les variations."""
        if output_dir is None:
            output_dir = self.manifest_path.parent / "rebuilt"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Créer template.yaml
        self._write_template(output_dir / "template.yaml")

        # Créer variations/
        variations_dir = output_dir / "variations"
        variations_dir.mkdir(exist_ok=True)
        self._write_variations(variations_dir)

        return output_dir

    def _write_template(self, path: Path):
        """Écrit le fichier template.yaml."""
        resolved = self.snapshot["resolved_template"]
        gen_params = self.snapshot["generation_params"]
        api_params = self.snapshot["api_params"]

        template = {
            "version": "2.0",
            "prompt": resolved["prompt"],
            "negative_prompt": resolved["negative"],
            "parameters": api_params,
            "generation": {
                "mode": gen_params["mode"],
                "seed_mode": gen_params["seed_mode"],
                "seed": gen_params["base_seed"],
                "num_images": gen_params["num_images"]
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, allow_unicode=True, sort_keys=False)

    def _write_variations(self, variations_dir: Path):
        """Écrit les fichiers de variations."""
        variations = self.snapshot.get("variations", {})

        for placeholder, values in variations.items():
            file_path = variations_dir / f"{placeholder}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(values))

    @property
    def variations(self) -> Dict[str, List[str]]:
        """Retourne les variations du snapshot."""
        return self.snapshot.get("variations", {})
```

## Tasks

- [ ] Créer `ManifestRebuilder` dans `templating/utils/rebuild.py`
- [ ] Ajouter commande `sdgen rebuild` dans CLI
- [ ] Parser le manifest V2 et valider structure
- [ ] Générer template.yaml depuis snapshot
- [ ] Générer fichiers de variations
- [ ] Gérer les cas d'erreur (manifest invalide, permissions, etc.)
- [ ] Ajouter option `--force` pour écraser si dossier existe
- [ ] Tester la reconstruction
- [ ] Tester que le template reconstruit génère le même résultat
- [ ] Documenter dans `docs/cli/usage/`

## Success Criteria

- ✅ Commande `sdgen rebuild manifest.json` fonctionne
- ✅ Génère un template.yaml valide et fonctionnel
- ✅ Génère tous les fichiers de variations
- ✅ Le template reconstruit peut être utilisé avec `sdgen generate`
- ✅ Les paramètres sont préservés (API params, generation params)
- ✅ Gestion d'erreur gracieuse si manifest invalide
- ✅ Option `--output-dir` personnalisable

## Tests

Tests à ajouter dans `CLI/tests/v2/unit/test_manifest_rebuilder.py` :
- Test parsing manifest V2 valide
- Test génération template.yaml
- Test génération fichiers variations
- Test erreur si manifest invalide
- Test erreur si pas de section snapshot
- Test avec différents types de paramètres

Tests d'intégration dans `CLI/tests/v2/integration/test_rebuild_roundtrip.py` :
- Test roundtrip complet : generate → rebuild → generate → compare
- Test que les prompts générés sont identiques
- Test avec différents modes (combinatorial, random)

**Coverage attendue** : >90%

## Documentation

### À créer
- `docs/cli/usage/rebuild_from_manifest.md` - Guide utilisateur complet
- Exemples d'usage dans le guide

### À mettre à jour
- `docs/cli/usage/getting_started.md` - Mentionner la commande rebuild
- `CLI/README.md` - Ajouter dans la section commands

## Use Cases

### 1. Reproduire une génération passée
```bash
# Tu as un vieux manifest, tu veux regénérer
sdgen rebuild old_manifest.json
sdgen generate -t rebuilt/template.yaml
```

### 2. Modifier une config qui a marché
```bash
# Rebuild, modifie le template, regenere
sdgen rebuild good_manifest.json --output-dir ./tweaked/
# Éditer tweaked/template.yaml (changer steps, cfg_scale, etc.)
sdgen generate -t tweaked/template.yaml
```

### 3. Partager une config
```bash
# Envoie juste le manifest à un collègue
# Il peut rebuild et regénérer
sdgen rebuild shared_manifest.json
```

## Notes

### Limitations
- Ne reconstruit PAS l'héritage (implements/imports)
- Template généré est toujours standalone
- Acceptable : focus sur reproductibilité, pas sur structure

### Future évolutions
- Option `--simplify` pour nettoyer les paramètres par défaut
- Option `--format` pour choisir le format de sortie (YAML, JSON, etc.)
- Support reconstruction partielle (juste variations, juste template, etc.)

### Questions ouvertes
- Faut-il recréer les commentaires dans les fichiers de variations ?
- Comment gérer les variations avec mapping (clé→valeur) ?
- Faut-il valider que le template reconstruit est fonctionnel ?
