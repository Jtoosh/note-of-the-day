import os
import random
import re
import sys

import nltk

# Make sure you have the Punkt tokenizer
# Run this once before first use:

# nltk.download('punkt_tab')

NOTES_DIR = ".."  # path to your .md files
MIN_LEN = 60           # minimum snippet length (chars)
MAX_LEN = 480          # maximum snippet length (chars)


def get_markdown_files(root):
    """Recursively gather all .md files under a directory."""
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith(".md"):
                yield os.path.join(dirpath, file)


def read_file_clean(path):
    """Read Markdown file and strip out code blocks, headers, lists."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Remove fenced code blocks ``` ... ```
    text = re.sub(r"```.*?```", "", text, flags=re.S)

    # Remove inline code `...`
    # text = re.sub(r"`.*?`", "", text)

    # Remove headers (# ...)
    text = re.sub(r"^#+.*$", "", text, flags=re.M)

    # Remove list markers (-, *, + at start of line)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)

    return text


def extract_sentences(text):
    """Split text into sentences with NLTK."""
    return nltk.sent_tokenize(text)


def filter_sentences(sentences):
    """Keep sentences that fit length and formatting rules."""
    good = []
    for s in sentences:
        s = s.strip()
        if MIN_LEN <= len(s) <= MAX_LEN:
            if s[0].isupper() and s[-1] in ".!?":
                good.append(s)
    return good


def generate_corpus():
    all_sentences = []
    for path in get_markdown_files(NOTES_DIR):
        text = read_file_clean(path)
        sentences = extract_sentences(text)
        all_sentences.extend(filter_sentences(sentences))

    if not all_sentences:
        return "⚠️ No suitable snippets found. Try adjusting filters."

    return all_sentences

def pick_snippet(text_corpus):
    return random.choice(text_corpus)


if __name__ == "__main__":
    if sys.argv[1] == "generate":
        corpus = generate_corpus()
    snippet = pick_snippet(corpus)
    print("─" * 40)
    print("💡 Snippet of the Day")
    print("─" * 40)
    print(snippet)
    print("─" * 40)
