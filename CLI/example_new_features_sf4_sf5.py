#!/usr/bin/env python3
"""
Exemple d'utilisation des nouvelles fonctionnalités SF-4 et SF-5.

Ce script démontre:
- SF-4: Enhanced File Naming avec filename_keys et camelCase
- SF-5: JSON Metadata Export avec metadata.json

Nouvelles fonctionnalités de la Phase 1:
✨ Nommage intelligent des fichiers avec filename_keys
✨ Génération automatique de metadata.json structuré
✨ Backward compatibility complète
"""

from image_variation_generator import ImageVariationGenerator, GenerationConfig


def example_with_filename_keys():
    """
    Exemple utilisant filename_keys pour des noms de fichiers descriptifs.

    Avant (SF-4):
      001.png, 002.png, 003.png...

    Après (SF-4):
      001_Expression-happySmile_Angle-frontView.png
      002_Expression-sadFace_Angle-sideView.png
      003_Expression-angry_Angle-backView.png
    """
    print("=" * 80)
    print("🎨 EXEMPLE 1: Nommage amélioré avec filename_keys (SF-4)")
    print("=" * 80)
    print()
    print("Ce générateur va créer des fichiers avec des noms descriptifs")
    print("incluant les valeurs des variations Expression et Angle.")
    print()

    generator = ImageVariationGenerator(
        prompt_template="masterpiece, {Expression}, {Angle}, beautiful anime girl, detailed",
        negative_prompt="low quality, blurry, bad anatomy",
        variation_files={
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt",
            "Angle": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/General_Angle.txt"
        },
        seed=42,
        max_images=20,
        generation_mode="combinatorial",
        seed_mode="progressive",
        session_name="anime_expressions_angles",
        filename_keys=["Expression", "Angle"]  # 🆕 NOUVELLE FONCTIONNALITÉ!
    )

    print("📋 Configuration:")
    print(f"  - Prompt: {generator.prompt_template}")
    print(f"  - Filename keys: {generator.filename_keys}")
    print(f"  - Session: {generator.session_name}")
    print()
    print("📝 Format des noms de fichiers générés:")
    print("  001_Expression-happySmile_Angle-frontView.png")
    print("  002_Expression-sadFace_Angle-sideView.png")
    print("  ...")
    print()

    # Note: Ne lance pas la génération réelle pour ce script de démo
    # success, total = generator.run()
    print("✅ Générateur configuré avec succès!")
    print()


def example_with_metadata_json():
    """
    Exemple montrant la génération de metadata.json (SF-5).

    Le fichier metadata.json contient toute l'information de la session:
    - Prompts utilisés
    - Variations chargées
    - Paramètres de génération
    - Timing et statistiques
    - Exemple de prompt résolu
    """
    print("=" * 80)
    print("📊 EXEMPLE 2: Métadonnées JSON structurées (SF-5)")
    print("=" * 80)
    print()
    print("Ce générateur va créer un fichier metadata.json complet")
    print("avec toutes les informations de la session de génération.")
    print()

    generator = ImageVariationGenerator(
        prompt_template="1girl, {Outfit}, {Pose}, {Lighting}, detailed, high quality",
        negative_prompt="low quality, blurry, bad hands",
        variation_files={
            "Outfit": "stable-diffusion-webui/prompts/my_prompts/outfit.txt",
            "Pose": "stable-diffusion-webui/prompts/my_prompts/solopose.txt",
            "Lighting": "stable-diffusion-webui/prompts/my_prompts/lighting.txt"
        },
        seed=123,
        max_images=50,
        generation_mode="random",
        seed_mode="progressive",
        session_name="character_study",
        filename_keys=["Outfit", "Pose"]
    )

    print("📋 Configuration:")
    print(f"  - Placeholders: {list(generator.variation_files.keys())}")
    print(f"  - Mode: {generator.generation_mode}")
    print(f"  - Seed mode: {generator.seed_mode}")
    print()
    print("📄 Le fichier metadata.json contiendra:")
    print("  ✓ Version du schema (1.0)")
    print("  ✓ Informations de session (date, durée, nombre d'images)")
    print("  ✓ Template de prompt et prompt négatif")
    print("  ✓ Exemple de prompt résolu")
    print("  ✓ Toutes les variations avec leurs valeurs")
    print("  ✓ Paramètres de génération (width, height, steps, etc.)")
    print("  ✓ Configuration de sortie (dossier, filename_keys)")
    print()
    print("📂 Emplacement: <output_folder>/metadata.json")
    print()

    # Note: Ne lance pas la génération réelle pour ce script de démo
    # success, total = generator.run()
    print("✅ Générateur configuré avec succès!")
    print()


def example_combined_features():
    """
    Exemple combinant toutes les nouvelles fonctionnalités.

    - Nommage descriptif des fichiers (SF-4)
    - Métadonnées JSON complètes (SF-5)
    - Configuration avancée des paramètres
    """
    print("=" * 80)
    print("🚀 EXEMPLE 3: Toutes les fonctionnalités combinées")
    print("=" * 80)
    print()

    # Configuration personnalisée des paramètres de génération
    custom_config = GenerationConfig(
        steps=40,
        cfg_scale=8.5,
        width=768,
        height=1024,
        sampler_name="DPM++ 2M Karras",
        batch_size=1,
        n_iter=1
    )

    generator = ImageVariationGenerator(
        prompt_template="masterpiece, {Character}, {Expression}, {Lighting}, cinematic, detailed",
        negative_prompt="low quality, blurry, bad anatomy, watermark",
        variation_files={
            "Character": "stable-diffusion-webui/prompts/my_prompts/characters.txt",
            "Expression": "stable-diffusion-webui/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt",
            "Lighting": "stable-diffusion-webui/prompts/my_prompts/lighting.txt"
        },
        seed=999,
        max_images=100,
        generation_mode="combinatorial",
        seed_mode="progressive",
        session_name="cinematic_portraits",
        filename_keys=["Character", "Expression", "Lighting"]  # 3 keys!
    )

    generator.set_generation_config(custom_config)

    print("📋 Configuration complète:")
    print(f"  - Session: {generator.session_name}")
    print(f"  - Filename keys: {generator.filename_keys}")
    print(f"  - Résolution: {custom_config.width}x{custom_config.height}")
    print(f"  - Steps: {custom_config.steps}")
    print(f"  - CFG Scale: {custom_config.cfg_scale}")
    print()
    print("📁 Résultats attendus:")
    print("  └── 20251001_143052_cinematicPortraits/")
    print("      ├── metadata.json                    # 🆕 Métadonnées structurées")
    print("      ├── session_config_legacy.txt        # Pour backward compatibility")
    print("      ├── 001_Character-emma_Expression-happySmile_Lighting-softLight.png")
    print("      ├── 002_Character-emma_Expression-sadFace_Lighting-dramaticShadow.png")
    print("      └── ...")
    print()
    print("✅ Générateur configuré avec toutes les nouvelles fonctionnalités!")
    print()


def example_backward_compatibility():
    """
    Exemple montrant que les anciens scripts fonctionnent toujours.

    Sans filename_keys, le comportement reste identique à avant:
    - Noms de fichiers simples: 001.png, 002.png, etc.
    - session_config.txt toujours généré
    - PLUS: metadata.json ajouté en bonus!
    """
    print("=" * 80)
    print("🔄 EXEMPLE 4: Backward Compatibility")
    print("=" * 80)
    print()
    print("Les scripts existants continuent de fonctionner exactement comme avant!")
    print()

    # Ancien style - sans filename_keys
    generator = ImageVariationGenerator(
        prompt_template="beautiful landscape, {Weather}, detailed",
        negative_prompt="low quality",
        variation_files={
            "Weather": "stable-diffusion-webui/prompts/my_prompts/weather.txt"
        },
        seed=42,
        session_name="landscapes"
        # Pas de filename_keys = comportement classique
    )

    print("📋 Configuration (style classique):")
    print(f"  - Pas de filename_keys spécifié")
    print(f"  - Comportement identique à avant")
    print()
    print("📁 Résultats (comme avant + bonus):")
    print("  └── 20251001_143052_landscapes/")
    print("      ├── session_config.txt           # Comme avant")
    print("      ├── metadata.json                # 🆕 BONUS automatique!")
    print("      ├── 001.png                      # Nommage classique")
    print("      ├── 002.png")
    print("      └── ...")
    print()
    print("✅ 100% compatible avec les scripts existants!")
    print()


def print_summary():
    """Affiche un résumé des nouvelles fonctionnalités."""
    print("=" * 80)
    print("📚 RÉSUMÉ DES NOUVELLES FONCTIONNALITÉS")
    print("=" * 80)
    print()
    print("🎯 Phase 1: Foundation (SF-4 & SF-5)")
    print()
    print("SF-4: Enhanced File Naming System")
    print("  ✓ Paramètre filename_keys pour noms descriptifs")
    print("  ✓ Sanitization automatique en camelCase")
    print("  ✓ Format: 001_Key1-value1_Key2-value2.png")
    print()
    print("SF-5: JSON Metadata Export")
    print("  ✓ Fichier metadata.json structuré et pretty-printed")
    print("  ✓ Toutes les infos de session (prompts, variations, params, timing)")
    print("  ✓ Exemple de prompt résolu automatique")
    print("  ✓ Backward compatibility avec session_config.txt")
    print()
    print("🔧 Utilisation:")
    print()
    print("  # Avec nouvelles fonctionnalités")
    print("  generator = ImageVariationGenerator(")
    print("      prompt_template=\"...\",")
    print("      variation_files={...},")
    print("      filename_keys=[\"Expression\", \"Angle\"]  # 🆕")
    print("  )")
    print()
    print("  # Sans changement (backward compatible)")
    print("  generator = ImageVariationGenerator(")
    print("      prompt_template=\"...\",")
    print("      variation_files={...}")
    print("      # Pas de filename_keys = comportement classique")
    print("  )")
    print()
    print("📖 Documentation complète: docs/json-config-feature.md")
    print()


if __name__ == "__main__":
    print()
    print("🌟" * 40)
    print()
    print("  DÉMONSTRATION DES NOUVELLES FONCTIONNALITÉS")
    print("  Phase 1: Foundation (SF-4 & SF-5)")
    print()
    print("🌟" * 40)
    print()

    # Lance les exemples
    example_with_filename_keys()
    example_with_metadata_json()
    example_combined_features()
    example_backward_compatibility()
    print_summary()

    print("🎉 FIN DE LA DÉMONSTRATION")
    print()
    print("Pour lancer une vraie génération, décommentez les lignes:")
    print("  # success, total = generator.run()")
    print()
