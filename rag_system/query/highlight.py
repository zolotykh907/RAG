import re
from difflib import SequenceMatcher


def _split_sentences(text):
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_ngrams(sentence, min_n=3, max_n=6):
    """Extract word n-grams from a sentence."""
    words = sentence.split()
    if len(words) < min_n:
        return [sentence] if len(words) >= 2 else []

    ngrams = []
    for n in range(max_n, min_n - 1, -1):
        for i in range(len(words) - n + 1):
            ngrams.append(' '.join(words[i:i + n]))
    return ngrams


def _find_fuzzy_match(ngram, source_text, threshold=0.7):
    """Find the best fuzzy match for an n-gram in source text.

    Returns (start, end) character offsets or None if no match above threshold.
    """
    ngram_lower = ngram.lower()
    source_lower = source_text.lower()
    ngram_len = len(ngram_lower)

    # Try exact match first (fast path)
    pos = source_lower.find(ngram_lower)
    if pos != -1:
        return pos, pos + ngram_len

    # Sliding window fuzzy match
    best_ratio = 0
    best_start = -1
    best_end = -1

    window_sizes = [ngram_len, int(ngram_len * 1.2), int(ngram_len * 0.8)]

    for window_size in window_sizes:
        if window_size > len(source_lower) or window_size < 5:
            continue
        step = max(1, window_size // 4)
        for i in range(0, len(source_lower) - window_size + 1, step):
            candidate = source_lower[i:i + window_size]
            ratio = SequenceMatcher(None, ngram_lower, candidate).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i
                best_end = i + window_size

    if best_ratio >= threshold:
        return best_start, best_end
    return None


def _merge_ranges(ranges):
    """Merge overlapping or adjacent ranges."""
    if not ranges:
        return []

    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]

    for start, end in sorted_ranges[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 5:  # merge if overlapping or within 5 chars
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def find_highlights(answer, source_texts):
    """Find fragments in source texts that were used to generate the answer.

    Args:
        answer: LLM-generated answer string.
        source_texts: list of source text chunks.

    Returns:
        list of lists, one per source text. Each inner list contains
        dicts with 'start' and 'end' character offsets.
    """
    if not answer or not source_texts:
        return [[] for _ in source_texts]

    sentences = _split_sentences(answer)

    all_highlights = []

    for source in source_texts:
        if not source:
            all_highlights.append([])
            continue

        ranges = []

        for sentence in sentences:
            ngrams = _extract_ngrams(sentence)

            for ngram in ngrams:
                if len(ngram) < 8:
                    continue
                match = _find_fuzzy_match(ngram, source)
                if match:
                    ranges.append(match)

        merged = _merge_ranges(ranges)

        # Filter out very short highlights (less than 10 chars)
        merged = [(s, e) for s, e in merged if e - s >= 10]

        all_highlights.append([{"start": s, "end": e} for s, e in merged])

    return all_highlights
