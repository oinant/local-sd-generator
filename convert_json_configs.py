#!/usr/bin/env python3
"""
Convertisseur intelligent JSON → .prompt.yaml Phase 2
Gère les multi-fichiers et résout les chemins vers les variations converties
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Union

LEGACY_BASE = Path("/mnt/d/StableDiffusion/private/configs")
TARGET_BASE = Path("/mnt/d/StableDiffusion/private-new")


def resolve_variation_path(var_path: str, placeholder: str) -> str:
    """
    Résout un chemin .txt legacy vers le chemin .yaml Phase 2

    Retourne le chemin relatif depuis prompts/{model}/ vers variations/
    """
    # Nettoyer le chemin
    var_path = var_path.replace('./', '')

    # Déterminer le dossier de destination
    if 'generalAndBasicPrompt_v19' in var_path:
        # Variations shared
        filename = Path(var_path).stem
        return f"../../variations/shared/{filename}.yaml"
    elif 'Hassaku-XL' in var_path:
        # Variations Hassaku avec sous-structure
        rel_path = var_path.split('Hassaku-XL/')[-1]
        yaml_path = Path(rel_path).with_suffix('.yaml')
        return f"../../variations/hassaku/{yaml_path}"
    elif 'my_prompts' in var_path:
        # Variations générales
        filename = Path(var_path).stem
        return f"../../variations/general/{filename}.yaml"
    else:
        # Fallback
        filename = Path(var_path).stem
        return f"../../variations/general/{filename}.yaml"


def create_multifield_yaml(placeholder: str, files: List[str]) -> Dict:
    """
    Crée un fichier multi-field pour gérer les arrays de variations
    """
    resolved_sources = [resolve_variation_path(f, placeholder) for f in files]

    return {
        'type': 'multi-field',
        'name': f"{placeholder} Combined",
        'version': '1.0',
        'sources': resolved_sources,
        'merge_strategy': 'combine'  # Combine toutes les variations
    }


def convert_config_to_yaml(json_path: Path) -> Dict:
    """Convertit une config JSON en structure YAML Phase 2"""

    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Déterminer le modèle/catégorie depuis le nom du fichier
    name = json_path.stem
    if 'Hassaku' in name:
        model = 'hassaku'
    elif 'CyberRealistic' in name:
        model = 'cyberrealistic'
    else:
        model = 'general'

    # Structure YAML Phase 2
    yaml_config = {
        'version': '2.0',
        'name': config.get('name', name),
        'description': config.get('description', ''),
        'base_path': '../..',  # Relatif à prompts/{model}/
    }

    # Template du prompt
    yaml_config['template'] = config['prompt']['template']
    yaml_config['negative_prompt'] = config['prompt']['negative']

    # Variations - Résoudre les chemins et gérer les multi-fichiers
    variations = {}
    multifields_to_create = {}

    for placeholder, var_path in config.get('variations', {}).items():
        if isinstance(var_path, list):
            # Multi-fichiers → créer un multi-field
            multifield_name = f"{placeholder.lower()}_combined"
            multifields_to_create[multifield_name] = {
                'placeholder': placeholder,
                'files': var_path
            }
            # Pointer vers le multi-field
            variations[placeholder] = f"../../variations/{model}/{multifield_name}.yaml"
        else:
            # Single file
            variations[placeholder] = resolve_variation_path(var_path, placeholder)

    yaml_config['variations'] = variations

    # Génération
    gen_config = config.get('generation', {})
    yaml_config['generation'] = {
        'mode': gen_config.get('mode', 'random'),
        'seed': gen_config.get('seed', 42),
        'seed_mode': gen_config.get('seed_mode', 'progressive'),
        'max_images': gen_config.get('max_images', 100)
    }

    # Paramètres
    yaml_config['parameters'] = config.get('parameters', {})

    # Output
    output_config = config.get('output', {})
    yaml_config['output'] = {
        'session_name': output_config.get('session_name', name),
        'filename_keys': output_config.get('filename_keys', [])
    }

    return yaml_config, multifields_to_create, model


def main():
    print("🔄 Conversion des configurations JSON → YAML\n")

    # Lister tous les JSON configs
    json_files = list(LEGACY_BASE.glob("*.json"))

    for json_file in json_files:
        print(f"📄 Conversion: {json_file.name}")

        # Convertir
        yaml_config, multifields, model = convert_config_to_yaml(json_file)

        # Créer les multi-fields si nécessaire
        for mf_name, mf_data in multifields.items():
            mf_content = create_multifield_yaml(mf_data['placeholder'], mf_data['files'])
            mf_path = TARGET_BASE / "variations" / model / f"{mf_name}.yaml"
            mf_path.parent.mkdir(parents=True, exist_ok=True)

            with open(mf_path, 'w', encoding='utf-8') as f:
                yaml.dump(mf_content, f,
                         default_flow_style=False,
                         allow_unicode=True,
                         sort_keys=False)
            print(f"  ✅ Multi-field créé: {mf_name}.yaml")

        # Sauvegarder le fichier .prompt.yaml
        output_path = TARGET_BASE / "prompts" / model / f"{json_file.stem}.prompt.yaml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # Ajouter un commentaire en-tête
            f.write(f"# Converti depuis: {json_file.name}\n")
            f.write(f"# Format: Phase 2 YAML Templating System\n\n")

            yaml.dump(yaml_config, f,
                     default_flow_style=False,
                     allow_unicode=True,
                     sort_keys=False,
                     width=120)

        print(f"  ✅ Config créée: {output_path.name}\n")

    print(f"\n✅ Conversion terminée! {len(json_files)} configurations converties.")
    print(f"📁 Fichiers créés dans: {TARGET_BASE}")


if __name__ == "__main__":
    main()
