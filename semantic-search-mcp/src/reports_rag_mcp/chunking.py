"""Chunk markdown files by heading section, per SPEC.md Decision #4.

Files with headings are split at each heading boundary. Sections longer than
CHUNK_WORD_CAP are further split into fixed-size word windows. Files with no
headings at all (e.g. daily notes) fall back to fixed-size chunking over the
whole file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CHUNK_WORD_CAP = 600
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    file_path: str  # path relative to the vault root, forward-slash separated
    heading: str  # nearest enclosing heading text, or the filename stem if none
    text: str


def _split_into_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown content into (heading, section_text) pairs.

    Content before the first heading (if any) is grouped under heading "".
    A file with zero headings yields a single ("", content) section.
    """
    lines = content.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def _split_into_word_windows(text: str, cap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    return [
        " ".join(words[i : i + cap]) for i in range(0, len(words), cap)
    ]


def chunk_markdown(content: str, file_path: str) -> list[Chunk]:
    """Chunk a single markdown file's content into heading-scoped chunks."""
    stem = Path(file_path).stem
    sections = _split_into_sections(content)

    if not sections:
        return []

    chunks: list[Chunk] = []
    for heading, section_text in sections:
        if not section_text.strip():
            continue
        display_heading = heading if heading else stem
        word_count = len(section_text.split())
        if word_count <= CHUNK_WORD_CAP:
            chunks.append(Chunk(file_path=file_path, heading=display_heading, text=section_text))
        else:
            for window in _split_into_word_windows(section_text, CHUNK_WORD_CAP):
                chunks.append(Chunk(file_path=file_path, heading=display_heading, text=window))

    return chunks


def chunk_file(path: Path, vault_root: Path) -> list[Chunk]:
    """Read and chunk a single file on disk, path relative to vault_root."""
    content = path.read_text(encoding="utf-8", errors="replace")
    rel_path = path.relative_to(vault_root).as_posix()
    return chunk_markdown(content, rel_path)
