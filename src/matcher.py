import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

LEVEL_ORDER = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3
}

class SkillMatcher:
    """
    Classifies each required skill into exactly one status:
    - EXISTING (1.0)
    - PARTIAL (level) (0.5 - 0.8)
    - PARTIAL (equivalent) (capped at 0.85)
    - MISSING (0.0)
    """

    def __init__(self, taxonomy: Dict[str, Any]):
        self.taxonomy = taxonomy

    def _level_distance_score(self, user_level: str, req_level: str) -> float:
        """Calculate match score for level mismatch (0.5 to 0.8)."""
        u_val = LEVEL_ORDER.get(user_level.lower(), 2)
        r_val = LEVEL_ORDER.get(req_level.lower(), 2)

        if u_val >= r_val:
            return 1.0

        diff = r_val - u_val
        if diff == 1:
            if r_val == 3 and u_val == 2:
                return 0.75  # Intermediate vs Advanced
            else:
                return 0.65  # Beginner vs Intermediate
        else:
            return 0.50      # Beginner vs Advanced

    def _find_best_equivalent(self, req_skill: str, user_skills: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], float]:
        """
        Check if user has a related/transferable skill from taxonomy.
        Checks both directions:
        1. req_skill's related list contains a user skill
        2. user skill's related list contains req_skill
        """
        best_skill = None
        best_weight = 0.0

        # Check req_skill -> related
        req_data = self.taxonomy.get(req_skill, {})
        req_related = req_data.get("related", {})
        for r_name, weight in req_related.items():
            if r_name in user_skills and weight > best_weight:
                best_weight = weight
                best_skill = r_name

        # Check reverse: user_skills -> req_skill
        for u_name in user_skills.keys():
            u_data = self.taxonomy.get(u_name, {})
            u_related = u_data.get("related", {})
            if req_skill in u_related and u_related[req_skill] > best_weight:
                best_weight = u_related[req_skill]
                best_skill = u_name

        # Equivalent match score capped at 0.85
        score = min(0.85, best_weight) if best_weight >= 0.3 else 0.0
        return best_skill, score

    def match_skills(
        self,
        required_skills: List[Dict[str, Any]],
        user_skills: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match profile skills against required skills.
        Each required skill receives exactly one of:
        EXISTING, PARTIAL (level), PARTIAL (equivalent), MISSING.
        """
        matches = []

        for req in required_skills:
            name = req["name"]
            req_level = req.get("level", "intermediate")
            importance = req.get("importance", 0.8)
            mandatory = req.get("mandatory", False)
            category = self.taxonomy.get(name, {}).get("category", "General")

            # Check 1: User has the skill directly
            if name in user_skills:
                user_info = user_skills[name]
                user_level = user_info.get("level", "intermediate")
                u_val = LEVEL_ORDER.get(user_level.lower(), 2)
                r_val = LEVEL_ORDER.get(req_level.lower(), 2)

                if u_val >= r_val:
                    status = "EXISTING"
                    score = 1.0
                else:
                    status = "PARTIAL (level)"
                    score = self._level_distance_score(user_level, req_level)

                matches.append({
                    "name": name,
                    "required_level": req_level,
                    "user_level": user_level,
                    "status": status,
                    "match_score": round(score, 2),
                    "matched_via": None,
                    "equivalent_overlap": 0.0,
                    "importance": importance,
                    "mandatory": mandatory,
                    "category": category
                })
                continue

            # Check 2: User has equivalent / related skill
            eq_skill, eq_score = self._find_best_equivalent(name, user_skills)
            if eq_skill and eq_score > 0.0:
                user_eq_level = user_skills[eq_skill].get("level", "intermediate")
                matches.append({
                    "name": name,
                    "required_level": req_level,
                    "user_level": f"via {eq_skill} ({user_eq_level})",
                    "status": "PARTIAL (equivalent)",
                    "match_score": round(eq_score, 2),
                    "matched_via": eq_skill,
                    "equivalent_overlap": round(eq_score, 2),
                    "importance": importance,
                    "mandatory": mandatory,
                    "category": category
                })
                continue

            # Check 3: MISSING
            matches.append({
                "name": name,
                "required_level": req_level,
                "user_level": "none",
                "status": "MISSING",
                "match_score": 0.0,
                "matched_via": None,
                "equivalent_overlap": 0.0,
                "importance": importance,
                "mandatory": mandatory,
                "category": category
            })

        return matches
