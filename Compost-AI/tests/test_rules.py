from compost_ai.contracts import EnvironmentalDecision
from compost_ai.rules import EnvironmentalRules


def test_unmapped_organic_material_requires_review():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    assert rules.decide("household", "food_scraps", True).decision is EnvironmentalDecision.REQUIRES_REVIEW


def test_legacy_organic_scene_is_unknown_to_individual_material_rules():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    assert rules.category_for("organic_food_waste_scene") is None
    assert rules.decide("household", "organic_food_waste_scene", True).decision is EnvironmentalDecision.REQUIRES_REVIEW
    assert rules.category_for("recyclable_material_scene") is None


def test_uncertain_recognition_requires_review():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    assert rules.decide("industrial", None, False).decision is EnvironmentalDecision.REQUIRES_REVIEW


def test_category_mapping_is_explicit_and_unknown_for_unmapped_materials():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    assert rules.category_for("plastic") == "inorganic"
    assert rules.category_for("coffee_grounds") is None
    assert rules.category_for(None) is None


def test_plastic_is_excluded_by_household_rules():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    result = rules.decide("household", "plastic", True)
    assert result.decision is EnvironmentalDecision.NO_COMPOSTABLE


def test_individual_organic_materials_follow_household_allowlist():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    for label in ["banana_peel", "potato_peel", "mango_peel", "sugarcane_husk"]:
        assert rules.category_for(label) == "organic"
        assert rules.decide("household", label, True).decision is EnvironmentalDecision.COMPOSTABLE
        assert rules.decide("household", label, False).decision is EnvironmentalDecision.REQUIRES_REVIEW


def test_glass_is_excluded_and_uncertain_glass_requires_review():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    assert rules.category_for("glass") == "inorganic"
    assert rules.decide("household", "glass", True).decision is EnvironmentalDecision.NO_COMPOSTABLE
    assert rules.decide("household", "glass", False).decision is EnvironmentalDecision.REQUIRES_REVIEW


def test_facility_allow_and_deny_rules_are_independent_of_model():
    rules = EnvironmentalRules("config/environmental_rules.yaml")
    rules.config["profiles"]["household"]["accepted_classes"] = ["coffee_grounds"]
    rules.config["profiles"]["household"]["excluded_classes"] = ["compostable_packaging"]
    assert rules.decide("household", "coffee_grounds", True).decision is EnvironmentalDecision.COMPOSTABLE
    assert rules.decide("household", "compostable_packaging", True).decision is EnvironmentalDecision.NO_COMPOSTABLE
