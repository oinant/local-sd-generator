"""
Module pour charger des variations depuis des fichiers texte.

Ce module fournit des fonctions pour lire des fichiers contenant des options
et les convertir en dictionnaires utilisables pour la génération d'images.

Formats supportés:
- "clé→valeur" : Utilise la clé fournie
- "numéro→valeur" : Génère une clé depuis la valeur
- "valeur" : Génère une clé depuis la valeur

Exemple d'utilisation:
    variations = load_variations_from_file("expressions.txt")
    all_vars = load_variations_from_files({"Expression": "expr.txt", "Angle": "angles.txt"})
"""

import os
import re
import random
from typing import Dict, Optional, Set, Tuple, List


def extract_placeholders_with_limits(text: str) -> Dict[str, Optional[int]]:
    """
    Extrait tous les placeholders avec leurs limites optionnelles d'un texte.

    Formats supportés:
    - {PlaceholderName} : Pas de limite
    - {PlaceholderName:15} : Limite à 15 variations

    Args:
        text: Le texte contenant les placeholders

    Returns:
        Dict {placeholder_name: limit} où limit peut être None
    """
    # Pattern pour trouver {PlaceholderName} ou {PlaceholderName:N}
    pattern = r'\{([^}:]+)(?::(\d+))?\}'
    matches = re.findall(pattern, text)

    placeholders = {}
    for placeholder, limit_str in matches:
        limit = int(limit_str) if limit_str else None
        placeholders[placeholder] = limit

    return placeholders


def extract_placeholders(text: str) -> Set[str]:
    """
    Extrait tous les placeholders {PlaceholderName} d'un texte (compatibilité).

    Args:
        text: Le texte contenant les placeholders

    Returns:
        Set des noms de placeholders trouvés
    """
    placeholders_with_limits = extract_placeholders_with_limits(text)
    return set(placeholders_with_limits.keys())


def normalize_key(text: str) -> str:
    """
    Normalise un texte pour créer une clé valide.

    Args:
        text: Le texte à normaliser

    Returns:
        Une clé normalisée (alphanumérique + underscores)
    """
    # Supprime la ponctuation et remplace par des underscores
    normalized = re.sub(r'[^\w\s-]', '', text.lower())
    # Remplace espaces et tirets par des underscores
    normalized = re.sub(r'[\s-]+', '_', normalized)
    # Supprime les underscores multiples
    normalized = re.sub(r'_+', '_', normalized)
    # Supprime les underscores en début/fin
    normalized = normalized.strip('_')

    return normalized if normalized else 'unnamed'


def limit_variations(variations: Dict[str, str], limit: int) -> Dict[str, str]:
    """
    Limite le nombre de variations en sélectionnant aléatoirement.

    Args:
        variations: Dictionnaire des variations
        limit: Nombre maximum de variations à garder

    Returns:
        Dictionnaire avec un nombre limité de variations
    """
    if limit >= len(variations):
        return variations

    # Sélectionne aléatoirement les clés à garder
    selected_keys = random.sample(list(variations.keys()), limit)

    return {key: variations[key] for key in selected_keys}


def create_random_combinations(variations_dict: Dict[str, Dict[str, str]],
                             count: int,
                             seed: int = None) -> List[Dict[str, str]]:
    """
    Crée un nombre spécifique de combinaisons aléatoires uniques.

    Args:
        variations_dict: Dictionnaire {placeholder: {key: value}}
        count: Nombre de combinaisons à créer
        seed: Seed pour la reproductibilité (optionnel)

    Returns:
        Liste de dictionnaires {placeholder: valeur_choisie}
    """
    if seed is not None:
        random.seed(seed)

    if not variations_dict:
        return []

    placeholders = list(variations_dict.keys())
    combinations = []
    used_combinations = set()

    # Calcule le nombre max de combinaisons possibles
    max_combinations = 1
    for variations in variations_dict.values():
        max_combinations *= len(variations)

    # Limite le count au nombre max possible
    actual_count = min(count, max_combinations)

    attempts = 0
    max_attempts = actual_count * 10  # Évite les boucles infinies

    while len(combinations) < actual_count and attempts < max_attempts:
        attempts += 1

        # Crée une combinaison aléatoire
        combination = {}
        combination_key = []

        for placeholder in placeholders:
            # Choisit une variation aléatoire pour ce placeholder
            variations = variations_dict[placeholder]
            chosen_key = random.choice(list(variations.keys()))
            combination[placeholder] = variations[chosen_key]
            combination_key.append(f"{placeholder}:{chosen_key}")

        # Vérifie l'unicité
        key_tuple = tuple(sorted(combination_key))
        if key_tuple not in used_combinations:
            used_combinations.add(key_tuple)
            combinations.append(combination)

    return combinations


def load_variations_from_file(filepath: str, encoding: str = 'utf-8') -> Dict[str, str]:
    """
    Charge les variations depuis un fichier texte.

    Formats supportés par ligne:
    - "clé→valeur" : Utilise la clé fournie
    - "numéro→valeur" : Génère une clé depuis la valeur
    - "valeur" : Génère une clé depuis la valeur
    - Lignes vides et commençant par # ignorées

    Args:
        filepath: Chemin vers le fichier à lire
        encoding: Encodage du fichier (défaut: utf-8)

    Returns:
        Dictionnaire {clé: valeur} des variations

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        UnicodeDecodeError: Si l'encodage est incorrect
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier non trouvé: {filepath}")

    variations = {}

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Ignore les lignes vides et commentaires
                if not line or line.startswith('#'):
                    continue

                # Format: "clé→valeur"
                if '→' in line:
                    parts = line.split('→', 1)
                    if len(parts) != 2:
                        continue

                    key, value = parts[0].strip(), parts[1].strip()

                    # Si la clé est vide ou numérique, génère une clé depuis la valeur
                    if not key or key.isdigit():
                        key = normalize_key(value)
                    else:
                        key = normalize_key(key)

                    variations[key] = value

                else:
                    # Format: juste "valeur"
                    value = line.strip()
                    key = normalize_key(value)
                    variations[key] = value

    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture de {filepath}. "
            f"Essayez encoding='latin1' ou 'cp1252'. Erreur: {e}"
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture de {filepath}: {e}")

    return variations


def load_variations_for_placeholders(prompt: str,
                                   file_mapping: Dict[str, str],
                                   encoding: str = 'utf-8',
                                   verbose: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Charge uniquement les variations nécessaires selon les placeholders du prompt.
    Supporte les limites définies dans le prompt {Placeholder:N}.

    Args:
        prompt: Le prompt contenant les placeholders
        file_mapping: Dictionnaire {placeholder: chemin_fichier}
        encoding: Encodage des fichiers
        verbose: Affiche les informations de chargement

    Returns:
        Dictionnaire {placeholder: {clé: valeur}} pour les placeholders trouvés
    """
    # Extrait les placeholders avec leurs limites du prompt
    placeholders_with_limits = extract_placeholders_with_limits(prompt)

    if verbose:
        print(f"🔍 Placeholders trouvés dans le prompt:")
        for placeholder, limit in placeholders_with_limits.items():
            if limit:
                print(f"  {placeholder} (limité à {limit})")
            else:
                print(f"  {placeholder} (toutes variations)")

    # Filtre le mapping pour ne garder que ceux nécessaires
    filtered_mapping = {
        placeholder: filepath
        for placeholder, filepath in file_mapping.items()
        if placeholder in placeholders_with_limits
    }

    if verbose and len(filtered_mapping) < len(file_mapping):
        ignored = set(file_mapping.keys()) - set(placeholders_with_limits.keys())
        print(f"⏭️  Placeholders ignorés (non présents dans le prompt): {ignored}")

    # Charge les variations filtrées
    all_variations = load_variations_from_files(filtered_mapping, encoding, verbose)

    # Applique les limites spécifiées dans le prompt
    limited_variations = {}
    for placeholder, variations in all_variations.items():
        limit = placeholders_with_limits.get(placeholder)

        if limit and limit < len(variations):
            if verbose:
                print(f"🎲 Limitation de {placeholder}: {len(variations)} → {limit} (sélection aléatoire)")
            limited_variations[placeholder] = limit_variations(variations, limit)
        else:
            limited_variations[placeholder] = variations

    return limited_variations


def load_variations_from_files(file_mapping: Dict[str, str],
                             encoding: str = 'utf-8',
                             verbose: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Charge les variations depuis plusieurs fichiers.

    Args:
        file_mapping: Dictionnaire {placeholder: chemin_fichier}
        encoding: Encodage des fichiers
        verbose: Affiche les informations de chargement

    Returns:
        Dictionnaire {placeholder: {clé: valeur}}
    """
    all_variations = {}

    for placeholder, filepath in file_mapping.items():
        if verbose:
            print(f"📁 Chargement de {placeholder} depuis {filepath}")

        try:
            variations = load_variations_from_file(filepath, encoding)

            if variations:
                all_variations[placeholder] = variations
                if verbose:
                    print(f"✅ {len(variations)} variations chargées pour {placeholder}")
            else:
                if verbose:
                    print(f"⚠️  Aucune variation trouvée dans {filepath}")

        except Exception as e:
            if verbose:
                print(f"❌ Erreur pour {placeholder}: {e}")

    return all_variations


def validate_file_format(filepath: str, encoding: str = 'utf-8') -> Dict[str, any]:
    """
    Valide le format d'un fichier de variations.

    Args:
        filepath: Chemin vers le fichier à valider
        encoding: Encodage du fichier

    Returns:
        Dictionnaire avec les statistiques de validation
    """
    if not os.path.exists(filepath):
        return {"valid": False, "error": "Fichier non trouvé"}

    stats = {
        "valid": True,
        "total_lines": 0,
        "valid_entries": 0,
        "empty_lines": 0,
        "comment_lines": 0,
        "invalid_lines": 0,
        "format_types": {"key_value": 0, "value_only": 0}
    }

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            for line_num, line in enumerate(f, 1):
                stats["total_lines"] += 1
                line = line.strip()

                if not line:
                    stats["empty_lines"] += 1
                elif line.startswith('#'):
                    stats["comment_lines"] += 1
                elif '→' in line:
                    parts = line.split('→', 1)
                    if len(parts) == 2 and parts[1].strip():
                        stats["valid_entries"] += 1
                        stats["format_types"]["key_value"] += 1
                    else:
                        stats["invalid_lines"] += 1
                else:
                    if line.strip():
                        stats["valid_entries"] += 1
                        stats["format_types"]["value_only"] += 1
                    else:
                        stats["invalid_lines"] += 1

    except Exception as e:
        stats["valid"] = False
        stats["error"] = str(e)

    return stats


if __name__ == "__main__":
    # Test du module
    test_file = "test_variations.txt"

    # Crée un fichier de test
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""# Expressions de test
1→angry
2→happy
3→sad
smiling
laughing
surprised→very surprised
""")

    print("🧪 Test du module variation_loader")

    # Test de chargement
    try:
        variations = load_variations_from_file(test_file)
        print(f"✅ Chargement réussi: {len(variations)} variations")
        for key, value in variations.items():
            print(f"  {key} → {value}")

        # Test de validation
        stats = validate_file_format(test_file)
        print(f"\n📊 Statistiques: {stats}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

    # Nettoyage
    os.remove(test_file)
    print("\n🧹 Fichier de test supprimé")