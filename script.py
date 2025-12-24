import os
import random
import sys
import json
import pprint
from ftplib import print_line

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

        if isinstance(element, block.List):
          content_text = reconstruct_list(element)
        else:
          content_text = get_node_text(element)

        # skip empty paragraphs
        if not content_text.strip():
          continue

        # get previous text for context
        if i > 0:
          j = i
          while j > 0 and isinstance(elements[j-1], block.BlankLine):
            j -= 1
          prev_element = elements[j-1]
          if isinstance(prev_element, block.List):
            prev_text = reconstruct_list(prev_element)
          else:
            prev_text = get_node_text(prev_element)
          if isinstance(prev_element, block.Heading):
            prev_text = ""

        next_text = ""
        if i < len(elements)-1:
          k = i
          while j < len(elements)-1 and isinstance(elements[k+1], block.BlankLine):
            k += 1
          next_element = elements[k+1]
          if isinstance(next_element, block.List):
            next_text = reconstruct_list(next_element)
          else:
            next_text = get_node_text(next_element)
          if isinstance(next_element, block.Heading):
            next_text = ""

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

def reconstruct_list(list_elem):
  list_lines = []

  is_ordered = list_elem.ordered
  start_num = list_elem.start if is_ordered else 1

  for i, item in enumerate(list_elem.children):
    if is_ordered:
      prefix = f"{i+start_num}. "
    else:
      prefix = "- "

    list_item_text = get_node_text(item)
    list_lines.append(f"{prefix}{list_item_text}")

  return "\n".join(list_lines)

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

def print_header_stack(heading_stack):
    print("-->".join(heading_stack))



if __name__ == "__main__":

    if len(sys.argv) == 2:
        if sys.argv[1] == "-generate":
            corpus = generate_corpus()
        else:
            print("usage: <python script.py -generate> to generate corpus\n or: <python script.py> to pick a snippet ")
            exit(0)
    snippet = pick_snippet()
    print("─" * 80)
    print("💡 Snippet of the Day: " + snippet.file)
    print("─" * 80)
    print_header_stack(snippet.header)
    # print(f"{snippet.prev_text}\n")
    print(f"{snippet.text}\n")
    if (snippet.text[len(snippet.text)-1] == ":"):
      print(f"{snippet.next_text}")
    print("─" * 80)
