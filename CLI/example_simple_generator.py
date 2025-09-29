#!/usr/bin/env python3
"""
Exemple d'utilisation simple d'ImageVariationGenerator.

Ce script démontre comment créer facilement un générateur personnalisé
avec seulement quelques lignes de code.
"""

from image_variation_generator import ImageVariationGenerator

def main():
    # Exemple 1: Générateur d'expressions faciales simple
    print("=== Exemple 1: Expressions faciales ===")

    expression_generator = ImageVariationGenerator(
        prompt_template="masterpiece, beautiful woman, {Expression}, detailed face, high quality",
        negative_prompt="low quality, blurry, deformed",
        variation_files={
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt"
        },
        seed=42,
        max_images=10,
        session_name="expressions"
    )

    # Lance la génération
    success, total = expression_generator.run()
    print(f"Résultat: {success}/{total} images générées avec succès\n")


def example_poses():
    """Exemple 2: Générateur de poses avec angles"""
    print("=== Exemple 2: Poses avec angles ===")

    pose_generator = ImageVariationGenerator(
        prompt_template="anime girl, {Pose}, {Angle}, beautiful, detailed",
        negative_prompt="low quality, bad anatomy",
        variation_files={
            "Pose": "stable-diffusion-webui/prompts/my_prompts/solopose.txt",
            "Angle": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/General_Angle.txt"
        },
        seed=123,
        generation_mode="random",  # Mode aléatoire
        seed_mode="progressive",   # Seeds progressives
        session_name="poses"
    )

    success, total = pose_generator.run()
    print(f"Résultat: {success}/{total} images générées avec succès\n")


def example_with_limitations():
    """Exemple 3: Utilisation des limitations dans le prompt"""
    print("=== Exemple 3: Limitations de variations ===")

    # Utilise seulement 5 expressions et 3 poses
    limited_generator = ImageVariationGenerator(
        prompt_template="masterpiece, {Expression:5}, {Pose:3}, beautiful character",
        negative_prompt="low quality",
        variation_files={
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt",
            "Pose": "stable-diffusion-webui/prompts/my_prompts/solopose.txt"
        },
        seed=456,
        generation_mode="combinatorial",
        seed_mode="fixed",
        session_name="limited"
    )

    success, total = limited_generator.run()
    print(f"Résultat: {success}/{total} images générées avec succès\n")


def example_no_variations():
    """Exemple 4: Générateur sans variations (une seule image)"""
    print("=== Exemple 4: Image unique ===")

    single_generator = ImageVariationGenerator(
        prompt_template="masterpiece, beautiful landscape, sunset, detailed",
        negative_prompt="low quality, blurry",
        # Aucun fichier de variation
        seed=789,
        session_name="landscape"
    )

    success, total = single_generator.run()
    print(f"Résultat: {success}/{total} images générées avec succès\n")


if __name__ == "__main__":
    print("🚀 Exemples d'utilisation d'ImageVariationGenerator\n")

    # Demande à l'utilisateur quel exemple lancer
    print("Choisissez un exemple à lancer:")
    print("1. Expressions faciales simples")
    print("2. Poses avec angles")
    print("3. Limitations de variations")
    print("4. Image unique (sans variations)")
    print("5. Lancer tous les exemples")

    choice = input("\nVotre choix (1-5) : ").strip()

    if choice == "1":
        main()
    elif choice == "2":
        example_poses()
    elif choice == "3":
        example_with_limitations()
    elif choice == "4":
        example_no_variations()
    elif choice == "5":
        main()
        example_poses()
        example_with_limitations()
        example_no_variations()
    else:
        print("Choix invalide, lancement de l'exemple 1 par défaut")
        main()

    print("✅ Terminé!")