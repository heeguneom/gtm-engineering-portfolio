from reports_rag_mcp.chunking import chunk_markdown, CHUNK_WORD_CAP


def test_splits_at_each_heading():
    content = "# Title\nintro text\n\n## Section A\nfirst section body\n\n## Section B\nsecond section body\n"
    chunks = chunk_markdown(content, "doc.md")

    headings = [c.heading for c in chunks]
    assert headings == ["Title", "Section A", "Section B"]
    assert "first section body" in chunks[1].text
    assert "second section body" in chunks[2].text


def test_headless_file_falls_back_to_filename_and_single_chunk():
    content = "Just plain notes with no headings at all.\nSecond line.\n"
    chunks = chunk_markdown(content, "2026-07-15.md")

    assert len(chunks) == 1
    assert chunks[0].heading == "2026-07-15"
    assert "plain notes" in chunks[0].text


def test_empty_file_produces_no_chunks():
    assert chunk_markdown("", "empty.md") == []
    assert chunk_markdown("   \n\n  ", "whitespace.md") == []


def test_long_section_splits_into_word_capped_windows():
    # The heading line itself ("# Big Section" -> 3 words) is part of the
    # section text before splitting, so the remainder is 50 + 3 = 53 words.
    words = " ".join(f"word{i}" for i in range(CHUNK_WORD_CAP * 2 + 50))
    content = f"# Big Section\n{words}\n"
    chunks = chunk_markdown(content, "long.md")

    assert len(chunks) == 3
    assert all(c.heading == "Big Section" for c in chunks)
    assert len(chunks[0].text.split()) <= CHUNK_WORD_CAP
    assert len(chunks[1].text.split()) <= CHUNK_WORD_CAP
    # last window holds the remainder (50 body words + 3-word heading line)
    assert len(chunks[2].text.split()) == 53


def test_short_section_is_not_split():
    content = "# Short\njust a few words here\n"
    chunks = chunk_markdown(content, "short.md")

    assert len(chunks) == 1
    assert chunks[0].heading == "Short"


def test_content_before_first_heading_uses_filename_as_heading():
    content = "preamble text before any heading\n\n## Real Section\nbody\n"
    chunks = chunk_markdown(content, "notes.md")

    assert chunks[0].heading == "notes"
    assert "preamble" in chunks[0].text
    assert chunks[1].heading == "Real Section"


def test_file_path_is_preserved_on_every_chunk():
    content = "# A\nbody a\n\n# B\nbody b\n"
    chunks = chunk_markdown(content, "sub/dir/doc.md")

    assert all(c.file_path == "sub/dir/doc.md" for c in chunks)
