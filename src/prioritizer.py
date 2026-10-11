import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SkillPrioritizer:
    """
    Computes priority score for each skill gap:
    gap = 1 - match_score
    priority = importance * gap * (1.5 if mandatory else 1.0) + 0.1 * unlock_bonus
    unlock_bonus = number of other missing/partial skills that list this skill as a prerequisite (0 to 1).
    Buckets:
    - priority >= 0.7 -> HIGH
    - 0.35 <= priority < 0.7 -> MEDIUM
    - priority < 0.35 -> LOW
    """

    def __init__(self, taxonomy: Dict[str, Any]):
        self.taxonomy = taxonomy

    def calculate_unlock_bonus(
        self,
        skill_name: str,
        missing_or_partial_skills: List[str]
    ) -> float:
        """
        Count how many other missing/partial skills list this skill as a prerequisite,
        normalized to [0, 1].
        """
        other_skills = [s for s in missing_or_partial_skills if s != skill_name]
        if not other_skills:
            return 0.0

        count = 0
        for other in other_skills:
            prereqs = self.taxonomy.get(other, {}).get("prerequisites", [])
            if skill_name in prereqs:
                count += 1

        # Also check broader taxonomy if within-role count is low to recognize true foundational skills
        broader_count = 0
        for tax_skill, tax_data in self.taxonomy.items():
            if tax_skill not in missing_or_partial_skills:
                continue
            if skill_name in tax_data.get("prerequisites", []):
                broader_count += 1

        effective_count = max(count, broader_count)
        # Normalize to 0..1 scale (e.g. 2+ prereqs = 1.0)
        return min(1.0, effective_count / 2.0) if effective_count > 0 else 0.0

    def prioritize(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates gap, unlock bonus, priority score, and bucket for each skill.
        Returns all matched skills enriched with priority metrics, sorted by priority descending.
        """
        # Identify missing or partial skills
        gap_skill_names = [
            m["name"] for m in matches if m["match_score"] < 1.0
        ]

        enriched = []
        for m in matches:
            gap = round(1.0 - m["match_score"], 2)
            importance = m.get("importance", 0.8)
            mandatory = m.get("mandatory", False)
            name = m["name"]

            if gap > 0.0:
                unlock_bonus = self.calculate_unlock_bonus(name, gap_skill_names)
                mandatory_multiplier = 1.5 if mandatory else 1.0
                priority_score = (importance * gap * mandatory_multiplier) + (0.1 * unlock_bonus)
            else:
                unlock_bonus = 0.0
                priority_score = 0.0

            priority_score = round(priority_score, 3)

            # Assign bucket
            if priority_score >= 0.7:
                bucket = "HIGH"
            elif priority_score >= 0.35:
                bucket = "MEDIUM"
            else:
                bucket = "LOW"

            item = dict(m)
            item.update({
                "gap": gap,
                "unlock_bonus": round(unlock_bonus, 2),
                "priority_score": priority_score,
                "priority_bucket": bucket
            })
            enriched.append(item)

        # Sort descending by priority score, then by mandatory flag, then by importance
        enriched.sort(key=lambda x: (x["priority_score"], x["mandatory"], x["importance"]), reverse=True)
        return enriched
