#!/usr/bin/env python3
"""
Test de l'expansion des variations imbriquées
"""

from variation_loader import expand_nested_variations, load_variations_from_file
import os

def test_expand_nested_variations():
    """Test de la fonction expand_nested_variations"""

    print("🧪 Test 1: Variation simple avec 2 options imbriquées")
    text1 = "breast slip,{|leaning forward},{|lactation|lactation,projectile_lactation}"
    result1 = expand_nested_variations(text1)
    print(f"Input: {text1}")
    print(f"Output ({len(result1)} variations):")
    for i, var in enumerate(result1, 1):
        print(f"  {i}. {var}")

    print("\n🧪 Test 2: Variation simple")
    text2 = "simple text"
    result2 = expand_nested_variations(text2)
    print(f"Input: {text2}")
    print(f"Output: {result2}")

    print("\n🧪 Test 3: Une seule option")
    text3 = "base,{|option1|option2}"
    result3 = expand_nested_variations(text3)
    print(f"Input: {text3}")
    print(f"Output ({len(result3)} variations):")
    for i, var in enumerate(result3, 1):
        print(f"  {i}. {var}")

    print("\n🧪 Test 4: Trois options imbriquées")
    text4 = "{|a},{|b},{|c}"
    result4 = expand_nested_variations(text4)
    print(f"Input: {text4}")
    print(f"Output ({len(result4)} variations):")
    for i, var in enumerate(result4, 1):
        print(f"  {i}. {var}")


def test_load_with_nested():
    """Test du chargement depuis fichier avec variations imbriquées"""

    print("\n\n📁 Test de chargement depuis fichier")

    # Créer un fichier de test
    test_file = "test_nested.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""# Test variations imbriquées
breast slip,{|leaning forward},{|lactation|lactation,projectile_lactation}
simple pose
standing,{|arms up|hands on hips}
sitting,{|legs crossed},{|reading book}
""")

    try:
        variations = load_variations_from_file(test_file)
        print(f"\n✅ {len(variations)} variations chargées:")
        for key, value in variations.items():
            print(f"  {key} → {value}")

    finally:
        # Nettoyage
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Fichier de test supprimé")


if __name__ == "__main__":
    test_expand_nested_variations()
    test_load_with_nested()
