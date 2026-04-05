"""
BRaaS Pipeline Stage 1 - NLP Intake Engine.

Parses natural language experiment requests using regex and keyword matching.
No external LLM dependency — purely rule-based extraction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from braas.core.enums import (
    ExperimentType,
    IntentType,
    Organism,
    SampleType,
)
from braas.core.models import IntakeRequest, IntakeResult, ParsedEntity


class NLPIntakeEngine:
    """
    Natural Language Processing engine for experiment intake.

    Uses regex patterns and keyword matching to extract structured
    experiment specifications from free-text research requests.
    """

    # ── Keyword Dictionaries ───────────────────────────────────────────

    EXPERIMENT_KEYWORDS: Dict[ExperimentType, List[str]] = {
        ExperimentType.ELISA: [
            "elisa", "enzyme-linked immunosorbent", "sandwich assay",
            "competitive elisa", "direct elisa", "indirect elisa",
        ],
        ExperimentType.QPCR: [
            "qpcr", "rt-pcr", "real-time pcr", "quantitative pcr",
            "real time pcr", "reverse transcription pcr", "taqman",
            "sybr green", "gene expression",
        ],
        ExperimentType.WESTERN_BLOT: [
            "western blot", "western-blot", "immunoblot", "immuno-blot",
            "protein blot", "sds-page", "sds page",
        ],
        ExperimentType.CELL_CULTURE: [
            "cell culture", "cell line", "passage", "transfection",
            "cell growth", "cell viability", "mtt assay", "proliferation",
            "confluency", "subculture",
        ],
        ExperimentType.FLOW_CYTOMETRY: [
            "flow cytometry", "facs", "cell sorting", "flow analysis",
        ],
        ExperimentType.IMMUNOFLUORESCENCE: [
            "immunofluorescence", "immunostaining", "if staining",
            "fluorescence microscopy", "confocal",
        ],
        ExperimentType.MASS_SPECTROMETRY: [
            "mass spectrometry", "mass spec", "ms/ms", "proteomics",
            "lc-ms", "maldi",
        ],
        ExperimentType.RNA_SEQ: [
            "rna-seq", "rna seq", "rnaseq", "transcriptomics",
            "differential expression", "bulk rna",
        ],
        ExperimentType.CRISPR: [
            "crispr", "cas9", "gene editing", "guide rna", "grna",
            "knockout", "knock-out", "gene ko",
        ],
        ExperimentType.CLONING: [
            "cloning", "ligation", "transformation", "plasmid",
            "restriction digest", "gibson assembly",
        ],
        ExperimentType.PROTEIN_PURIFICATION: [
            "protein purification", "his-tag", "affinity chromatography",
            "column purification", "ni-nta", "gst pulldown",
        ],
    }

    ORGANISM_KEYWORDS: Dict[Organism, List[str]] = {
        Organism.HUMAN: [
            "human", "homo sapiens", "h. sapiens", "hek293", "hela",
            "jurkat", "patient", "clinical",
        ],
        Organism.MOUSE: [
            "mouse", "murine", "mus musculus", "m. musculus", "balb/c",
            "c57bl", "nod",
        ],
        Organism.RAT: [
            "rat", "rattus", "r. norvegicus", "sprague", "wistar",
        ],
        Organism.RABBIT: [
            "rabbit", "oryctolagus", "bunny",
        ],
        Organism.E_COLI: [
            "e. coli", "e.coli", "escherichia", "bacteria", "bacterial",
            "bl21", "dh5a", "top10",
        ],
        Organism.YEAST: [
            "yeast", "saccharomyces", "s. cerevisiae", "pichia",
        ],
        Organism.DROSOPHILA: [
            "drosophila", "fruit fly", "fly",
        ],
        Organism.ZEBRAFISH: [
            "zebrafish", "danio rerio", "d. rerio",
        ],
        Organism.C_ELEGANS: [
            "c. elegans", "c.elegans", "nematode", "worm",
        ],
    }

    SAMPLE_KEYWORDS: Dict[SampleType, List[str]] = {
        SampleType.SERUM: ["serum"],
        SampleType.PLASMA: ["plasma"],
        SampleType.WHOLE_BLOOD: ["whole blood", "blood"],
        SampleType.TISSUE: ["tissue", "biopsy", "organ"],
        SampleType.CELL_LYSATE: ["cell lysate", "lysate", "lysis"],
        SampleType.CELL_SUSPENSION: ["cell suspension", "suspended cells"],
        SampleType.RNA: ["rna", "mrna", "total rna"],
        SampleType.DNA: ["dna", "genomic dna", "cdna"],
        SampleType.PROTEIN: ["protein", "protein extract", "total protein"],
        SampleType.SUPERNATANT: ["supernatant", "conditioned medium", "conditioned media"],
        SampleType.URINE: ["urine"],
        SampleType.CSF: ["csf", "cerebrospinal fluid", "spinal fluid"],
    }

    INTENT_PATTERNS: Dict[IntentType, List[str]] = {
        IntentType.NEW_EXPERIMENT: [
            r"\b(run|perform|do|conduct|set up|start|begin|initiate)\b",
            r"\b(i want to|i need to|we want to|we need to|please)\b.*\b(measure|detect|quantif|analyz)\b",
        ],
        IntentType.REPEAT_EXPERIMENT: [
            r"\b(repeat|replicate|redo|re-run|rerun)\b",
            r"\b(same experiment|again|another round)\b",
        ],
        IntentType.OPTIMIZATION: [
            r"\b(optimiz|improv|enhanc|better|fine.?tune|titrat)\b",
            r"\b(increase|decrease|adjust|tweak)\b.*\b(sensitivity|signal|yield)\b",
        ],
        IntentType.TROUBLESHOOTING: [
            r"\b(troubleshoot|debug|fix|problem|issue|not working|failed)\b",
            r"\b(high background|no signal|low signal|nonspecific|contamina)\b",
        ],
        IntentType.COMPARISON: [
            r"\b(compar|versus|vs\.?|difference between|head.?to.?head)\b",
        ],
        IntentType.SCREENING: [
            r"\b(screen|high.?throughput|hts|library|panel)\b",
        ],
    }

    # ── Protein name patterns ──────────────────────────────────────────

    PROTEIN_PATTERNS: List[str] = [
        r"\b(IL-?\d+[a-zA-Z]?)\b",           # Interleukins: IL-6, IL-1beta
        r"\b(TNF-?[αβa-z]*)\b",               # TNF-alpha, TNFa
        r"\b(IFN-?[αβγa-z]*)\b",              # Interferons
        r"\b(TGF-?[αβa-z]\d*)\b",             # TGF-beta
        r"\b(VEGF[A-D]?)\b",                   # VEGF
        r"\b(EGF[R]?)\b",                      # EGF/EGFR
        r"\b(p\d{2,3})\b",                     # p53, p21
        r"\b(Bcl-?\d*)\b",                     # Bcl-2
        r"\b(CD\d{1,3}[a-z]?)\b",             # CD markers
        r"\b(GFP|RFP|YFP|mCherry)\b",         # Fluorescent proteins
        r"\b(GAPDH|actin|tubulin|histone)\b",  # Housekeeping
        r"\b(caspase-?\d*)\b",                 # Caspases
        r"\b(ERK|JNK|AKT|mTOR|MAPK)\b",       # Kinases
        r"\b(BRCA[12]?|TP53|KRAS|MYC)\b",     # Oncogenes/tumor suppressors
        r"\b(HER2|PD-?L?\d?|CTLA-?\d)\b",     # Immune checkpoints
        r"\b(insulin|albumin|hemoglobin|collagen)\b",  # Common proteins
        r"\b([A-Z]{2,5}\d{0,2})\b",           # Generic gene symbols (fallback)
    ]

    # Regex for numeric counts
    COUNT_PATTERNS: List[str] = [
        r"(\d+)\s*(?:samples?|wells?|replicates?|plates?|reactions?|tubes?)",
        r"(?:n\s*=\s*)(\d+)",
        r"(\d+)\s*(?:biological|technical)\s*replicates?",
        r"(?:triplicate|in triplicate)",
        r"(?:duplicate|in duplicate)",
    ]

    SPECIAL_REQUIREMENT_KEYWORDS: List[str] = [
        "sterile", "rnase-free", "dnase-free", "endotoxin-free",
        "low-binding", "ice", "cold", "4 degrees", "4°c", "37°c",
        "room temperature", "dark", "light-sensitive", "hypoxia",
        "serum-free", "antibiotic-free", "time course", "dose response",
        "dose-response", "serial dilution", "overnight", "kinetic",
        "endpoint", "multiplex", "high throughput", "low volume",
    ]

    def __init__(self) -> None:
        """Initialize the NLP intake engine with compiled patterns."""
        self._compiled_protein_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PROTEIN_PATTERNS[:-1]
        ]
        # Generic gene symbol pattern compiled separately (lower priority)
        self._generic_gene_pattern = re.compile(
            self.PROTEIN_PATTERNS[-1]
        )

    async def parse_request(self, request: IntakeRequest) -> IntakeResult:
        """
        Parse a natural language experiment request into structured data.

        Args:
            request: The raw intake request containing free-text description.

        Returns:
            IntakeResult with extracted experiment parameters.
        """
        text = request.raw_text.strip()
        text_lower = text.lower()

        # Extract all entities
        entities = await self.extract_entities(text)

        # Classify intent
        intent, intent_confidence = await self.classify_intent(text)

        # Extract specific fields
        experiment_type = self._extract_experiment_type(text_lower)
        organism = self._extract_organism(text_lower)
        sample_type = self._extract_sample_type(text_lower)
        target_protein = self._extract_target_protein(text)
        sample_count = self._extract_sample_count(text_lower)
        special_reqs = self._extract_special_requirements(text_lower)

        # Calculate overall confidence
        field_scores = [
            1.0 if experiment_type != ExperimentType.UNKNOWN else 0.0,
            1.0 if organism != Organism.UNKNOWN else 0.0,
            1.0 if sample_type != SampleType.UNKNOWN else 0.0,
            1.0 if target_protein else 0.0,
            intent_confidence,
        ]
        overall_confidence = sum(field_scores) / len(field_scores)

        return IntakeResult(
            request_id=request.id,
            intent=intent,
            experiment_type=experiment_type,
            target_protein=target_protein,
            organism=organism,
            sample_type=sample_type,
            sample_count=sample_count,
            special_requirements=special_reqs,
            entities=entities,
            confidence=round(overall_confidence, 3),
            raw_text=text,
        )

    async def extract_entities(self, text: str) -> List[ParsedEntity]:
        """
        Extract all named entities from the input text.

        Args:
            text: Raw input text.

        Returns:
            List of ParsedEntity objects found in the text.
        """
        entities: List[ParsedEntity] = []
        text_lower = text.lower()

        # Extract experiment type entities
        for exp_type, keywords in self.EXPERIMENT_KEYWORDS.items():
            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                for match in pattern.finditer(text):
                    entities.append(ParsedEntity(
                        entity_type="experiment_type",
                        value=exp_type.value,
                        confidence=0.95,
                        span=(match.start(), match.end()),
                    ))

        # Extract organism entities
        for org, keywords in self.ORGANISM_KEYWORDS.items():
            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                for match in pattern.finditer(text):
                    entities.append(ParsedEntity(
                        entity_type="organism",
                        value=org.value,
                        confidence=0.9,
                        span=(match.start(), match.end()),
                    ))

        # Extract sample type entities
        for stype, keywords in self.SAMPLE_KEYWORDS.items():
            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                for match in pattern.finditer(text):
                    entities.append(ParsedEntity(
                        entity_type="sample_type",
                        value=stype.value,
                        confidence=0.9,
                        span=(match.start(), match.end()),
                    ))

        # Extract protein entities
        for pat in self._compiled_protein_patterns:
            for match in pat.finditer(text):
                entities.append(ParsedEntity(
                    entity_type="protein",
                    value=match.group(1),
                    confidence=0.85,
                    span=(match.start(), match.end()),
                ))

        # Extract numeric values
        number_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*(µl|ul|ml|µg|ug|mg|ng|pg|nm|µm|mm|hours?|hrs?|minutes?|min|°c|celsius)",
            re.IGNORECASE,
        )
        for match in number_pattern.finditer(text):
            entities.append(ParsedEntity(
                entity_type="measurement",
                value=f"{match.group(1)} {match.group(2)}",
                confidence=0.95,
                span=(match.start(), match.end()),
            ))

        return entities

    async def classify_intent(self, text: str) -> Tuple[IntentType, float]:
        """
        Classify the user's intent from the input text.

        Args:
            text: Raw input text.

        Returns:
            Tuple of (IntentType, confidence_score).
        """
        text_lower = text.lower()
        scores: Dict[IntentType, float] = {
            intent: 0.0 for intent in IntentType
        }

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                matches = pattern.findall(text_lower)
                if matches:
                    scores[intent] += len(matches) * 0.3

        # Find best intent
        best_intent = max(scores, key=scores.get)  # type: ignore
        best_score = scores[best_intent]

        if best_score == 0.0:
            return IntentType.NEW_EXPERIMENT, 0.3  # default assumption

        # Normalize score to [0, 1]
        confidence = min(best_score, 1.0)
        return best_intent, round(confidence, 3)

    # ── Private Extraction Methods ─────────────────────────────────────

    def _extract_experiment_type(self, text_lower: str) -> ExperimentType:
        """Match experiment type from text using keyword scoring."""
        scores: Dict[ExperimentType, float] = {}

        for exp_type, keywords in self.EXPERIMENT_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    # Longer keyword matches are more specific
                    score += len(keyword.split()) * 0.5
            if score > 0:
                scores[exp_type] = score

        if not scores:
            return ExperimentType.UNKNOWN

        return max(scores, key=scores.get)  # type: ignore

    def _extract_organism(self, text_lower: str) -> Organism:
        """Extract organism from text."""
        for org, keywords in self.ORGANISM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return org
        return Organism.UNKNOWN

    def _extract_sample_type(self, text_lower: str) -> SampleType:
        """Extract sample type from text."""
        # Check multi-word keywords first (more specific)
        all_matches: List[Tuple[SampleType, int]] = []
        for stype, keywords in self.SAMPLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    all_matches.append((stype, len(keyword)))

        if not all_matches:
            return SampleType.UNKNOWN

        # Return the most specific (longest keyword) match
        all_matches.sort(key=lambda x: x[1], reverse=True)
        return all_matches[0][0]

    def _extract_target_protein(self, text: str) -> Optional[str]:
        """Extract target protein/gene name from text."""
        # Try specific protein patterns first
        for pat in self._compiled_protein_patterns:
            match = pat.search(text)
            if match:
                return match.group(1)

        # Fallback: look for "target X" or "protein X" patterns
        target_pattern = re.compile(
            r"(?:target|protein|gene|marker|analyte|antigen|antibody(?:\s+against)?)\s+(\w+)",
            re.IGNORECASE,
        )
        match = target_pattern.search(text)
        if match:
            candidate = match.group(1)
            # Filter out common non-protein words
            stopwords = {
                "is", "the", "a", "an", "in", "on", "at", "for", "of",
                "and", "or", "with", "from", "to", "using", "expression",
                "level", "levels", "concentration",
            }
            if candidate.lower() not in stopwords:
                return candidate

        return None

    def _extract_sample_count(self, text_lower: str) -> int:
        """Extract sample count from text."""
        # Check for triplicate/duplicate first
        if "triplicate" in text_lower:
            return 3
        if "duplicate" in text_lower:
            return 2

        for pattern_str in self.COUNT_PATTERNS:
            match = re.search(pattern_str, text_lower)
            if match:
                try:
                    groups = match.groups()
                    if groups:
                        return int(groups[0])
                except (ValueError, IndexError):
                    continue

        return 1  # default

    def _extract_special_requirements(self, text_lower: str) -> List[str]:
        """Extract special requirements from text."""
        found: List[str] = []
        for req in self.SPECIAL_REQUIREMENT_KEYWORDS:
            if req in text_lower:
                found.append(req)
        return found
