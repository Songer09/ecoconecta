from pathlib import Path
from typing import Any

import yaml

from compost_ai.contracts import EnvironmentalDecision, EnvironmentalResult


class EnvironmentalRules:
    """Independent, configurable policy engine; it never inspects image pixels."""

    def __init__(self, path: str | Path):
        with Path(path).open(encoding="utf-8") as stream:
            self.config: dict[str, Any] = yaml.safe_load(stream)

    def category_for(self, material: str | None) -> str | None:
        """Return a broad waste category only for explicitly mapped labels."""
        if material is None:
            return None
        mapping = self.config.get("category_by_class", {})
        return mapping.get(material.casefold())

    def decide(self, profile: str, predicted_class: str | None, accepted: bool) -> EnvironmentalResult:
        profiles = self.config.get("profiles", {})
        if profile not in profiles:
            raise ValueError(f"Unknown compost profile: {profile}")
        rules = profiles[profile]
        if not accepted or predicted_class is None:
            return EnvironmentalResult(
                decision=EnvironmentalDecision.REQUIRES_REVIEW,
                profile=profile,
                reason="Recognition is uncertain or out of distribution; manual review is required.",
            )
        label = predicted_class.casefold()
        excluded = {item.casefold() for item in rules.get("excluded_classes", [])}
        accepted_classes = {item.casefold() for item in rules.get("accepted_classes", [])}
        if label in excluded:
            return EnvironmentalResult(
                decision=EnvironmentalDecision.NO_COMPOSTABLE,
                profile=profile,
                reason="This class is excluded by the configured facility rules.",
            )
        if label in accepted_classes:
            return EnvironmentalResult(
                decision=EnvironmentalDecision.COMPOSTABLE,
                profile=profile,
                reason="This class is explicitly accepted by the configured facility rules.",
            )
        if self.category_for(label) != "organic":
            return EnvironmentalResult(
                decision=EnvironmentalDecision.REQUIRES_REVIEW,
                profile=profile,
                reason=rules.get(
                    "unclassified_material_note",
                    "No explicit facility rule for this material; manual review is required.",
                ),
            )
        organic = rules.get("organic", {})
        return EnvironmentalResult(
            decision=EnvironmentalDecision(organic.get("decision", "REQUIRES_REVIEW")),
            profile=profile,
            reason=organic.get("note", "No explicit facility rule; review required."),
        )
