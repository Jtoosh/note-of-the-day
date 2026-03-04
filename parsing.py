import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterator, List, Sequence, Set, Tuple, Union

import marko
from marko import block, inline

from snippet import Snippet, SnippetEncoder

SNIPPET_BLOCK_TYPES: Tuple[type, ...] = (
    block.Paragraph,
    block.CodeBlock,
    block.FencedCode,
    block.List,
)
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
CONNECTOR_PREFIXES = (
    "and ",
    "or ",
    "but ",
    "because ",
    "so ",
    "then ",
    "also ",
    "this ",
    "these ",
    "those ",
    "it ",
    "they ",
)
MIN_SNIPPET_CHARS = 220
MAX_SNIPPET_CHARS = 680


@dataclass(frozen=True)
class ContentBlock:
    """Normalized parse block used to build context-aware snippets."""

    text: str
    header: Tuple[str, ...]
    source_index: int


def get_markdown_files(root: str) -> Iterator[str]:
    """Recursively gather all .md files under a directory."""
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith(".md"):
                yield os.path.join(dirpath, file)


def get_node_text(node: Any) -> str:
    """Flatten a Marko node into plain text recursively."""
    if isinstance(node, (inline.RawText, inline.CodeSpan)):
        return node.children

    if hasattr(node, "children"):
        if isinstance(node.children, str):
            return node.children
        return "".join(get_node_text(child) for child in node.children)

    return ""


def reconstruct_list(list_elem: block.List) -> str:
    """Rebuild list markdown so list item structure is preserved."""
    list_lines = []
    is_ordered = list_elem.ordered
    start_num = list_elem.start if is_ordered else 1

    for i, item in enumerate(list_elem.children):
        prefix = f"{i + start_num}. " if is_ordered else "- "
        list_item_text = get_node_text(item)
        list_lines.append(f"{prefix}{list_item_text}")

    return "\n".join(list_lines)


def get_block_text(element: Any) -> str:
    """Extract text from a supported snippet block."""
    if isinstance(element, block.List):
        return reconstruct_list(element)
    return get_node_text(element)


def get_adjacent_text(elements: Sequence[Any], start_index: int, direction: int) -> str:
    """
    Return nearest non-blank sibling text in the requested direction.

    Headings are treated as boundaries (structural context, not content context),
    so they return an empty string.
    """
    index = start_index + direction

    while 0 <= index < len(elements) and isinstance(elements[index], block.BlankLine):
        index += direction

    if index < 0 or index >= len(elements):
        return ""

    neighbor = elements[index]
    if isinstance(neighbor, block.Heading):
        return ""

    return get_block_text(neighbor)


def to_content_blocks(elements: Sequence[Any]) -> List[ContentBlock]:
    """
    Convert Marko top-level elements into normalized content blocks with heading context.
    """
    heading_stack: List[str] = []
    content_blocks: List[ContentBlock] = []

    for i, element in enumerate(elements):
        if isinstance(element, block.Heading):
            header_text = get_node_text(element)
            level = element.level
            heading_stack = heading_stack[: level - 1] + [header_text]
            continue

        if not isinstance(element, SNIPPET_BLOCK_TYPES):
            continue

        text = get_block_text(element).strip()
        if not text:
            continue

        content_blocks.append(
            ContentBlock(
                text=text,
                header=tuple(heading_stack),
                source_index=i,
            )
        )

    return content_blocks


def is_same_section(content_blocks: Sequence[ContentBlock], left: int, right: int) -> bool:
    """Keep context windows inside the same heading path."""
    return content_blocks[left].header == content_blocks[right].header


def needs_leading_context(text: str) -> bool:
    """
    Heuristic: include leading context for bullets, numbered steps, and continuation phrasing.
    """
    if not text:
        return False

    first_line = text.splitlines()[0].strip()
    if not first_line:
        return False

    lowered = first_line.lower()
    if LIST_PREFIX_RE.match(first_line):
        return True
    if lowered.startswith(CONNECTOR_PREFIXES):
        return True
    if first_line[0].islower():
        return True
    return False


def needs_trailing_context(text: str) -> bool:
    """Heuristic: include trailing context for setup lines that imply follow-up content."""
    if not text:
        return False
    stripped = text.rstrip()
    return stripped.endswith(":")


def expand_context_window(content_blocks: Sequence[ContentBlock], anchor_index: int) -> Tuple[int, int]:
    """
    Build a deterministic context window around an anchor block.

    Rules:
    1. Expand to satisfy structural cues (list/setup lines).
    2. Expand further until snippet reaches a minimum useful length.
    3. Never exceed MAX_SNIPPET_CHARS and never cross heading boundaries.
    """
    left = anchor_index
    right = anchor_index
    total_chars = len(content_blocks[anchor_index].text)
    anchor_text = content_blocks[anchor_index].text

    if needs_leading_context(anchor_text) and left > 0 and is_same_section(content_blocks, left - 1, left):
        candidate = content_blocks[left - 1]
        if total_chars + len(candidate.text) <= MAX_SNIPPET_CHARS:
            left -= 1
            total_chars += len(candidate.text)

    if needs_trailing_context(anchor_text) and right + 1 < len(content_blocks):
        if is_same_section(content_blocks, right, right + 1):
            candidate = content_blocks[right + 1]
            if total_chars + len(candidate.text) <= MAX_SNIPPET_CHARS:
                right += 1
                total_chars += len(candidate.text)

    while total_chars < MIN_SNIPPET_CHARS:
        left_candidate_index = left - 1
        right_candidate_index = right + 1

        left_candidate = None
        if left_candidate_index >= 0 and is_same_section(content_blocks, left_candidate_index, left):
            left_candidate = content_blocks[left_candidate_index]

        right_candidate = None
        if right_candidate_index < len(content_blocks) and is_same_section(content_blocks, right, right_candidate_index):
            right_candidate = content_blocks[right_candidate_index]

        if left_candidate is None and right_candidate is None:
            break

        # Deterministic tie-breaker: prefer the shorter neighbor, then left side.
        choose_left = False
        if left_candidate and right_candidate:
            if len(left_candidate.text) <= len(right_candidate.text):
                choose_left = True
        elif left_candidate:
            choose_left = True

        chosen = left_candidate if choose_left else right_candidate
        if chosen is None:
            break

        if total_chars + len(chosen.text) > MAX_SNIPPET_CHARS:
            break

        if choose_left:
            left -= 1
        else:
            right += 1

        total_chars += len(chosen.text)

    return left, right


def parse_markdown(file_path: str) -> List[Snippet]:
    """
    Parse a markdown file into context-aware snippets.

    Each content block is treated as an anchor, then expanded into a deterministic
    context window so snippets are understandable in isolation.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    document = marko.parse(text)
    content_blocks = to_content_blocks(document.children)
    doc_snippets: List[Snippet] = []
    seen_snippets: Set[Tuple[Tuple[str, ...], str]] = set()
    filename = os.path.basename(file_path)

    for anchor_index, anchor_block in enumerate(content_blocks):
        left, right = expand_context_window(content_blocks, anchor_index)
        snippet_text = "\n\n".join(block_item.text for block_item in content_blocks[left : right + 1])

        dedupe_key = (anchor_block.header, snippet_text)
        if dedupe_key in seen_snippets:
            continue
        seen_snippets.add(dedupe_key)

        prev_text = ""
        if left > 0 and is_same_section(content_blocks, left - 1, left):
            prev_text = content_blocks[left - 1].text

        next_text = ""
        if right + 1 < len(content_blocks) and is_same_section(content_blocks, right, right + 1):
            next_text = content_blocks[right + 1].text

        snippet = Snippet(
            text=snippet_text,
            header=list(anchor_block.header),
            file=filename,
            prev_text=prev_text,
            next_text=next_text,
        )
        doc_snippets.append(snippet)

    return doc_snippets


def generate_corpus(notes_dir: str, out_file: str) -> Union[List[Snippet], str]:
    all_snippets: List[Snippet] = []

    for path in get_markdown_files(notes_dir):
        file_snippets = parse_markdown(path)
        all_snippets.extend(file_snippets)

    if not all_snippets:
        return "⚠️ No suitable snippets found. Try adjusting filters."

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_snippets, f, cls=SnippetEncoder, indent=4)

    return all_snippets
