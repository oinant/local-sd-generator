#!/usr/bin/env python3
"""
Test du chargement depuis plusieurs fichiers pour un même placeholder
"""

from variation_loader import load_variations_from_files
import os

def test_multiple_files():
    """Test du chargement depuis plusieurs fichiers"""

    # Créer des fichiers de test
    file1 = "test_poses_basic.txt"
    file2 = "test_poses_advanced.txt"
    file3 = "test_expressions.txt"

    with open(file1, 'w', encoding='utf-8') as f:
        f.write("""# Poses basiques
standing
sitting
lying down
""")

    with open(file2, 'w', encoding='utf-8') as f:
        f.write("""# Poses avancées
handstand
splits
backbend,{|arms extended|hands on ground}
""")

    with open(file3, 'w', encoding='utf-8') as f:
        f.write("""# Expressions
happy
sad
angry
""")

    try:
        print("🧪 Test 1: Un seul fichier par placeholder")
        mapping1 = {
            "Pose": file1,
            "Expression": file3
        }
        variations1 = load_variations_from_files(mapping1)
        print(f"\n✅ Résultats:")
        for placeholder, vars_dict in variations1.items():
            print(f"\n{placeholder}: {len(vars_dict)} variations")
            for key, value in vars_dict.items():
                print(f"  {key} → {value}")

        print("\n" + "="*60)
        print("🧪 Test 2: Plusieurs fichiers pour un placeholder")
        mapping2 = {
            "Pose": [file1, file2],  # Liste de fichiers
            "Expression": file3
        }
        variations2 = load_variations_from_files(mapping2)
        print(f"\n✅ Résultats:")
        for placeholder, vars_dict in variations2.items():
            print(f"\n{placeholder}: {len(vars_dict)} variations")
            for key, value in vars_dict.items():
                print(f"  {key} → {value}")

        print("\n" + "="*60)
        print("📊 Comparaison:")
        print(f"  Test 1 - Pose: {len(variations1['Pose'])} variations")
        print(f"  Test 2 - Pose: {len(variations2['Pose'])} variations (fusionné depuis 2 fichiers)")
        print(f"  Différence: +{len(variations2['Pose']) - len(variations1['Pose'])} variations")

    finally:
        # Nettoyage
        for f in [file1, file2, file3]:
            if os.path.exists(f):
                os.remove(f)
        print("\n🧹 Fichiers de test supprimés")


if __name__ == "__main__":
    test_multiple_files()
