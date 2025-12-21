import os
import random
import sys
import json
import pprint

import marko
from marko import block, inline

from snippet import Snippet, SnippetEncoder

NOTES_DIR = "../notesrepo"  # path to your .md files
OUT_FILE = "snippets.json"
MIN_LEN = 640       # minimum snippet length (chars)
MAX_LEN = 960        # maximum snippet length (chars)


def get_markdown_files(root):
    """Recursively gather all .md files under a directory."""
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith(".md"):
                yield os.path.join(dirpath, file)


def parse_markdown (file_path):
  with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

    document = marko.parse(text)

    doc_snippets = []
    heading_stack = []

    elements = document.children

    for i, element in enumerate(elements):
      if isinstance(element, block.Heading):
        header_text = get_node_text(element)
        level = element.level

        #This will truncate the heading stack to the contain only headings of the higher level
        heading_stack = heading_stack[:level-1] + [header_text]
        continue
      if isinstance(element, (block.Paragraph, block.CodeBlock, block.FencedCode, block.List)):

        content_text = get_node_text(element)

        # skip empty paragraphs
        if not content_text.strip():
          continue

        # get previous text for context
        if i > 0:
          prev_element = elements[i-1]

          prev_text = get_node_text(prev_element)

        next_text = ""
        if i < len(elements)-1:
          next_element = elements[i+1]
          next_text = get_node_text(next_element)

        filename = file_path.split("/")[-1]
        snippet = Snippet(content_text, heading_stack, filename, prev_text, next_text)
        doc_snippets.append(snippet)
    return doc_snippets

def get_node_text(node):

  if isinstance(node, inline.RawText):
    return node.children
  if isinstance(node, inline.CodeSpan):
    return node.children
  if hasattr(node, "children"):
    if isinstance(node.children, str):
      return node.children
    return "".join(get_node_text(child) for child in node.children)
  return ""

def generate_corpus():
    all_snippets = []
    for path in get_markdown_files(NOTES_DIR):
        # Scrap out unwanted text

        file_snippets = parse_markdown(path)
        all_snippets.extend(file_snippets)
    if not all_snippets:
        return "⚠️ No suitable snippets found. Try adjusting filters."

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump( all_snippets, f, cls=SnippetEncoder, indent=4)
    return all_snippets

def pick_snippet():
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        snippet_corpus = json.load(f, object_hook=Snippet.custom_decoder)
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
    print(snippet.header)
    # print(snippet.prev_text)
    print(snippet.text)
    print(snippet.next_text)
    print("─" * 40)
