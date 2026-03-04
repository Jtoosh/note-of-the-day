import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from parsing import generate_corpus, parse_markdown


class ParsingTests(unittest.TestCase):
    def test_parse_markdown_builds_context_aware_snippets(self) -> None:
        with TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "sample.md"
            md_file.write_text(
                "# Course\n\n"
                "Intro paragraph.\n\n"
                "## Topic\n\n"
                "Key commands:\n\n"
                "- ls\n"
                "- cat\n\n"
                "Final note.\n",
                encoding="utf-8",
            )

            snippets = parse_markdown(str(md_file))

            # Intro block stands alone under the top-level heading.
            self.assertEqual(snippets[0].text, "Intro paragraph.")
            self.assertEqual(snippets[0].header, ["Course"])

            # Topic snippet is expanded into a self-contained context window.
            self.assertEqual(len(snippets), 2)
            self.assertEqual(
                snippets[1].text,
                "Key commands:\n\n- ls\n- cat\n\nFinal note.",
            )
            self.assertEqual(snippets[1].header, ["Course", "Topic"])
            self.assertEqual(snippets[1].prev_text, "")
            self.assertEqual(snippets[1].next_text, "")

    def test_parse_markdown_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "sample.md"
            md_file.write_text(
                "# Header\n\n"
                "Definition:\n\n"
                "- step one\n"
                "- step two\n\n"
                "Summary line.\n",
                encoding="utf-8",
            )

            first_run = parse_markdown(str(md_file))
            second_run = parse_markdown(str(md_file))

            self.assertEqual(
                [(s.text, s.header, s.prev_text, s.next_text) for s in first_run],
                [(s.text, s.header, s.prev_text, s.next_text) for s in second_run],
            )

    def test_generate_corpus_writes_output_file_and_returns_snippets(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            notes_dir = tmp / "notes"
            notes_dir.mkdir()
            out_file = tmp / "snippets.json"

            (notes_dir / "one.md").write_text(
                "# Header\n\nA first snippet.\n\nSecond snippet.\n",
                encoding="utf-8",
            )
            (notes_dir / "ignore.txt").write_text("not markdown", encoding="utf-8")

            result = generate_corpus(str(notes_dir), str(out_file))

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertTrue(out_file.exists())

            raw = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(len(raw), 1)
            self.assertEqual(raw[0]["__type__"], "Snippet")

    def test_generate_corpus_returns_warning_when_no_markdown_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            notes_dir = tmp / "empty_notes"
            notes_dir.mkdir()
            out_file = tmp / "snippets.json"

            result = generate_corpus(str(notes_dir), str(out_file))

            self.assertIsInstance(result, str)
            self.assertIn("No suitable snippets found", result)
            self.assertFalse(out_file.exists())


if __name__ == "__main__":
    unittest.main()
