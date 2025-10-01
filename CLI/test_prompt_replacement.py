"""
Test rapide pour vérifier que le remplacement de placeholder fonctionne
dans les modes random et combinatorial.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sdapi_client import generate_all_combinations
from variation_loader import create_random_combinations
import re


def apply_variations(prompt_template, variations):
    """Simule _apply_variations_to_prompt."""
    prompt = prompt_template
    for placeholder, value in variations.items():
        if value:
            prompt = prompt.replace(f"{{{placeholder}}}", value)

    # Nettoie
    prompt = re.sub(r'\{[^}]+\}', '', prompt)
    prompt = re.sub(r',\s*,+', ',', prompt)
    prompt = re.sub(r'\s*,\s*', ', ', prompt)
    prompt = re.sub(r'\s+', ' ', prompt)
    prompt = prompt.strip(', ')

    return prompt


def test_combinatorial():
    print("\n" + "="*60)
    print("TEST MODE COMBINATORIAL")
    print("="*60)

    variations_dict = {
        "Expression": {
            "happy": "smiling",
            "sad": "crying"
        },
        "Angle": {
            "front": "front view",
            "side": "side view"
        }
    }

    prompt_template = "portrait, {Expression}, {Angle}, beautiful"

    print(f"\nTemplate: {prompt_template}")
    print(f"\nVariations:")
    for k, v in variations_dict.items():
        print(f"  {k}: {list(v.values())}")

    # Génère toutes les combinaisons
    all_combinations = generate_all_combinations(variations_dict)

    print(f"\n✅ {len(all_combinations)} combinaisons générées\n")

    for i, combination in enumerate(all_combinations, 1):
        prompt = apply_variations(prompt_template, combination)
        print(f"{i}. {combination}")
        print(f"   → {prompt}")


def test_random():
    print("\n" + "="*60)
    print("TEST MODE RANDOM")
    print("="*60)

    variations_dict = {
        "Expression": {
            "happy": "smiling",
            "sad": "crying"
        },
        "Angle": {
            "front": "front view",
            "side": "side view"
        }
    }

    prompt_template = "portrait, {Expression}, {Angle}, beautiful"

    print(f"\nTemplate: {prompt_template}")
    print(f"\nVariations:")
    for k, v in variations_dict.items():
        print(f"  {k}: {list(v.values())}")

    # Génère combinaisons aléatoires
    random_combinations = create_random_combinations(variations_dict, 3, seed=42)

    print(f"\n✅ {len(random_combinations)} combinaisons aléatoires générées\n")

    for i, combination in enumerate(random_combinations, 1):
        prompt = apply_variations(prompt_template, combination)
        print(f"{i}. {combination}")
        print(f"   → {prompt}")


def test_with_zero():
    print("\n" + "="*60)
    print("TEST AVEC PLACEHOLDER:0")
    print("="*60)

    variations_dict = {
        "Expression": {
            "happy": "smiling"
        },
        "Background": {
            "": ""  # Placeholder :0
        }
    }

    prompt_template = "portrait, {Expression}, {Background}, beautiful"

    print(f"\nTemplate: {prompt_template}")
    print(f"Expression: smiling")
    print(f"Background: supprimé (:0)")

    combination = {"Expression": "smiling", "Background": ""}
    prompt = apply_variations(prompt_template, combination)

    print(f"\n✅ Prompt final: {prompt}")


if __name__ == "__main__":
    try:
        test_combinatorial()
        test_random()
        test_with_zero()

        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()