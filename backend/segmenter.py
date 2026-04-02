"""
segmenter.py — ClauseGuard Document Segmenter

Breaks raw ToS / Privacy Policy text into meaningful clause-level chunks
suitable for per-clause risk classification.

Segmentation strategy (in order):
  1. Normalize whitespace and line endings
  2. Promote implicit paragraph boundaries (single-newline text from paste/DOM)
  3. Split on paragraph breaks (2+ blank lines) or numbered list markers
  4. Attempt to further split overly long paragraphs at sentence boundaries
     using spaCy (preferred) or a regex fallback if spaCy isn't installed
  5. Group very short sentences with adjacent ones for context
  6. Filter out navigation text, headers, and duplicate blocks

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
MIN_WORDS = 8
MAX_WORDS_BEFORE_SPLIT = 120
SENTENCE_GROUP_MIN = 12


def segment_document(text: str) -> list[str]:
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
            continue

        if word_count > MAX_WORDS_BEFORE_SPLIT:
            sentence_chunks = _split_into_sentences(block)
            clauses.extend(sentence_chunks)
        else:
            clauses.append(block)

    return _deduplicate_and_filter(clauses)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """
    Normalizes line endings, collapses whitespace, and — critically —
    promotes implicit paragraph breaks in single-newline text.

    Three sources produce single-newline text:
      - Browser copy-paste (most common)
      - Chrome extension DOM innerText extraction
      - BeautifulSoup get_text() with separator='\\n'

    All three are normalized to double-newline paragraph breaks here so
    _split_into_blocks() can reliably segment them.
    """
    # Normalize line endings
    text = re.sub(r'\r\n|\r', '\n', text)

    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.splitlines()]
    text = '\n'.join(lines)

    # ── Promote implicit paragraph breaks ──────────────────────────────────
    # These patterns reliably indicate a new clause/section in legal docs
    # even when the source only has single newlines between them.

    result_lines = []
    for i, line in enumerate(lines):
        result_lines.append(line)

        if i >= len(lines) - 1:
            continue

        next_line = lines[i + 1].strip()
        cur_stripped = line.strip()

        if not cur_stripped or not next_line:
            continue

        # Already have a blank line coming — don't double-insert
        if next_line == '':
            continue

        # Rule 1: ALL CAPS line → section header, insert break after it
        if (cur_stripped.isupper() and len(cur_stripped) > 4
                and not cur_stripped.endswith(',')
                and not cur_stripped[-1].isdigit()):
            result_lines.append('')
            continue

        # Rule 2: Next line starts a numbered/lettered section
        # e.g. "14.", "(b)", "Section 3", "Article IV"
        if re.match(
            r'^(?:\d+\.|[a-z]\.|[A-Z]\.|[ivxIVX]+\.'
            r'|\([a-z0-9]\)|Section\s+\d|Article\s+[IVXLC\d])',
            next_line
        ):
            result_lines.append('')
            continue

        # Rule 3: Current line ends a sentence AND next starts with capital
        # — strong signal of a new paragraph in paste/DOM text
        if (cur_stripped and cur_stripped[-1] in '.!?'
                and next_line[0].isupper()
                and len(cur_stripped.split()) >= 6):
            result_lines.append('')
            continue

        # Rule 4: Current line ends with colon (introduces a list/section)
        if cur_stripped.endswith(':') and len(cur_stripped.split()) >= 2:
            result_lines.append('')
            continue

    text = '\n'.join(result_lines)

    # Final collapse — the insertions above may create 3+ blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def _split_into_blocks(text: str) -> list[str]:
    """
    Splits document on paragraph boundaries and common list markers.
    """
    blocks = re.split(r'\n{2,}', text)

    refined: list[str] = []
    for block in blocks:
        sub_blocks = re.split(
            r'\n(?=\s*(?:\d+\.|[a-z]\.|[ivxIVX]+\.|\([a-z0-9]\))\s)',
            block
        )
        refined.extend(sub_blocks)

    return refined


def _split_into_sentences(text: str) -> list[str]:
    sentences = _get_sentences(text)
    return _group_short_sentences(sentences)


def _get_sentences(text: str) -> list[str]:
    try:
        import spacy  # type: ignore
        nlp = _load_spacy_model()
        if nlp:
            doc = nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    except ImportError:
        pass

    logger.debug("spaCy not available. Using regex sentence splitter.")
    return _regex_sentence_split(text)


def _load_spacy_model():
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
    abbreviations = ['Mr', 'Mrs', 'Dr', 'Prof', 'Inc', 'Ltd', 'Corp', 'Co',
                     'vs', 'etc', 'U.S', 'U.K', 'e.g', 'i.e']
    protected = text
    for abbr in abbreviations:
        protected = protected.replace(f'{abbr}.', f'{abbr}PLACEHOLDER')

    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)
    return [p.replace('PLACEHOLDER', '.').strip() for p in parts if p.strip()]


def _group_short_sentences(sentences: list[str]) -> list[str]:
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
    seen: set[str] = set()
    filtered: list[str] = []

    for clause in clauses:
        key = ' '.join(clause.lower().split())

        if key in seen:
            continue
        seen.add(key)

        if len(clause.split()) >= MIN_WORDS:
            filtered.append(clause)

    return filtered


def segment_document_numbered(text: str) -> list[dict]:
    clauses = segment_document(text)
    return [
        {"clause_number": i + 1, "text": clause}
        for i, clause in enumerate(clauses)
    ]