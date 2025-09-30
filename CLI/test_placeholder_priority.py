"""
Test du système de poids de priorité pour l'ordre des boucles.

Ce script teste la fonctionnalité permettant de contrôler l'ordre des boucles
dans la génération combinatoire via des poids.
"""

from variation_loader import extract_placeholders_with_limits, sort_placeholders_by_priority

def test_priority_parsing():
    """Test du parsing des poids de priorité"""
    print("=" * 60)
    print("TEST 1: Parsing des poids de priorité")
    print("=" * 60)

    test_cases = [
        ("{Outfit:$2}", "Poids uniquement"),
        ("{Angle:$10}", "Poids uniquement"),
        ("{Expression:15$5}", "Limite avec poids"),
        ("{Pose:#|1|5|22$8}", "Index avec poids"),
        ("{Style:#|3$7}", "Index unique avec poids"),
        ("{Color}", "Sans poids (défaut)"),
    ]

    for placeholder_str, description in test_cases:
        result = extract_placeholders_with_limits(placeholder_str)
        print(f"\n{description}: {placeholder_str}")
        for name, options in result.items():
            print(f"  → {name}")
            print(f"     Type: {options['type']}")
            print(f"     Value: {options.get('value')}")
            print(f"     Priority: {options.get('priority', 0)}")

def test_priority_sorting():
    """Test du tri par priorité"""
    print("\n" + "=" * 60)
    print("TEST 2: Tri des placeholders par priorité")
    print("=" * 60)

    prompt = "1girl, {Outfit:$2}, {Angle:$10}, {Lighting:$5}, {Expression}, beautiful"

    print(f"\nPrompt: {prompt}")

    placeholders = extract_placeholders_with_limits(prompt)
    sorted_placeholders = sort_placeholders_by_priority(placeholders)

    print("\nOrdre des boucles (extérieur → intérieur):")
    for placeholder in sorted_placeholders:
        priority = placeholders[placeholder].get('priority', 0)
        print(f"  {placeholder} (poids: {priority})")

def test_combination_order():
    """Test de l'ordre des combinaisons générées"""
    print("\n" + "=" * 60)
    print("TEST 3: Ordre des combinaisons")
    print("=" * 60)

    from sdapi_client import generate_all_combinations
    from variation_loader import sort_placeholders_by_priority

    # Données de test simples
    variations = {
        "Outfit": {"outfit1": "dress", "outfit2": "jeans"},
        "Angle": {"angle1": "front view", "angle2": "side view", "angle3": "back view"}
    }

    print("\n--- Sans ordre spécifié (ordre naturel du dict) ---")
    combinations_natural = generate_all_combinations(variations)
    for i, combo in enumerate(combinations_natural[:6], 1):
        print(f"{i}. {combo}")

    print("\n--- Avec poids: Outfit=$2, Angle=$10 (Outfit extérieur) ---")

    # Simule les poids
    placeholder_options = {
        "Outfit": {"type": "none", "value": None, "priority": 2},
        "Angle": {"type": "none", "value": None, "priority": 10}
    }

    ordered_placeholders = sort_placeholders_by_priority(placeholder_options)
    print(f"Ordre calculé: {ordered_placeholders}")

    combinations_ordered = generate_all_combinations(variations, ordered_placeholders)
    for i, combo in enumerate(combinations_ordered[:6], 1):
        print(f"{i}. {combo}")

    print("\n--- Avec poids inversés: Outfit=$10, Angle=$2 (Angle extérieur) ---")

    placeholder_options_reversed = {
        "Outfit": {"type": "none", "value": None, "priority": 10},
        "Angle": {"type": "none", "value": None, "priority": 2}
    }

    ordered_placeholders_reversed = sort_placeholders_by_priority(placeholder_options_reversed)
    print(f"Ordre calculé: {ordered_placeholders_reversed}")

    combinations_reversed = generate_all_combinations(variations, ordered_placeholders_reversed)
    for i, combo in enumerate(combinations_reversed[:6], 1):
        print(f"{i}. {combo}")

if __name__ == "__main__":
    print("\n🧪 Tests du système de priorité des placeholders\n")

    test_priority_parsing()
    test_priority_sorting()
    test_combination_order()

    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)