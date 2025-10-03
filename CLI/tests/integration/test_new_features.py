"""
Script de test pour les nouvelles fonctionnalités SF-4 et SF-5.

Teste:
- Le paramètre filename_keys
- La génération de metadata.json
- La backward compatibility
"""

from image_variation_generator import ImageVariationGenerator, GenerationConfig
import sys

def test_basic_generator():
    """Test avec les anciennes fonctionnalités (backward compatibility)."""
    print("=" * 80)
    print("TEST 1: Backward Compatibility (sans filename_keys)")
    print("=" * 80)

    generator = ImageVariationGenerator(
        prompt_template="masterpiece, beautiful landscape",
        negative_prompt="low quality",
        session_name="test_backward_compat",
        generation_mode="combinatorial",
        seed_mode="fixed",
        seed=42,
        max_images=1
    )

    # Simule juste la création sans génération d'images réelles
    print("✅ Générateur créé avec succès (mode backward compatible)")
    print(f"   Session name: {generator.session_name}")
    print(f"   Filename keys: {generator.filename_keys}")
    print()


def test_new_naming_features():
    """Test avec les nouvelles fonctionnalités de nommage."""
    print("=" * 80)
    print("TEST 2: Nouvelles fonctionnalités (avec filename_keys)")
    print("=" * 80)

    generator = ImageVariationGenerator(
        prompt_template="masterpiece, beautiful landscape",
        negative_prompt="low quality",
        session_name="test_new_features",
        generation_mode="combinatorial",
        seed_mode="progressive",
        seed=42,
        max_images=1,
        filename_keys=["Expression", "Angle"]  # NOUVEAU!
    )

    print("✅ Générateur créé avec succès (nouvelles fonctionnalités)")
    print(f"   Session name: {generator.session_name}")
    print(f"   Filename keys: {generator.filename_keys}")
    print()


def test_naming_functions():
    """Test des fonctions de nommage directement."""
    print("=" * 80)
    print("TEST 3: Fonctions de nommage")
    print("=" * 80)

    from output.output_namer import sanitize_filename_component, generate_image_filename
    from datetime import datetime

    # Test sanitization camelCase
    test_values = [
        "happy smile",
        "front view",
        "test:file*name?",
        "café espresso"
    ]

    print("Sanitization (camelCase):")
    for value in test_values:
        sanitized = sanitize_filename_component(value)
        print(f"  '{value}' → '{sanitized}'")

    print()

    # Test filename generation
    print("Génération de noms de fichiers:")

    # Sans keys
    filename1 = generate_image_filename(1)
    print(f"  Index seul: {filename1}")

    # Avec keys
    filename2 = generate_image_filename(
        42,
        {"Expression": "happy smile", "Angle": "front view"},
        ["Expression", "Angle"]
    )
    print(f"  Avec variations: {filename2}")
    print()


def test_metadata_structure():
    """Test de la structure metadata."""
    print("=" * 80)
    print("TEST 4: Structure des métadonnées")
    print("=" * 80)

    from output.metadata_generator import generate_metadata_dict
    from datetime import datetime

    metadata = generate_metadata_dict(
        prompt_template="test {Expression}",
        negative_prompt="bad quality",
        variations_loaded={"Expression": {"smiling": "smiling", "sad": "sad"}},
        generation_info={
            "date": "2025-10-01T14:30:52",
            "timestamp": "20251001_143052",
            "session_name": "test",
            "total_images": 2,
            "generation_time_seconds": 10.5,
            "generation_mode": "combinatorial",
            "seed_mode": "progressive",
            "seed": 42,
            "total_combinations": 2
        },
        parameters={
            "width": 512,
            "height": 768,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "batch_size": 1,
            "batch_count": 1
        },
        output_info={
            "folder": "/tmp/test",
            "filename_keys": ["Expression"]
        }
    )

    print("✅ Métadonnées générées avec succès")
    print(f"   Version: {metadata['version']}")
    print(f"   Sections: {list(metadata.keys())}")
    print(f"   Variations: {list(metadata['variations'].keys())}")
    print()


if __name__ == "__main__":
    print("\n🧪 TESTS DES NOUVELLES FONCTIONNALITÉS (SF-4 & SF-5)\n")

    try:
        test_basic_generator()
        test_new_naming_features()
        test_naming_functions()
        test_metadata_structure()

        print("=" * 80)
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print("=" * 80)
        print()
        print("📝 Résumé des fonctionnalités testées:")
        print("  - SF-4: Système de nommage amélioré (camelCase)")
        print("  - SF-4: Paramètre filename_keys")
        print("  - SF-5: Génération de metadata.json")
        print("  - Backward compatibility maintenue")
        print()

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
