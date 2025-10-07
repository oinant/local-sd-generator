"""Tests pour les placeholders dans le negative prompt."""
import pytest
from pathlib import Path
import sys

# Add CLI to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from variation_loader import (
    extract_placeholders_with_limits,
    load_variations_for_placeholders
)
from image_variation_generator import ImageVariationGenerator


class TestNegativePromptPlaceholderExtraction:
    """Tests d'extraction des placeholders depuis prompt ET negative prompt."""

    def test_extract_from_negative_only(self):
        """Entrée: negative avec placeholders → Sortie: placeholders détectés."""
        prompt = "masterpiece, beautiful girl"
        negative = "low quality, {NegStyle}"

        # Simule l'extraction comme dans load_variations_for_placeholders
        prompt_placeholders = extract_placeholders_with_limits(prompt)
        negative_placeholders = extract_placeholders_with_limits(negative)

        # Fusionne
        all_placeholders = dict(prompt_placeholders)
        for placeholder, options in negative_placeholders.items():
            if placeholder not in all_placeholders:
                all_placeholders[placeholder] = options

        assert "NegStyle" in all_placeholders
        assert all_placeholders["NegStyle"]["type"] == "none"

    def test_extract_from_both_prompt_and_negative(self):
        """Entrée: placeholders dans prompt ET negative → Sortie: tous détectés."""
        prompt = "masterpiece, {Subject}, {Style}"
        negative = "low quality, {NegStyle}"

        prompt_placeholders = extract_placeholders_with_limits(prompt)
        negative_placeholders = extract_placeholders_with_limits(negative)

        all_placeholders = dict(prompt_placeholders)
        for placeholder, options in negative_placeholders.items():
            if placeholder not in all_placeholders:
                all_placeholders[placeholder] = options

        assert "Subject" in all_placeholders
        assert "Style" in all_placeholders
        assert "NegStyle" in all_placeholders
        assert len(all_placeholders) == 3

    def test_shared_placeholder_in_both(self):
        """Entrée: même placeholder dans prompt et negative → Sortie: chargé une seule fois."""
        prompt = "masterpiece, {Style}"
        negative = "low quality, {Style}"

        prompt_placeholders = extract_placeholders_with_limits(prompt)
        negative_placeholders = extract_placeholders_with_limits(negative)

        all_placeholders = dict(prompt_placeholders)
        for placeholder, options in negative_placeholders.items():
            if placeholder not in all_placeholders:
                all_placeholders[placeholder] = options

        # Style doit être présent une seule fois
        assert "Style" in all_placeholders
        assert len(all_placeholders) == 1

    def test_negative_with_selectors(self):
        """Entrée: negative avec sélecteurs (#|, :N) → Sortie: options détectées."""
        negative = "{NegStyle:#|1|3}, {Quality:2}"

        placeholders = extract_placeholders_with_limits(negative)

        assert placeholders["NegStyle"]["type"] == "indices"
        assert placeholders["NegStyle"]["value"] == [1, 3]
        assert placeholders["Quality"]["type"] == "limit"
        assert placeholders["Quality"]["value"] == 2


class TestNegativePromptVariationLoading:
    """Tests de chargement de variations pour negative prompt."""

    @pytest.fixture
    def temp_variation_files(self, tmp_path):
        """Fixture: crée des fichiers temporaires de variations."""
        style_file = tmp_path / "styles.txt"
        style_file.write_text("anime\nrealistic\npainting\n")

        negstyle_file = tmp_path / "negstyles.txt"
        negstyle_file.write_text(
            "sdxl→low quality, bad anatomy, blurry\n"
            "illustrious→worst quality, low quality, displeasing\n"
            "pony→3d, worst quality, bad anatomy\n"
        )

        return {
            "Style": str(style_file),
            "NegStyle": str(negstyle_file)
        }

    def test_load_variations_from_negative(self, temp_variation_files):
        """Entrée: negative avec placeholder → Sortie: variations chargées."""
        prompt = "masterpiece, {Style}"
        negative = "{NegStyle}"

        result = load_variations_for_placeholders(
            prompt,
            temp_variation_files,
            verbose=False,
            negative_prompt=negative
        )

        assert "Style" in result
        assert "NegStyle" in result
        assert len(result["Style"]) == 3
        assert len(result["NegStyle"]) == 3

    def test_load_variations_negative_only(self, temp_variation_files):
        """Entrée: seul negative a placeholders → Sortie: variations chargées."""
        prompt = "masterpiece, beautiful"
        negative = "{NegStyle}"

        result = load_variations_for_placeholders(
            prompt,
            temp_variation_files,
            verbose=False,
            negative_prompt=negative
        )

        assert "NegStyle" in result
        assert len(result["NegStyle"]) == 3

    def test_shared_placeholder_loads_once(self, temp_variation_files):
        """Entrée: même placeholder dans les deux → Sortie: chargé une fois."""
        prompt = "masterpiece, {Style}"
        negative = "bad {Style}"

        result = load_variations_for_placeholders(
            prompt,
            temp_variation_files,
            verbose=False,
            negative_prompt=negative
        )

        # Style doit être chargé une seule fois
        assert "Style" in result
        assert len(result["Style"]) == 3

    def test_negative_with_limit(self, temp_variation_files):
        """Entrée: negative avec :N → Sortie: N variations."""
        prompt = "masterpiece"
        negative = "{NegStyle:2}"

        result = load_variations_for_placeholders(
            prompt,
            temp_variation_files,
            verbose=False,
            negative_prompt=negative
        )

        assert "NegStyle" in result
        assert len(result["NegStyle"]) == 2

    def test_negative_with_indices(self, temp_variation_files):
        """Entrée: negative avec #|indices → Sortie: variations sélectionnées."""
        prompt = "masterpiece"
        negative = "{NegStyle:#|0|2}"

        result = load_variations_for_placeholders(
            prompt,
            temp_variation_files,
            verbose=False,
            negative_prompt=negative
        )

        assert "NegStyle" in result
        assert len(result["NegStyle"]) == 2


class TestNegativePromptApplication:
    """Tests d'application des variations au negative prompt."""

    def test_apply_variations_to_negative(self):
        """Entrée: variations → Sortie: negative prompt avec valeurs remplacées."""
        generator = ImageVariationGenerator(
            prompt_template="masterpiece, {Subject}",
            negative_prompt="low quality, {NegStyle}",
            variation_files={}
        )

        variations = {
            "Subject": "beautiful girl",
            "NegStyle": "blurry, watermark"
        }

        prompt, negative, keys = generator._apply_variations_to_prompt(
            "masterpiece, {Subject}",
            variations,
            "low quality, {NegStyle}"
        )

        assert prompt == "masterpiece, beautiful girl"
        assert negative == "low quality, blurry, watermark"
        assert len(keys) == 2

    def test_apply_shared_placeholder(self):
        """Entrée: placeholder partagé → Sortie: même valeur dans les deux."""
        generator = ImageVariationGenerator(
            prompt_template="{Style} artwork",
            negative_prompt="bad {Style}",
            variation_files={}
        )

        variations = {"Style": "anime"}

        prompt, negative, keys = generator._apply_variations_to_prompt(
            "{Style} artwork",
            variations,
            "bad {Style}"
        )

        assert prompt == "anime artwork"
        assert negative == "bad anime"

    def test_apply_empty_negative(self):
        """Entrée: negative vide → Sortie: negative reste vide."""
        generator = ImageVariationGenerator(
            prompt_template="{Subject}",
            negative_prompt="",
            variation_files={}
        )

        variations = {"Subject": "girl"}

        prompt, negative, keys = generator._apply_variations_to_prompt(
            "{Subject}",
            variations,
            ""
        )

        assert prompt == "girl"
        assert negative == ""

    def test_clean_negative_prompt(self):
        """Entrée: negative avec placeholders vides → Sortie: nettoyé."""
        generator = ImageVariationGenerator(
            prompt_template="masterpiece",
            negative_prompt="low quality, {Extra}, blurry",
            variation_files={}
        )

        # Placeholder non fourni dans variations
        variations = {}

        prompt, negative, keys = generator._apply_variations_to_prompt(
            "masterpiece",
            variations,
            "low quality, {Extra}, blurry"
        )

        # Le placeholder non remplacé devrait être nettoyé
        assert "{Extra}" not in negative
        assert "low quality" in negative
        assert "blurry" in negative


class TestNegativePromptIntegration:
    """Tests d'intégration end-to-end avec negative prompt."""

    @pytest.fixture
    def temp_files(self, tmp_path):
        """Crée des fichiers de test temporaires."""
        negstyle_file = tmp_path / "negstyles.txt"
        negstyle_file.write_text("sdxl→low quality, bad\nillustrious→worst quality\n")

        return {
            "NegStyle": str(negstyle_file)
        }

    def test_generator_with_negative_variations(self, temp_files):
        """Test complet: créer générateur avec variations dans negative."""
        generator = ImageVariationGenerator(
            prompt_template="masterpiece, beautiful girl",
            negative_prompt="{NegStyle}",
            variation_files=temp_files,
            generation_mode="combinatorial",
            seed_mode="fixed",
            max_images=2
        )

        # Teste la création de variations
        from variation_loader import load_variations_for_placeholders
        variations = load_variations_for_placeholders(
            generator.prompt_template,
            generator.variation_files,
            verbose=False,
            negative_prompt=generator.negative_prompt
        )

        assert "NegStyle" in variations
        assert len(variations["NegStyle"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
