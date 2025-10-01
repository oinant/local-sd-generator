#!/usr/bin/env python3
"""
Générateur d'expressions faciales refactorisé utilisant ImageVariationGenerator.

Ce script utilise maintenant la classe générique ImageVariationGenerator
pour une configuration plus simple et claire.
"""

from image_variation_generator import ImageVariationGenerator

# Configuration spécifique à ce générateur
PROMPT_TEMPLATE = """NSFW, score_9, score_8_up, score_7_up, score_6_up, detailed skin texture, finely detailed hair, ultra-detailed photo, best_quality, details in Ultra HD quality, best quality, amazing quality, highest score, absurdres, high details, highres,

very aesthetic,( light particles:1.4), bokeh, nsfw, light background,
dirty street, concrete floor, brick walls, desert street, night, neon lights, 
1girl, {Angle}, {Framing},
supermodel, slim build, {HairColor}, {HairCut},
chocker collar, Oversized Glasses, Earrings, Nose Ring, Cuff Bracelet, Pearl Bracelet, Nose Ring, 
black pleated miniskirt, revealing miniskirt, stockings and garter belt,
office white shirt, cleavage,  
{Tits}, no bra,
{SoloPose2},{SoloPoseHands},{SoloPoseLegs}, fucking stranger, anal sex, ({cum}:1.5),
looking at viewer, {FacialExpression}, bright eyes, very sweaty, pussy juice on finger

<lora:Real_Beauty:0.7> <lora:Dramatic Lighting Slider:0.4> <lora:Smooth Pony Booster:0.4> <lora:Perfect_Booty_XL_V1:1> <lora:zy_Realism_Enhancer_v1:0.3>
"""

# PROMPT_TEMPLATE = """NSFW, score_9, score_8_up, score_7_up, score_6_up, detailed skin texture, finely detailed hair, ultra-detailed photo, best_quality, details in Ultra HD quality, best quality, amazing quality, highest score, absurdres, high details, highres,
# {Places}
# 1girl, {AngleToViewer:#|24|25|26}
# supermodel, slim build, {HairColor}, {HairCut},
# chocker collar, Oversized Glasses, Earrings, Cuff Bracelet, Pearl Bracelet, pleated miniskirt, black thong, school uniform
# {Tits:#|0|1|2|9|10|11}, perfect ass, round ass,
# {SexScene},{SoloPoseHands:0},{SoloPoseLegs:0}, {SexAct:0}, {Focus},
# {FacialExpression:0}, bright eyes, very sweaty, {Cum:0}, {Cum:0}
#  <lora:Round_Breasts_XL_XV7:1> <lora:Body Tattoo Pony_alpha1.0_rank4_noxattn_last:1.4> <lora:igbaddie-PN:0.8> <lora:Real_Beauty:0.5> <lora:Dramatic Lighting Slider:0.4> <lora:Smooth Pony Booster:0.4> <lora:Perfect_Booty_XL_V1:1>
# """


# PROMPT_TEMPLATE = """masterpiece, ultra-HD, ultra-realistic, high detail, depth of field, (blurred background), best quality, very aesthetic,( light particles:1.4), bokeh, nsfw, light background,
# crowded restaurant, daylight,
# 1girl, {AngleToViewer}, very wide shot,
# supermodel, slim build, {HairColor}, {HairCut},
# chocker collar, Oversized Glasses, Earrings, Cuff Bracelet, Pearl Bracelet, pleated miniskirt, black thong, school uniform
# {Tits:#|0|1|2|9|10|11},
# {SexScene},{SoloPoseHands:0},{SoloPoseLegs:0}, {SexAct:0}, {Focus},
# {FacialExpression:0}, bright eyes, very sweaty, {Cum:0}, {Cum:0}
#
#
# <lora:Illustrious_V2:0.9> <lora:StS_PonyXL_Detail_Slider_v1.4_iteration_3:0.5>"""

#dirty street, concrete floor, brick walls, desert street, night, neon lights,
# black pleated miniskirt, revealing miniskirt, stockings and garter belt,office white shirt, cleavage,
#{SoloPose}, {SoloAction}, {SoloAction2},
#1girl, {Angle:#|6$2}, {Framing:#|6},
#chocker collar, Earrings, Nose Ring, Cuff Bracelet, Pearl Bracelet, Nose Ring,
#secretary outfit, cleavage, no bra,

# score_9, score_8_up, score_7_up,
# score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs
#NEGATIVE_PROMPT = "3d, worst quality, low quality, displeasing, text, watermark, bad anatomy, text, artist name, signature, hearts, deformed hands, missing finger, shiny skin,child,children"
#NEGATIVE_PROMPT = "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs, child,children"
NEGATIVE_PROMPT = "score_4, score_5, score_6, shiny face,  furniture, bed, plump lips, plump cheeks, man's face visible, worst quality, low quality, old, deformed, malformed, bad hands, bad fingers, long body, blurry, duplicated, cloned, duplicate body parts, extra limbs, fused fingers, extra fingers, twisted, distorted, malformed hands, malformed fingers, mutated hands and fingers, conjoined, missing limbs, bad anatomy, bad proportions, logo, watermark, text, lowres, mutated, mutilated, blend, artifacts, gross,"

# Fichiers de variations disponibles
VARIATION_FILES = {
    "FacialExpression": "private_generators/prompts/generalAndBasicPrompt_v19/Pony_FactialExpression.txt",
    "Angle": "private_generators/prompts/generalAndBasicPrompt_v19/General_Angle.txt",
    "Framing": "private_generators/prompts/generalAndBasicPrompt_v19/General_Framing.txt",
    "Shoes": "private_generators/prompts/generalAndBasicPrompt_v19/Attires_NSFW_Shoes.txt",
    "Waist": "private_generators/prompts/generalAndBasicPrompt_v19/Attires_Accessory_Waist.txt",
    "Style": "private_generators/prompts/generalAndBasicPrompt_v19/General_Styles.txt",
    "BreastFeature": "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BreastFeature.txt",
    "BreastShape": "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BreastShape.txt",
    "BreastSize": "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BreastSize.txt",
    "Cum": "private_generators/prompts/generalAndBasicPrompt_v19/Pony_Cum.txt",
    "Outfits": "private_generators/prompts/my_prompts/outfits.txt",
    "Tits": "private_generators/prompts/my_prompts/tits.txt",
    "HairCut": "private_generators/prompts/my_prompts/haircuts.txt",
    "SoloAction": "private_generators/prompts/my_prompts/soloaction.txt",
    "SoloAction2": "private_generators/prompts/my_prompts/soloaction2.txt",
    "SoloPose": "private_generators/prompts/my_prompts/solopose.txt",
    "SoloPose2": "private_generators/prompts/my_prompts/solopose2.txt",
    "SoloPoseHands": "private_generators/prompts/my_prompts/soloposehands.txt",
    "SoloPoseLegs": "private_generators/prompts/my_prompts/soloposelegs.txt",
    "HairColor" : "private_generators/prompts/my_prompts/haircolors.txt",
    "SexAct" : "private_generators/prompts/my_prompts/sexact.txt",
    "Focus" : "private_generators/prompts/my_prompts/focus.txt",
    "Places" : "private_generators/prompts/my_prompts/places.txt",
    "BottomOutfits" : "private_generators/prompts/generalAndBasicPrompt_v19/Attires_NSFW_Lowerbody.txt",
    "BottomOutfits2" : "private_generators/prompts/my_prompts/bottoms/categories.txt",
    "AngleToViewer" : "private_generators/prompts/my_prompts/angletoviewer.txt",
    "GeneralPosing" : "private_generators/prompts/generalAndBasicPrompt_v19/General_Posing.txt",
    "SexScene" : [
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex.txt",
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex1.txt",
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex2.txt",
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl2boySex.txt",
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girlSexSolo.txt",
                    "private_generators/prompts/generalAndBasicPrompt_v19/Pony_2girlSex.txt",
                  ],
    "SexSceneIncBdsm": [
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex1.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl1boySex2.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girl2boySex.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_1girlSexSolo.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_2girlSex.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BDSM1girl1boy.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BDSMGroup.txt",
        "private_generators/prompts/generalAndBasicPrompt_v19/Pony_BDSMSolo.txt",
    ],
}


def main():
    """Fonction principale - crée et lance le générateur."""
    print("🚀 Générateur d'expressions faciales avancé")
    print("📝 Utilisation de la classe ImageVariationGenerator")
    print()

    # Crée le générateur avec la configuration
    generator = ImageVariationGenerator(
        prompt_template=PROMPT_TEMPLATE,
        negative_prompt=NEGATIVE_PROMPT,
        variation_files=VARIATION_FILES,
        api_url="http://127.0.0.1:7860",
        seed=42,
        max_images=50,
        generation_mode="ask",  # Demande à l'utilisateur
        seed_mode="ask",       # Demande à l'utilisateur
        session_name="facial_expressions"
    )

    # Configuration optionnelle des paramètres de génération
    from sdapi_client import GenerationConfig
    config = GenerationConfig(
        steps=30,
        cfg_scale=7,
        width=832,
        height=1216,
        sampler_name="DPM++ 2M Karras",
        batch_size=1,
        n_iter=1
    )
    generator.set_generation_config(config)

    # Lance la génération
    try:
        success_count, total_count = generator.run()
        print(f"\n🎉 Génération terminée: {success_count}/{total_count} images réussies")

        if success_count == total_count:
            print("✅ Toutes les images ont été générées avec succès!")
        elif success_count > 0:
            print(f"⚠️  {total_count - success_count} images ont échoué")
        else:
            print("❌ Aucune image générée avec succès")

    except KeyboardInterrupt:
        print("\n⏹️  Génération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")


def create_custom_generator():
    """Exemple de création d'un générateur personnalisé rapide."""
    print("=== Générateur personnalisé rapide ===")

    # Version ultra-simple
    simple_generator = ImageVariationGenerator(
        prompt_template="beautiful anime girl, {SoloPose}, {SoloAction}, detailed",
        negative_prompt="low quality, blurry",
        variation_files={
            "SoloPose": "stable-diffusion-webui/prompts/my_prompts/solopose.txt",
            "SoloAction": "stable-diffusion-webui/prompts/my_prompts/soloaction.txt"
        },
        seed=123,
        max_images=20,
        generation_mode="random",
        seed_mode="progressive",
        session_name="simple_poses"
    )

    success, total = simple_generator.run()
    print(f"Générateur simple: {success}/{total} images")


if __name__ == "__main__":
    print("🔧 PRÉREQUIS:")
    print("1. Démarrez WebUI avec --api")
    print("2. Vérifiez que l'API est accessible sur http://127.0.0.1:7860")
    print("3. Assurez-vous que les fichiers de variations existent")
    print()

    print("Choisissez une option:")
    print("1. Lancer le générateur complet (original)")
    print("2. Lancer un générateur personnalisé simple")

    choice = input("\nVotre choix (1-2, Entrée=1) : ").strip() or "1"

    if choice == "2":
        create_custom_generator()
    else:
        main()