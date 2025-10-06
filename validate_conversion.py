#!/usr/bin/env python3
"""
Script de validation de la conversion Legacy → Phase 2
Vérifie l'intégrité de tous les fichiers convertis
"""

import yaml
from pathlib import Path
from typing import Dict, List

TARGET_BASE = Path("/mnt/d/StableDiffusion/private-new")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def validate_yaml_file(file_path: Path) -> tuple[bool, str]:
    """Valide qu'un fichier YAML est bien formé"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            return False, "Fichier vide"

        return True, "OK"
    except Exception as e:
        return False, str(e)


def validate_prompt_yaml(file_path: Path) -> tuple[bool, List[str]]:
    """Valide la structure d'un fichier .prompt.yaml"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Vérifier les champs requis
        required_fields = ['version', 'name', 'template', 'variations']
        for field in required_fields:
            if field not in config:
                issues.append(f"Champ requis manquant: {field}")

        # Vérifier que la version est 2.0
        if config.get('version') != '2.0':
            issues.append(f"Version incorrecte: {config.get('version')} (attendu: 2.0)")

        # Vérifier qu'il y a au moins une variation
        if not config.get('variations'):
            issues.append("Aucune variation définie")

        # Vérifier les chemins de variations
        variations = config.get('variations', {})
        for placeholder, var_path in variations.items():
            # Résoudre le chemin relatif
            full_path = (file_path.parent / var_path).resolve()
            if not full_path.exists():
                issues.append(f"Variation introuvable: {placeholder} -> {var_path}")

        return len(issues) == 0, issues

    except Exception as e:
        return False, [f"Erreur de parsing: {e}"]


def validate_variation_yaml(file_path: Path) -> tuple[bool, List[str]]:
    """Valide la structure d'un fichier de variations"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Vérifier le type
        if 'type' not in data:
            issues.append("Champ 'type' manquant")
        elif data['type'] not in ['variations', 'multi-field', 'chunk']:
            issues.append(f"Type inconnu: {data['type']}")

        # Vérifications spécifiques au type
        if data.get('type') == 'variations':
            if 'variations' not in data or not data['variations']:
                issues.append("Aucune variation définie")

        elif data.get('type') == 'multi-field':
            if 'sources' not in data or not data['sources']:
                issues.append("Aucune source définie pour le multi-field")

        elif data.get('type') == 'chunk':
            if 'fields' not in data:
                issues.append("Aucun field défini pour le chunk")
            if 'template' not in data:
                issues.append("Aucun template défini pour le chunk")

        return len(issues) == 0, issues

    except Exception as e:
        return False, [f"Erreur de parsing: {e}"]


def main():
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}🔍 Validation de la conversion Legacy → Phase 2{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

    total_files = 0
    valid_files = 0
    invalid_files = 0

    # 1. Valider tous les prompts
    print(f"{Colors.YELLOW}📄 Validation des fichiers .prompt.yaml...{Colors.END}\n")

    prompt_files = list(TARGET_BASE.glob("prompts/**/*.prompt.yaml"))
    for prompt_file in prompt_files:
        total_files += 1
        is_valid, issues = validate_prompt_yaml(prompt_file)

        rel_path = prompt_file.relative_to(TARGET_BASE)
        if is_valid:
            print(f"{Colors.GREEN}✅{Colors.END} {rel_path}")
            valid_files += 1
        else:
            print(f"{Colors.RED}❌{Colors.END} {rel_path}")
            for issue in issues:
                print(f"   {Colors.RED}→ {issue}{Colors.END}")
            invalid_files += 1

    # 2. Valider toutes les variations
    print(f"\n{Colors.YELLOW}📦 Validation des fichiers de variations...{Colors.END}\n")

    variation_files = list(TARGET_BASE.glob("variations/**/*.yaml"))
    for var_file in variation_files:
        total_files += 1
        is_valid, issues = validate_variation_yaml(var_file)

        rel_path = var_file.relative_to(TARGET_BASE)
        if is_valid:
            # Afficher seulement les erreurs pour les variations
            valid_files += 1
        else:
            print(f"{Colors.RED}❌{Colors.END} {rel_path}")
            for issue in issues:
                print(f"   {Colors.RED}→ {issue}{Colors.END}")
            invalid_files += 1

    print(f"{Colors.GREEN}✅ {valid_files}/{len(variation_files)} fichiers de variations valides{Colors.END}")

    # 3. Valider les chunks
    print(f"\n{Colors.YELLOW}🎭 Validation des chunks character...{Colors.END}\n")

    chunk_files = list(TARGET_BASE.glob("characters/**/*.char.yaml"))
    for chunk_file in chunk_files:
        total_files += 1
        is_valid, issues = validate_variation_yaml(chunk_file)

        rel_path = chunk_file.relative_to(TARGET_BASE)
        if is_valid:
            print(f"{Colors.GREEN}✅{Colors.END} {rel_path}")
            valid_files += 1
        else:
            print(f"{Colors.RED}❌{Colors.END} {rel_path}")
            for issue in issues:
                print(f"   {Colors.RED}→ {issue}{Colors.END}")
            invalid_files += 1

    # Résumé
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}📊 Résumé de la validation{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

    print(f"Total de fichiers validés : {total_files}")
    print(f"{Colors.GREEN}✅ Fichiers valides       : {valid_files}{Colors.END}")
    if invalid_files > 0:
        print(f"{Colors.RED}❌ Fichiers invalides     : {invalid_files}{Colors.END}")

    success_rate = (valid_files / total_files * 100) if total_files > 0 else 0
    print(f"\nTaux de succès : {success_rate:.1f}%")

    if invalid_files == 0:
        print(f"\n{Colors.GREEN}🎉 Toutes les conversions sont valides !{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Certains fichiers nécessitent une correction.{Colors.END}")
        return 1


if __name__ == "__main__":
    exit(main())
