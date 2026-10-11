import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

class SkillNormalizer:
    """
    Normalizes arbitrary skill strings to canonical skills from skills_taxonomy.json.
    Three-tier matching:
    1. Exact canonical and alias lookup.
    2. Rapidfuzz token_set_ratio (>= 90).
    3. Sentence-Transformers cosine similarity (>= 0.80) with graceful offline fallback.
    """

    def __init__(self, taxonomy: Optional[Dict[str, Any]] = None, taxonomy_path: Optional[str] = None):
        if taxonomy is not None:
            self.taxonomy = taxonomy
        elif taxonomy_path:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                self.taxonomy = json.load(f)
        else:
            default_path = Path(__file__).resolve().parent.parent / "data" / "skills_taxonomy.json"
            with open(default_path, "r", encoding="utf-8") as f:
                self.taxonomy = json.load(f)

        self.alias_to_canonical: Dict[str, str] = {}
        self.canonical_skills: List[str] = list(self.taxonomy.keys())
        self._build_alias_map()

        self._embedder = None
        self._canonical_embeddings = None
        self._embedder_attempted = False

    def _build_alias_map(self):
        """Construct case-insensitive alias lookup map."""
        for canonical, data in self.taxonomy.items():
            norm_c = self._clean_raw_text(canonical).lower()
            self.alias_to_canonical[canonical.lower()] = canonical
            if norm_c:
                self.alias_to_canonical[norm_c] = canonical

            for alias in data.get("aliases", []):
                self.alias_to_canonical[alias.lower().strip()] = canonical
                norm_a = self._clean_raw_text(alias).lower()
                if norm_a:
                    self.alias_to_canonical[norm_a] = canonical

        # Pre-seed special common tech variants
        special_variants = {
            "reactjs": "React",
            "react.js": "React",
            "vuejs": "Vue.js" if "Vue.js" in self.taxonomy else "React",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "nextjs": "Next.js",
            "next.js": "Next.js",
            "expressjs": "Express.js",
            "express.js": "Express.js",
            "sklearn": "scikit-learn",
            "scikit learn": "scikit-learn",
            "scikit-learn": "scikit-learn",
            "golang": "Go",
            "postgres": "PostgreSQL",
            "k8s": "Kubernetes",
            "tf": "TensorFlow",
            "py": "Python",
            "ts": "TypeScript",
            "js": "JavaScript",
            "cpp": "C++",
            "c plus plus": "C++",
            "csharp": "C#",
            "c sharp": "C#",
        }
        for k, v in special_variants.items():
            if v in self.canonical_skills:
                self.alias_to_canonical[k] = v

    def _clean_raw_text(self, text: str) -> str:
        """Strip versions like 3.10, v2, .js, etc. while preserving C++, C#, CI/CD."""
        if not text:
            return ""
        s = text.strip()

        # Handle version numbers like "Python 3.10" -> "Python"
        s = re.sub(r'\s+v?\d+(\.\d+)*\b', '', s, flags=re.IGNORECASE)
        # Handle trailing version like "python3" -> "python"
        s = re.sub(r'^(python)\s*\d+$', r'\1', s, flags=re.IGNORECASE)

        # Handle specific common suffixes like .js or js
        s = re.sub(r'\.js\b', '', s, flags=re.IGNORECASE)
        if s.lower() in ["reactjs", "nodejs", "nextjs", "expressjs"]:
            s = s[:-2]

        # Strip surrounding punctuation except + and #
        s = re.sub(r'^[^\w+#]+|[^\w+#]+$', '', s)
        return s.strip()

    def _get_embedder(self):
        """Lazy load sentence transformers with fallback."""
        if self._embedder_attempted:
            return self._embedder
        self._embedder_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            # Try to load lightweight model locally or download
            model = SentenceTransformer("all-MiniLM-L6-v2")
            self._embedder = model
            self._canonical_embeddings = model.encode(self.canonical_skills, convert_to_numpy=True)
            logger.info("SentenceTransformer all-MiniLM-L6-v2 loaded successfully.")
        except Exception as e:
            logger.warning(f"SentenceTransformer not available or failed to load: {e}. Falling back to fuzzy matching.")
            self._embedder = None
            self._canonical_embeddings = None
        return self._embedder

    def normalize(self, skill_name: str) -> Tuple[Optional[str], float, str]:
        """
        Normalize skill string to (canonical_name, confidence, method).
        Methods: 'exact', 'alias', 'fuzzy', 'embedding', 'unrecognized'.
        """
        if not skill_name or not skill_name.strip():
            return None, 0.0, "unrecognized"

        raw = skill_name.strip()
        lower_raw = raw.lower()

        # 1. Exact canonical check
        if raw in self.taxonomy:
            return raw, 1.0, "exact"

        # 2. Exact alias lookup
        if lower_raw in self.alias_to_canonical:
            return self.alias_to_canonical[lower_raw], 1.0, "alias"

        # Cleaned version lookup (e.g. "Python 3.10" -> "python" -> "Python")
        cleaned = self._clean_raw_text(raw).lower()
        if cleaned in self.alias_to_canonical:
            return self.alias_to_canonical[cleaned], 0.98, "alias"

        # 3. Fuzzy matching via RapidFuzz
        try:
            from rapidfuzz import fuzz, process
            # Match against all known aliases and canonicals
            all_keys = list(self.alias_to_canonical.keys())
            match = process.extractOne(
                cleaned or lower_raw,
                all_keys,
                scorer=fuzz.token_set_ratio,
                score_cutoff=88
            )
            if match:
                matched_key, score, _ = match
                canonical = self.alias_to_canonical[matched_key]
                confidence = round(score / 100.0, 3)
                if score >= 90:
                    return canonical, confidence, "fuzzy"
                elif score >= 88:
                    # marginal fuzzy
                    return canonical, confidence, "fuzzy"
        except ImportError:
            pass

        # 4. Semantic similarity via sentence-transformers (offline fallback safe)
        embedder = self._get_embedder()
        if embedder is not None and self._canonical_embeddings is not None:
            try:
                import numpy as np
                query_vec = embedder.encode([raw], convert_to_numpy=True)[0]
                # Cosine similarity
                norm_q = np.linalg.norm(query_vec)
                norm_canon = np.linalg.norm(self._canonical_embeddings, axis=1)
                sims = np.dot(self._canonical_embeddings, query_vec) / (norm_canon * norm_q + 1e-9)

                best_idx = int(np.argmax(sims))
                best_sim = float(sims[best_idx])
                if best_sim >= 0.80:
                    return self.canonical_skills[best_idx], round(best_sim, 3), "embedding"
            except Exception as e:
                logger.debug(f"Embedding similarity calculation error: {e}")

        return None, 0.0, "unrecognized"
