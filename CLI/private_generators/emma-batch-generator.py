from sdapi_client import StableDiffusionAPIClient, GenerationConfig, create_prompt_configs_from_combinations

# Configuration
API_URL = "http://127.0.0.1:7860"
EMMA_SEED = 3842499774  # Seed exacte de votre Emma parfaite
TOTAL_IMAGES = 60  # Augmenté pour plus de variations

# Prompt de base d'Emma (vos métadonnées exactes)
BASE_PROMPT = "Emma, beautiful european woman, brown hair, long hair no bangs, pale skin, light brown almond eyes, intense gaze, defined light eyebrows, long eyelashes, strong chin, medium lips slightly pink, small dimples, thin horizontal scar on left cheek, detailed face, professional photography, high quality, realistic"

BASE_NEGATIVE = "glasses, sunglasses, dark lenses, tinted glasses, blurry, bad anatomy, deformed face, asian, dark skin, short hair, bangs, blue eyes, green eyes, no glasses, thin eyebrows, weak chin, extra fingers, low quality, distorted"

# Variations d'angles de vue (avec clés courtes pour nommage)
ANGLES = {
    "front": "straight front view, looking directly at camera",
    "3quarter": "three quarter view, head turned 45 degrees",
    "profile_left": "side profile view, head turned 90 degrees left",
    "profile_right": "side profile view, head turned 90 degrees right",
    "shoulder": "slight head turn, looking over shoulder",

    # "tilt_up": "head tilted up, looking up at camera, chin raised",
    # "tilt_down": "head tilted down, looking down, lowered gaze",
    # "tilt_left": "head tilted slightly left, neck angled",
    # "tilt_right": "head tilted slightly right, neck angled",
    #
    # "low_angle": "shot from below, low camera angle, looking up at subject",
    # "high_angle": "shot from above, high camera angle, looking down at subject",
    # "extreme_low": "extreme low angle, dramatic upward view",
    # "extreme_high": "extreme high angle, bird's eye view, overhead shot",
    #
    # "dutch": "dutch angle, tilted camera, diagonal composition",
    # "closeup": "extreme close-up, face filling frame",
    # "portrait": "portrait crop, head and shoulders only",
    # "bust": "bust shot, upper body visible",
    #
    # "look_left": "looking to the left, head straight",
    # "look_right": "looking to the right, head straight",
    # "look_up_side": "looking up and to the side, contemplative angle",
    # "shoulder_left": "looking over left shoulder, back three quarter view",
    # "shoulder_right": "looking over right shoulder, back three quarter view"
}

# Variations d'expressions (avec clés courtes pour nommage)
EXPRESSIONS = {
    # Expressions neutres/douces
    "neutral": "neutral expression, relaxed face",
    "slight_smile": "slight smile, soft eyes",
    "gentle": "gentle smile, warm eyes",
    "serene": "serene expression, peaceful face",
    "thoughtful": "thoughtful expression, distant gaze",

    # Expressions confiantes/intenses
    "confident": "confident smile, direct gaze",
    "intense": "intense stare, focused eyes",
    "determined": "determined expression, firm jaw",
    "fierce": "fierce look, narrowed eyes",
    "bold": "bold expression, raised chin",
    "assertive": "assertive gaze, strong eyebrows",

    # Expressions émotionnelles fortes
    "excited": "wide excited eyes, open mouth smile",
    "angry": "frowning eyebrows, clenched jaw, intense stare",
    "furious": "furious look, narrowed angry eyes, tense face",
    "panicked": "wide fearful eyes, open mouth, worried eyebrows",
    "shocked": "shocked wide eyes, raised eyebrows, open mouth",
    "laughing": "laughing mouth wide open, squinting happy eyes",
    "hilarious": "uncontrollable laughter, tears in eyes, big smile",

    # Expressions séductrices/mystérieuses
    "seductive": "seductive half-closed eyes, subtle smile",
    "mysterious": "mysterious smile, knowing look",
    "mischievous": "mischievous smirk, playful eyes",
    "playful": "playful wink, teasing smile",
    "sultry": "sultry look, bedroom eyes",

    # Expressions complexes
    "defiant": "defiant raised chin, challenging stare",
    "rebellious": "rebellious smirk, defiant eyes",
    "sarcastic": "sarcastic smile, eye roll",
    "contemptuous": "contemptuous look, disdainful expression",
    "disgusted": "disgusted expression, wrinkled nose",
    "bored": "bored expression, half-closed tired eyes"
}

# Variations d'éclairage (avec clés courtes pour nommage)
LIGHTING = {
    "studio": "studio lighting",
    # "natural": "natural lighting",
    # "soft": "soft lighting",
    # "dramatic": "dramatic lighting",
    # "golden": "golden hour lighting",
    # "pro": "professional photography lighting",
    # "window": "window light",
    # "ambient": "ambient lighting"
}


def create_variations():
    """Crée toutes les variations d'Emma"""
    variations_dict = {
        "angles": ANGLES,
        "expressions": EXPRESSIONS,
        "lighting": LIGHTING
    }

    # Utilise la fonction du module pour créer les combinaisons
    prompt_configs = create_prompt_configs_from_combinations(
        base_prompt=BASE_PROMPT,
        negative_prompt=BASE_NEGATIVE,
        seed=EMMA_SEED,
        variations=variations_dict,
        filename_pattern="emma_{counter:03d}_{keys}.png"
    )

    # Limite au nombre max d'images demandé
    return prompt_configs[:TOTAL_IMAGES]


def main():
    """Fonction principale"""
    print("🚀 Début de la génération du dataset Emma")
    print(f"🎯 Nombre d'images: {TOTAL_IMAGES}")
    print(f"🌱 Seed d'Emma: {EMMA_SEED}")

    # Initialisation du client API avec timestamp
    client = StableDiffusionAPIClient(
        api_url=API_URL,
        base_output_dir="apioutput",
        session_name="emma_dataset"
    )

    # Configuration de génération (paramètres originaux)
    config = GenerationConfig(
        steps=30,
        cfg_scale=7,
        width=512,
        height=768,
        sampler_name="DPM++ 2M Karras",
        batch_size=1,
        n_iter=1
    )
    client.set_generation_config(config)

    # Génération des variations
    prompt_configs = create_variations()

    print(f"📋 {len(prompt_configs)} variations préparées")

    # Informations additionnelles pour la config
    additional_info = {
        "seed_principal": EMMA_SEED,
        "nombre_angles": len(ANGLES),
        "nombre_expressions": len(EXPRESSIONS),
        "nombre_eclairages": len(LIGHTING),
        "variations_totales_possibles": len(ANGLES) * len(EXPRESSIONS) * len(LIGHTING)
    }

    # Génération du batch avec le client
    success_count, total_count = client.generate_batch(
        prompt_configs=prompt_configs,
        delay_between_images=2.0,
        base_prompt=BASE_PROMPT,
        negative_prompt=BASE_NEGATIVE,
        additional_info=additional_info
    )


if __name__ == "__main__":
    # Configuration à modifier
    print("🔧 CONFIGURATION REQUISE:")
    print("1. Modifiez EMMA_SEED avec votre seed parfaite")
    print("2. Ajustez BASE_PROMPT selon votre Emma")
    print("3. Démarrez WebUI avec --api")
    print("4. Les images seront sauvées dans apioutput/")
    print("\nAppuyez sur Entrée pour continuer...")
    input()

    main()