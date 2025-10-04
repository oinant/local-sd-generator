import requests
import json
import base64
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class GenerationConfig:
    """Configuration pour la génération d'images"""
    steps: int = 30
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 768
    sampler_name: str = "DPM++ 2M Karras"
    batch_size: int = 1
    n_iter: int = 1


@dataclass
class PromptConfig:
    """Configuration pour un prompt spécifique"""
    prompt: str
    negative_prompt: str = ""
    seed: Optional[int] = None
    filename: str = ""


class StableDiffusionAPIClient:
    """Client pour l'API Stable Diffusion WebUI"""

    def __init__(self, api_url: str = "http://127.0.0.1:7860",
                 base_output_dir: str = "apioutput",
                 session_name: str = None,
                 dry_run: bool = False):
        self.api_url = api_url
        self.base_output_dir = base_output_dir
        self.session_name = session_name
        self.dry_run = dry_run
        self.session_start_time = datetime.now()
        self.output_dir = self._create_session_dir()
        self.generation_config = GenerationConfig()

    def _create_session_dir(self) -> str:
        """Crée le dossier de session avec timestamp"""
        timestamp = self.session_start_time.strftime("%Y-%m-%d_%H%M%S")
        if self.session_name:
            session_dir_name = f"{timestamp}_{self.session_name}"
        else:
            session_dir_name = timestamp

        # En mode dry-run, utiliser un sous-dossier /dryrun
        if self.dry_run:
            base_dir = os.path.join(self.base_output_dir, "dryrun")
        else:
            base_dir = self.base_output_dir

        session_dir = os.path.join(base_dir, session_dir_name)
        return session_dir

    def set_generation_config(self, config: GenerationConfig):
        """Définit la configuration de génération"""
        self.generation_config = config

    def test_connection(self) -> bool:
        """Teste la connexion à l'API WebUI"""
        try:
            response = requests.get(f"{self.api_url}/sdapi/v1/options", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion API: {e}")
            return False

    def create_output_dir(self):
        """Crée le dossier de sortie s'il n'existe pas"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Dossier créé: {self.output_dir}")

    def save_session_config(self, base_prompt: str = "", negative_prompt: str = "",
                           additional_info: Dict = None):
        """Sauvegarde la configuration de la session dans un fichier texte"""
        config_filename = "session_config.txt"
        config_path = os.path.join(self.output_dir, config_filename)

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SESSION CONFIGURATION\n")
            f.write("=" * 60 + "\n\n")

            # Informations de session
            f.write(f"Date de génération: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nom de session: {self.session_name or 'Non spécifié'}\n")
            f.write(f"URL API: {self.api_url}\n")
            f.write(f"Dossier de sortie: {self.output_dir}\n\n")

            # Prompts
            f.write("-" * 40 + "\n")
            f.write("PROMPTS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Prompt de base:\n{base_prompt}\n\n")
            f.write(f"Prompt négatif:\n{negative_prompt}\n\n")

            # Paramètres de génération
            f.write("-" * 40 + "\n")
            f.write("PARAMÈTRES DE GÉNÉRATION\n")
            f.write("-" * 40 + "\n")
            config_dict = asdict(self.generation_config)
            for key, value in config_dict.items():
                f.write(f"{key}: {value}\n")

            # Informations additionnelles
            if additional_info:
                f.write("\n" + "-" * 40 + "\n")
                f.write("INFORMATIONS ADDITIONNELLES\n")
                f.write("-" * 40 + "\n")
                for key, value in additional_info.items():
                    f.write(f"{key}: {value}\n")

        print(f"📄 Configuration sauvée: {config_path}")

    def generate_single_image(self, prompt_config: PromptConfig) -> bool:
        """Génère une seule image"""
        payload = {
            "prompt": prompt_config.prompt,
            "negative_prompt": prompt_config.negative_prompt,
            "seed": prompt_config.seed if prompt_config.seed is not None else -1,
            "steps": self.generation_config.steps,
            "cfg_scale": self.generation_config.cfg_scale,
            "width": self.generation_config.width,
            "height": self.generation_config.height,
            "sampler_name": self.generation_config.sampler_name,
            "batch_size": self.generation_config.batch_size,
            "n_iter": self.generation_config.n_iter
        }

        try:
            # Mode dry-run: sauver le JSON au lieu d'appeler l'API
            if self.dry_run:
                self.create_output_dir()
                # Remplacer .png par .json pour le nom de fichier
                json_filename = prompt_config.filename.replace('.png', '.json')
                filepath = os.path.join(self.output_dir, json_filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)

                return True

            # Mode normal: appeler l'API
            response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload)
            response.raise_for_status()
            result = response.json()

            # Sauvegarde de l'image
            image_data = base64.b64decode(result['images'][0])
            filepath = os.path.join(self.output_dir, prompt_config.filename)

            with open(filepath, 'wb') as f:
                f.write(image_data)

            return True

        except Exception as e:
            print(f"❌ Erreur génération {prompt_config.filename}: {e}")
            return False

    def generate_batch(self, prompt_configs: List[PromptConfig],
                      delay_between_images: float = 2.0,
                      progress_callback: Optional[callable] = None,
                      base_prompt: str = "",
                      negative_prompt: str = "",
                      additional_info: Dict = None) -> Tuple[int, int]:
        """
        Génère un batch d'images

        Args:
            prompt_configs: Liste des configurations de prompts
            delay_between_images: Délai en secondes entre chaque génération
            progress_callback: Fonction appelée pour chaque image (index, total, filename, success)

        Returns:
            Tuple (succès, total)
        """
        self.create_output_dir()

        # Sauvegarde de la configuration avant de commencer
        if base_prompt or negative_prompt:
            info = additional_info or {}
            info["nombre_images_demandees"] = len(prompt_configs)
            self.save_session_config(base_prompt, negative_prompt, info)

        # En mode dry-run, skip le test de connexion
        if not self.dry_run:
            if not self.test_connection():
                print("❌ Impossible de se connecter à l'API WebUI")
                return 0, len(prompt_configs)

        success_count = 0
        total_images = len(prompt_configs)
        start_time = time.time()

        print(f"🚀 Début de génération de {total_images} images")
        print(f"📁 Dossier de sortie: {self.output_dir}")
        print("-" * 50)

        for i, prompt_config in enumerate(prompt_configs, 1):
            print(f"🎨 [{i}/{total_images}] Génération: {prompt_config.filename}")

            success = self.generate_single_image(prompt_config)
            if success:
                success_count += 1
                print(f"✅ Image sauvée: {prompt_config.filename}")

            # Callback de progression si fourni
            if progress_callback:
                progress_callback(i, total_images, prompt_config.filename, success)

            # Pause entre les générations
            if i < total_images:
                time.sleep(delay_between_images)

            # Estimation du temps restant
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (total_images - i) * avg_time
                print(f"⏱️  Temps restant estimé: {remaining / 60:.1f} minutes\n")

        # Résumé final
        total_time = time.time() - start_time
        print("-" * 50)
        print(f"✅ Génération terminée!")
        print(f"📊 Succès: {success_count}/{total_images} images")
        print(f"⏱️  Temps total: {total_time / 60:.1f} minutes")
        print(f"📁 Images dans: {self.output_dir}")

        return success_count, total_images


def generate_all_combinations(variations: Dict[str, Dict[str, str]],
                            placeholder_order: List[str] = None) -> List[Dict[str, str]]:
    """
    Génère toutes les combinaisons possibles de variations.

    DEPRECATED: Cette fonction peut causer des problèmes de mémoire avec de grandes combinaisons.
    Utilisez generate_combinations_lazy() à la place.

    Args:
        variations: Dict de variations {"placeholder": {"key": "value", ...}, ...}
        placeholder_order: Ordre des placeholders (optionnel). Si fourni, les boucles
                          seront imbriquées dans cet ordre (premier = extérieur, dernier = intérieur)

    Returns:
        Liste de dicts {placeholder: value} pour chaque combinaison
    """
    # Convertit le générateur lazy en liste pour compatibilité avec ancien code
    return list(generate_combinations_lazy(variations, placeholder_order))


def generate_combinations_lazy(variations: Dict[str, Dict[str, str]],
                                placeholder_order: List[str] = None):
    """
    Génère les combinaisons de variations de manière paresseuse (lazy).

    Cette version ne crée pas toutes les combinaisons en mémoire, mais les génère
    une par une à la demande. Utile pour de très grandes combinaisons.

    Args:
        variations: Dict de variations {"placeholder": {"key": "value", ...}, ...}
        placeholder_order: Ordre des placeholders (optionnel). Si fourni, les boucles
                          seront imbriquées dans cet ordre (premier = extérieur, dernier = intérieur)

    Yields:
        Dict {placeholder: value} pour chaque combinaison
    """
    # Si ordre fourni, utilise-le; sinon utilise l'ordre naturel du dict
    if placeholder_order:
        # Filtre pour ne garder que les placeholders présents dans variations
        ordered_keys = [p for p in placeholder_order if p in variations]
        # Ajoute les clés manquantes à la fin
        for key in variations:
            if key not in ordered_keys:
                ordered_keys.append(key)
    else:
        ordered_keys = list(variations.keys())

    def generate(remaining_keys, current_combination=None):
        if current_combination is None:
            current_combination = {}

        if not remaining_keys:
            # Toutes les catégories traitées, yield la combinaison
            yield current_combination.copy()
            return

        # Traiter le premier placeholder de l'ordre
        category_name = remaining_keys[0]
        category_variations = variations[category_name]
        remaining = remaining_keys[1:]

        for key, value in category_variations.items():
            current_combination[category_name] = value
            yield from generate(remaining, current_combination)
            del current_combination[category_name]

    yield from generate(ordered_keys)


def create_prompt_configs_from_combinations(base_prompt: str,
                                          negative_prompt: str,
                                          seed: Optional[int],
                                          variations: Dict[str, Dict[str, str]],
                                          filename_pattern: str = "{counter:03d}_{keys}.png") -> List[PromptConfig]:
    """
    Crée une liste de PromptConfig à partir de combinations de variations

    Args:
        base_prompt: Prompt de base
        negative_prompt: Prompt négatif
        seed: Seed fixe (optionnel)
        variations: Dict de variations {"category": {"key": "description", ...}, ...}
        filename_pattern: Pattern pour le nom de fichier (utilise {counter} et {keys})

    Returns:
        Liste de PromptConfig
    """
    prompt_configs = []
    counter = 1

    def generate_combinations(categories, current_combination=None, current_keys=None):
        nonlocal counter

        if current_combination is None:
            current_combination = []
            current_keys = []

        if not categories:
            # Toutes les catégories ont été traitées, créer le prompt
            # Filtre les descriptions vides
            non_empty_combinations = [desc for desc in current_combination if desc]
            if non_empty_combinations:
                full_prompt = f"{base_prompt}, {', '.join(non_empty_combinations)}"
            else:
                full_prompt = base_prompt

            # Filtre les clés vides pour le filename
            non_empty_keys = [key for key in current_keys if key]
            keys_str = "_".join(non_empty_keys) if non_empty_keys else "default"
            filename = filename_pattern.format(counter=counter, keys=keys_str)

            prompt_configs.append(PromptConfig(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                filename=filename
            ))
            counter += 1
            return

        # Traiter la première catégorie
        category_name, category_variations = list(categories.items())[0]
        remaining_categories = {k: v for k, v in categories.items() if k != category_name}

        for key, description in category_variations.items():
            generate_combinations(
                remaining_categories,
                current_combination + [description],
                current_keys + [key]
            )

    generate_combinations(variations)
    return prompt_configs