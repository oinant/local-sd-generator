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

from sdapi_client import StableDiffusionAPIClient, GenerationConfig, create_prompt_configs_from_combinations, PromptConfig
from variation_loader import load_variations_for_placeholders, create_random_combinations
import re
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
                 seed: int = 42,
                 max_images: int = 50,
                 generation_mode: str = "ask",  # "combinatorial", "random", "ask"
                 seed_mode: str = "ask",  # "fixed", "progressive", "random", "ask"
                 session_name: str = "variations"):
        """
        Initialise le générateur.

        Args:
            prompt_template: Template du prompt avec placeholders {PlaceholderName}
            negative_prompt: Prompt négatif
            variation_files: Dict {placeholder: chemin_fichier}
            api_url: URL de l'API Stable Diffusion
            seed: Seed de base
            max_images: Nombre maximum d'images par défaut
            generation_mode: Mode de génération ("combinatorial", "random", "ask")
            seed_mode: Mode de seed ("fixed", "progressive", "random", "ask")
            session_name: Nom de la session pour les fichiers de sortie
        """
        self.prompt_template = prompt_template
        self.negative_prompt = negative_prompt
        self.variation_files = variation_files or {}
        self.api_url = api_url
        self.seed = seed
        self.max_images = max_images
        self.generation_mode = generation_mode
        self.seed_mode = seed_mode
        self.session_name = session_name

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

    def set_generation_config(self, config: GenerationConfig):
        """Configure les paramètres de génération."""
        self.generation_config = config

    def run(self) -> tuple[int, int]:
        """
        Lance la génération d'images.

        Returns:
            Tuple (success_count, total_count)
        """
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
            base_output_dir="apioutput",
            session_name=self.session_name
        )
        client.set_generation_config(self.generation_config)

        # Prépare les informations additionnelles
        all_variations = load_variations_for_placeholders(self.prompt_template, self.variation_files, verbose=False)
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

        # Charge les variations nécessaires
        variations_dict = load_variations_for_placeholders(self.prompt_template, self.variation_files)

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

        actual_images = self._ask_number_of_images(max_images, default_images, mode)

        print(f"✅ {actual_images} images seront générées")
        print(f"🎲 Mode génération: {mode}")
        print(f"🌱 Mode seed: {seed_mode}")

        # Nettoie le prompt template
        clean_prompt = re.sub(r'\{([^}:]+):\d+\}', r'{\1}', self.prompt_template)

        if mode == "random":
            return self._create_random_variations(variations_dict, clean_prompt, actual_images, seed_mode)
        else:
            return self._create_combinatorial_variations(variations_dict, clean_prompt, actual_images, seed_mode)

    def _create_random_variations(self, variations_dict: Dict[str, Dict[str, str]],
                                clean_prompt: str, actual_images: int, seed_mode: str) -> List[PromptConfig]:
        """Crée des variations aléatoires."""
        random_combinations = create_random_combinations(variations_dict, actual_images, self.seed)

        prompt_configs = []
        for i, combination in enumerate(random_combinations):
            # Remplace les placeholders
            prompt = clean_prompt
            keys = []
            for placeholder, value in combination.items():
                prompt = prompt.replace(f"{{{placeholder}}}", value)
                keys.append(f"{placeholder}_{self._clean_filename(value)}")

            # Calcule la seed
            image_seed = self._calculate_seed(seed_mode, self.seed, i)

            config = PromptConfig(
                prompt=prompt,
                negative_prompt=self.negative_prompt,
                seed=image_seed,
                filename=f"random_{i+1:03d}_{'_'.join(keys[:2])}.png"
            )
            prompt_configs.append(config)

        return prompt_configs

    def _create_combinatorial_variations(self, variations_dict: Dict[str, Dict[str, str]],
                                       clean_prompt: str, actual_images: int, seed_mode: str) -> List[PromptConfig]:
        """Crée des variations combinatoires."""
        prompt_configs = create_prompt_configs_from_combinations(
            base_prompt=clean_prompt,
            negative_prompt=self.negative_prompt,
            seed=self.seed,
            variations=variations_dict,
            filename_pattern=f"{self.session_name}_{{counter:03d}}_{{keys}}.png"
        )

        # Applique le mode de seed
        for i, config in enumerate(prompt_configs[:actual_images]):
            config.seed = self._calculate_seed(seed_mode, self.seed, i)

        return prompt_configs[:actual_images]

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