import json
import os
from typing import Any, Iterator, List, Sequence, Tuple, Union

import marko
from marko import block, inline

from snippet import Snippet, SnippetEncoder

SNIPPET_BLOCK_TYPES: Tuple[type, ...] = (
    block.Paragraph,
    block.CodeBlock,
    block.FencedCode,
    block.List,
)


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


def parse_markdown(file_path: str) -> List[Snippet]:
    """Parse a markdown file into snippet objects."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    document = marko.parse(text)
    elements = document.children

    doc_snippets = []
    heading_stack = []
    filename = os.path.basename(file_path)

    for i, element in enumerate(elements):
        if isinstance(element, block.Heading):
            header_text = get_node_text(element)
            level = element.level

            # Keep all higher-level headings and replace any same/lower level trail.
            heading_stack = heading_stack[: level - 1] + [header_text]
            continue

        if not isinstance(element, SNIPPET_BLOCK_TYPES):
            continue

        content_text = get_block_text(element).strip()
        if not content_text:
            continue

        prev_text = get_adjacent_text(elements, i, -1)
        next_text = get_adjacent_text(elements, i, 1)

        # Copy heading_stack so each snippet keeps its own heading context.
        snippet = Snippet(content_text, heading_stack.copy(), filename, prev_text, next_text)
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
