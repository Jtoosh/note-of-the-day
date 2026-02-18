import json
import re
import shutil
import textwrap
from typing import Any, Dict, Optional

from snippet import Snippet


def build_snippet_payload(snippet: Snippet) -> Dict[str, Any]:
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


def wrap_markdownish_text(text: str, width: int) -> str:
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


def render_terminal_snippet(payload: Dict[str, Any], width: Optional[int] = None) -> str:
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


def render_json_snippet(payload: Dict[str, Any]) -> str:
    """Serialize snippet payload for frontend/widget consumption."""
    return json.dumps(payload, indent=2, ensure_ascii=False)
