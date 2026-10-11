import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SkillExplainer:
    """
    Generates human-readable, fact-based explanations for why a skill is classified
    and prioritized the way it is.
    """

    def __init__(self, taxonomy: Dict[str, Any]):
        self.taxonomy = taxonomy

    def explain_skill(self, item: Dict[str, Any], role_name: str = "Target Role") -> str:
        """Builds a factual explanation for an individual skill match."""
        name = item["name"]
        status = item["status"]
        importance = item.get("importance", 0.8)
        mandatory = item.get("mandatory", False)
        bucket = item.get("priority_bucket", "LOW")
        req_level = item.get("required_level", "intermediate")
        user_level = item.get("user_level", "none")
        matched_via = item.get("matched_via")
        overlap = item.get("equivalent_overlap", 0.0)
        unlock_bonus = item.get("unlock_bonus", 0.0)

        # 1. EXISTING
        if status == "EXISTING":
            mand_str = "mandatory" if mandatory else "recommended"
            return (
                f"You already possess {name} at {user_level} proficiency, "
                f"fully meeting the {mand_str} requirement for {role_name} (importance {importance})."
            )

        # 2. PARTIAL (equivalent)
        if status == "PARTIAL (equivalent)":
            pct = int(overlap * 100) if overlap > 0 else 75
            return (
                f"You know {matched_via}, which transfers directly to {name} (~{pct}% conceptual overlap). "
                f"A short, targeted course is sufficient rather than learning from scratch."
            )

        # 3. PARTIAL (level)
        if status == "PARTIAL (level)":
            mand_str = "mandatory" if mandatory else "core"
            return (
                f"{name} is {bucket} priority: you currently possess {user_level} level, "
                f"whereas {role_name} demands {req_level} proficiency (importance {importance}, {mand_str}). "
                f"Elevating this skill will eliminate practical execution bottlenecks."
            )

        # 4. MISSING
        mand_clause = "mandatory" if mandatory else "a recommended skill"
        unlock_clause = ""
        # Find which topics this skill unlocks
        tax_entry = self.taxonomy.get(name, {})
        unlocked_skills = []
        for other_skill, data in self.taxonomy.items():
            if name in data.get("prerequisites", []):
                unlocked_skills.append(other_skill)

        if unlocked_skills:
            sample_unlocked = ", ".join(unlocked_skills[:2])
            unlock_clause = f", and mastering it unlocks downstream areas such as {sample_unlocked}"
        elif unlock_bonus > 0.0:
            unlock_clause = ", and it establishes essential foundations for upcoming role competencies"

        return (
            f"{name} is {bucket} priority: it is {mand_clause} for {role_name} (importance {importance}), "
            f"you have no direct or equivalent background in it{unlock_clause}."
        )

    def attach_explanations(self, items: List[Dict[str, Any]], role_name: str = "Target Role") -> List[Dict[str, Any]]:
        """Add explanation string to every skill item."""
        enriched = []
        for item in items:
            copy_item = dict(item)
            copy_item["explanation"] = self.explain_skill(item, role_name)
            enriched.append(copy_item)
        return enriched
