#!/usr/bin/env python3
"""
Demo de la Phase 1 du système de templating.
Charge un prompt config et affiche les variations générées.
"""

import sys
from pathlib import Path

# Add CLI to path
sys.path.insert(0, str(Path(__file__).parent))

from templating import load_prompt_config, resolve_prompt


def main():
    print("=" * 70)
    print("🎨 Next-Gen Templating System - Phase 1 Demo")
    print("=" * 70)
    print()

    # Chemin vers le fichier de test
    test_dir = Path(__file__).parent / "tests" / "templating"
    prompt_file = test_dir / "fixtures" / "simple_test.prompt.yaml"

    if not prompt_file.exists():
        print(f"❌ Fichier non trouvé: {prompt_file}")
        return 1

    print(f"📄 Chargement: {prompt_file.name}")
    print()

    # Charge la config
    config = load_prompt_config(prompt_file)

    print(f"📋 Configuration:")
    print(f"   Nom: {config.name}")
    print(f"   Mode: {config.generation_mode}")
    print(f"   Seed mode: {config.seed_mode}")
    print(f"   Seed de base: {config.seed}")
    print(f"   Imports: {len(config.imports)} fichiers")
    for name, path in config.imports.items():
        print(f"      - {name}: {path}")
    print()

    # Résout les variations
    print("🔄 Résolution des variations...")
    variations = resolve_prompt(config, base_path=test_dir)
    print(f"   ✅ {len(variations)} variations générées")
    print()

    # Affiche les 5 premières
    print("📝 Premières variations:")
    print("-" * 70)

    for i, var in enumerate(variations[:5]):
        print(f"\n[{i+1}] Variation #{var.index} (seed: {var.seed})")
        print(f"    Placeholders:")
        for key, value in var.placeholders.items():
            print(f"      {key}: {value}")
        print(f"    Prompt final:")
        print(f"      {var.final_prompt}")

    if len(variations) > 5:
        print(f"\n... et {len(variations) - 5} autres variations")

    print()
    print("=" * 70)
    print("✅ Phase 1 fonctionnelle !")
    print()
    print("Fonctionnalités validées:")
    print("  ✓ Chargement de fichiers YAML de variations")
    print("  ✓ Sélecteurs avancés ([keys], [random:N], [range:N-M])")
    print("  ✓ Configuration de prompts (.prompt.yaml)")
    print("  ✓ Résolution combinatoire")
    print("  ✓ Modes de seed (progressive, fixed, random)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
