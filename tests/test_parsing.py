import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from parsing import generate_corpus, parse_markdown


class ParsingTests(unittest.TestCase):
    def test_parse_markdown_extracts_heading_context_and_adjacent_text(self):
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

            self.assertEqual(len(snippets), 4)

            intro = snippets[0]
            key_commands = snippets[1]
            list_block = snippets[2]
            final_note = snippets[3]

            self.assertEqual(intro.text, "Intro paragraph.")
            self.assertEqual(intro.header, ["Course"])
            self.assertEqual(intro.prev_text, "")
            self.assertEqual(intro.next_text, "")

            self.assertEqual(key_commands.text, "Key commands:")
            self.assertEqual(key_commands.header, ["Course", "Topic"])
            self.assertEqual(key_commands.prev_text, "")
            self.assertEqual(key_commands.next_text, "- ls\n- cat")

            self.assertEqual(list_block.text, "- ls\n- cat")
            self.assertEqual(list_block.header, ["Course", "Topic"])
            self.assertEqual(list_block.prev_text, "Key commands:")
            self.assertEqual(list_block.next_text, "Final note.")

            self.assertEqual(final_note.text, "Final note.")
            self.assertEqual(final_note.header, ["Course", "Topic"])

    def test_generate_corpus_writes_output_file_and_returns_snippets(self):
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
            self.assertEqual(len(result), 2)
            self.assertTrue(out_file.exists())

            raw = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(len(raw), 2)
            self.assertEqual(raw[0]["__type__"], "Snippet")

    def test_generate_corpus_returns_warning_when_no_markdown_files(self):
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
