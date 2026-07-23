import numpy as np

from reports_rag_mcp.linking import SUGGESTION_THRESHOLD, suggest_links
from reports_rag_mcp.search import Index


def _make_index(entries: list[tuple[str, str, str, list[float]]]) -> Index:
    metadata = [
        {"file": file, "heading": heading, "text": text}
        for file, heading, text, _ in entries
    ]
    vectors = np.array([vec for *_rest, vec in entries], dtype=np.float32)
    return Index(metadata, vectors)


def test_suggests_similar_unlinked_files():
    index = _make_index(
        [
            ("a.md", "A", "no links here", [1.0, 0.0]),
            ("b.md", "B", "no links here either", [0.9, 0.1]),
        ]
    )

    results = suggest_links(index, threshold=0.0)

    assert len(results) == 1
    assert {results[0].file_a, results[0].file_b} == {"a.md", "b.md"}


def test_excludes_already_linked_pairs():
    index = _make_index(
        [
            ("a.md", "A", "see also [[b]]", [1.0, 0.0]),
            ("b.md", "B", "no links here", [0.9, 0.1]),
        ]
    )

    results = suggest_links(index, threshold=0.0)

    assert results == []


def test_recognizes_all_wikilink_syntax_variants():
    variants = ["[[b]]", "[[b|Display Name]]", "[[b#Heading]]", "[[b#Heading|Display]]"]
    for variant in variants:
        index = _make_index(
            [
                ("a.md", "A", f"see also {variant}", [1.0, 0.0]),
                ("b.md", "B", "no links here", [0.9, 0.1]),
            ]
        )
        assert suggest_links(index, threshold=0.0) == [], f"variant {variant} not recognized as a link"


def test_recognizes_full_path_links_not_just_bare_basenames():
    # A link written as the full relative path (e.g. because the writer
    # avoided an ambiguous bare basename) must still be recognized as a
    # real link -- this was a real bug: the resolver originally only ever
    # checked the basename/stem, so [[folder/target]]-style links were
    # silently never matched, and an already-linked pair kept getting
    # re-suggested.
    index = _make_index(
        [
            ("folder-a/report.md", "R", "see also [[folder-b/report]]", [1.0, 0.0]),
            ("folder-b/report.md", "R", "unrelated", [0.99, 0.01]),
        ]
    )

    assert suggest_links(index, threshold=0.0) == []


def test_fail_open_on_ambiguous_basename():
    # Two files share the basename "report" across different folders --
    # a link to [[report]] must not be resolved to either one (D6).
    index = _make_index(
        [
            ("topic-a/report.md", "R", "see also [[report]]", [1.0, 0.0]),
            ("topic-b/report.md", "R", "unrelated content", [0.0, 1.0]),
            ("c.md", "C", "close to topic-a's report", [0.95, 0.05]),
        ]
    )

    results = suggest_links(index, threshold=0.5)

    # The ambiguous [[report]] link must not suppress the genuine
    # similarity between topic-a/report.md and c.md.
    pairs = [{r.file_a, r.file_b} for r in results]
    assert {"topic-a/report.md", "c.md"} in pairs


def test_filters_results_below_threshold():
    index = _make_index(
        [
            ("a.md", "A", "text", [1.0, 0.0]),
            ("b.md", "B", "unrelated", [0.0, 1.0]),
        ]
    )

    results = suggest_links(index, threshold=0.9)

    assert results == []


def test_default_threshold_matches_spec_decision_3():
    assert SUGGESTION_THRESHOLD == 0.5


def test_excludes_self_pairs_and_dedupes_symmetric_pairs():
    index = _make_index(
        [
            ("a.md", "A", "chunk one", [1.0, 0.0]),
            ("a.md", "A2", "chunk two, same file", [1.0, 0.0]),
            ("b.md", "B", "similar text", [0.95, 0.05]),
        ]
    )

    results = suggest_links(index, threshold=0.0)

    pairs = [{r.file_a, r.file_b} for r in results]
    assert {"a.md"} not in pairs  # no file ever paired with itself
    assert pairs.count({"a.md", "b.md"}) == 1  # counted once, not twice


def test_multi_chunk_file_uses_centroid_not_single_chunk():
    # a.md has one chunk pointing at b.md and one pointing away; the
    # centroid should land in between, not match b.md at full strength.
    index = _make_index(
        [
            ("a.md", "A1", "matches b closely", [1.0, 0.0]),
            ("a.md", "A2", "points elsewhere entirely", [0.0, 1.0]),
            ("b.md", "B", "target", [1.0, 0.0]),
        ]
    )

    results = suggest_links(index, threshold=0.0)
    pair = next(r for r in results if {r.file_a, r.file_b} == {"a.md", "b.md"})

    assert pair.score < 1.0  # centroid dilutes the single strong chunk match


def test_respects_top_k_limit():
    entries = [(f"{i}.md", f"H{i}", "text", [1.0, 0.0]) for i in range(10)]
    index = _make_index(entries)

    results = suggest_links(index, top_k=3, threshold=0.0)

    assert len(results) == 3


def test_empty_index_returns_empty_list():
    index = Index(metadata=[], vectors=np.zeros((0, 2), dtype=np.float32))

    assert suggest_links(index) == []


def test_single_file_returns_empty_list():
    index = _make_index([("a.md", "A", "only one file, nothing to pair", [1.0, 0.0])])

    assert suggest_links(index, threshold=0.0) == []


def test_excludes_template_files_from_both_sides_of_a_pair():
    # Two tailored resumes score ~identically by design (same master
    # template) -- must never surface as a suggestion (D7).
    index = _make_index(
        [
            ("resume-2026/HeeGun-Eom-Resume-Acme.md", "R", "resume text", [1.0, 0.0]),
            ("resume-2026/HeeGun-Eom-Resume-Zenith.md", "R", "resume text", [0.99, 0.01]),
            ("c.md", "C", "a genuine report, not a resume", [0.98, 0.02]),
        ]
    )

    results = suggest_links(index, threshold=0.0)

    pairs = [{r.file_a, r.file_b} for r in results]
    assert not any("Resume-" in f for pair in pairs for f in pair)
    # c.md should still get suggestions against non-excluded files if any existed;
    # here it's alone, so results should be empty, not error.
    assert results == []
