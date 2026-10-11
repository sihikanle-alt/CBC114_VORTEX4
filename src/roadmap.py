import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RoadmapGenerator:
    """
    Generates an ordered, phased learning roadmap:
    1. Topologically sorts skill gaps by prerequisite relationships, broken by priority.
    2. Groups into Phase 1 (Foundations), Phase 2 (Core Role Skills), Phase 3 (Nice-to-Have).
    3. Attaches curated learning resources from courses.json.
    4. Calculates estimated study hours and weeks (reducing hours by 40% for equivalent skills).
    """

    def __init__(
        self,
        taxonomy: Dict[str, Any],
        courses: Optional[Dict[str, Any]] = None,
        courses_path: Optional[str] = None
    ):
        self.taxonomy = taxonomy
        if courses is not None:
            self.courses = courses
        elif courses_path:
            with open(courses_path, "r", encoding="utf-8") as f:
                self.courses = json.load(f)
        else:
            default_path = Path(__file__).resolve().parent.parent / "data" / "courses.json"
            try:
                with open(default_path, "r", encoding="utf-8") as f:
                    self.courses = json.load(f)
            except Exception:
                self.courses = {}

    def _topological_sort(self, gap_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort gaps respecting prerequisites first, and by priority score descending.
        """
        gap_names = {item["name"] for item in gap_items}
        item_map = {item["name"]: item for item in gap_items}

        # in_degree: count how many prerequisites of skill X are ALSO in gap_names
        in_degree = {name: 0 for name in gap_names}
        dependents = defaultdict(list)

        for name in gap_names:
            prereqs = self.taxonomy.get(name, {}).get("prerequisites", [])
            for p in prereqs:
                if p in gap_names:
                    in_degree[name] += 1
                    dependents[p].append(name)

        # Queue of available skills (in_degree == 0)
        # Sort available skills by priority_score descending
        available = [name for name in gap_names if in_degree[name] == 0]
        available.sort(key=lambda n: item_map[n].get("priority_score", 0), reverse=True)

        ordered: List[Dict[str, Any]] = []

        while available:
            # Pick highest priority node that has zero remaining prerequisites
            current = available.pop(0)
            ordered.append(item_map[current])

            # For each dependent of current, decrement in_degree
            for dep in dependents[current]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    available.append(dep)

            # Re-sort available to keep highest priority first
            available.sort(key=lambda n: item_map[n].get("priority_score", 0), reverse=True)

        # Cycle safety: if any remaining nodes wasn't visited due to cyclical dependencies
        visited_names = {item["name"] for item in ordered}
        for name in gap_names:
            if name not in visited_names:
                ordered.append(item_map[name])

        return ordered

    def _get_courses_for_skill(self, skill_name: str) -> List[Dict[str, Any]]:
        """Fetch courses from courses.json or generate high-quality fallback."""
        if skill_name in self.courses:
            return self.courses[skill_name]

        category = self.taxonomy.get(skill_name, {}).get("category", "General")
        # High quality fallback resources
        return [
            {
                "title": f"Mastering {skill_name}: Applied Guide",
                "provider": "Official Documentation & Tutorials",
                "url": f"https://www.google.com/search?q={skill_name.replace(' ', '+')}+tutorial",
                "type": "official docs",
                "est_hours": 15,
                "level": "intermediate"
            },
            {
                "title": f"{skill_name} Fundamentals & Practice Projects",
                "provider": "freeCodeCamp / Kaggle",
                "url": "https://www.freecodecamp.org/",
                "type": "course",
                "est_hours": 20,
                "level": "beginner"
            }
        ]

    def generate_roadmap(
        self,
        scored_items: List[Dict[str, Any]],
        weekly_hours: float = 8.0
    ) -> Dict[str, Any]:
        """
        Generate complete phased roadmap for all skill gaps.
        """
        weekly_hours = max(1.0, float(weekly_hours))

        # Filter to actual gaps
        gaps = [item for item in scored_items if item.get("gap", 0.0) > 0.0]
        if not gaps:
            return {
                "phases": [],
                "total_hours": 0.0,
                "total_weeks": 0.0,
                "weekly_hours": weekly_hours,
                "summary": "No skill gaps detected! Your profile completely covers the requirements."
            }

        # Step 1: Topologically sort
        ordered_gaps = self._topological_sort(gaps)

        # Step 2: Assign phases
        # Phase 1: Foundations (unlocked prerequisites, or high priority foundations)
        # Phase 2: Core role skills (mandatory and high/medium priority skills)
        # Phase 3: Nice-to-have (low priority, optional, polish)
        phase_1_items = []
        phase_2_items = []
        phase_3_items = []

        total_ordered = len(ordered_gaps)
        for idx, item in enumerate(ordered_gaps):
            unlock_bonus = item.get("unlock_bonus", 0.0)
            is_mandatory = item.get("mandatory", False)
            bucket = item.get("priority_bucket", "LOW")

            # Skills that unlock others or are early foundational steps
            if (unlock_bonus > 0.0 and idx < total_ordered // 2 + 1) or (idx == 0 and is_mandatory):
                phase_1_items.append(item)
            elif is_mandatory or bucket in ["HIGH", "MEDIUM"]:
                phase_2_items.append(item)
            else:
                phase_3_items.append(item)

        # Fallback distribution if any phase is empty but we have items
        if not phase_1_items and phase_2_items:
            phase_1_items.append(phase_2_items.pop(0))
        if not phase_2_items and phase_3_items:
            phase_2_items.append(phase_3_items.pop(0))

        phases_def = [
            ("Phase 1: Foundations & Prerequisites", phase_1_items, "Establish essential foundational knowledge and unblock downstream skills."),
            ("Phase 2: Core Role Competencies", phase_2_items, "Build critical, mandatory day-to-day role proficiencies and execution strength."),
            ("Phase 3: Specialized & Nice-to-Have Topics", phase_3_items, "Round out your domain expertise and edge differentiators.")
        ]

        roadmap_phases = []
        grand_total_hours = 0.0

        for phase_name, items, desc in phases_def:
            if not items:
                continue

            phase_hours = 0.0
            enriched_items = []

            for item in items:
                raw_courses = self._get_courses_for_skill(item["name"])
                # Calculate hours: use the primary or average course hours
                base_hours = sum(c.get("est_hours", 15) for c in raw_courses[:2])
                
                # Rule: Reduce hours by 40% for PARTIAL (equivalent) skills
                if item["status"] == "PARTIAL (equivalent)":
                    effective_hours = base_hours * 0.60
                    discount_note = "40% reduction applied (transferable skill synergy)"
                elif item["status"] == "PARTIAL (level)":
                    effective_hours = base_hours * 0.75
                    discount_note = "25% reduction applied (existing baseline)"
                else:
                    effective_hours = float(base_hours)
                    discount_note = "Standard comprehensive curriculum"

                effective_hours = round(effective_hours, 1)
                est_weeks = max(0.5, round(effective_hours / weekly_hours, 1))

                phase_hours += effective_hours
                enriched_item = dict(item)
                enriched_item.update({
                    "base_hours": base_hours,
                    "effective_hours": effective_hours,
                    "estimated_weeks": est_weeks,
                    "discount_note": discount_note,
                    "courses": raw_courses
                })
                enriched_items.append(enriched_item)

            phase_weeks = max(0.5, round(phase_hours / weekly_hours, 1))
            grand_total_hours += phase_hours

            roadmap_phases.append({
                "phase_title": phase_name,
                "description": desc,
                "items": enriched_items,
                "phase_hours": round(phase_hours, 1),
                "phase_weeks": phase_weeks
            })

        grand_total_weeks = max(0.5, round(grand_total_hours / weekly_hours, 1))

        return {
            "phases": roadmap_phases,
            "total_hours": round(grand_total_hours, 1),
            "total_weeks": grand_total_weeks,
            "weekly_hours": weekly_hours,
            "total_gap_count": len(gaps)
        }
