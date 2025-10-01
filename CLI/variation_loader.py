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
import time
import itertools
from typing import Dict, Optional, Set, Tuple, List, Union


def expand_nested_variations(text: str) -> List[str]:
    """
    Expanse les variations imbriquées dans le format {|option1|option2}.

    Format supporté:
    - "{|option1|option2}" génère ["option1", "option2", ""]
    - "prefix,{|suffix1|suffix2}" génère ["prefix", "prefix,suffix1", "prefix,suffix2"]
    - Peut avoir plusieurs placeholders : "a,{|b},{|c|d}" génère toutes les combinaisons

    Le pattern {|} seul génère une option vide (permet d'avoir "avec" ou "sans").

    Args:
        text: Le texte contenant des variations imbriquées

    Returns:
        Liste de toutes les variations possibles

    Examples:
        >>> expand_nested_variations("breast slip,{|leaning forward},{|lactation|lactation,projectile_lactation}")
        [
            "breast slip",
            "breast slip,leaning forward",
            "breast slip,lactation",
            "breast slip,leaning forward,lactation",
            "breast slip,lactation,projectile_lactation",
            "breast slip,leaning forward,lactation,projectile_lactation"
        ]
    """
    # Pattern pour trouver {|option1|option2|...}
    pattern = r'\{\|([^}]*)\}'

    # Trouve tous les placeholders de variations
    matches = list(re.finditer(pattern, text))

    if not matches:
        # Pas de variations imbriquées, retourne le texte tel quel
        return [text]

    # Extrait les options pour chaque placeholder
    all_options = []
    for match in matches:
        options_str = match.group(1)
        # Split par | et ajoute toujours l'option vide (pour "sans")
        options = [""] + [opt.strip() for opt in options_str.split("|") if opt.strip()]
        all_options.append(options)

    # Génère toutes les combinaisons
    results = []
    for combination in itertools.product(*all_options):
        # Reconstruit le texte avec cette combinaison
        result = text
        for i, match in enumerate(reversed(matches)):  # Reverse pour ne pas décaler les index
            replacement = combination[len(matches) - 1 - i]
            result = result[:match.start()] + replacement + result[match.end():]

        # Nettoie les virgules multiples et en début/fin
        result = re.sub(r',+', ',', result)  # Virgules multiples
        result = re.sub(r'^,|,$', '', result)  # Virgules début/fin
        result = result.strip()

        if result:  # Ne garde que les résultats non vides
            results.append(result)

    # Déduplique tout en préservant l'ordre
    seen = set()
    unique_results = []
    for r in results:
        if r not in seen:
            seen.add(r)
            unique_results.append(r)

    return unique_results


def extract_placeholders_with_limits(text: str) -> Dict[str, dict]:
    """
    Extrait tous les placeholders avec leurs options d'un texte.

    Formats supportés:
    - {PlaceholderName} : Pas de limite
    - {PlaceholderName:15} : Limite à 15 variations aléatoires
    - {PlaceholderName:0} : Supprime le placeholder (valeur vide)
    - {PlaceholderName:#|1|5|22} : Sélectionne les index 1, 5 et 22 spécifiquement
    - {PlaceholderName:#|6|4|2$8} : Indices 6,4,2 avec poids de priorité 8
    - {PlaceholderName:15$8} : Limite 15 variations avec poids 8
    - {PlaceholderName:$8} : Toutes variations avec poids 8

    Le poids détermine l'ordre des boucles en mode combinatorial :
    - Plus grand poids = boucle plus imbriquée (intérieure)
    - Plus petit poids = boucle extérieure

    Args:
        text: Le texte contenant les placeholders

    Returns:
        Dict {placeholder_name: {"type": "limit"|"zero"|"indices"|"none", "value": ..., "priority": int}}
    """
    # Pattern pour trouver {PlaceholderName} avec options optionnelles
    pattern = r'\{([^}:]+)(?::([^}]+))?\}'
    matches = re.findall(pattern, text)

    placeholders = {}
    for placeholder, option_str in matches:
        priority = 0  # Poids par défaut

        if not option_str:
            # Pas d'option : toutes les variations
            placeholders[placeholder] = {"type": "none", "value": None, "priority": priority}
        elif option_str == "0":
            # :0 = suppression du placeholder
            placeholders[placeholder] = {"type": "zero", "value": 0, "priority": priority}
        else:
            # Extrait le poids si présent (format: ....$N)
            if "$" in option_str:
                main_part, priority_str = option_str.rsplit("$", 1)
                try:
                    priority = int(priority_str.strip())
                except ValueError:
                    priority = 0
            else:
                main_part = option_str

            # Parse la partie principale
            if not main_part:
                # Juste un poids: {PlaceholderName:$8}
                placeholders[placeholder] = {"type": "none", "value": None, "priority": priority}
            elif main_part.startswith("#|"):
                # #|1|5|22 = sélection d'index spécifiques
                indices_str = main_part[2:]  # Enlève "#|"
                try:
                    indices = [int(idx.strip()) for idx in indices_str.split("|") if idx.strip()]
                    placeholders[placeholder] = {"type": "indices", "value": indices, "priority": priority}
                except ValueError:
                    # Si parsing échoue, traiter comme limite normale
                    placeholders[placeholder] = {"type": "none", "value": None, "priority": priority}
            else:
                # N = limite à N variations aléatoires
                try:
                    limit = int(main_part)
                    placeholders[placeholder] = {"type": "limit", "value": limit, "priority": priority}
                except ValueError:
                    # Si parsing échoue, pas de limite
                    placeholders[placeholder] = {"type": "none", "value": None, "priority": priority}

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


def select_variations_by_indices(variations: Dict[str, str], indices: List[int]) -> Dict[str, str]:
    """
    Sélectionne des variations spécifiques par leurs index.

    Args:
        variations: Dictionnaire des variations
        indices: Liste des index à sélectionner (0-based)

    Returns:
        Dictionnaire avec uniquement les variations aux index spécifiés
    """
    variations_list = list(variations.items())
    selected = {}

    for idx in indices:
        if 0 <= idx < len(variations_list):
            key, value = variations_list[idx]
            selected[key] = value

    return selected


def sort_placeholders_by_priority(placeholders_dict: Dict[str, dict]) -> List[str]:
    """
    Trie les placeholders par leur poids de priorité pour l'ordre des boucles.

    Plus grand poids = boucle plus imbriquée (intérieure)
    Plus petit poids = boucle extérieure

    Args:
        placeholders_dict: Dict {placeholder: {"type": ..., "value": ..., "priority": int}}

    Returns:
        Liste des noms de placeholders triés par priorité décroissante
    """
    # Trie par priorité décroissante (plus grand poids en dernier = plus imbriqué)
    sorted_items = sorted(
        placeholders_dict.items(),
        key=lambda item: item[1].get("priority", 0),
        reverse=False  # Ordre croissant: petit poids d'abord (boucle extérieure)
    )

    return [placeholder for placeholder, _ in sorted_items]


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
    #if seed is not None:
    #    random.seed(seed)
    random.seed(time.time())

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
    - Variations imbriquées : "valeur,{|option1|option2}" expanse toutes les combinaisons

    Args:
        filepath: Chemin vers le fichier à lire
        encoding: Encodage du fichier (défaut: utf-8)

    Returns:
        Dictionnaire {clé: valeur} des variations (expansées si variations imbriquées)

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

                    # Expanse les variations imbriquées si présentes
                    expanded_values = expand_nested_variations(value)

                    for expanded_value in expanded_values:
                        # Si la clé est vide ou numérique, génère une clé depuis la valeur
                        if not key or key.isdigit():
                            expanded_key = normalize_key(expanded_value)
                        else:
                            # Pour les clés explicites avec variations, ajoute un suffixe
                            if len(expanded_values) > 1:
                                expanded_key = normalize_key(key + "_" + expanded_value)
                            else:
                                expanded_key = normalize_key(key)

                        variations[expanded_key] = expanded_value

                else:
                    # Format: juste "valeur"
                    value = line.strip()

                    # Expanse les variations imbriquées si présentes
                    expanded_values = expand_nested_variations(value)

                    for expanded_value in expanded_values:
                        key = normalize_key(expanded_value)
                        variations[key] = expanded_value

    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            f"Erreur d'encodage lors de la lecture de {filepath}. "
            f"Essayez encoding='latin1' ou 'cp1252'. Erreur: {e}"
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture de {filepath}: {e}")

    return variations


def load_variations_for_placeholders(prompt: str,
                                   file_mapping: Dict[str, Union[str, List[str]]],
                                   encoding: str = 'utf-8',
                                   verbose: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Charge uniquement les variations nécessaires selon les placeholders du prompt.

    Supporte plusieurs formats :
    - {Placeholder} : Toutes les variations
    - {Placeholder:N} : N variations aléatoires
    - {Placeholder:0} : Supprime le placeholder (retourne dict vide)
    - {Placeholder:#|1|5|22} : Sélectionne les index 1, 5 et 22

    Supporte plusieurs fichiers par placeholder :
    - {placeholder: "file.txt"} : Un seul fichier
    - {placeholder: ["file1.txt", "file2.txt"]} : Plusieurs fichiers fusionnés

    Args:
        prompt: Le prompt contenant les placeholders
        file_mapping: Dictionnaire {placeholder: chemin_fichier ou [chemins_fichiers]}
        encoding: Encodage des fichiers
        verbose: Affiche les informations de chargement

    Returns:
        Dictionnaire {placeholder: {clé: valeur}} pour les placeholders trouvés
    """
    # Extrait les placeholders avec leurs options du prompt
    placeholders_with_options = extract_placeholders_with_limits(prompt)

    if verbose:
        print(f"🔍 Placeholders trouvés dans le prompt:")
        for placeholder, options in placeholders_with_options.items():
            option_type = options["type"]
            option_value = options["value"]

            if option_type == "zero":
                print(f"  {placeholder} (supprimé :0)")
            elif option_type == "limit":
                print(f"  {placeholder} (limité à {option_value} variations)")
            elif option_type == "indices":
                print(f"  {placeholder} (index spécifiques: {option_value})")
            else:
                print(f"  {placeholder} (toutes variations)")

    # Filtre le mapping pour ne garder que ceux nécessaires (sauf :0)
    filtered_mapping = {
        placeholder: filepath
        for placeholder, filepath in file_mapping.items()
        if placeholder in placeholders_with_options
        and placeholders_with_options[placeholder]["type"] != "zero"
    }

    if verbose and len(filtered_mapping) < len(file_mapping):
        ignored = set(file_mapping.keys()) - set(placeholders_with_options.keys())
        if ignored:
            print(f"⏭️  Placeholders ignorés (non présents dans le prompt): {ignored}")

    # Charge les variations filtrées
    all_variations = load_variations_from_files(filtered_mapping, encoding, verbose)

    # Applique les options spécifiées dans le prompt
    processed_variations = {}
    for placeholder, variations in all_variations.items():
        options = placeholders_with_options.get(placeholder)
        if not options:
            processed_variations[placeholder] = variations
            continue

        option_type = options["type"]
        option_value = options["value"]

        if option_type == "zero":
            # Placeholder à supprimer : retourne dict vide
            processed_variations[placeholder] = {"": ""}
            if verbose:
                print(f"🚫 {placeholder} sera supprimé du prompt")

        elif option_type == "limit" and option_value < len(variations):
            # Limitation aléatoire
            if verbose:
                print(f"🎲 Limitation de {placeholder}: {len(variations)} → {option_value} (sélection aléatoire)")
            processed_variations[placeholder] = limit_variations(variations, option_value)

        elif option_type == "indices":
            # Sélection par index
            selected = select_variations_by_indices(variations, option_value)
            if verbose:
                print(f"🎯 Sélection de {placeholder}: {len(selected)} variations aux index {option_value}")
            processed_variations[placeholder] = selected if selected else variations

        else:
            # Pas de modification
            processed_variations[placeholder] = variations

    # Ajoute les placeholders :0 qui ne sont pas dans file_mapping
    for placeholder, options in placeholders_with_options.items():
        if options["type"] == "zero" and placeholder not in processed_variations:
            processed_variations[placeholder] = {"": ""}
            if verbose:
                print(f"🚫 {placeholder} sera supprimé du prompt")

    return processed_variations


def load_variations_from_files(file_mapping: Dict[str, Union[str, List[str]]],
                             encoding: str = 'utf-8',
                             verbose: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Charge les variations depuis plusieurs fichiers.

    Supporte maintenant plusieurs fichiers par placeholder :
    - {placeholder: "file.txt"} : Un seul fichier
    - {placeholder: ["file1.txt", "file2.txt"]} : Plusieurs fichiers fusionnés

    Args:
        file_mapping: Dictionnaire {placeholder: chemin_fichier ou [chemins_fichiers]}
        encoding: Encodage des fichiers
        verbose: Affiche les informations de chargement

    Returns:
        Dictionnaire {placeholder: {clé: valeur}}
    """
    all_variations = {}

    for placeholder, filepaths in file_mapping.items():
        # Normalise en liste si c'est une string
        if isinstance(filepaths, str):
            filepaths = [filepaths]

        merged_variations = {}

        for filepath in filepaths:
            if verbose:
                if len(filepaths) > 1:
                    print(f"📁 Chargement de {placeholder} depuis {filepath} ({filepaths.index(filepath) + 1}/{len(filepaths)})")
                else:
                    print(f"📁 Chargement de {placeholder} depuis {filepath}")

            try:
                variations = load_variations_from_file(filepath, encoding)

                if variations:
                    # Fusionne avec les variations précédentes
                    merged_variations.update(variations)
                    if verbose:
                        print(f"✅ {len(variations)} variations chargées")
                else:
                    if verbose:
                        print(f"⚠️  Aucune variation trouvée dans {filepath}")

            except Exception as e:
                if verbose:
                    print(f"❌ Erreur pour {filepath}: {e}")

        if merged_variations:
            all_variations[placeholder] = merged_variations
            if verbose and len(filepaths) > 1:
                print(f"✨ Total pour {placeholder}: {len(merged_variations)} variations (depuis {len(filepaths)} fichiers)")

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