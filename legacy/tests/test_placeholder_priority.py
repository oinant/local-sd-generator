"""Tests fonctionnels pour le système de priorité des placeholders."""
import pytest
from variation_loader import extract_placeholders_with_limits, sort_placeholders_by_priority
from sdapi_client import generate_all_combinations


class TestPriorityParsing:
    """Tests du parsing des poids de priorité."""

    @pytest.mark.parametrize("placeholder_str,expected_priority", [
        ("{Outfit:$2}", 2),
        ("{Angle:$10}", 10),
        ("{Expression:15$5}", 5),
        ("{Pose:#|1|5|22$8}", 8),
        ("{Style:#|3$7}", 7),
        ("{Color}", 0),  # Pas de poids = 0 par défaut
    ])
    def test_extract_priority(self, placeholder_str, expected_priority):
        """Entrée: placeholder avec $N → Sortie: priority=N."""
        result = extract_placeholders_with_limits(placeholder_str)

        # Récupère le premier (et seul) placeholder
        placeholder_name = list(result.keys())[0]
        actual_priority = result[placeholder_name].get('priority', 0)

        assert actual_priority == expected_priority

    def test_priority_with_limit(self):
        """Entrée: {Placeholder:15$5} → Sortie: limit=15, priority=5."""
        result = extract_placeholders_with_limits("{Expression:15$5}")

        options = result["Expression"]
        assert options["type"] == "limit"
        assert options["value"] == 15
        assert options.get("priority", 0) == 5

    def test_priority_with_indices(self):
        """Entrée: {Placeholder:#|1|5$8} → Sortie: indices=[1,5], priority=8."""
        result = extract_placeholders_with_limits("{Pose:#|1|5|22$8}")

        options = result["Pose"]
        assert options["type"] == "indices"
        assert options["value"] == [1, 5, 22]
        assert options.get("priority", 0) == 8


class TestPrioritySorting:
    """Tests du tri par priorité."""

    def test_sort_ascending_priority(self):
        """Entrée: poids mélangés → Sortie: ordre croissant (petit=extérieur, grand=intérieur)."""
        placeholders = {
            "Outfit": {"type": "none", "value": None, "priority": 2},
            "Angle": {"type": "none", "value": None, "priority": 10},
            "Lighting": {"type": "none", "value": None, "priority": 5},
            "Expression": {"type": "none", "value": None, "priority": 0}
        }

        result = sort_placeholders_by_priority(placeholders)

        # Ordre attendu: Expression(0), Outfit(2), Lighting(5), Angle(10)
        assert result == ["Expression", "Outfit", "Lighting", "Angle"]

    def test_sort_same_priority(self):
        """Entrée: poids identiques → Sortie: ordre stable."""
        placeholders = {
            "A": {"type": "none", "value": None, "priority": 5},
            "B": {"type": "none", "value": None, "priority": 5},
            "C": {"type": "none", "value": None, "priority": 5}
        }

        result = sort_placeholders_by_priority(placeholders)

        # L'ordre doit être stable (dépend de l'ordre d'insertion du dict)
        assert len(result) == 3
        assert set(result) == {"A", "B", "C"}

    def test_sort_without_priority(self):
        """Entrée: aucun poids → Sortie: ordre naturel (priority=0)."""
        placeholders = {
            "Style": {"type": "none", "value": None},
            "Color": {"type": "none", "value": None},
            "Pose": {"type": "none", "value": None}
        }

        result = sort_placeholders_by_priority(placeholders)

        # Tous ont priority=0, ordre naturel conservé
        assert len(result) == 3


class TestCombinationOrder:
    """Tests de l'ordre des combinaisons générées selon les priorités."""

    @pytest.fixture
    def simple_variations(self):
        """Fixture: variations simples."""
        return {
            "Outfit": {"o1": "dress", "o2": "jeans"},
            "Angle": {"a1": "front", "a2": "side", "a3": "back"}
        }

    def test_combination_order_with_priority(self, simple_variations):
        """Entrée: Outfit(poids=2) Angle(poids=10) → Sortie: boucle sur Outfit d'abord."""
        # Ordre: ["Outfit", "Angle"] (Outfit en boucle extérieure)
        ordered_placeholders = ["Outfit", "Angle"]

        result = generate_all_combinations(simple_variations, ordered_placeholders)

        # 2 outfits × 3 angles = 6 combinaisons
        assert len(result) == 6

        # Les 3 premières combinaisons doivent avoir le même Outfit
        assert result[0]["Outfit"] == result[1]["Outfit"] == result[2]["Outfit"]
        # Les 3 suivantes doivent avoir un autre Outfit
        assert result[3]["Outfit"] == result[4]["Outfit"] == result[5]["Outfit"]
        # Les deux groupes doivent avoir des Outfits différents
        assert result[0]["Outfit"] != result[3]["Outfit"]

    def test_combination_order_reversed(self, simple_variations):
        """Entrée: Angle(poids=2) Outfit(poids=10) → Sortie: boucle sur Angle d'abord."""
        # Ordre: ["Angle", "Outfit"] (Angle en boucle extérieure)
        ordered_placeholders = ["Angle", "Outfit"]

        result = generate_all_combinations(simple_variations, ordered_placeholders)

        assert len(result) == 6

        # Les 2 premières combinaisons doivent avoir le même Angle
        assert result[0]["Angle"] == result[1]["Angle"]
        # Les 2 suivantes un autre Angle
        assert result[2]["Angle"] == result[3]["Angle"]
        # Les 2 dernières encore un autre Angle
        assert result[4]["Angle"] == result[5]["Angle"]

    def test_no_order_specified(self, simple_variations):
        """Entrée: sans ordre spécifié → Sortie: ordre naturel du dict."""
        result = generate_all_combinations(simple_variations)

        # 6 combinaisons générées
        assert len(result) == 6

        # Toutes les combinaisons doivent être présentes
        outfits = set(combo["Outfit"] for combo in result)
        angles = set(combo["Angle"] for combo in result)

        assert outfits == {"dress", "jeans"}
        assert angles == {"front", "side", "back"}
