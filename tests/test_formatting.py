import json
import unittest

from formatting import (
    build_snippet_payload,
    render_json_snippet,
    render_terminal_snippet,
    wrap_markdownish_text,
)
from snippet import Snippet


class FormattingTests(unittest.TestCase):
    def test_build_snippet_payload_includes_continuation_for_colon_suffix(self) -> None:
        snippet = Snippet(
            text="Key commands:",
            header=["CS 260", "Shell"],
            file="notes.md",
            prev_text="Some previous context",
            next_text="- ls\n- cat",
        )

        payload = build_snippet_payload(snippet)

        self.assertEqual(payload["title"], "Snippet of the Day")
        self.assertEqual(payload["source_file"], "notes.md")
        self.assertEqual(payload["breadcrumbs"], ["CS 260", "Shell"])
        self.assertEqual(payload["breadcrumbs_text"], "CS 260 > Shell")
        self.assertEqual(payload["text"], "Key commands:")
        self.assertEqual(payload["continuation"], "- ls\n- cat")
        self.assertEqual(payload["previous_context"], "Some previous context")

    def test_build_snippet_payload_omits_continuation_when_not_colon_terminated(self) -> None:
        snippet = Snippet(
            text="A complete sentence.",
            header=[],
            file="notes.md",
            prev_text=None,
            next_text="should not be used",
        )

        payload = build_snippet_payload(snippet)

        self.assertEqual(payload["breadcrumbs_text"], "")
        self.assertEqual(payload["continuation"], "")
        self.assertEqual(payload["previous_context"], "")

    def test_wrap_markdownish_text_preserves_bullet_prefix(self) -> None:
        wrapped = wrap_markdownish_text("- this is a long bullet entry", width=12)
        wrapped_lines = wrapped.splitlines()

        self.assertTrue(wrapped_lines[0].startswith("- "))
        self.assertGreater(len(wrapped_lines), 1)
        self.assertTrue(wrapped_lines[1].startswith("  "))

    def test_render_terminal_snippet_contains_sections_and_continuation(self) -> None:
        payload = {
            "title": "Snippet of the Day",
            "source_file": "notes.md",
            "breadcrumbs": ["Course", "Week 1"],
            "breadcrumbs_text": "Course > Week 1",
            "text": "Key commands:",
            "continuation": "- ls\n- cat",
            "previous_context": "",
        }

        output = render_terminal_snippet(payload, width=80)

        self.assertIn("Snippet of the Day", output)
        self.assertIn("Source: notes.md", output)
        self.assertIn("Path:   Course > Week 1", output)
        self.assertIn("[Continuation]", output)
        self.assertIn("- ls", output)

    def test_render_json_snippet_is_valid_json(self) -> None:
        payload = {
            "title": "Snippet of the Day",
            "source_file": "notes.md",
            "breadcrumbs": ["A", "B"],
            "breadcrumbs_text": "A > B",
            "text": "Hello",
            "continuation": "",
            "previous_context": "",
        }

        rendered = render_json_snippet(payload)
        parsed = json.loads(rendered)

        self.assertEqual(parsed, payload)


if __name__ == "__main__":
    unittest.main()
