# note-of-the-day

## About

`note-of-the-day` is an ambient flashcard-style app that can run as a CLI tool or through a small web frontend. It pulls snippets from markdown notes and displays one snippet at runtime.

The project is organized so parsing, formatting, backend API, and frontend UI are separated, making the system easier to maintain and extend.

**AI Use Disclosure**: This project has been a personal experiment in using Agentic Coding tools. The vast majority of the code in this project was written by Codex by OpenAI as I prompted it, with my personal review and testing.

## Technical Overview

### High-Level Flow

1. Parse markdown files from a notes directory into `Snippet` objects.
2. Serialize snippets to `snippets.json` (corpus generation mode).
3. Load corpus, pick one snippet randomly.
4. Convert snippet into a UI-friendly payload.
5. Render payload as either terminal-friendly text or JSON for frontend consumption.
6. Frontend requests `/api/snippet` and renders the snippet card in the browser.

### Project Structure

- `script.py`: CLI entrypoint and orchestration layer.
- `server/app.py`: FastAPI server layer for HTTP clients.
- `frontend/`: TypeScript React app (Vite) for browser UI.
- `parsing.py`: markdown parsing and corpus generation logic.
- `formatting.py`: output payload construction + text/JSON rendering.
- `snippet.py`: `Snippet` data object + JSON encoder/decoder.
- `snippets.json`: generated snippet corpus.
- `tests/`: unit tests for formatting, parsing/generation, and main script behavior.

## Core Modules

### `snippet.py`

Defines the core data model:

- `Snippet(text, header, file, prev_text, next_text)`
- `SnippetEncoder`: converts `Snippet` objects to JSON records.
- `Snippet.custom_decoder`: reconstructs `Snippet` objects when reading JSON.

This model is the contract between parsing, persistence, selection, and formatting.

### `parsing.py`

Responsible for extracting snippets from markdown:

- `get_markdown_files(root)`: recursively finds `.md` files.
- `get_node_text(node)`: recursively flattens Marko AST nodes to text.
- `reconstruct_list(list_elem)`: rebuilds list blocks (`-`, `1.`) so list structure is preserved.
- `get_adjacent_text(elements, start_index, direction)`: finds nearest non-blank sibling block for `prev_text`/`next_text`, while treating headings as structural boundaries.
- `parse_markdown(file_path)`: converts a markdown file into snippet objects while maintaining heading context (`heading_stack`).
- `generate_corpus(notes_dir, out_file)`: parses all markdown files and writes JSON corpus.

#### Parsing behavior notes

- Heading context is hierarchical: lower/equal heading levels replace prior levels in the heading stack.
- Snippet blocks currently include paragraphs, code blocks, fenced code blocks, and lists.
- Blank text blocks are ignored.
- Neighbor context (`prev_text`, `next_text`) skips blank lines and excludes headings as context text.

### `formatting.py`

Responsible for turning a `Snippet` into display-ready output:

- `build_snippet_payload(snippet)`: normalized payload for both terminal and frontend output.
- `wrap_markdownish_text(text, width)`: wraps text while preserving list prefixes and indented blocks.
- `render_terminal_snippet(payload, width=None)`: card-style CLI rendering with source/path/content sections.
- `render_json_snippet(payload)`: JSON serialization for frontend/widget integration.

#### Payload schema

- `title`: display title (currently `Snippet of the Day`).
- `source_file`: source markdown filename.
- `breadcrumbs`: heading stack as list.
- `breadcrumbs_text`: heading stack joined for display.
- `text`: primary snippet text.
- `continuation`: populated when snippet ends with `:` and has next context.
- `previous_context`: previous context block.

### `script.py`

Thin coordinator layer:

- CLI args:
  - `-generate`: regenerate corpus before selecting snippet.
  - `--format text|json`: choose output format.
  - `--width N`: optional terminal render width.
- `pick_snippet()`: loads corpus and chooses random snippet.
- `main(argv)`: orchestrates generation, selection, payload creation, and rendering.

### `server/app.py`

Backend API layer:

- `GET /health`: simple readiness check.
- `GET /api/snippet`: returns one random snippet payload as JSON.
- `POST /api/corpus/regenerate`: rebuilds `snippets.json` from markdown notes.

Configuration via environment variables:

- `SNIPPETS_FILE`: corpus JSON path (defaults to `<project>/snippets.json`).
- `NOTES_DIR`: markdown notes directory used by regeneration endpoint.
- `CORS_ALLOW_ORIGINS`: comma-separated CORS origins (defaults to `*`).

### `frontend/` (TypeScript React + Vite)

Frontend stack and behavior:

- React 18 + TypeScript.
- Vite dev server with an API proxy to the FastAPI backend.
- Single-page app in `frontend/src/App.tsx` that:
  - Fetches `GET /api/snippet` on initial load.
  - Displays snippet metadata (`source_file`, `breadcrumbs_text`) and body text.
  - Includes a `Get New Snippet` button that fetches another random snippet.
  - Handles loading and error states.

Frontend build/config files:

- `frontend/package.json`: scripts/dependencies.
- `frontend/vite.config.ts`: dev server config and `/api` proxy to `http://127.0.0.1:8000`.
- `frontend/tsconfig*.json`: TypeScript compiler settings.
- `frontend/src/App.tsx`: page UI + fetch logic.
- `frontend/src/App.css` and `frontend/src/index.css`: styling.

## CLI Usage

### Show snippet as formatted terminal card

```bash
.venv/bin/python script.py --format text
```

### Show snippet as JSON payload (frontend/widget-ready)

```bash
.venv/bin/python script.py --format json
```

### Regenerate corpus then output snippet

```bash
.venv/bin/python script.py -generate --format text
```

## Backend API Usage

### Install dependencies

```bash
.venv/bin/python -m pip install -r requirements.txt
```

### Run the server

```bash
.venv/bin/python -m uvicorn server.app:app --reload
```

### Example request

```bash
curl http://127.0.0.1:8000/api/snippet
```

## Frontend Usage

### Install frontend dependencies

```bash
cd frontend
npm install
```

### Run frontend dev server

```bash
npm run dev
```

By default, Vite serves the frontend at `http://127.0.0.1:5173` and proxies `/api/*` requests to `http://127.0.0.1:8000`.

### Run full stack locally (recommended)

In terminal 1 (backend):

```bash
.venv/bin/python -m uvicorn server.app:app --reload --port 8000
```

In terminal 2 (frontend):

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173` and use **Get New Snippet** to load random snippets from the backend.

## Testing

Tests use Python stdlib `unittest` and run with discovery.

### Run tests

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

### Test Coverage Overview

#### `tests/test_formatting.py`

Validates output/presentation behavior:

- Payload field correctness and continuation rules.
- Breadcrumb string generation.
- Text wrapping behavior for markdown-like bullets.
- Terminal card rendering sections (`Source`, `Path`, continuation block).
- JSON rendering output validity/round-tripping.

#### `tests/test_parsing.py`

Validates markdown parsing and corpus generation:

- Heading stack behavior across heading levels.
- Snippet extraction from paragraphs and lists.
- `prev_text` and `next_text` adjacency behavior.
- Corpus file creation and JSON record shape.
- Empty-input behavior when no markdown files are available.

#### `tests/test_script.py`

Validates orchestration and CLI output paths:

- Snippet selection from saved corpus.
- JSON output mode from `main()`.
- Text output mode from `main()`.
- `-generate` path calls corpus generation with expected paths.

## Requirements

- Python 3.x
- Node.js 18+ and npm (for frontend)
- [`marko`](https://pypi.org/project/marko/) for markdown parsing
- [`fastapi`](https://pypi.org/project/fastapi/) for the HTTP API
- [`uvicorn`](https://pypi.org/project/uvicorn/) as the ASGI server

Install dependencies in your virtual environment before running generation/parsing.
