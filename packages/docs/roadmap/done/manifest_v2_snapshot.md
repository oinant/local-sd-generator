# Manifest V2 - Snapshot System

**Status:** done
**Priority:** 2
**Component:** cli
**Created:** 2025-10-13
**Completed:** 2025-10-14

## Description

Enrichir le manifest.json généré lors des runs avec un **snapshot complet** de la configuration utilisée, permettant de reproduire exactement le "feeling" d'une génération passée sans dépendre des fichiers template originaux.

### Problème résolu
- Workflow actuel : modifications fréquentes du même fichier prompt (tests, itérations)
- Risque de perte de configurations qui fonctionnent bien
- Impossibilité de reproduire une ancienne génération après modification du template
- Manque de traçabilité sur les paramètres réellement utilisés

### Solution
Ajouter une section `snapshot` dans le manifest contenant :
- Le prompt résolu (avec placeholders)
- Les tableaux de variations utilisés (valeurs complètes)
- Les paramètres de génération et API complets
- Les infos runtime (checkpoint réel, etc.)
- Les métadonnées par image (seed réelle, prompt final)

## Implementation

### Structure du Manifest V2

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-13T14:23:45Z",

    "runtime_info": {
      "sd_model_checkpoint": "animefull_v1.safetensors [abc123def]"
    },

    "resolved_template": {
      "prompt": "masterpiece, {Expression}, {Angle}, beautiful girl, detailed",
      "negative": "low quality, {Defect}, blurry"
    },

    "generation_params": {
      "mode": "random",
      "seed_mode": "progressive",
      "base_seed": 42,
      "num_images": 100,
      "total_combinations": 40
    },

    "api_params": {
      "steps": 30,
      "cfg_scale": 7.5,
      "width": 512,
      "height": 768,
      "sampler_name": "DPM++ 2M Karras",
      "scheduler": "karras",
      "alwayson_scripts": {},
      // ... TOUS les paramètres API
    },

    "variations": {
      "Expression": ["happy", "sad", "angry", "surprised", "neutral"],
      "Angle": ["front", "side", "back", "3/4 view"],
      "Defect": ["blurry", "distorted"]
    }
  },

  "images": [
    {
      "filename": "img_0001.png",
      "seed": 42,
      "prompt": "masterpiece, happy, front, beautiful girl, detailed",
      "negative_prompt": "low quality, blurry, blurry",
      "applied_variations": {
        "Expression": "happy",
        "Angle": "front",
        "Defect": "blurry"
      }
    }
  ]
}
```

### Modifications à apporter

#### 1. V2Pipeline - Génération du snapshot

**Fichier** : `CLI/src/templating/orchestrator.py` (classe `V2Pipeline`)

**Méthode à ajouter** :
```python
def _get_runtime_info(self) -> dict:
    """Récupère les infos runtime de l'API SD."""
    try:
        response = requests.get(f"{self.api_url}/sdapi/v1/options")
        data = response.json()
        return {
            "sd_model_checkpoint": data.get("sd_model_checkpoint", "unknown")
        }
    except Exception as e:
        logger.warning(f"Could not fetch runtime info: {e}")
        return {"sd_model_checkpoint": "unknown"}

def _create_snapshot(self, config: TemplateConfig,
                     variations: Dict[str, List[str]],
                     total_combinations: int) -> dict:
    """Crée le snapshot de la configuration."""
    return {
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "runtime_info": self._get_runtime_info(),
        "resolved_template": {
            "prompt": config.prompt,
            "negative": config.negative_prompt
        },
        "generation_params": {
            "mode": self.mode,
            "seed_mode": self.seed_mode,
            "base_seed": self.seed,
            "num_images": self.num_images,
            "total_combinations": total_combinations
        },
        "api_params": self._get_api_params(config),
        "variations": variations
    }

def _get_api_params(self, config: TemplateConfig) -> dict:
    """Extrait tous les paramètres API de la config."""
    # Retourne TOUS les paramètres du payload API
    # (steps, cfg_scale, sampler, alwayson_scripts, etc.)
    return {
        "steps": config.parameters.steps,
        "cfg_scale": config.parameters.cfg_scale,
        "width": config.parameters.width,
        "height": config.parameters.height,
        "sampler_name": config.parameters.sampler_name,
        "scheduler": config.parameters.scheduler,
        # ... tous les autres champs
    }
```

**Méthode à modifier** :
```python
def run(self, template_path: str, num_images: Optional[int] = None):
    # ... (code existant)

    # Après génération des prompts, avant la génération d'images
    snapshot = self._create_snapshot(config, variations, total_combinations)

    # ... génération des images ...

    # Lors de la sauvegarde du manifest
    manifest = {
        "snapshot": snapshot,
        "images": [
            {
                "filename": img.filename,
                "seed": img.seed,  # Seed RÉELLE
                "prompt": img.prompt,  # Prompt FINAL résolu
                "negative_prompt": img.negative_prompt,
                "applied_variations": img.variations
            }
            for img in generated_images
        ]
    }
```

#### 2. API Client - Récupération checkpoint

**Fichier** : `CLI/src/api/client.py`

**Méthode à ajouter** :
```python
def get_options(self) -> dict:
    """Récupère les options/settings de l'API."""
    response = self.session.get(f"{self.base_url}/sdapi/v1/options")
    response.raise_for_status()
    return response.json()

def get_model_checkpoint(self) -> str:
    """Récupère le checkpoint actuellement chargé."""
    options = self.get_options()
    return options.get("sd_model_checkpoint", "unknown")
```

#### 3. Manifest Writer

**Fichier** : Nouveau fichier `CLI/src/execution/manifest.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Any
import json
from pathlib import Path

@dataclass
class ManifestImage:
    filename: str
    seed: int
    prompt: str
    negative_prompt: str
    applied_variations: Dict[str, str]

class ManifestWriter:
    """Écrit les manifests V2 avec snapshot."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def write(self, snapshot: dict, images: List[ManifestImage]):
        """Écrit le manifest complet."""
        manifest = {
            "snapshot": snapshot,
            "images": [
                {
                    "filename": img.filename,
                    "seed": img.seed,
                    "prompt": img.prompt,
                    "negative_prompt": img.negative_prompt,
                    "applied_variations": img.applied_variations
                }
                for img in images
            ]
        }

        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest_path
```

## Tasks

- [x] Ajouter `_get_runtime_info()` dans V2Executor
- [x] Ajouter `_create_snapshot()` dans V2Executor
- [x] Ajouter `_extract_variations_from_prompts()` dans V2Executor
- [x] Ajouter `save_manifest()` dans V2Executor
- [x] Ajouter `get_options()` et `get_model_checkpoint()` dans API client
- [x] Créer `ManifestWriter` dans `execution/manifest.py`
- [x] Créer `ManifestImage` dataclass dans `execution/manifest.py`
- [x] Intégrer snapshot system dans CLI (`_generate()`)
- [x] Ajouter seed réelle dans les metadata d'image
- [x] Ajouter prompt final dans les metadata d'image
- [x] Ajouter tests unitaires pour ManifestWriter (11 tests)
- [x] Ajouter tests unitaires pour get_options/get_model_checkpoint (3 tests)
- [x] Documenter la nouvelle structure dans `docs/cli/technical/manifest_v2_format.md`
- [x] Tester avec une génération réelle
- [x] Valider le format JSON généré
- [x] Fix: Filtrer variations pour n'inclure que celles avec placeholder dans template
- [x] Fix: Randomisation des sélecteurs avec SystemRandom (indépendant de seed)
- [x] Fix: Retirer seed de la sélection des variations (seed n'affecte que SD)

## Success Criteria

- ✅ Manifest contient la section `snapshot` avec toutes les infos
- ✅ `runtime_info.sd_model_checkpoint` récupéré de l'API
- ✅ `resolved_template` contient le prompt avec placeholders
- ✅ `variations` contient les tableaux complets de valeurs
- ✅ `generation_params` et `api_params` complets
- ✅ Chaque image a : filename, seed réelle, prompt final, variations appliquées
- ✅ Possibilité de reproduire une génération depuis le manifest uniquement
- ✅ Pas de dépendance aux fichiers template originaux
- ✅ Gestion gracieuse si API inaccessible (sd_model_checkpoint = "unknown")

## Tests

### Tests Unitaires Implémentés

**`CLI/tests/execution/test_manifest.py`** (11 tests - ✅ 100% pass):

*TestManifestImage:*
- ✅ test_manifest_image_creation
- ✅ test_manifest_image_to_dict

*TestManifestWriter:*
- ✅ test_manifest_writer_init
- ✅ test_write_manifest_creates_file
- ✅ test_write_manifest_content
- ✅ test_write_manifest_utf8_encoding
- ✅ test_write_manifest_indented
- ✅ test_write_manifest_dict
- ✅ test_write_empty_images_list
- ✅ test_write_multiple_images
- ✅ test_manifest_path_returned

**`CLI/tests/api/test_sdapi_client.py`** (3 tests ajoutés - ✅ 100% pass):
- ✅ test_get_options
- ✅ test_get_model_checkpoint
- ✅ test_get_model_checkpoint_unknown

### Tests d'Intégration (à implémenter)

Tests à ajouter dans `CLI/tests/v2/integration/test_manifest_generation.py` :
- [ ] Test génération complète avec snapshot
- [ ] Test reproductibilité depuis manifest
- [ ] Test avec différents modes (combinatorial/random, seed modes)

**Coverage actuelle** : 100% sur ManifestWriter et nouvelles méthodes API

## Documentation

### Créée
- ✅ `docs/cli/technical/manifest_v2_format.md` - Spécification complète du format
  - Structure détaillée du manifest
  - Tous les champs expliqués avec exemples
  - Use cases et exemples de code
  - Notes d'implémentation
  - Migration depuis V1
  - Extensions futures

### À créer
- [ ] `docs/cli/usage/reproducing_generations.md` - Guide utilisateur

### À mettre à jour
- [ ] `docs/cli/usage/getting_started.md` - Mentionner le snapshot automatique
- [ ] `CLI/README.md` - Ajouter section sur la reproductibilité

## Notes

### Portabilité
- `api_params` contient TOUS les paramètres, y compris scripts (ADetailer, ControlNet)
- Structure pensée pour être portable (peut être adapté à ComfyUI/Forge)
- Focus sur reproductibilité du "feeling" plutôt que bit-perfect

### Trade-offs
- Manifests plus volumineux (acceptable, disque pas cher)
- Perte de l'historique d'héritage (acceptable, on peut rebuild en standalone)
- Duplication d'infos entre snapshot et images (acceptable pour self-contained)

### Future évolutions possibles
- Rebuild tool (voir `future/rebuild_tool.md`)
- Diff tool pour comparer sessions
- Commande `sdgen inspect manifest.json` pour explorer
- Compression des manifests si trop volumineux
