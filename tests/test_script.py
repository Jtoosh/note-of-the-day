import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import script
from snippet import Snippet, SnippetEncoder


class ScriptTests(unittest.TestCase):
    def test_pick_snippet_reads_corpus_and_uses_random_choice(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "snippets.json"
            snippets = [
                Snippet("first", ["H1"], "one.md", "", ""),
                Snippet("second", ["H2"], "two.md", "", ""),
            ]
            out_file.write_text(
                json.dumps(snippets, cls=SnippetEncoder, indent=2),
                encoding="utf-8",
            )

            with patch.object(script, "OUT_FILE", str(out_file)):
                with patch.object(script.random, "choice", side_effect=lambda seq: seq[1]):
                    chosen = script.pick_snippet()

            self.assertIsInstance(chosen, Snippet)
            self.assertEqual(chosen.text, "second")
            self.assertEqual(chosen.file, "two.md")

    def test_main_json_output(self) -> None:
        snippet = Snippet(
            text="Key commands:",
            header=["CS 260", "Shell"],
            file="notes.md",
            prev_text="context",
            next_text="- ls",
        )

        with patch.object(script, "pick_snippet", return_value=snippet):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = script.main(["script.py", "--format", "json"])

        parsed = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(parsed["title"], "Snippet of the Day")
        self.assertEqual(parsed["source_file"], "notes.md")
        self.assertEqual(parsed["continuation"], "- ls")

    def test_main_text_output(self) -> None:
        snippet = Snippet(
            text="Key commands:",
            header=["CS 260", "Shell"],
            file="notes.md",
            prev_text="context",
            next_text="- ls\n- cat",
        )

        with patch.object(script, "pick_snippet", return_value=snippet):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = script.main(
                    ["script.py", "--format", "text", "--width", "80"]
                )

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Snippet of the Day", output)
        self.assertIn("Source: notes.md", output)
        self.assertIn("Path:   CS 260 > Shell", output)
        self.assertIn("[Continuation]", output)

    def test_main_generate_calls_corpus_generation(self) -> None:
        snippet = Snippet(
            text="Done.",
            header=["H1"],
            file="notes.md",
            prev_text="",
            next_text="",
        )

        with patch.object(script, "generate_corpus", return_value=[]) as generate_mock:
            with patch.object(script, "pick_snippet", return_value=snippet):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = script.main(
                        ["script.py", "-generate", "--format", "text", "--width", "72"]
                    )

        self.assertEqual(exit_code, 0)
        generate_mock.assert_called_once_with(script.NOTES_DIR, script.OUT_FILE)


if __name__ == "__main__":
    unittest.main()
