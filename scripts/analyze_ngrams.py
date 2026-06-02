"""N-gram analysis of ordine-zi item descriptions.

A deterministic, wordcloud-style tool that tokenizes Romanian parliamentary text,
removes stopwords, and surfaces the most common n-gram phrases. Useful for:
  - Discovering formulaic patterns not yet covered by regex extraction
  - Detecting drift in legislative language over time
  - Validating the existing entity taxonomy

Usage:
    PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024
    PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --ngram 3 --top 80
    PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --compare  # extracted vs unextracted diff
    PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --words    # single-word topical frequencies
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Romanian stopwords (curated for parliamentary context) ──────────────

RO_STOPWORDS: set[str] = {
    # Function words (closed class)
    "de", "la", "și", "în", "din", "cu", "pe", "se", "nu", "ca", "o", "un", "sau",
    "a", "al", "ai", "ale", "lui", "lor", "unui", "unei", "unor",
    "către", "pentru", "privind", "asupra",
    "acest", "această", "acestei", "acestui", "aceste", "acestor",
    "sunt", "este", "fi", "fost", "fiind", "era", "erau",
    "vor", "va", "au", "am", "ar",
    "mai", "mult", "doar", "însă", "dar", "sau", "ori",
    "partea", "precum", "respectiv",
    # Procedural boilerplate (not topical)
    "data", "prezentării", "biroul", "permanent",
    "termenul", "constituțional", "dezbatere", "vot",
    "potrivit", "regulamentului", "constituției",
    "documente", "casetele", "deputaților",
    "inițiate", "inițiată", "inițiat", "distribuit", "distribuirea",
    "art", "alin",
    # High-frequency parliamentary structure words
    "proiectul", "lege", "legea", "legii", "hotărâre", "hotărârea",
    "propunerea", "legislativă", "ordonanței", "ordonanța",
    "urgență", "guvernului",
    "aprobarea", "modificarea", "completarea",
    "nr", "pl-x", "ph", "cd",
    "raport", "raportul", "comun",
    "comisia", "comisiei",
    "adoptat", "senat", "organică", "ordinară",
    "procedură", "decizională", "cameră",
    "româniei", "românia",
}


def _normalize_ro(text: str) -> str:
    """Normalize Romanian diacritics to comma-below (canonical) form."""
    return (
        text.replace("ş", "ș").replace("Ş", "Ș")
        .replace("ţ", "ț").replace("Ţ", "Ț")
    )


def _strip_html(html: str) -> str:
    """Strip HTML tags, converting <br> to newline."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _tokenize(text: str, stopwords: set[str] | None = None) -> list[str]:
    """Tokenize Romanian text for n-gram analysis.

    Handles diacritics, camelCase/missing-space boundaries (e.g. "urgențăCameră"),
    and filters stopwords + short tokens.
    """
    if stopwords is None:
        stopwords = RO_STOPWORDS

    text = _normalize_ro(text)
    # Insert space at lower→upper boundaries (fixes "urgențăCameră" → "urgență Cameră")
    text = re.sub(r"(?<=[a-zăâîșț0-9])(?=[A-ZĂÂÎȘȚ])", " ", text)
    text = text.lower()

    tokens = re.findall(r"[a-zăâîșț0-9]+(?:-[a-zăâîșț0-9]+)*", text)
    return [t for t in tokens if t not in stopwords and len(t) > 3]


def _extract_ngrams(tokens: list[str], n: int) -> list[str]:
    """Extract n-grams from a token list."""
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _load_descriptions(leg: int) -> list[tuple[str, bool]]:
    """Load item descriptions from ordine-zi JSON.

    Returns list of (plain_text, has_entities) tuples.
    """
    path = Path(f"data/v1/ordine-zi/legislatura-{leg}.json")
    if not path.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    results: list[tuple[str, bool]] = []
    for session in data.get("data", []):
        for item in session.get("items", []):
            desc = item.get("descriere", "") or ""
            plain = _strip_html(desc)
            has_entities = item.get("entities") is not None
            results.append((plain, has_entities))
    return results


# ── Commands ────────────────────────────────────────────────────────────


def cmd_ngrams(descs: list[str], n: int, top: int) -> None:
    """Print top-N n-grams across all descriptions."""
    all_tokens = [_tokenize(d) for d in descs]
    counter: Counter[str] = Counter()
    for tokens in all_tokens:
        counter.update(_extract_ngrams(tokens, n))

    header = {2: "BIGRAMS", 3: "TRIGRAMS", 4: "4-GRAMS"}
    label = header.get(n, f"{n}-GRAMS")
    print(f"\n{'=' * 70}")
    print(f"TOP {top} {label}  ({len(descs)} items)")
    print(f"{'=' * 70}\n")
    for phrase, count in counter.most_common(top):
        bar = "█" * min(count // 20, 60)
        print(f"  {count:5d}  {phrase:<50s} {bar}")


def cmd_words(descs: list[str], top: int) -> None:
    """Print top single-word frequencies (topical nouns only)."""
    all_tokens: list[str] = []
    for d in descs:
        all_tokens.extend(_tokenize(d))

    counter = Counter(all_tokens)
    print(f"\n{'=' * 70}")
    print(f"TOP {top} TOPICAL SINGLE WORDS  ({len(descs)} items)")
    print(f"{'=' * 70}\n")
    for word, count in counter.most_common(top):
        print(f"  {count:5d}  {word}")


def cmd_compare(extracted: list[str], unextracted: list[str], n: int, top: int) -> None:
    """Compare n-gram frequencies: extracted vs unextracted items.

    Shows two views:
      1. N-grams over-represented in unextracted (possible regex gaps)
      2. N-grams unique to unextracted (never seen in extracted items)
    """
    ext_tokens = [_tokenize(d) for d in extracted]
    unx_tokens = [_tokenize(d) for d in unextracted]

    ext_ngrams: Counter[str] = Counter()
    for tokens in ext_tokens:
        ext_ngrams.update(_extract_ngrams(tokens, n))

    unx_ngrams: Counter[str] = Counter()
    for tokens in unx_tokens:
        unx_ngrams.update(_extract_ngrams(tokens, n))

    label = {2: "bigram", 3: "trigram", 4: "4-gram"}.get(n, f"{n}-gram")

    # ── Over-represented in unextracted ──
    print(f"\n{'=' * 70}")
    print(f"{label.upper()}S OVER-REPRESENTED IN UNEXTRACTED ITEMS")
    print(f"(ratio = unextracted / extracted, min 5 in unextracted)")
    print(f"{'=' * 70}\n")

    ratios: list[tuple[str, int, int, float]] = []
    for ng, unx_count in unx_ngrams.most_common(200):
        ext_count = ext_ngrams.get(ng, 1)
        if unx_count >= 5:
            ratios.append((ng, unx_count, ext_count, unx_count / ext_count))
    ratios.sort(key=lambda x: -x[3])

    for ng, unx_c, ext_c, ratio in ratios[:top]:
        flag = " ⚠️ NEW" if ext_c <= 2 else ""
        print(f"  {unx_c:4d}/{ext_c:<4d}  (×{ratio:.1f})   {ng}{flag}")

    # ── Unique to unextracted ──
    unique = [(ng, c) for ng, c in unx_ngrams.most_common(300) if ext_ngrams.get(ng, 0) == 0]
    if unique:
        print(f"\n{'=' * 70}")
        print(f"{label.upper()}S UNIQUE TO UNEXTRACTED (0 occurrences in extracted)")
        print(f"{'=' * 70}\n")
        for ng, c in unique[:top]:
            print(f"  {c:4d}  {ng}")


# ── CLI ─────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="N-gram analysis of ordine-zi item descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024
  PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --ngram 4 --top 40
  PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --words
  PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --compare
        """,
    )
    parser.add_argument("--leg", type=int, default=2024, help="Legislatura (default: 2024)")
    parser.add_argument("--ngram", "-n", type=int, default=2, choices=[2, 3, 4],
                        help="N-gram size: 2=bigrams, 3=trigrams, 4=4-grams (default: 2)")
    parser.add_argument("--top", "-t", type=int, default=50,
                        help="Number of results to show (default: 50)")
    parser.add_argument("--words", "-w", action="store_true",
                        help="Show single-word topical frequencies instead of n-grams")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Compare extracted vs. unextracted items (gap analysis)")
    args = parser.parse_args()

    items = _load_descriptions(args.leg)
    print(f"Loaded {len(items)} items from legislatura-{args.leg}")

    if args.compare:
        extracted = [d for d, has_e in items if has_e]
        unextracted = [d for d, has_e in items if not has_e]
        print(f"  with entities:    {len(extracted)}")
        print(f"  without entities: {len(unextracted)}")
        cmd_compare(extracted, unextracted, args.ngram, args.top)
    elif args.words:
        cmd_words([d for d, _ in items], args.top)
    else:
        cmd_ngrams([d for d, _ in items], args.ngram, args.top)


if __name__ == "__main__":
    main()
