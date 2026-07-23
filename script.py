import argparse
import json
import random
import sys
from typing import Sequence

from formatting import build_snippet_payload, render_terminal_snippet
from parsing import CorpusEmpty, generate_corpus
from snippet import Snippet

DEFAULT_NOTES_DIR = "../notesrepo"  # path to your .md files
OUT_FILE = "snippets.json"


def pick_snippet() -> Snippet:
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        snippet_corpus = json.load(f, object_hook=Snippet.from_dict)
    return random.choice(snippet_corpus)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or display a note snippet.")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Regenerate snippets.json from markdown files before selecting a snippet.",
    )
    parser.add_argument(
        "--notes-dir",
        default=DEFAULT_NOTES_DIR,
        help="Directory containing markdown files for corpus generation.",
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


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    if args.generate:
        try:
            generate_corpus(args.notes_dir, OUT_FILE)
        except CorpusEmpty as exc:
            print(exc)
            return 1

    snippet = pick_snippet()
    payload = build_snippet_payload(snippet)

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_terminal_snippet(payload, width=args.width))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
