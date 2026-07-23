"""Suggest [[wiki-link]] candidates between semantically-close, currently
unlinked files, per specs/2026-07-20-link-suggestion-tool/SPEC.md.

Per D2: aggregation is a per-file centroid (mean-pool of that file's existing
chunk vectors), not chunk-pair max-pool -- reuses the same embeddings at a
fraction of the cost (561^2 file pairs vs 11,536^2 chunk pairs at current
scale) and stays cheap as the corpus grows, since file count grows far slower
than chunk count.

Per D5: "already linked" is parsed from the already-loaded index's chunk
text (grouped by file), not a fresh disk read -- avoids an unaccounted
second full-vault I/O pass and keeps both signals (links, similarity)
sourced from the same last-reindex() snapshot.

Per D6: wiki-link target resolution is case-insensitive basename matching,
fail-open on zero or multiple matches -- a false "already linked" (wrongly
suppressing a real gap) is a worse failure than an occasional redundant
suggestion.

This module never writes to any file (NG4, inherited from the base spec's
Decision 6) -- it only reads the in-memory index and returns suggestions.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath

import numpy as np

from reports_rag_mcp.search import Index

SUGGESTION_THRESHOLD = 0.5

# Template/boilerplate exclusion (D7, added after first live validation run):
# tailored resumes all share one master template re-angled per company, so
# they score 0.97-1.0 against each other -- indistinguishable by threshold
# from genuine connections, and dominated the first real suggest_links()
# output (14 of top 15 results). Confirmed via direct corpus check: all 95
# files matching "resume" case-insensitively use this exact naming
# convention (HeeGun-Eom-Resume-<Company>.md), 0 exceptions -- so a precise
# basename substring match, not a broad heuristic.
_TEMPLATE_EXCLUDE_RE = re.compile(r"Resume-")

# Captures the link target up to the first `]`, `|`, or `#`, so it handles
# [[Target]], [[Target|Display]], [[Target#Heading]], and the combined
# [[Target#Heading|Display]] form uniformly (D6, completeness re-sweep).
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


@dataclass(frozen=True)
class LinkSuggestion:
    file_a: str
    file_b: str
    score: float


def _group_by_file(metadata: list[dict]) -> dict[str, list[int]]:
    """Map each file path to the indices of its chunks in metadata/vectors.

    Files matching the template-exclusion pattern (D7) are dropped here, so
    they never enter centroid computation or appear in any suggestion.
    """
    groups: dict[str, list[int]] = defaultdict(list)
    for i, entry in enumerate(metadata):
        file_path = entry["file"]
        if _TEMPLATE_EXCLUDE_RE.search(PurePosixPath(file_path).name):
            continue
        groups[file_path].append(i)
    return groups


def _compute_centroids(
    file_to_indices: dict[str, list[int]], vectors: np.ndarray
) -> tuple[list[str], np.ndarray]:
    """Mean-pool each file's chunk vectors into one centroid (D2)."""
    file_paths = sorted(file_to_indices)  # deterministic order
    dim = vectors.shape[1] if vectors.size else 0
    centroids = np.zeros((len(file_paths), dim), dtype=np.float32)
    for i, file_path in enumerate(file_paths):
        centroids[i] = vectors[file_to_indices[file_path]].mean(axis=0)
    return file_paths, centroids


def _resolve_target(target: str, file_paths: list[str]) -> str | None:
    """Resolve a wiki-link target to an indexed file path.

    Tries a full relative-path match first (case-insensitive, `.md` optional
    -- needed for links like `[[folder/REPORT]]`, which is exactly what a
    fail-open-aware writer uses when a bare basename would be ambiguous,
    e.g. any of the 53 files literally named REPORT.md), then falls back to
    a bare-basename match (for links like `[[APPLICATIONS]]`). Fail-open
    (D6) at each tier: zero or multiple matches return None (unresolved)
    rather than guessing -- an unresolved target risks a redundant
    suggestion, never a silently suppressed real one.
    """
    needle = target.strip().lower()

    path_matches = [fp for fp in file_paths if fp.lower() in (needle, f"{needle}.md")]
    if len(path_matches) == 1:
        return path_matches[0]
    if len(path_matches) > 1:
        return None

    basename_matches = [fp for fp in file_paths if PurePosixPath(fp).stem.lower() == needle]
    return basename_matches[0] if len(basename_matches) == 1 else None


def _build_linked_pairs(
    file_to_indices: dict[str, list[int]], metadata: list[dict], file_paths: list[str]
) -> set[frozenset[str]]:
    """Scan each file's already-loaded chunk text for [[links]] (D5) and
    resolve them to an undirected set of already-linked file pairs (D6).
    """
    linked: set[frozenset[str]] = set()
    for file_path, indices in file_to_indices.items():
        combined_text = "\n".join(metadata[i]["text"] for i in indices)
        for match in _WIKILINK_RE.finditer(combined_text):
            resolved = _resolve_target(match.group(1), file_paths)
            if resolved is not None and resolved != file_path:
                linked.add(frozenset({file_path, resolved}))
    return linked


def suggest_links(
    index: Index, top_k: int = 10, threshold: float = SUGGESTION_THRESHOLD
) -> list[LinkSuggestion]:
    """Rank candidate [[link]] pairs between semantically-close, currently
    unlinked files. See module docstring for the aggregation/resolution
    decisions this implements. Files matching the template-exclusion
    pattern (D7) are never considered, on either side of a pair.
    """
    metadata = index._metadata  # noqa: SLF001 -- same-package access, Index is a plain data holder
    vectors = index._vectors  # noqa: SLF001

    if len(metadata) == 0:
        return []

    file_to_indices = _group_by_file(metadata)
    file_paths, centroids = _compute_centroids(file_to_indices, vectors)
    linked_pairs = _build_linked_pairs(file_to_indices, metadata, file_paths)

    norms = centroids / (np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-10)
    sim_matrix = norms @ norms.T

    n = len(file_paths)
    candidates: list[LinkSuggestion] = []
    for i in range(n):
        for j in range(i + 1, n):  # i<j: excludes self-pairs, dedupes symmetric pairs
            score = float(sim_matrix[i, j])
            if score < threshold:
                continue
            if frozenset({file_paths[i], file_paths[j]}) in linked_pairs:
                continue
            candidates.append(LinkSuggestion(file_a=file_paths[i], file_b=file_paths[j], score=score))

    candidates.sort(key=lambda c: -c.score)
    return candidates[:top_k]
