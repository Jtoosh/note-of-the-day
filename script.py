import os
import random
import re
import sys
import json

import nltk

from snippet import Snippet, SnippetEncoder

# Make sure you have the Punkt tokenizer
# Run this once before first use:

# nltk.download('punkt_tab')

NOTES_DIR = ".."  # path to your .md files
OUT_FILE = "snippets.json"
MIN_LEN = 60          # minimum snippet length (chars)
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
    text: str = re.sub(r"^#+.*$", "", text, flags=re.M)

    # Remove blank newlines
    text = re.sub(r"^\n","", text, flags=re.M)

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

def build_snippet_objects(text_list, file):
    snippets = []
    for text in text_list:
        snippet = Snippet(text, None, file)
        snippets.append(snippet)
    return snippets

def generate_corpus():
    all_snippets = []
    for path in get_markdown_files(NOTES_DIR):
        text = read_file_clean(path)
        filename = path.split("/")[-1]
        sentences = extract_sentences(text)
        correct_len_sentences = filter_sentences(sentences)
        built_snippets = build_snippet_objects(correct_len_sentences, filename)
        all_snippets.extend(built_snippets)

    if not all_snippets:
        return "⚠️ No suitable snippets found. Try adjusting filters."

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump( all_snippets, f, cls=SnippetEncoder, indent=4)
    return all_snippets

def pick_snippet():
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        json_corpus = json.load(f, object_hook=Snippet.custom_decoder)
        snippet_corpus = json.loads(json_corpus)
    return random.choice(snippet_corpus)


if __name__ == "__main__":

    if len(sys.argv) == 2:
        if sys.argv[1] == "-generate":
            corpus = generate_corpus()
        else:
            print("usage: <python script.py -generate> to generate corpus\n or: <python script.py> to pick a snippet ")
            exit(0)
    snippet = pick_snippet()
    print("─" * 40)
    print("💡 Snippet of the Day: " + snippet.file)
    print("─" * 40)
    print(snippet.text)
    print("─" * 40)
