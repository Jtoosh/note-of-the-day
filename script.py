import argparse
import json
import os
import random
import re
import shutil
import sys
import textwrap

import marko
from marko import block, inline

from snippet import Snippet, SnippetEncoder

NOTES_DIR = "../notesrepo"  # path to your .md files
OUT_FILE = "snippets.json"
MIN_LEN = 640  # minimum snippet length (chars)
MAX_LEN = 960  # maximum snippet length (chars)

SNIPPET_BLOCK_TYPES = (
    block.Paragraph,
    block.CodeBlock,
    block.FencedCode,
    block.List,
)


def get_markdown_files(root):
    """Recursively gather all .md files under a directory."""
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith(".md"):
                yield os.path.join(dirpath, file)


def get_node_text(node):
    """Flatten a Marko node into plain text recursively."""
    if isinstance(node, (inline.RawText, inline.CodeSpan)):
        return node.children

    if hasattr(node, "children"):
        if isinstance(node.children, str):
            return node.children
        return "".join(get_node_text(child) for child in node.children)

    return ""


def reconstruct_list(list_elem):
    """Rebuild list markdown so list item structure is preserved."""
    list_lines = []
    is_ordered = list_elem.ordered
    start_num = list_elem.start if is_ordered else 1

    for i, item in enumerate(list_elem.children):
        prefix = f"{i + start_num}. " if is_ordered else "- "
        list_item_text = get_node_text(item)
        list_lines.append(f"{prefix}{list_item_text}")

    return "\n".join(list_lines)


def get_block_text(element):
    """Extract text from a supported snippet block."""
    if isinstance(element, block.List):
        return reconstruct_list(element)
    return get_node_text(element)


def get_adjacent_text(elements, start_index, direction):
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


def parse_markdown(file_path):
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


def generate_corpus():
    all_snippets = []

    for path in get_markdown_files(NOTES_DIR):
        file_snippets = parse_markdown(path)
        all_snippets.extend(file_snippets)

    if not all_snippets:
        return "⚠️ No suitable snippets found. Try adjusting filters."

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_snippets, f, cls=SnippetEncoder, indent=4)

    return all_snippets


def pick_snippet():
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        snippet_corpus = json.load(f, object_hook=Snippet.custom_decoder)
    return random.choice(snippet_corpus)


def build_snippet_payload(snippet):
    """
    Build a UI-friendly payload for both terminal and frontend rendering.
    """
    continuation_text = ""
    if snippet.text and snippet.text[-1] == ":":
        continuation_text = snippet.next_text or ""

    return {
        "title": "Snippet of the Day",
        "source_file": snippet.file,
        "breadcrumbs": snippet.header,
        "breadcrumbs_text": " > ".join(snippet.header) if snippet.header else "",
        "text": snippet.text,
        "continuation": continuation_text,
        "previous_context": snippet.prev_text or "",
    }


def wrap_markdownish_text(text, width):
    """
    Wrap plain text while preserving markdown-like list prefixes.
    """
    wrapped_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            wrapped_lines.append("")
            continue

        # Preserve indentation-based formatting (e.g., code blocks).
        if line.startswith(("    ", "\t")):
            wrapped_lines.append(line)
            continue

        bullet_match = re.match(r"^(\s*(?:[-*+]|\d+\.)\s+)(.+)$", line)
        if bullet_match:
            prefix, content = bullet_match.groups()
            wrapped = textwrap.fill(
                content,
                width=width,
                initial_indent=prefix,
                subsequent_indent=" " * len(prefix),
            )
        else:
            wrapped = textwrap.fill(line.strip(), width=width)

        wrapped_lines.extend(wrapped.splitlines())

    return "\n".join(wrapped_lines)


def render_terminal_snippet(payload, width=None):
    """
    Render the snippet as a readable terminal card.
    """
    terminal_width = shutil.get_terminal_size((100, 24)).columns
    card_width = width or min(max(72, terminal_width), 110)
    body_width = max(40, card_width - 4)

    sections = []
    sections.append("=" * card_width)
    sections.append(payload["title"].center(card_width))
    sections.append("-" * card_width)
    sections.append(f"Source: {payload['source_file']}")

    if payload["breadcrumbs_text"]:
        sections.append(f"Path:   {payload['breadcrumbs_text']}")

    sections.append("-" * card_width)
    sections.append(wrap_markdownish_text(payload["text"], body_width))

    if payload["continuation"]:
        sections.append("")
        sections.append("[Continuation]")
        sections.append(wrap_markdownish_text(payload["continuation"], body_width))

    sections.append("=" * card_width)
    return "\n".join(sections)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Generate or display a note snippet.")
    parser.add_argument(
        "-generate",
        action="store_true",
        help="Regenerate snippets.json from markdown files before selecting a snippet.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the selected snippet.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Optional card width for text output.",
    )
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)

    if args.generate:
        generate_corpus()

    snippet = pick_snippet()
    payload = build_snippet_payload(snippet)

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_terminal_snippet(payload, width=args.width))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
