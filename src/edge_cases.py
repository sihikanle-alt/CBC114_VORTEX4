import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

logger = logging.getLogger(__name__)

AMBIGUOUS_TERMS_MAP: Dict[str, List[str]] = {
    "cloud knowledge": ["AWS", "Azure", "Google Cloud Platform (GCP)"],
    "cloud experience": ["AWS", "Azure", "Google Cloud Platform (GCP)"],
    "good with data": ["SQL", "pandas", "Data Visualization", "Statistics"],
    "working with data": ["SQL", "pandas", "Data Visualization"],
    "data background": ["SQL", "pandas", "Statistics"],
    "ml experience": ["Machine Learning", "scikit-learn", "PyTorch", "Feature Engineering"],
    "machine learning experience": ["Machine Learning", "scikit-learn", "PyTorch"],
    "deep learning experience": ["Deep Learning", "PyTorch", "TensorFlow"],
    "strong communication": ["Communication", "Collaboration"],
    "communication skills": ["Communication", "Collaboration"],
    "big data": ["Apache Spark", "Data Engineering", "PySpark"],
    "devops skills": ["Docker", "CI/CD", "Linux", "Kubernetes"],
    "devops experience": ["Docker", "CI/CD", "Linux"],
    "frontend knowledge": ["React", "JavaScript", "HTML/CSS"],
    "backend knowledge": ["FastAPI", "Python", "REST APIs", "PostgreSQL"],
    "ai experience": ["Large Language Models", "Prompt Engineering", "LangChain"],
    "generative ai": ["Large Language Models", "Prompt Engineering", "LangChain"]
}

class EdgeCaseHandler:
    """
    Handles domain edge cases:
    1. Equivalent experience under different names (banners & synergy detection).
    2. Ambiguous JD terms expansion with user confirmation.
    3. Multiple mandatory missing skills with Readiness Score & 'Start Here' top 3.
    4. Empty or too-short input validation.
    5. Unrecognized tokens with 'Did you mean?' suggestions.
    6. Deduplication and conflict resolution.
    """

    def __init__(self, taxonomy: Dict[str, Any]):
        self.taxonomy = taxonomy

    def validate_profile_input(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate profile string to prevent empty or unhelpful inputs."""
        if not text or not text.strip():
            return False, "Profile is empty. Please enter your resume summary, paste skills, or upload a file."

        words = text.strip().split()
        if len(words) < 3 or len(text.strip()) < 12:
            return False, "Profile text is too brief to analyze meaningful skill gaps. Please add a sentence or list a few skills/tools."

        return True, None

    def detect_ambiguous_terms(self, text: str) -> Dict[str, List[str]]:
        """
        Detect ambiguous requirements like 'cloud knowledge' or 'ml experience'.
        Returns: {ambiguous_phrase: [candidate_canonical_skills]}
        """
        if not text:
            return {}

        found: Dict[str, List[str]] = {}
        lower_text = text.lower()

        for term, candidates in AMBIGUOUS_TERMS_MAP.items():
            pattern = rf'\b{re.escape(term)}\b'
            if re.search(pattern, lower_text):
                found[term] = candidates

        return found

    def detect_equivalent_skills(self, matched_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify detected equivalent competencies where the candidate has a transferable alternative.
        """
        equivalents = []
        for item in matched_items:
            if item.get("status") == "PARTIAL (equivalent)":
                equivalents.append({
                    "target_skill": item["name"],
                    "user_skill": item.get("matched_via"),
                    "overlap": item.get("equivalent_overlap", 0.75),
                    "importance": item.get("importance", 0.8),
                    "mandatory": item.get("mandatory", False)
                })
        return equivalents

    def calculate_readiness_score(self, matched_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates role readiness score, verdict, and 'Start Here' Top 3 recommendations.
        Readiness formula:
        - Weighted % of mandatory skills match score (if mandatory skills exist)
        - Otherwise weighted % across all required skills
        Verdict:
        - >= 80%: Ready
        - 50% - 79%: Almost there
        - < 50%: Needs foundation
        """
        if not matched_items:
            return {
                "readiness_score": 0.0,
                "verdict": "Needs foundation",
                "start_here": [],
                "mandatory_count": 0,
                "mandatory_met": 0
            }

        mandatory_items = [m for m in matched_items if m.get("mandatory", False)]
        eval_items = mandatory_items if mandatory_items else matched_items

        total_weight = sum(m.get("importance", 0.8) for m in eval_items)
        earned_weight = sum(m.get("match_score", 0.0) * m.get("importance", 0.8) for m in eval_items)

        if total_weight > 0:
            score = round((earned_weight / total_weight) * 100.0, 1)
        else:
            score = 0.0

        if score >= 80.0:
            verdict = "Ready"
        elif score >= 50.0:
            verdict = "Almost there"
        else:
            verdict = "Needs foundation"

        # Determine 'Start Here' top 3:
        # High priority mandatory gaps first, then other gaps
        gaps = [m for m in matched_items if m.get("match_score", 1.0) < 1.0]
        # Sort by: mandatory desc, priority_score desc, gap desc
        sorted_gaps = sorted(
            gaps,
            key=lambda x: (
                x.get("mandatory", False),
                x.get("priority_score", 0.0),
                x.get("gap", 0.0)
            ),
            reverse=True
        )

        start_here = [g["name"] for g in sorted_gaps[:3]]

        mand_met = sum(1 for m in mandatory_items if m.get("match_score", 0.0) >= 1.0)

        return {
            "readiness_score": score,
            "verdict": verdict,
            "start_here": start_here,
            "mandatory_count": len(mandatory_items),
            "mandatory_met": mand_met
        }

    def suggest_unrecognized_tokens(
        self,
        text: str,
        recognized_skills: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract potentially misspelled or unknown skill terms and suggest taxonomy matches.
        """
        tokens = [t.strip() for t in re.split(r'[,;\n•\t|]+', text) if t.strip()]
        unrecognized = []

        try:
            from rapidfuzz import fuzz, process
            taxonomy_keys = list(self.taxonomy.keys())

            for tok in tokens:
                # If short token and not recognized
                if 2 <= len(tok) <= 25 and tok not in recognized_skills:
                    # Check if close to something in taxonomy
                    match = process.extractOne(tok, taxonomy_keys, scorer=fuzz.ratio, score_cutoff=65)
                    if match:
                        suggested, score, _ = match
                        if score < 90:  # Not an exact/already matched
                            unrecognized.append({
                                "token": tok,
                                "suggestion": suggested,
                                "similarity": score
                            })
        except Exception:
            pass

        return unrecognized
