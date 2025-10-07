"""
Générateur d'images avec variations configurable et réutilisable.

Ce module fournit une classe générique pour créer facilement des générateurs
d'images Stable Diffusion avec système de placeholders.

Exemple d'utilisation:
    generator = ImageVariationGenerator(
        prompt_template="masterpiece, {Expression}, {Pose}, detailed",
        negative_prompt="low quality, blurry",
        variation_files={
            "Expression": "path/to/expressions.txt",
            "Pose": "path/to/poses.txt"
        }
    )
    generator.run()
"""

from sdapi_client import StableDiffusionAPIClient, GenerationConfig, generate_all_combinations, PromptConfig
from variation_loader import load_variations_for_placeholders, create_random_combinations, extract_placeholders_with_limits, sort_placeholders_by_priority
from output.output_namer import generate_image_filename, format_timestamp_iso
from output.metadata_generator import generate_metadata_dict, save_metadata_json, create_legacy_config_text
import re
from datetime import datetime
from typing import Dict, Optional, List


class ImageVariationGenerator:
    """
    Générateur d'images avec variations configurable.

    Permet de créer facilement des générateurs personnalisés en spécifiant
    seulement le prompt template, negative prompt et fichiers de variations.
    """

    def __init__(self,
                 prompt_template: str,
                 negative_prompt: str = "",
                 variation_files: Dict[str, str] = None,
                 api_url: str = "http://127.0.0.1:7860",
                 base_output_dir: str = "apioutput",
                 seed: int = 42,
                 max_images: int = 50,
                 generation_mode: str = "ask",  # "combinatorial", "random", "ask"
                 seed_mode: str = "ask",  # "fixed", "progressive", "random", "ask"
                 session_name: str = "variations",
                 filename_keys: Optional[List[str]] = None,
                 dry_run: bool = False):
        """
        Initialise le générateur.

        Args:
            prompt_template: Template du prompt avec placeholders {PlaceholderName}
            negative_prompt: Prompt négatif
            variation_files: Dict {placeholder: chemin_fichier}
            api_url: URL de l'API Stable Diffusion
            base_output_dir: Dossier de base pour les sorties (défaut: "apioutput")
            seed: Seed de base
            max_images: Nombre maximum d'images par défaut
            generation_mode: Mode de génération ("combinatorial", "random", "ask")
            seed_mode: Mode de seed ("fixed", "progressive", "random", "ask")
            session_name: Nom de la session pour les fichiers de sortie
            filename_keys: Liste des keys à inclure dans les noms de fichiers (optionnel)
        """
        self.prompt_template = prompt_template
        self.negative_prompt = negative_prompt
        self.variation_files = variation_files or {}
        self.api_url = api_url
        self.base_output_dir = base_output_dir
        self.seed = seed
        self.max_images = max_images
        self.generation_mode = generation_mode
        self.seed_mode = seed_mode
        self.session_name = session_name
        self.filename_keys = filename_keys or []
        self.dry_run = dry_run

        # Configuration de génération par défaut
        self.generation_config = GenerationConfig(
            steps=30,
            cfg_scale=7,
            width=512,
            height=768,
            sampler_name="DPM++ 2M Karras",
            batch_size=1,
            n_iter=1
        )

        # Tracking pour metadata
        self.start_time = None
        self.end_time = None
        self.variations_loaded = None

    def set_generation_config(self, config: GenerationConfig):
        """Configure les paramètres de génération."""
        self.generation_config = config

    def run(self) -> tuple[int, int]:
        """
        Lance la génération d'images.

        Returns:
            Tuple (success_count, total_count)
        """
        self.start_time = datetime.now()

        print("🚀 Début de la génération avec variations")
        print(f"🎯 Limite d'images: {self.max_images}")
        print(f"🌱 Seed: {self.seed}")

        if self.variation_files:
            print(f"📁 Fichiers configurés: {list(self.variation_files.keys())}")
            print("\n📋 Configuration des fichiers:")
            for placeholder, filepath in self.variation_files.items():
                print(f"  {placeholder} → {filepath}")

        # Génère les configurations de prompts
        prompt_configs = self._create_variations()

        if not prompt_configs:
            print("❌ Aucune configuration générée!")
            return 0, 0

        print(f"📋 {len(prompt_configs)} variations préparées")

        # Initialise le client API
        client = StableDiffusionAPIClient(
            api_url=self.api_url,
            base_output_dir=self.base_output_dir,
            session_name=self.session_name,
            dry_run=self.dry_run
        )
        client.set_generation_config(self.generation_config)

        # Prépare les informations additionnelles
        all_variations = load_variations_for_placeholders(
            self.prompt_template,
            self.variation_files,
            verbose=False,
            negative_prompt=self.negative_prompt
        )
        self.variations_loaded = all_variations  # Store for metadata

        total_variations = 1
        variation_counts = {}
        for placeholder, variations in all_variations.items():
            variation_counts[placeholder] = len(variations)
            total_variations *= len(variations)

        additional_info = {
            "seed_principal": self.seed,
            "limite_max_images": self.max_images,
            "images_generees": len(prompt_configs),
            "fichiers_variations": self.variation_files,
            "nombre_par_type": variation_counts,
            "combinaisons_totales_possibles": total_variations,
            "prompt_template": self.prompt_template,
            "negative_prompt": self.negative_prompt
        }

        # Lance la génération
        success_count, total_count = client.generate_batch(
            prompt_configs=prompt_configs,
            delay_between_images=2.0,
            base_prompt=self.prompt_template,
            negative_prompt=self.negative_prompt,
            additional_info=additional_info
        )

        self.end_time = datetime.now()

        # Génère le metadata.json (SF-5)
        self._save_metadata(client.output_dir, total_variations, len(prompt_configs))

        return success_count, total_count

    def _create_variations(self) -> List[PromptConfig]:
        """Crée les variations selon le mode choisi."""
        if not self.variation_files:
            print("⚠️  Aucun fichier de variation configuré - génération d'une seule image")
            return [PromptConfig(
                prompt=self.prompt_template,
                negative_prompt=self.negative_prompt,
                seed=self.seed,
                filename=f"{self.session_name}_001.png"
            )]

        # Charge les variations nécessaires (pour prompt ET negative prompt)
        variations_dict = load_variations_for_placeholders(
            self.prompt_template,
            self.variation_files,
            negative_prompt=self.negative_prompt
        )

        if not variations_dict:
            print("❌ Aucune variation chargée depuis les fichiers!")
            return []

        # Calcule le nombre total de combinaisons
        total_combinations = 1
        for placeholder, variations in variations_dict.items():
            total_combinations *= len(variations)

        print(f"📊 Combinaisons possibles: {total_combinations}")
        print(f"⚙️  Limite par défaut: {self.max_images}")
        print(f"🎲 Mode de génération: {self.generation_mode}")
        print(f"🌱 Mode de seed: {self.seed_mode}")

        # Détermine les modes à utiliser
        mode = self._choose_generation_mode()
        seed_mode = self._choose_seed_mode()

        # Détermine le nombre d'images
        if mode == "random":
            max_images = total_combinations
            default_images = min(self.max_images, total_combinations)
        else:
            max_images = total_combinations
            default_images = min(self.max_images, total_combinations)

        # Si les modes sont déjà configurés (pas "ask"), utilise max_images directement
        # Sinon demande interactivement
        if self.generation_mode != "ask" and self.seed_mode != "ask":
            actual_images = default_images
        else:
            actual_images = self._ask_number_of_images(max_images, default_images, mode)

        print(f"✅ {actual_images} images seront générées")
        print(f"🎲 Mode génération: {mode}")
        print(f"🌱 Mode seed: {seed_mode}")

        # Nettoie le prompt template (enlève les options pour garder juste {Placeholder})
        clean_prompt = re.sub(r'\{([^}:]+):[^}]+\}', r'{\1}', self.prompt_template)

        if mode == "random":
            return self._create_random_variations(variations_dict, clean_prompt, actual_images, seed_mode)
        else:
            return self._create_combinatorial_variations(variations_dict, clean_prompt, actual_images, seed_mode)

    def _create_random_variations(self, variations_dict: Dict[str, Dict[str, str]],
                                clean_prompt: str, actual_images: int, seed_mode: str) -> List[PromptConfig]:
        """Crée des variations aléatoires."""
        random_combinations = create_random_combinations(variations_dict, actual_images, self.seed)

        # Nettoie aussi le negative prompt template
        clean_negative = re.sub(r'\{([^}:]+):[^}]+\}', r'{\1}', self.negative_prompt)

        prompt_configs = []
        for i, combination in enumerate(random_combinations):
            # Applique les variations au prompt ET negative
            prompt, negative, keys = self._apply_variations_to_prompt(
                clean_prompt, combination, clean_negative
            )

            # Calcule la seed
            image_seed = self._calculate_seed(seed_mode, self.seed, i)

            config = PromptConfig(
                prompt=prompt,
                negative_prompt=negative,
                seed=image_seed,
                filename=f"random_{i+1:03d}_{'_'.join(keys[:2]) if keys else 'default'}.png"
            )
            prompt_configs.append(config)

        return prompt_configs

    def _create_combinatorial_variations(self, variations_dict: Dict[str, Dict[str, str]],
                                       clean_prompt: str, actual_images: int, seed_mode: str) -> List[PromptConfig]:
        """Crée des variations combinatoires."""
        # Extrait les priorités depuis le prompt template
        placeholders_with_options = extract_placeholders_with_limits(self.prompt_template)

        # Trie les placeholders par priorité pour déterminer l'ordre des boucles
        placeholder_order = sort_placeholders_by_priority(placeholders_with_options)

        # Filtre pour ne garder que ceux présents dans variations_dict
        placeholder_order = [p for p in placeholder_order if p in variations_dict]

        # Affiche l'ordre des boucles si des poids sont définis
        priorities_defined = any(
            placeholders_with_options.get(p, {}).get("priority", 0) != 0
            for p in placeholder_order
        )

        if priorities_defined:
            print("\n🔄 Ordre des boucles (extérieur → intérieur):")
            for p in placeholder_order:
                priority = placeholders_with_options.get(p, {}).get("priority", 0)
                print(f"  {p} (poids: {priority})")

        # Génère les combinaisons de manière paresseuse (lazy) pour éviter les problèmes de mémoire
        # Utilise itertools.islice pour ne prendre que les N premières combinaisons nécessaires
        from itertools import islice
        from sdapi_client import generate_combinations_lazy

        # Nettoie aussi le negative prompt template
        clean_negative = re.sub(r'\{([^}:]+):[^}]+\}', r'{\1}', self.negative_prompt)

        combinations_generator = generate_combinations_lazy(variations_dict, placeholder_order)

        prompt_configs = []
        for i, combination in enumerate(islice(combinations_generator, actual_images)):
            # Applique les variations au prompt ET negative
            prompt, negative, keys = self._apply_variations_to_prompt(
                clean_prompt, combination, clean_negative
            )

            # Calcule la seed
            image_seed = self._calculate_seed(seed_mode, self.seed, i)

            # Crée le nom de fichier
            keys_str = "_".join(keys[:2]) if keys else "default"
            filename = f"{self.session_name}_{i+1:03d}_{keys_str}.png"

            config = PromptConfig(
                prompt=prompt,
                negative_prompt=negative,
                seed=image_seed,
                filename=filename
            )
            prompt_configs.append(config)

        return prompt_configs

    def _choose_generation_mode(self) -> str:
        """Choisit le mode de génération."""
        if self.generation_mode in ["combinatorial", "random"]:
            return self.generation_mode

        while True:
            print("\n🎲 Modes de génération disponibles:")
            print("1. combinatorial - Génère toutes les combinaisons possibles")
            print("2. random - Génère des combinaisons aléatoires uniques")

            choice = input("\nChoisissez le mode (1/2 ou 'c'/'r') : ").strip().lower()

            if choice in ['1', 'c', 'combinatorial']:
                return "combinatorial"
            elif choice in ['2', 'r', 'random']:
                return "random"
            else:
                print("❌ Choix invalide")

    def _choose_seed_mode(self) -> str:
        """Choisit le mode de seed."""
        if self.seed_mode in ["fixed", "progressive", "random"]:
            return self.seed_mode

        while True:
            print("\n🌱 Modes de seed disponibles:")
            print("1. fixed - Même seed pour toutes les images")
            print("2. progressive - Seeds incrémentées (SEED, SEED+1, SEED+2...)")
            print("3. random - Seed aléatoire (-1) pour chaque image")

            choice = input("\nChoisissez le mode de seed (1/2/3 ou 'f'/'p'/'r') : ").strip().lower()

            if choice in ['1', 'f', 'fixed']:
                return "fixed"
            elif choice in ['2', 'p', 'progressive']:
                return "progressive"
            elif choice in ['3', 'r', 'random']:
                return "random"
            else:
                print("❌ Choix invalide")

    def _calculate_seed(self, seed_mode: str, base_seed: int, index: int) -> int:
        """Calcule la seed selon le mode."""
        if seed_mode == "fixed":
            return base_seed
        elif seed_mode == "progressive":
            return base_seed + index
        elif seed_mode == "random":
            return -1
        else:
            return base_seed

    def _ask_number_of_images(self, max_images: int, default_images: int, mode: str) -> int:
        """Demande le nombre d'images à générer."""
        if mode == "random":
            prompt_text = f"\n🎯 Combien d'images aléatoires voulez-vous générer ? (défaut: {default_images}) : "
        else:
            prompt_text = f"\n🎯 Combien d'images voulez-vous générer ? (max: {max_images}, défaut: {default_images}) : "

        while True:
            try:
                user_input = input(prompt_text).strip()

                if not user_input:
                    return default_images

                requested_images = int(user_input)

                if requested_images <= 0:
                    print("❌ Le nombre doit être positif")
                    continue
                elif mode != "random" and requested_images > max_images:
                    print(f"⚠️  Impossible de générer plus de {max_images} images (nombre de combinaisons)")
                    continue
                else:
                    return requested_images

            except ValueError:
                print("❌ Veuillez entrer un nombre valide")
                continue

    def _clean_filename(self, text: str) -> str:
        """Nettoie le texte pour les noms de fichiers."""
        return text.replace(' ', '_').replace(',', '_').replace('/', '_').replace('\\', '_')

    def _clean_prompt_with_empty_placeholders(self, prompt: str) -> str:
        """
        Nettoie un prompt en supprimant les placeholders vides et virgules en trop.

        Args:
            prompt: Le prompt à nettoyer

        Returns:
            Prompt nettoyé
        """
        # Supprime les placeholders qui restent (pas remplacés)
        prompt = re.sub(r'\{[^}]+\}', '', prompt)

        # Nettoie les virgules et espaces multiples
        prompt = re.sub(r',\s*,+', ',', prompt)  # Virgules doubles ou plus
        prompt = re.sub(r'\s*,\s*', ', ', prompt)  # Espaces autour des virgules
        prompt = re.sub(r'\s+', ' ', prompt)  # Espaces multiples

        # Supprime virgules en début/fin
        prompt = prompt.strip(', ')

        return prompt

    def _apply_variations_to_prompt(self, prompt_template: str, variations: Dict[str, str],
                                   negative_template: str = "") -> tuple[str, str, List[str]]:
        """
        Applique des variations à un prompt template et negative prompt en remplaçant les placeholders.

        Args:
            prompt_template: Template avec placeholders {Name}
            variations: Dict {placeholder_name: value}
            negative_template: Negative prompt template avec placeholders {Name} (optionnel)

        Returns:
            Tuple (prompt_final, negative_final, keys_for_filename)
        """
        prompt = prompt_template
        negative = negative_template
        keys = []

        for placeholder, value in variations.items():
            if value:  # Ne remplace que si valeur non vide
                prompt = prompt.replace(f"{{{placeholder}}}", value)
                negative = negative.replace(f"{{{placeholder}}}", value)
                keys.append(f"{placeholder}_{self._clean_filename(value)}")

        # Nettoie le prompt et negative finaux
        prompt = self._clean_prompt_with_empty_placeholders(prompt)
        negative = self._clean_prompt_with_empty_placeholders(negative)

        return prompt, negative, keys

    def _save_metadata(self, output_dir: str, total_combinations: int, images_generated: int):
        """
        Sauvegarde les métadonnées de la session en JSON (SF-5).

        Args:
            output_dir: Dossier de sortie de la session
            total_combinations: Nombre total de combinaisons possibles
            images_generated: Nombre d'images générées
        """
        if not self.start_time or not self.variations_loaded:
            print("⚠️  Impossible de générer les métadonnées (données manquantes)")
            return

        generation_time = (self.end_time - self.start_time).total_seconds()

        # Détermine les modes utilisés
        actual_mode = self.generation_mode if self.generation_mode in ["combinatorial", "random"] else "combinatorial"
        actual_seed_mode = self.seed_mode if self.seed_mode in ["fixed", "progressive", "random"] else "progressive"

        metadata = generate_metadata_dict(
            prompt_template=self.prompt_template,
            negative_prompt=self.negative_prompt,
            variations_loaded=self.variations_loaded,
            generation_info={
                "date": format_timestamp_iso(self.start_time),
                "timestamp": self.start_time.strftime("%Y%m%d_%H%M%S"),
                "session_name": self.session_name,
                "total_images": images_generated,
                "generation_time_seconds": round(generation_time, 2),
                "generation_mode": actual_mode,
                "seed_mode": actual_seed_mode,
                "seed": self.seed,
                "total_combinations": total_combinations
            },
            parameters={
                "width": self.generation_config.width,
                "height": self.generation_config.height,
                "steps": self.generation_config.steps,
                "cfg_scale": self.generation_config.cfg_scale,
                "sampler": self.generation_config.sampler_name,
                "batch_size": self.generation_config.batch_size,
                "batch_count": self.generation_config.n_iter
            },
            output_info={
                "folder": output_dir,
                "filename_keys": self.filename_keys
            }
        )

        # Sauvegarde le metadata.json
        try:
            metadata_path = save_metadata_json(metadata, output_dir)
            print(f"✅ Métadonnées sauvegardées: {metadata_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des métadonnées: {e}")

        # Garde aussi le .txt pour backward compatibility
        try:
            legacy_text = create_legacy_config_text(metadata)
            legacy_path = f"{output_dir}/session_config_legacy.txt"
            with open(legacy_path, 'w', encoding='utf-8') as f:
                f.write(legacy_text)
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde du fichier legacy: {e}")


# Fonction utilitaire pour créer rapidement un générateur
def create_generator(prompt_template: str,
                    negative_prompt: str = "",
                    variation_files: Dict[str, str] = None,
                    **kwargs) -> ImageVariationGenerator:
    """
    Fonction utilitaire pour créer rapidement un générateur.

    Args:
        prompt_template: Template du prompt avec placeholders
        negative_prompt: Prompt négatif
        variation_files: Dict {placeholder: chemin_fichier}
        **kwargs: Arguments supplémentaires pour ImageVariationGenerator

    Returns:
        Instance d'ImageVariationGenerator configurée
    """
    return ImageVariationGenerator(
        prompt_template=prompt_template,
        negative_prompt=negative_prompt,
        variation_files=variation_files,
        **kwargs
    )