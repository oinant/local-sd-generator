"""Tests fonctionnels pour les options de placeholder."""
import pytest
from variation_loader import (
    extract_placeholders_with_limits,
    select_variations_by_indices,
    load_variations_for_placeholders
)
from pathlib import Path
import tempfile


class TestPlaceholderExtraction:
    """Tests d'extraction des placeholders avec options."""

    @pytest.mark.parametrize("prompt,expected", [
        (
            "portrait, {Hair}, {Expression}",
            {"Hair": {"type": "none", "value": None}, "Expression": {"type": "none", "value": None}}
        ),
        (
            "portrait, {Hair:5}, {Expression:3}",
            {"Hair": {"type": "limit", "value": 5}, "Expression": {"type": "limit", "value": 3}}
        ),
        (
            "portrait, {Hair:0}, {Expression}",
            {"Hair": {"type": "zero", "value": 0}, "Expression": {"type": "none", "value": None}}
        ),
        (
            "portrait, {Hair:#|1|5|22}",
            {"Hair": {"type": "indices", "value": [1, 5, 22]}}
        ),
        (
            "portrait, {Hair:#|0|2}",
            {"Hair": {"type": "indices", "value": [0, 2]}}
        ),
    ])
    def test_extract_placeholders(self, prompt, expected):
        """Entrée: prompt avec placeholders → Sortie: dict des options."""
        result = extract_placeholders_with_limits(prompt)

        for key, expected_opts in expected.items():
            assert key in result
            assert result[key]["type"] == expected_opts["type"]
            assert result[key]["value"] == expected_opts["value"]


class TestVariationSelection:
    """Tests de sélection de variations par index."""

    @pytest.fixture
    def sample_variations(self):
        """Fixture: variations de test."""
        return {
            "opt0": "Option 0",
            "opt1": "Option 1",
            "opt2": "Option 2",
            "opt3": "Option 3",
            "opt4": "Option 4",
            "opt5": "Option 5",
        }

    @pytest.mark.parametrize("indices,expected_keys", [
        ([0, 2, 4], ["opt0", "opt2", "opt4"]),
        ([1, 3, 5], ["opt1", "opt3", "opt5"]),
        ([0], ["opt0"]),
        ([5, 3, 1], ["opt5", "opt3", "opt1"]),  # Ordre conservé de la sélection
    ])
    def test_select_by_indices(self, sample_variations, indices, expected_keys):
        """Entrée: variations + indices → Sortie: sous-ensemble sélectionné."""
        result = select_variations_by_indices(sample_variations, indices)

        assert len(result) == len(expected_keys)
        assert list(result.keys()) == expected_keys

    def test_select_invalid_indices(self, sample_variations):
        """Entrée: indices hors limites → Sortie: dict vide."""
        result = select_variations_by_indices(sample_variations, [10, 20])
        assert len(result) == 0


class TestVariationLoading:
    """Tests de chargement de variations depuis fichiers."""

    @pytest.fixture
    def temp_variation_files(self, tmp_path):
        """Fixture: crée des fichiers temporaires de variations."""
        hair_file = tmp_path / "hair.txt"
        hair_file.write_text("short blonde\nlong black\ncurly red\nstraight brown\nwavy silver\n")

        expression_file = tmp_path / "expression.txt"
        expression_file.write_text("smiling\nserious\nlaughing\nsurprised\n")

        return {
            "Hair": str(hair_file),
            "Expression": str(expression_file)
        }

    def test_load_all_variations(self, temp_variation_files):
        """Entrée: prompt sans limites → Sortie: toutes variations chargées."""
        prompt = "portrait, {Hair}, {Expression}"
        result = load_variations_for_placeholders(prompt, temp_variation_files, verbose=False)

        assert "Hair" in result
        assert "Expression" in result
        assert len(result["Hair"]) == 5
        assert len(result["Expression"]) == 4

    def test_load_with_limit(self, temp_variation_files):
        """Entrée: prompt avec :N → Sortie: N variations aléatoires."""
        prompt = "portrait, {Hair:2}, {Expression:2}"
        result = load_variations_for_placeholders(prompt, temp_variation_files, verbose=False)

        assert len(result["Hair"]) == 2
        assert len(result["Expression"]) == 2

    def test_load_with_indices(self, temp_variation_files):
        """Entrée: prompt avec #|indices → Sortie: variations aux indices spécifiés."""
        prompt = "portrait, {Hair:#|0|2|4}, {Expression:#|1|3}"
        result = load_variations_for_placeholders(prompt, temp_variation_files, verbose=False)

        assert len(result["Hair"]) == 3
        assert len(result["Expression"]) == 2

    def test_load_with_zero(self, temp_variation_files):
        """Entrée: prompt avec :0 → Sortie: placeholder présent mais vide."""
        prompt = "portrait, {Hair:0}, {Expression}"
        result = load_variations_for_placeholders(prompt, temp_variation_files, verbose=False)

        # Le comportement actuel retourne {'': ''} pour :0
        assert "Hair" in result
        assert result["Hair"] == {"": ""}
        assert "Expression" in result
        assert len(result["Expression"]) == 4


class TestPromptCleaning:
    """Tests de nettoyage de prompt après remplacement."""

    @pytest.mark.parametrize("input_prompt,expected", [
        ("portrait, {Hair}, beautiful", "portrait, beautiful"),
        ("portrait, , beautiful", "portrait, beautiful"),
        ("portrait,,, beautiful", "portrait, beautiful"),
        ("{Hair}, portrait, {Expression}", "portrait"),
        ("portrait, beautiful, {Hair}", "portrait, beautiful"),
        ("{Hair}", ""),
        ("  portrait  ,  beautiful  ", "portrait, beautiful"),
    ])
    def test_clean_prompt(self, input_prompt, expected):
        """Entrée: prompt avec artefacts → Sortie: prompt nettoyé."""
        import re

        # Simule le nettoyage de prompt
        cleaned = re.sub(r'\{[^}]+\}', '', input_prompt)
        cleaned = re.sub(r',\s*,+', ',', cleaned)
        cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(', ')

        assert cleaned == expected
