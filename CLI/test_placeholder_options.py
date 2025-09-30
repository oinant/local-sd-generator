"""
Script de test pour les nouvelles options de placeholder.

Teste les formats:
- {Placeholder:0} : Suppression du placeholder
- {Placeholder:#|1|5|22} : Sélection d'index spécifiques
"""

import sys
import os

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(__file__))

from variation_loader import (
    extract_placeholders_with_limits,
    load_variations_for_placeholders,
    select_variations_by_indices
)


def test_extract_placeholders():
    """Test d'extraction des placeholders avec options."""
    print("\n" + "="*60)
    print("TEST 1: Extraction des placeholders")
    print("="*60)

    test_cases = [
        ("portrait, {Hair}, {Expression}", "Sans options"),
        ("portrait, {Hair:5}, {Expression:3}", "Avec limites"),
        ("portrait, {Hair:0}, {Expression}", "Avec suppression"),
        ("portrait, {Hair:#|1|5|22}, {Expression:#|0|2}", "Avec index spécifiques"),
        ("portrait, {Hair:#|1|5|22}, {Expression:0}, {Background:3}", "Mix de tout"),
    ]

    for prompt, description in test_cases:
        print(f"\n📝 {description}")
        print(f"   Prompt: {prompt}")
        result = extract_placeholders_with_limits(prompt)
        for placeholder, options in result.items():
            option_type = options["type"]
            option_value = options["value"]
            if option_type == "zero":
                print(f"   ✓ {placeholder}: SUPPRIMÉ (:0)")
            elif option_type == "limit":
                print(f"   ✓ {placeholder}: limité à {option_value}")
            elif option_type == "indices":
                print(f"   ✓ {placeholder}: index {option_value}")
            else:
                print(f"   ✓ {placeholder}: toutes variations")


def test_select_by_indices():
    """Test de sélection par index."""
    print("\n" + "="*60)
    print("TEST 2: Sélection par index")
    print("="*60)

    # Crée des variations de test
    test_variations = {
        "opt0": "Option 0",
        "opt1": "Option 1",
        "opt2": "Option 2",
        "opt3": "Option 3",
        "opt4": "Option 4",
        "opt5": "Option 5",
    }

    print(f"\n📦 Variations disponibles:")
    for i, (key, value) in enumerate(test_variations.items()):
        print(f"   [{i}] {key} → {value}")

    test_cases = [
        ([0, 2, 4], "Index 0, 2, 4"),
        ([1, 3, 5], "Index 1, 3, 5"),
        ([0], "Index 0 uniquement"),
        ([10, 20], "Index invalides (hors limites)"),
    ]

    for indices, description in test_cases:
        print(f"\n🎯 {description}")
        print(f"   Index demandés: {indices}")
        result = select_variations_by_indices(test_variations, indices)
        print(f"   Résultat ({len(result)} variations):")
        for key, value in result.items():
            print(f"     - {key} → {value}")


def test_load_with_options():
    """Test de chargement avec fichiers réels."""
    print("\n" + "="*60)
    print("TEST 3: Chargement avec fichiers (simulation)")
    print("="*60)

    # Crée des fichiers temporaires de test
    test_files = {
        "test_hair.txt": [
            "short blonde",
            "long black",
            "curly red",
            "straight brown",
            "wavy silver"
        ],
        "test_expression.txt": [
            "smiling",
            "serious",
            "laughing",
            "surprised"
        ]
    }

    # Crée les fichiers
    for filename, lines in test_files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")

    # Test avec différents prompts
    test_cases = [
        (
            "portrait, {Hair}, {Expression}",
            {"Hair": "test_hair.txt", "Expression": "test_expression.txt"},
            "Toutes variations"
        ),
        (
            "portrait, {Hair:2}, {Expression:2}",
            {"Hair": "test_hair.txt", "Expression": "test_expression.txt"},
            "Limité à 2 chaque"
        ),
        (
            "portrait, {Hair:#|0|2|4}, {Expression}",
            {"Hair": "test_hair.txt", "Expression": "test_expression.txt"},
            "Hair avec index spécifiques"
        ),
        (
            "portrait, {Hair:0}, {Expression}",
            {"Hair": "test_hair.txt", "Expression": "test_expression.txt"},
            "Hair supprimé"
        ),
    ]

    for prompt, file_mapping, description in test_cases:
        print(f"\n🔍 Test: {description}")
        print(f"   Prompt: {prompt}")
        try:
            result = load_variations_for_placeholders(prompt, file_mapping, verbose=True)
            print(f"\n   ✅ Chargement réussi:")
            for placeholder, variations in result.items():
                print(f"      {placeholder}: {len(variations)} variations")
                if len(variations) <= 5:
                    for key, value in variations.items():
                        print(f"        - {value}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

    # Nettoyage
    print("\n🧹 Nettoyage des fichiers de test...")
    for filename in test_files.keys():
        if os.path.exists(filename):
            os.remove(filename)
            print(f"   ✓ {filename} supprimé")


def test_prompt_cleaning():
    """Test du nettoyage de prompt avec placeholders vides."""
    print("\n" + "="*60)
    print("TEST 4: Nettoyage de prompts")
    print("="*60)

    import re

    def clean_prompt(prompt: str) -> str:
        """Fonction de nettoyage du prompt."""
        # Supprime les placeholders
        prompt = re.sub(r'\{[^}]+\}', '', prompt)
        # Nettoie virgules et espaces
        prompt = re.sub(r',\s*,+', ',', prompt)
        prompt = re.sub(r'\s*,\s*', ', ', prompt)
        prompt = re.sub(r'\s+', ' ', prompt)
        prompt = prompt.strip(', ')
        return prompt

    test_cases = [
        "portrait, {Hair}, beautiful",
        "portrait, , beautiful",
        "portrait,,, beautiful",
        "{Hair}, portrait, {Expression}",
        "portrait, beautiful, {Hair}",
        "{Hair}",
    ]

    for prompt in test_cases:
        cleaned = clean_prompt(prompt)
        print(f"\n   Original: '{prompt}'")
        print(f"   Nettoyé:  '{cleaned}'")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS DES NOUVELLES OPTIONS DE PLACEHOLDER")
    print("="*60)

    try:
        test_extract_placeholders()
        test_select_by_indices()
        test_load_with_options()
        test_prompt_cleaning()

        print("\n" + "="*60)
        print("✅ TOUS LES TESTS TERMINÉS")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ERREUR DURANT LES TESTS: {e}")
        import traceback
        traceback.print_exc()