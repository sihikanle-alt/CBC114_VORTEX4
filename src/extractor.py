import re
import io
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from .normalizer import SkillNormalizer

logger = logging.getLogger(__name__)

LEVEL_ORDER = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3
}

ADVANCED_KEYWORDS = [
    r"\bexpert\b", r"\bproduction\b", r"\bbuilt\b", r"\b\d+\+?\s*years?\b",
    r"\bsenior\b", r"\blead\b", r"\badvanced\b", r"\bdeployed\b",
    r"\barchitected\b", r"\bmastery\b", r"\bproficient\b"
]

BEGINNER_KEYWORDS = [
    r"\bfamiliar\b", r"\bbasic\b", r"\bcoursework\b", r"\bbeginner\b",
    r"\bintroductory\b", r"\bnovice\b", r"\blearning\b", r"\bexposure\b"
]

MANDATORY_JD_KEYWORDS = [
    r"\bmust\b", r"\bmust have\b", r"\brequired\b", r"\brequirement\b",
    r"\bessential\b", r"\bmandatory\b", r"\bkey requirement\b", r"\bminimum\b",
    r"\bnecessary\b", r"\bcore\b"
]

PREFERRED_JD_KEYWORDS = [
    r"\bpreferred\b", r"\bnice to have\b", r"\bplus\b", r"\bbonus\b",
    r"\boptional\b", r"\bgood to have\b", r"\bdesired\b", r"\badvantage\b"
]

class SkillExtractor:
    """
    Extracts skills from text (free-text resume, skills list, job descriptions)
    using spaCy PhraseMatcher / regex fallback, determines proficiency levels,
    and extracts JD importance/mandatory flags.
    """

    def __init__(self, normalizer: Optional[SkillNormalizer] = None):
        self.normalizer = normalizer or SkillNormalizer()
        self.taxonomy = self.normalizer.taxonomy
        self.nlp = None
        self.matcher = None
        self._init_spacy_matcher()

    def _init_spacy_matcher(self):
        """Initialize spaCy PhraseMatcher with fallback to blank model or regex."""
        try:
            import spacy
            from spacy.matcher import PhraseMatcher
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                # Fallback to blank english model with sentencizer
                self.nlp = spacy.blank("en")
                if "sentencizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("sentencizer")
            
            self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            # Register canonical and aliases
            patterns = []
            for canonical, data in self.taxonomy.items():
                patterns.append(self.nlp.make_doc(canonical))
                for alias in data.get("aliases", []):
                    if len(alias.strip()) > 1:
                        patterns.append(self.nlp.make_doc(alias.strip()))
            self.matcher.add("SKILLS", patterns)
            logger.info("spaCy PhraseMatcher initialized.")
        except Exception as e:
            logger.warning(f"spaCy initialization failed ({e}), using regex matching.")
            self.nlp = None
            self.matcher = None

    def _infer_proficiency(self, context_text: str, skill_term: Optional[str] = None) -> str:
        """Analyze surrounding sentence or clause to detect beginner / intermediate / advanced."""
        ctx = context_text.lower()

        # If a skill term is provided, focus on the clause containing the skill
        if skill_term:
            skill_low = skill_term.lower()
            # Split by clauses (e.g. semicolons, commas, or periods)
            clauses = re.split(r'[;\n]+', ctx)
            for clause in clauses:
                if skill_low in clause:
                    ctx = clause
                    break

        has_adv = any(re.search(kw, ctx) for kw in ADVANCED_KEYWORDS)
        has_beg = any(re.search(kw, ctx) for kw in BEGINNER_KEYWORDS)

        if has_adv and not has_beg:
            return "advanced"
        elif has_beg and not has_adv:
            return "beginner"
        elif has_adv and has_beg:
            # Check which keyword is closest to skill_term if provided
            if skill_term and skill_term.lower() in ctx:
                pos = ctx.find(skill_term.lower())
                adv_dist = min([abs(m.start() - pos) for kw in ADVANCED_KEYWORDS for m in [re.search(kw, ctx)] if m] or [999])
                beg_dist = min([abs(m.start() - pos) for kw in BEGINNER_KEYWORDS for m in [re.search(kw, ctx)] if m] or [999])
                return "advanced" if adv_dist < beg_dist else "beginner"
            return "advanced"

        return "intermediate"

    def _infer_jd_skill_properties(self, context_text: str) -> Tuple[float, bool, str]:
        """Infer (importance, mandatory, level) from JD context."""
        ctx = context_text.lower()
        mandatory = False
        importance = 0.7

        for kw in MANDATORY_JD_KEYWORDS:
            if re.search(kw, ctx):
                mandatory = True
                importance = 1.0
                break

        if not mandatory:
            for kw in PREFERRED_JD_KEYWORDS:
                if re.search(kw, ctx):
                    mandatory = False
                    importance = 0.5
                    break

        # Level inference
        if any(w in ctx for w in ["expert", "senior", "lead", "advanced", "5+ years", "extensive"]):
            level = "advanced"
        elif any(w in ctx for w in ["junior", "entry", "intern", "basic", "fundamental"]):
            level = "beginner"
        else:
            level = "intermediate"

        return importance, mandatory, level

    def extract_from_profile(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract user skills from profile text or comma-separated list.
        Returns: {canonical_name: {"level": str, "source_text": str, "method": str, "confidence": float}}
        Deduplicates by keeping highest proficiency level.
        """
        if not text or not text.strip():
            return {}

        results: Dict[str, Dict[str, Any]] = {}
        cleaned_text = text.strip()

        # Strategy 1: spaCy PhraseMatcher
        if self.nlp and self.matcher:
            doc = self.nlp(cleaned_text)
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                match_str = span.text
                canonical, conf, method = self.normalizer.normalize(match_str)
                if canonical:
                    # Scope context to the specific sentence containing the match
                    context_str = ""
                    try:
                        context_str = span.sent.text.strip()
                    except Exception:
                        pass

                    if not context_str:
                        # Use character offsets in text
                        s_char = span.start_char
                        e_char = span.end_char
                        p1 = cleaned_text.rfind('.', 0, s_char)
                        p2 = cleaned_text.rfind('\n', 0, s_char)
                        start_pos = max(0, max(p1, p2) + 1)

                        n1 = cleaned_text.find('.', e_char)
                        n2 = cleaned_text.find('\n', e_char)
                        candidates_end = [idx for idx in [n1, n2] if idx != -1]
                        end_pos = min(candidates_end) if candidates_end else len(cleaned_text)

                        context_str = cleaned_text[start_pos:end_pos].strip()

                    level = self._infer_proficiency(context_str, match_str)

                    self._add_or_update_skill(results, canonical, level, match_str, method, conf)

        # Strategy 2: Comma or line separated list & Regex fallback check
        # Handles inputs like "Python, React, SQL, sklearn"
        tokens = [t.strip() for t in re.split(r'[,;\n•\t|]+', cleaned_text) if t.strip()]
        for token in tokens:
            # Check if this token matches a skill
            if len(token) <= 45:
                canonical, conf, method = self.normalizer.normalize(token)
                if canonical:
                    level = self._infer_proficiency(token)
                    self._add_or_update_skill(results, canonical, level, token, method, conf)

        # Strategy 3: Regex word boundary search for canonical and aliases if no match found
        if not results:
            for canonical, data in self.taxonomy.items():
                all_names = [canonical] + data.get("aliases", [])
                for name in all_names:
                    pattern = rf'\b{re.escape(name)}\b'
                    m = re.search(pattern, cleaned_text, re.IGNORECASE)
                    if m:
                        # Extract window around match
                        start_pos = max(0, m.start() - 60)
                        end_pos = min(len(cleaned_text), m.end() + 60)
                        ctx = cleaned_text[start_pos:end_pos]
                        level = self._infer_proficiency(ctx)
                        self._add_or_update_skill(results, canonical, level, m.group(0), "regex", 0.95)

        return results

    def _add_or_update_skill(self, results: Dict[str, Dict[str, Any]], canonical: str,
                             level: str, source_text: str, method: str, conf: float):
        """Add skill or keep the one with higher proficiency level."""
        if canonical not in results:
            results[canonical] = {
                "name": canonical,
                "level": level,
                "source_text": source_text,
                "method": method,
                "confidence": conf
            }
        else:
            existing_level = results[canonical]["level"]
            if LEVEL_ORDER.get(level, 2) > LEVEL_ORDER.get(existing_level, 2):
                results[canonical]["level"] = level
                results[canonical]["source_text"] = source_text

    def extract_from_jd(self, jd_text: str) -> List[Dict[str, Any]]:
        """
        Extract required skills from custom JD text.
        Returns list of {"name": canonical, "importance": float, "mandatory": bool, "level": str}
        """
        if not jd_text or not jd_text.strip():
            return []

        skills_map: Dict[str, Dict[str, Any]] = {}

        # Look sentence by sentence to infer context
        sentences = re.split(r'[.\n;]+', jd_text)
        for sentence in sentences:
            s_clean = sentence.strip()
            if not s_clean:
                continue

            extracted_in_sentence = set()
            # Token search and normalizer
            for canonical, data in self.taxonomy.items():
                all_names = [canonical] + data.get("aliases", [])
                for name in all_names:
                    if re.search(rf'\b{re.escape(name)}\b', s_clean, re.IGNORECASE):
                        extracted_in_sentence.add(canonical)
                        break

            for canon in extracted_in_sentence:
                importance, mandatory, level = self._infer_jd_skill_properties(s_clean)
                if canon not in skills_map:
                    skills_map[canon] = {
                        "name": canon,
                        "importance": importance,
                        "mandatory": mandatory,
                        "level": level
                    }
                else:
                    # Upgrade if sentence had higher importance or mandatory
                    if mandatory:
                        skills_map[canon]["mandatory"] = True
                        skills_map[canon]["importance"] = max(skills_map[canon]["importance"], importance)
                    if LEVEL_ORDER.get(level, 2) > LEVEL_ORDER.get(skills_map[canon]["level"], 2):
                        skills_map[canon]["level"] = level

        return list(skills_map.values())

    def extract_from_file(self, file_bytes: bytes, filename: str) -> str:
        """Extract plain text from uploaded .txt or .pdf file."""
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_parts = []
                for page in pdf_reader.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
                return "\n".join(text_parts)
            except Exception as e:
                logger.error(f"Failed to parse PDF: {e}")
                return ""
        else:
            # Assume text or markdown
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="ignore")
