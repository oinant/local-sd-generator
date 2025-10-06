#!/usr/bin/env python3
"""
Script de conversion Legacy JSON → Phase 2 YAML
Convertit les configurations et variations du format ancien vers le nouveau système de templating
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Union

# Chemins
LEGACY_BASE = Path("/mnt/d/StableDiffusion/private/configs")
TARGET_BASE = Path("/mnt/d/StableDiffusion/private-new")


def load_txt_variations(txt_path: str) -> Dict[str, str]:
    """
    Charge un fichier .txt de variations et retourne un dict YAML-compatible

    Gère les formats :
    - Simple liste: "value"
    - Avec clé: "key→value"
    - Avec clé numérique: "1→value"
    """
    variations = {}

    with open(txt_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()

            # Ignorer les commentaires et lignes vides
            if not line or line.startswith('#'):
                continue

            # Format "key→value"
            if '→' in line:
                key, value = line.split('→', 1)
                key = key.strip()
                value = value.strip()

                # Si la clé est numérique, utiliser idx pour générer une clé lisible
                if key.isdigit():
                    variations[f"var_{int(key):02d}"] = value
                else:
                    variations[key] = value
            else:
                # Format simple liste - générer une clé
                clean_key = line.lower().replace(' ', '_').replace(',', '').replace('-', '_')
                # Limiter à 30 caractères max
                clean_key = clean_key[:30]

                # Si la clé existe déjà, ajouter un suffixe
                if clean_key in variations:
                    clean_key = f"{clean_key}_{idx}"

                variations[clean_key] = line

    return variations


def convert_variation_file(txt_path: Path, output_path: Path, name: str = None):
    """Convertit un fichier .txt de variations en .yaml"""

    if not name:
        name = txt_path.stem.replace('_', ' ').title()

    variations = load_txt_variations(str(txt_path))

    yaml_content = {
        'type': 'variations',
        'name': name,
        'version': '1.0',
        'variations': variations
    }

    # Créer le répertoire parent si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False,
                  width=120)

    print(f"✅ Converti: {txt_path.name} → {output_path.name}")


def resolve_variation_path(var_path: str, config_dir: Path) -> Path:
    """Résout un chemin de variation relatif au fichier config"""
    # Nettoyer le chemin
    var_path = var_path.replace('./', '')
    return config_dir / var_path


def convert_json_config(json_path: Path, output_path: Path):
    """Convertit une config JSON legacy en .prompt.yaml Phase 2"""

    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Structure YAML Phase 2
    yaml_config = {
        'version': '2.0',
        'name': config.get('name', json_path.stem),
        'description': config.get('description', ''),
        'base_path': '../..',  # Relatif à prompts/xxx/
    }

    # Template du prompt
    yaml_config['template'] = config['prompt']['template']
    yaml_config['negative_prompt'] = config['prompt']['negative']

    # Variations - Convertir les chemins
    variations = {}
    for placeholder, var_path in config.get('variations', {}).items():
        if isinstance(var_path, list):
            # Multi-fichiers → on créera un multi-field plus tard
            # Pour l'instant, on pointe vers le premier fichier
            variations[placeholder] = f"variations/xxx/{placeholder.lower()}.yaml"
        else:
            # Single file
            variations[placeholder] = f"variations/xxx/{placeholder.lower()}.yaml"

    yaml_config['variations'] = variations

    # Génération
    yaml_config['generation'] = config.get('generation', {})

    # Paramètres
    yaml_config['parameters'] = config.get('parameters', {})

    # Output
    yaml_config['output'] = config.get('output', {})

    # Écrire le fichier
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_config, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False,
                  width=120)

    print(f"✅ Converti config: {json_path.name} → {output_path.name}")


def main():
    print("🔄 Conversion Legacy → Phase 2 YAML\n")

    # Phase 1: Convertir toutes les variations .txt → .yaml
    print("📁 Conversion des variations...")

    variations_dir = LEGACY_BASE / "variations"

    # Variations shared (generalAndBasicPrompt_v19)
    shared_source = variations_dir / "generalAndBasicPrompt_v19"
    if shared_source.exists():
        for txt_file in shared_source.glob("*.txt"):
            output_file = TARGET_BASE / "variations" / "shared" / f"{txt_file.stem}.yaml"
            convert_variation_file(txt_file, output_file)

    # Variations Hassaku
    hassaku_source = variations_dir / "my_prompts" / "Hassaku-XL"
    if hassaku_source.exists():
        for txt_file in hassaku_source.rglob("*.txt"):
            # Garder la structure de sous-répertoires
            rel_path = txt_file.relative_to(hassaku_source)
            output_file = TARGET_BASE / "variations" / "hassaku" / rel_path.with_suffix('.yaml')
            convert_variation_file(txt_file, output_file)

    # Variations générales (my_prompts root)
    general_source = variations_dir / "my_prompts"
    if general_source.exists():
        for txt_file in general_source.glob("*.txt"):
            output_file = TARGET_BASE / "variations" / "general" / f"{txt_file.stem}.yaml"
            convert_variation_file(txt_file, output_file)

    print("\n✅ Conversion des variations terminée!")
    print(f"\n📊 Structure créée dans: {TARGET_BASE}")


if __name__ == "__main__":
    main()
