"""Tests fonctionnels pour le remplacement de placeholders dans les prompts."""
import pytest
from sdapi_client import generate_all_combinations
from variation_loader import create_random_combinations
from image_variation_generator import ImageVariationGenerator


class TestCombinatorialGeneration:
    """Tests du mode combinatorial : toutes les combinaisons possibles."""

    @pytest.fixture
    def simple_variations(self):
        """Fixture: variations simples pour tests."""
        return {
            "Expression": {
                "happy": "smiling",
                "sad": "crying"
            },
            "Angle": {
                "front": "front view",
                "side": "side view"
            }
        }

    def test_generate_all_combinations_count(self, simple_variations):
        """Entrée: 2 expressions × 2 angles → Sortie: 4 combinaisons."""
        result = generate_all_combinations(simple_variations)
        assert len(result) == 4

    def test_generate_all_combinations_content(self, simple_variations):
        """Entrée: variations → Sortie: toutes combinaisons uniques."""
        result = generate_all_combinations(simple_variations)

        expected_combinations = [
            {"Expression": "smiling", "Angle": "front view"},
            {"Expression": "smiling", "Angle": "side view"},
            {"Expression": "crying", "Angle": "front view"},
            {"Expression": "crying", "Angle": "side view"},
        ]

        assert len(result) == len(expected_combinations)
        for combo in expected_combinations:
            assert combo in result

    def test_single_placeholder(self):
        """Entrée: 1 placeholder avec 3 valeurs → Sortie: 3 combinaisons."""
        variations = {
            "Style": {
                "a": "anime",
                "b": "realistic",
                "c": "cartoon"
            }
        }

        result = generate_all_combinations(variations)
        assert len(result) == 3

        expected = [
            {"Style": "anime"},
            {"Style": "realistic"},
            {"Style": "cartoon"}
        ]
        for combo in expected:
            assert combo in result

    def test_three_placeholders(self):
        """Entrée: 2×2×2 variations → Sortie: 8 combinaisons."""
        variations = {
            "A": {"a1": "val_a1", "a2": "val_a2"},
            "B": {"b1": "val_b1", "b2": "val_b2"},
            "C": {"c1": "val_c1", "c2": "val_c2"}
        }

        result = generate_all_combinations(variations)
        assert len(result) == 8


class TestRandomGeneration:
    """Tests du mode random : combinaisons aléatoires uniques."""

    @pytest.fixture
    def simple_variations(self):
        """Fixture: variations simples pour tests."""
        return {
            "Expression": {
                "happy": "smiling",
                "sad": "crying",
                "neutral": "neutral face"
            },
            "Angle": {
                "front": "front view",
                "side": "side view"
            }
        }

    def test_random_combinations_count(self, simple_variations):
        """Entrée: demande 3 combinaisons → Sortie: 3 combinaisons."""
        result = create_random_combinations(simple_variations, 3, seed=42)
        assert len(result) == 3

    def test_random_combinations_unique(self, simple_variations):
        """Entrée: N combinaisons → Sortie: N combinaisons uniques."""
        result = create_random_combinations(simple_variations, 5, seed=42)

        # Convertit en tuples pour vérifier l'unicité
        combinations_as_tuples = [tuple(sorted(combo.items())) for combo in result]
        assert len(combinations_as_tuples) == len(set(combinations_as_tuples))

    def test_random_combinations_different_seeds(self, simple_variations):
        """Entrée: seeds différentes → Sortie: combinaisons différentes."""
        result1 = create_random_combinations(simple_variations, 3, seed=123)
        result2 = create_random_combinations(simple_variations, 3, seed=456)

        assert result1 != result2

    def test_random_max_combinations(self, simple_variations):
        """Entrée: demande plus que possible → Sortie: maximum disponible."""
        # 3 expressions × 2 angles = 6 combinaisons max
        result = create_random_combinations(simple_variations, 100, seed=42)
        assert len(result) <= 6


class TestPromptReplacement:
    """Tests du remplacement effectif dans les prompts."""

    def test_simple_replacement(self):
        """Entrée: template + variations → Sortie: prompt avec valeurs."""
        gen = ImageVariationGenerator(
            prompt_template="portrait, {Expression}, {Angle}, beautiful",
            negative_prompt="low quality"
        )

        variations = {"Expression": "smiling", "Angle": "front view"}
        result, _ = gen._apply_variations_to_prompt(gen.prompt_template, variations)

        assert result == "portrait, smiling, front view, beautiful"

    def test_replacement_with_empty_value(self):
        """Entrée: valeur vide → Sortie: placeholder supprimé proprement."""
        gen = ImageVariationGenerator(
            prompt_template="portrait, {Expression}, {Background}, beautiful",
            negative_prompt="low quality"
        )

        variations = {"Expression": "smiling", "Background": ""}
        result, _ = gen._apply_variations_to_prompt(gen.prompt_template, variations)

        assert result == "portrait, smiling, beautiful"
        assert "{Background}" not in result

    def test_all_placeholders_removed(self):
        """Entrée: template avec seulement placeholders vides → Sortie: chaîne vide ou propre."""
        gen = ImageVariationGenerator(
            prompt_template="{A}, {B}, {C}",
            negative_prompt="low quality"
        )

        variations = {"A": "", "B": "", "C": ""}
        result, _ = gen._apply_variations_to_prompt(gen.prompt_template, variations)

        # Le résultat doit être propre (pas de virgules pendantes)
        assert result.strip() == ""

    def test_multiple_replacements_same_prompt(self):
        """Entrée: plusieurs variations → Sortie: prompts différents."""
        gen = ImageVariationGenerator(
            prompt_template="portrait, {Expression}, beautiful",
            negative_prompt="low quality"
        )

        variations1 = {"Expression": "smiling"}
        variations2 = {"Expression": "serious"}

        result1, _ = gen._apply_variations_to_prompt(gen.prompt_template, variations1)
        result2, _ = gen._apply_variations_to_prompt(gen.prompt_template, variations2)

        assert "smiling" in result1
        assert "serious" in result2
        assert result1 != result2
