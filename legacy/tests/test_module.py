#!/usr/bin/env python3

from sdapi_client import StableDiffusionAPIClient, GenerationConfig, PromptConfig

def test_simple_generation():
    """Test basique du module avec quelques prompts"""

    # Configuration du client avec timestamp
    client = StableDiffusionAPIClient(
        api_url="http://127.0.0.1:7860",
        base_output_dir="apioutput",
        session_name="test_module"
    )

    # Configuration de génération
    config = GenerationConfig(
        steps=20,  # Plus rapide pour le test
        cfg_scale=7,
        width=512,
        height=512,  # Format carré pour le test
        sampler_name="DPM++ 2M Karras"
    )
    client.set_generation_config(config)

    # Quelques prompts de test
    test_prompts = [
        PromptConfig(
            prompt="beautiful woman, portrait, professional photography",
            negative_prompt="blurry, low quality",
            seed=12345,
            filename="test_001_portrait.png"
        ),
        PromptConfig(
            prompt="beautiful woman, smiling, natural lighting",
            negative_prompt="blurry, low quality",
            seed=12346,
            filename="test_002_smile.png"
        ),
        PromptConfig(
            prompt="beautiful woman, side profile, dramatic lighting",
            negative_prompt="blurry, low quality",
            seed=12347,
            filename="test_003_profile.png"
        )
    ]

    # Test de connexion
    print("🧪 Test du module sdapi_client")
    if not client.test_connection():
        print("❌ Impossible de se connecter à l'API. Assurez-vous que WebUI est démarré avec --api")
        return

    print("✅ Connexion API OK")

    # Génération du batch avec sauvegarde de config
    success, total = client.generate_batch(
        prompt_configs=test_prompts,
        delay_between_images=1.0,  # Délai réduit pour le test
        base_prompt="beautiful woman",
        negative_prompt="blurry, low quality",
        additional_info={
            "test_type": "Module validation",
            "nombre_prompts_test": len(test_prompts)
        }
    )

    print(f"\n🎯 Test terminé: {success}/{total} images générées avec succès")

if __name__ == "__main__":
    test_simple_generation()