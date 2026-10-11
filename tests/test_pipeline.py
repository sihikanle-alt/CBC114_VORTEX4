import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.normalizer import SkillNormalizer
from src.extractor import SkillExtractor
from src.matcher import SkillMatcher
from src.prioritizer import SkillPrioritizer
from src.explainer import SkillExplainer
from src.roadmap import RoadmapGenerator
from src.edge_cases import EdgeCaseHandler
from src.pipeline import SkillGapPipeline

@pytest.fixture(scope="module")
def pipeline():
    return SkillGapPipeline()

@pytest.fixture(scope="module")
def normalizer(pipeline):
    return pipeline.normalizer

@pytest.fixture(scope="module")
def edge_case_handler(pipeline):
    return pipeline.edge_cases

# ==========================================
# 1. Alias & Normalization Tests
# ==========================================
def test_alias_normalization(normalizer):
    # sklearn -> scikit-learn
    c1, conf1, m1 = normalizer.normalize("sklearn")
    assert c1 == "scikit-learn"
    assert conf1 >= 0.9

    # ReactJS -> React
    c2, conf2, m2 = normalizer.normalize("ReactJS")
    assert c2 == "React"

    # Python 3.10 -> Python
    c3, conf3, m3 = normalizer.normalize("Python 3.10")
    assert c3 == "Python"

    # K8s -> Kubernetes
    c4, conf4, m4 = normalizer.normalize("k8s")
    assert c4 == "Kubernetes"

# ==========================================
# 2. Equivalent Skill Scoring Tests
# ==========================================
def test_equivalent_skill_scoring(pipeline):
    # If user has TensorFlow, PyTorch should get PARTIAL (equivalent) with related weight
    user_skills = {
        "TensorFlow": {"name": "TensorFlow", "level": "intermediate"}
    }
    required = [
        {"name": "PyTorch", "importance": 0.9, "mandatory": True, "level": "intermediate"}
    ]
    matches = pipeline.matcher.match_skills(required, user_skills)
    assert len(matches) == 1
    match = matches[0]
    assert match["status"] == "PARTIAL (equivalent)"
    assert match["matched_via"] == "TensorFlow"
    assert 0.7 <= match["match_score"] <= 0.85
    assert match["equivalent_overlap"] >= 0.7

# ==========================================
# 3. Priority Ordering (Mandatory > Optional)
# ==========================================
def test_priority_ordering(pipeline):
    # Two missing skills with equal gap (1.0) and equal importance, one mandatory
    raw_matches = [
        {"name": "SkillOptional", "match_score": 0.0, "importance": 0.8, "mandatory": False, "category": "ML"},
        {"name": "SkillMandatory", "match_score": 0.0, "importance": 0.8, "mandatory": True, "category": "ML"}
    ]
    prioritized = pipeline.prioritizer.prioritize(raw_matches)
    # SkillMandatory must have higher priority score than SkillOptional
    mand_item = next(p for p in prioritized if p["name"] == "SkillMandatory")
    opt_item = next(p for p in prioritized if p["name"] == "SkillOptional")
    assert mand_item["priority_score"] > opt_item["priority_score"]
    assert mand_item["priority_bucket"] == "HIGH"

# ==========================================
# 4. Ambiguous Terms Handling
# ==========================================
def test_ambiguous_term_handling(edge_case_handler):
    text = "Candidate has cloud knowledge and good with data, plus strong communication."
    found = edge_case_handler.detect_ambiguous_terms(text)
    assert "cloud knowledge" in found
    assert "good with data" in found
    assert "strong communication" in found
    assert "AWS" in found["cloud knowledge"]
    assert "SQL" in found["good with data"]

# ==========================================
# 5. Empty / Too-Short Input
# ==========================================
def test_empty_input_validation(pipeline):
    res_empty = pipeline.analyze("")
    assert res_empty["success"] is False
    assert "Profile is empty" in res_empty["error"]

    res_short = pipeline.analyze("hi")
    assert res_short["success"] is False
    assert "too brief" in res_short["error"]

# ==========================================
# 6. Readiness Score Calculation & Verdicts
# ==========================================
def test_readiness_score_calculation(edge_case_handler):
    # Ready (>=80%)
    matches_ready = [
        {"name": "A", "match_score": 1.0, "importance": 1.0, "mandatory": True, "gap": 0.0, "priority_score": 0.0},
        {"name": "B", "match_score": 0.8, "importance": 1.0, "mandatory": True, "gap": 0.2, "priority_score": 0.3}
    ]
    r1 = edge_case_handler.calculate_readiness_score(matches_ready)
    assert r1["readiness_score"] >= 80.0
    assert r1["verdict"] == "Ready"

    # Needs foundation (<50%)
    matches_low = [
        {"name": "A", "match_score": 0.0, "importance": 1.0, "mandatory": True, "gap": 1.0, "priority_score": 1.5},
        {"name": "B", "match_score": 0.0, "importance": 1.0, "mandatory": True, "gap": 1.0, "priority_score": 1.5}
    ]
    r2 = edge_case_handler.calculate_readiness_score(matches_low)
    assert r2["readiness_score"] < 50.0
    assert r2["verdict"] == "Needs foundation"

# ==========================================
# 7. Roadmap Prerequisite Ordering & Equivalent Discount
# ==========================================
def test_roadmap_prerequisites_and_discount(pipeline):
    # PyTorch has prerequisites: Python, Deep Learning, Linear Algebra
    scored_items = [
        {
            "name": "PyTorch",
            "gap": 0.25,
            "match_score": 0.75,
            "status": "PARTIAL (equivalent)",
            "priority_score": 0.6,
            "priority_bucket": "MEDIUM",
            "mandatory": True,
            "unlock_bonus": 0.0,
            "category": "Deep Learning"
        },
        {
            "name": "Deep Learning",
            "gap": 1.0,
            "match_score": 0.0,
            "status": "MISSING",
            "priority_score": 0.8,
            "priority_bucket": "HIGH",
            "mandatory": True,
            "unlock_bonus": 1.0,
            "category": "Deep Learning"
        }
    ]
    roadmap = pipeline.roadmap_gen.generate_roadmap(scored_items, weekly_hours=8.0)
    assert len(roadmap["phases"]) >= 1
    # Check that Deep Learning comes before PyTorch
    flat_items = [it["name"] for phase in roadmap["phases"] for it in phase["items"]]
    assert flat_items.index("Deep Learning") < flat_items.index("PyTorch")

    # Check 40% hours discount applied to PARTIAL (equivalent)
    pytorch_item = next(it for phase in roadmap["phases"] for it in phase["items"] if it["name"] == "PyTorch")
    assert "40% reduction" in pytorch_item["discount_note"]
    assert pytorch_item["effective_hours"] == round(pytorch_item["base_hours"] * 0.6, 1)

# ==========================================
# 8. Data Scientist Demo Verification
# ==========================================
def test_demo_sample_profile_data_scientist(pipeline):
    sample_text = (
        "Final-year CS student. Built projects in Python using pandas, numpy, matplotlib and sklearn. "
        "Know basic SQL from coursework. Completed a TensorFlow image classifier. "
        "Familiar with Git and Streamlit."
    )
    result = pipeline.analyze(sample_text, role_name="Data Scientist")
    assert result["success"] is True

    match_dict = {m["name"]: m for m in result["matches"]}

    # EXISTING: Python, scikit-learn (from 'sklearn')
    assert "Python" in match_dict
    assert match_dict["Python"]["status"] == "EXISTING"

    assert "scikit-learn" in match_dict
    assert match_dict["scikit-learn"]["status"] == "EXISTING"

    # PARTIAL: SQL (beginner vs intermediate)
    assert "SQL" in match_dict
    assert match_dict["SQL"]["status"] == "PARTIAL (level)"

    # PARTIAL: Deep Learning (via TensorFlow classifier)
    assert "Deep Learning" in match_dict
    assert match_dict["Deep Learning"]["status"] == "PARTIAL (equivalent)"

    # MISSING: Statistics (HIGH, mandatory)
    assert "Statistics" in match_dict
    assert match_dict["Statistics"]["status"] == "MISSING"
    assert match_dict["Statistics"]["mandatory"] is True
    assert match_dict["Statistics"]["priority_bucket"] == "HIGH"

    # Top "Start here" contains Statistics, SQL, Deep Learning
    start_here = result["readiness"]["start_here"]
    assert "Statistics" in start_here
    assert "SQL" in start_here

    # Every recommendation must have an explanation
    for m in result["matches"]:
        assert "explanation" in m
        assert len(m["explanation"]) > 10

    # Roadmap generated
    assert len(result["roadmap"]["phases"]) > 0
    assert result["roadmap"]["total_hours"] > 0

# ==========================================
# 9. ML Engineer Role Verification
# ==========================================
def test_sample_profile_ml_engineer(pipeline):
    sample_text = (
        "Final-year CS student. Built projects in Python using pandas, numpy, matplotlib and sklearn. "
        "Know basic SQL from coursework. Completed a TensorFlow image classifier. "
        "Familiar with Git and Streamlit."
    )
    result = pipeline.analyze(sample_text, role_name="ML Engineer")
    assert result["success"] is True
    match_dict = {m["name"]: m for m in result["matches"]}

    # Python should be EXISTING
    assert match_dict["Python"]["status"] == "EXISTING"

    # PyTorch is required; candidate has TensorFlow -> PARTIAL (equivalent)
    assert "PyTorch" in match_dict
    assert match_dict["PyTorch"]["status"] == "PARTIAL (equivalent)"
    assert match_dict["PyTorch"]["matched_via"] == "TensorFlow"

# ==========================================
# 10. Deduplication & Conflict Resolution
# ==========================================
def test_deduplication_highest_proficiency(pipeline):
    # Candidate lists both basic and advanced Python
    profile = "Basic Python from school. Built production Python systems with high throughput."
    extracted = pipeline.extractor.extract_from_profile(profile)
    assert "Python" in extracted
    # Should resolve to the higher proficiency level (advanced)
    assert extracted["Python"]["level"] == "advanced"

# ==========================================
# 11. Custom Job Description Analysis
# ==========================================
def test_custom_job_description(pipeline):
    custom_jd = (
        "We are looking for a backend engineer. Must have strong Python and PostgreSQL. "
        "Preferred experience with Docker and AWS. Familiarity with Redis is a plus."
    )
    profile = "Experienced in Python and PostgreSQL. Basic Docker knowledge."
    result = pipeline.analyze(profile, custom_jd_text=custom_jd)
    assert result["success"] is True
    assert result["role_name"] == "Custom Job Description"

    match_dict = {m["name"]: m for m in result["matches"]}
    assert "Python" in match_dict
    assert "PostgreSQL" in match_dict
    # Python & PostgreSQL were 'Must have' -> mandatory True
    assert match_dict["Python"]["mandatory"] is True
    assert match_dict["PostgreSQL"]["mandatory"] is True

# ==========================================
# 12. Unrecognized Tokens / Typo Suggestions
# ==========================================
def test_unrecognized_token_suggestions(pipeline):
    # User lists misspelled skill 'tensoflow' or 'dockr'
    profile = "tensoflow, dockr, pythn"
    res = pipeline.analyze(profile)
    # Check unrecognized suggestions
    unrecognized = res["unrecognized_tokens"]
    suggested_map = {u["token"]: u["suggestion"] for u in unrecognized}
    assert "dockr" in suggested_map or "tensoflow" in suggested_map

# ==========================================
# 13. Multi-Role Benchmarking & Report Generation
# ==========================================
def test_multi_role_and_reports(pipeline):
    sample_text = (
        "Final-year CS student. Built projects in Python using pandas, numpy, matplotlib and sklearn. "
        "Know basic SQL from coursework. Completed a TensorFlow image classifier. "
        "Familiar with Git and Streamlit."
    )
    multi_res = pipeline.compare_multiple_roles(sample_text)
    assert len(multi_res) == 10
    # Best-fit roles are sorted descending by readiness score
    assert multi_res[0]["readiness_score"] >= multi_res[-1]["readiness_score"]

    # Test markdown report generation
    single_res = pipeline.analyze(sample_text, role_name="Data Scientist")
    md_report = pipeline.generate_markdown_report(single_res)
    assert "# Skill Gap Analysis & Learning Roadmap: Data Scientist" in md_report
    assert "Readiness Score:" in md_report
    assert "Top 'Start Here' Recommendations" in md_report
