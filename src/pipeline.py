import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from .normalizer import SkillNormalizer
from .extractor import SkillExtractor
from .matcher import SkillMatcher
from .prioritizer import SkillPrioritizer
from .explainer import SkillExplainer
from .roadmap import RoadmapGenerator
from .edge_cases import EdgeCaseHandler

logger = logging.getLogger(__name__)

class SkillGapPipeline:
    """
    End-to-end orchestration pipeline for the AI-Based Skill Gap Analyzer.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None
    ):
        base_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data"

        # Load taxonomy
        tax_path = base_dir / "skills_taxonomy.json"
        with open(tax_path, "r", encoding="utf-8") as f:
            self.taxonomy = json.load(f)

        # Load roles
        roles_path = base_dir / "roles.json"
        with open(roles_path, "r", encoding="utf-8") as f:
            self.roles = json.load(f)

        # Load courses
        courses_path = base_dir / "courses.json"
        with open(courses_path, "r", encoding="utf-8") as f:
            self.courses = json.load(f)

        # Initialize sub-modules
        self.normalizer = SkillNormalizer(taxonomy=self.taxonomy)
        self.extractor = SkillExtractor(normalizer=self.normalizer)
        self.matcher = SkillMatcher(taxonomy=self.taxonomy)
        self.prioritizer = SkillPrioritizer(taxonomy=self.taxonomy)
        self.explainer = SkillExplainer(taxonomy=self.taxonomy)
        self.roadmap_gen = RoadmapGenerator(taxonomy=self.taxonomy, courses=self.courses)
        self.edge_cases = EdgeCaseHandler(taxonomy=self.taxonomy)

    def analyze(
        self,
        profile_text: str,
        role_name: Optional[str] = "Data Scientist",
        custom_jd_text: Optional[str] = None,
        weekly_hours: float = 8.0,
        confirmed_ambiguous_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute full skill gap analysis workflow.
        """
        # Step 1: Validation
        is_valid, warn_msg = self.edge_cases.validate_profile_input(profile_text)
        if not is_valid:
            return {
                "success": False,
                "error": warn_msg,
                "matches": [],
                "readiness": {"readiness_score": 0.0, "verdict": "Needs foundation", "start_here": []},
                "roadmap": {"phases": [], "total_hours": 0.0, "total_weeks": 0.0}
            }

        # Step 2: Extract skills from candidate profile
        user_skills = self.extractor.extract_from_profile(profile_text)

        # Step 3: Determine target role and required skills
        effective_role_name = role_name
        if custom_jd_text and custom_jd_text.strip():
            effective_role_name = "Custom Job Description"
            required_skills = self.extractor.extract_from_jd(custom_jd_text)
            ambiguous_terms = self.edge_cases.detect_ambiguous_terms(custom_jd_text)
        else:
            role_data = self.roles.get(role_name, {})
            required_skills = list(role_data.get("skills", []))
            ambiguous_terms = self.edge_cases.detect_ambiguous_terms(profile_text)

        # If user explicitly confirmed skills from ambiguous terms, merge them
        if confirmed_ambiguous_skills:
            existing_req_names = {r["name"] for r in required_skills}
            for skill_name in confirmed_ambiguous_skills:
                if skill_name in self.taxonomy and skill_name not in existing_req_names:
                    required_skills.append({
                        "name": skill_name,
                        "importance": 0.75,
                        "mandatory": False,
                        "level": "intermediate"
                    })

        if not required_skills:
            # Fallback if custom JD yielded no skills
            required_skills = self.roles.get("Data Scientist", {}).get("skills", [])
            effective_role_name = "Data Scientist (Fallback)"

        # Step 4: Matching
        raw_matches = self.matcher.match_skills(required_skills, user_skills)

        # Step 5: Prioritization
        prioritized_matches = self.prioritizer.prioritize(raw_matches)

        # Step 6: Explanations
        enriched_matches = self.explainer.attach_explanations(prioritized_matches, effective_role_name)

        # Step 7: Edge cases & Readiness
        readiness = self.edge_cases.calculate_readiness_score(enriched_matches)
        equivalents = self.edge_cases.detect_equivalent_skills(enriched_matches)
        unrecognized = self.edge_cases.suggest_unrecognized_tokens(profile_text, set(user_skills.keys()))

        # Step 8: Learning Roadmap
        roadmap = self.roadmap_gen.generate_roadmap(enriched_matches, weekly_hours=weekly_hours)

        # Metrics overview
        existing_count = sum(1 for m in enriched_matches if m["status"] == "EXISTING")
        partial_count = sum(1 for m in enriched_matches if m["status"].startswith("PARTIAL"))
        missing_count = sum(1 for m in enriched_matches if m["status"] == "MISSING")

        return {
            "success": True,
            "role_name": effective_role_name,
            "user_skills": user_skills,
            "required_skills": required_skills,
            "matches": enriched_matches,
            "readiness": readiness,
            "equivalents": equivalents,
            "ambiguous_terms": ambiguous_terms,
            "unrecognized_tokens": unrecognized,
            "roadmap": roadmap,
            "summary_stats": {
                "total_required": len(required_skills),
                "existing": existing_count,
                "partial": partial_count,
                "missing": missing_count,
                "readiness_score": readiness["readiness_score"],
                "verdict": readiness["verdict"]
            }
        }

    def compare_multiple_roles(self, profile_text: str) -> List[Dict[str, Any]]:
        """
        Compare profile across all available target roles to find the best-fit role.
        """
        results = []
        for role_name in self.roles.keys():
            res = self.analyze(profile_text, role_name=role_name)
            if res.get("success"):
                stats = res["summary_stats"]
                results.append({
                    "role_name": role_name,
                    "readiness_score": stats["readiness_score"],
                    "verdict": stats["verdict"],
                    "existing": stats["existing"],
                    "partial": stats["partial"],
                    "missing": stats["missing"],
                    "total_required": stats["total_required"]
                })
        results.sort(key=lambda r: r["readiness_score"], reverse=True)
        return results

    def generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Create a cleanly formatted Markdown report."""
        if not analysis.get("success"):
            return f"# Skill Gap Analysis Report\n\nError: {analysis.get('error')}"

        role = analysis.get("role_name", "Target Role")
        stats = analysis["summary_stats"]
        readiness = analysis["readiness"]

        lines = [
            f"# Skill Gap Analysis & Learning Roadmap: {role}",
            "",
            f"**Readiness Score:** {readiness['readiness_score']}% ({readiness['verdict']})  ",
            f"**Required Competencies:** {stats['total_required']} | **Existing:** {stats['existing']} | **Partial:** {stats['partial']} | **Missing:** {stats['missing']}",
            "",
            "## 🎯 Top 'Start Here' Recommendations",
            ""
        ]
        for idx, rec in enumerate(readiness.get("start_here", []), 1):
            lines.append(f"{idx}. **{rec}**")

        lines.extend([
            "",
            "## 📊 Skill Comparison Matrix",
            "",
            "| Skill | Required Level | Your Level | Status | Match Score | Priority | Mandatory |",
            "|---|---|---|---|---|---|---|"
        ])
        for m in analysis["matches"]:
            lines.append(
                f"| {m['name']} | {m['required_level']} | {m['user_level']} | {m['status']} | {int(m['match_score']*100)}% | {m.get('priority_bucket', 'N/A')} | {'Yes' if m.get('mandatory') else 'No'} |"
            )

        lines.extend([
            "",
            "## 💡 Priority Improvement Areas & Explanations",
            ""
        ])
        for m in analysis["matches"]:
            if m.get("gap", 0) > 0:
                lines.append(f"### {m['name']} [{m.get('priority_bucket')}]")
                lines.append(f"- **Explanation:** {m.get('explanation')}")
                lines.append(f"- **Match:** {int(m['match_score']*100)}% | **Importance:** {m.get('importance')} | **Mandatory:** {m.get('mandatory')}")
                lines.append("")

        lines.extend([
            "## 🗺️ Phased Learning Roadmap",
            f"Estimated total study commitment: **{analysis['roadmap']['total_hours']} hours** (~**{analysis['roadmap']['total_weeks']} weeks** at {analysis['roadmap']['weekly_hours']} hrs/week).",
            ""
        ])
        for phase in analysis["roadmap"]["phases"]:
            lines.append(f"### {phase['phase_title']} ({phase['phase_weeks']} weeks, {phase['phase_hours']} hrs)")
            lines.append(f"*{phase['description']}*")
            lines.append("")
            for item in phase["items"]:
                lines.append(f"- **{item['name']}** ({item['effective_hours']} hrs) - *{item['discount_note']}*")
                for c in item.get("courses", [])[:2]:
                    lines.append(f"  - [{c['title']}]({c['url']}) ({c['provider']}, {c['est_hours']}h)")
            lines.append("")

        return "\n".join(lines)
