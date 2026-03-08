"""
segmenter.py — ClauseGuard Document Segmenter

Breaks raw ToS / Privacy Policy text into meaningful clause-level chunks
suitable for per-clause risk classification.

Segmentation strategy (in order):
  1. Normalize whitespace and line endings
  2. Split on paragraph breaks (2+ blank lines) or numbered list markers
  3. Attempt to further split overly long paragraphs at sentence boundaries
     using spaCy (preferred) or a regex fallback if spaCy isn't installed
  4. Group very short sentences with adjacent ones for context
  5. Filter out navigation text, headers, and duplicate blocks

Why not just split on every sentence?
  ToS clauses are legal statements that often span 2-4 sentences. Splitting
  too finely loses the context needed for accurate classification. Splitting
  too broadly lumps unrelated clauses together. The grouping logic below
  aims for chunks of roughly 15–80 words.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Tuning constants
MIN_WORDS = 8          # Shorter chunks are likely headers or noise
MAX_WORDS_BEFORE_SPLIT = 120   # Paragraphs longer than this get sentence-split
SENTENCE_GROUP_MIN = 12        # Sentences shorter than this get merged with neighbors


def segment_document(text: str) -> list[str]:
    """
    Main entry point. Takes raw document text, returns a list of clause strings.

    Args:
        text: Full text of a ToS or Privacy Policy document.

    Returns:
        List of clause strings, each representing a meaningful unit of legal text.
    """
    if not text or not text.strip():
        return []

    text = _normalize_text(text)
    raw_blocks = _split_into_blocks(text)

    clauses: list[str] = []
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        word_count = len(block.split())

        if word_count < MIN_WORDS:
            # Too short to be meaningful — likely a heading or nav element
            continue

        if word_count > MAX_WORDS_BEFORE_SPLIT:
            # Too long — break into sentence-level chunks
            sentence_chunks = _split_into_sentences(block)
            clauses.extend(sentence_chunks)
        else:
            clauses.append(block)

    return _deduplicate_and_filter(clauses)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Normalizes line endings and collapses excessive whitespace."""
    # Normalize line endings
    text = re.sub(r'\r\n|\r', '\n', text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing whitespace on each line
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return text


def _split_into_blocks(text: str) -> list[str]:
    """
    Splits document on paragraph boundaries and common list markers.
    These are the natural "section" boundaries in legal documents.
    """
    # Primary split: double newline (paragraph break)
    blocks = re.split(r'\n{2,}', text)

    refined: list[str] = []
    for block in blocks:
        # Secondary split: numbered or lettered list items acting as sub-clauses
        # e.g., "1. You agree...\n2. We may..." or "(a) ...\n(b) ..."
        sub_blocks = re.split(r'\n(?=\s*(?:\d+\.|[a-z]\.|[ivxIVX]+\.|\([a-z0-9]\))\s)', block)
        refined.extend(sub_blocks)

    return refined


def _split_into_sentences(text: str) -> list[str]:
    """
    Splits a long paragraph into sentence-level chunks.
    Prefers spaCy for accuracy; falls back to regex if unavailable.
    Groups short consecutive sentences to maintain clause context.
    """
    sentences = _get_sentences(text)
    return _group_short_sentences(sentences)


def _get_sentences(text: str) -> list[str]:
    """Attempts sentence splitting with spaCy, falls back to regex."""
    try:
        import spacy  # type: ignore
        # Load a small model (user must run: python -m spacy download en_core_web_sm)
        nlp = _load_spacy_model()
        if nlp:
            doc = nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    except ImportError:
        pass  # spaCy not installed — use fallback

    logger.debug("spaCy not available. Using regex sentence splitter.")
    return _regex_sentence_split(text)


def _load_spacy_model():
    """Loads spaCy model, returns None on failure."""
    try:
        import spacy  # type: ignore
        return spacy.load("en_core_web_sm")
    except OSError:
        logger.warning(
            "spaCy model 'en_core_web_sm' not found. "
            "Run: python -m spacy download en_core_web_sm"
        )
        return None


def _regex_sentence_split(text: str) -> list[str]:
    """
    Regex-based sentence splitter.
    Handles common abbreviations (e.g., U.S., Inc., etc.) to avoid false splits.
    """
    # Protect common abbreviations from being split on
    abbreviations = ['Mr', 'Mrs', 'Dr', 'Prof', 'Inc', 'Ltd', 'Corp', 'Co',
                     'vs', 'etc', 'U.S', 'U.K', 'e.g', 'i.e']
    protected = text
    for abbr in abbreviations:
        protected = protected.replace(f'{abbr}.', f'{abbr}PLACEHOLDER')

    # Split on sentence-ending punctuation followed by whitespace + capital
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)

    # Restore abbreviations
    return [p.replace('PLACEHOLDER', '.').strip() for p in parts if p.strip()]


def _group_short_sentences(sentences: list[str]) -> list[str]:
    """
    Merges consecutive short sentences to form meaningful clause-level chunks.
    A sentence shorter than SENTENCE_GROUP_MIN words is merged with the next.
    """
    if not sentences:
        return []

    grouped: list[str] = []
    buffer: str = ""

    for sentence in sentences:
        word_count = len(sentence.split())
        if not buffer:
            buffer = sentence
        elif len(buffer.split()) < SENTENCE_GROUP_MIN or word_count < SENTENCE_GROUP_MIN:
            buffer = buffer + " " + sentence
        else:
            grouped.append(buffer.strip())
            buffer = sentence

    if buffer:
        grouped.append(buffer.strip())

    return [g for g in grouped if len(g.split()) >= MIN_WORDS]


def _deduplicate_and_filter(clauses: list[str]) -> list[str]:
    """
    Removes duplicate clauses and filters out noise.
    Deduplication is case-insensitive and ignores extra whitespace.
    """
    seen: set[str] = set()
    filtered: list[str] = []

    for clause in clauses:
        # Normalize for dedup comparison
        key = ' '.join(clause.lower().split())

        if key in seen:
            continue
        seen.add(key)

        # Final length check
        if len(clause.split()) >= MIN_WORDS:
            filtered.append(clause)

    return filtered
