#!/usr/bin/env python3
"""
Démonstration de la facilité de création de générateurs avec ImageVariationGenerator.

Ce script montre comment créer rapidement différents types de générateurs
avec seulement quelques lignes de code chacun.
"""

from image_variation_generator import ImageVariationGenerator, create_generator


def landscape_generator():
    """Générateur de paysages avec variations météo et éclairage."""
    print("=== Générateur de paysages ===")

    generator = create_generator(
        prompt_template="beautiful landscape, {Weather}, {Lighting}, detailed, high quality",
        negative_prompt="low quality, blurry, people",
        variation_files={
            "Weather": "stable-diffusion-webui/prompts/weather.txt",  # À créer
            "Lighting": "stable-diffusion-webui/prompts/lighting.txt"
        },
        seed=100,
        session_name="landscapes"
    )

    return generator.run()


def portrait_generator():
    """Générateur de portraits avec expressions et coiffures."""
    print("=== Générateur de portraits ===")

    generator = create_generator(
        prompt_template="professional portrait, {Expression}, {HairStyle}, studio lighting",
        negative_prompt="low quality, blurry, multiple people",
        variation_files={
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt",
            "HairStyle": "stable-diffusion-webui/prompts/my_prompts/haircuts.txt"
        },
        seed=200,
        generation_mode="combinatorial",
        seed_mode="progressive",
        max_images=25,
        session_name="portraits"
    )

    return generator.run()


def anime_character_generator():
    """Générateur de personnages anime avec poses et actions."""
    print("=== Générateur de personnages anime ===")

    generator = create_generator(
        prompt_template="anime character, {Pose:5}, {Action:3}, {Expression:10}, kawaii style",
        negative_prompt="realistic, 3d, low quality",
        variation_files={
            "Pose": "stable-diffusion-webui/prompts/my_prompts/solopose.txt",
            "Action": "stable-diffusion-webui/prompts/my_prompts/soloaction.txt",
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt"
        },
        seed=300,
        generation_mode="random",
        seed_mode="random",
        max_images=30,
        session_name="anime_chars"
    )

    return generator.run()


def concept_art_generator():
    """Générateur d'art conceptuel avec styles et thèmes."""
    print("=== Générateur d'art conceptuel ===")

    generator = create_generator(
        prompt_template="concept art, {Style}, {Theme}, professional, detailed",
        negative_prompt="low quality, amateur",
        variation_files={
            "Style": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/General_Styles.txt",
            "Theme": "stable-diffusion-webui/prompts/themes.txt"  # À créer
        },
        seed=400,
        generation_mode="combinatorial",
        seed_mode="fixed",
        session_name="concept_art"
    )

    return generator.run()


def minimal_test_generator():
    """Générateur minimal pour tests rapides."""
    print("=== Test minimal (une variation) ===")

    generator = create_generator(
        prompt_template="test image, {Expression}, simple",
        negative_prompt="complex, detailed",
        variation_files={
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt"
        },
        seed=500,
        max_images=5,
        generation_mode="random",
        session_name="test"
    )

    return generator.run()


def no_variation_generator():
    """Générateur sans variations (image unique)."""
    print("=== Image unique (sans variations) ===")

    generator = create_generator(
        prompt_template="masterpiece, beautiful sunset over mountains, detailed",
        negative_prompt="low quality, people",
        # Pas de variation_files = image unique
        seed=600,
        session_name="single_image"
    )

    return generator.run()


def main():
    """Menu principal pour choisir le type de générateur."""
    generators = {
        "1": ("Paysages", landscape_generator),
        "2": ("Portraits", portrait_generator),
        "3": ("Personnages anime", anime_character_generator),
        "4": ("Art conceptuel", concept_art_generator),
        "5": ("Test minimal", minimal_test_generator),
        "6": ("Image unique", no_variation_generator)
    }

    print("🎨 Démonstration de générateurs variés")
    print("=====================================")
    print()

    print("Générateurs disponibles:")
    for key, (name, _) in generators.items():
        print(f"{key}. {name}")

    print("7. Lancer tous les générateurs")
    print()

    choice = input("Choisissez un générateur (1-7) : ").strip()

    if choice in generators:
        name, generator_func = generators[choice]
        print(f"\n🚀 Lancement du générateur: {name}")
        try:
            success, total = generator_func()
            print(f"✅ {name}: {success}/{total} images générées")
        except Exception as e:
            print(f"❌ Erreur avec {name}: {e}")

    elif choice == "7":
        print("\n🚀 Lancement de tous les générateurs...")
        results = {}

        for key, (name, generator_func) in generators.items():
            print(f"\n--- {name} ---")
            try:
                success, total = generator_func()
                results[name] = (success, total)
                print(f"✅ {name}: {success}/{total}")
            except Exception as e:
                results[name] = (0, 0)
                print(f"❌ {name}: {e}")

        print("\n📊 Résumé final:")
        total_success = sum(r[0] for r in results.values())
        total_images = sum(r[1] for r in results.values())
        print(f"Total: {total_success}/{total_images} images générées")

        for name, (success, total) in results.items():
            print(f"  {name}: {success}/{total}")

    else:
        print("❌ Choix invalide")


if __name__ == "__main__":
    print("⚠️  Note: Certains générateurs utilisent des fichiers qui n'existent peut-être pas.")
    print("   Créez les fichiers manquants ou modifiez les chemins selon votre configuration.")
    print()

    main()