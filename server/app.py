import json
import os
import random
from pathlib import Path
from typing import List, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from formatting import build_snippet_payload
from parsing import generate_corpus
from snippet import Snippet

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTES_DIR = (PROJECT_ROOT / "../notesrepo").resolve()
DEFAULT_SNIPPETS_FILE = PROJECT_ROOT / "snippets.json"

NOTES_DIR = Path(os.getenv("NOTES_DIR", str(DEFAULT_NOTES_DIR))).resolve()
SNIPPETS_FILE = Path(os.getenv("SNIPPETS_FILE", str(DEFAULT_SNIPPETS_FILE))).resolve()


class HealthResponse(BaseModel):
    status: str


class SnippetPayload(BaseModel):
    title: str
    source_file: str
    breadcrumbs: List[str]
    breadcrumbs_text: str
    text: str
    continuation: str
    previous_context: str


class RegenerateResponse(BaseModel):
    status: str
    message: str
    snippet_count: int
    output_file: str


app = FastAPI(
    title="note-of-the-day API",
    description="Serve snippet payloads for frontend clients.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_snippet_corpus(corpus_file: Path) -> List[Snippet]:
    if not corpus_file.exists():
        raise FileNotFoundError(f"Snippet corpus was not found at {corpus_file}")

    with corpus_file.open("r", encoding="utf-8") as corpus_stream:
        raw_items = json.load(corpus_stream, object_hook=Snippet.custom_decoder)

    if not isinstance(raw_items, list):
        raise ValueError("Snippet corpus JSON must be a top-level list.")

    snippets = [item for item in raw_items if isinstance(item, Snippet)]
    if not snippets:
        raise ValueError("Snippet corpus does not contain any valid snippets.")

    return snippets


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/snippet", response_model=SnippetPayload)
def get_snippet() -> SnippetPayload:
    try:
        snippet = random.choice(load_snippet_corpus(SNIPPETS_FILE))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    payload = build_snippet_payload(snippet)
    return SnippetPayload(**payload)


@app.post("/api/corpus/regenerate", response_model=RegenerateResponse)
def regenerate_corpus() -> RegenerateResponse:
    result: Union[List[Snippet], str] = generate_corpus(str(NOTES_DIR), str(SNIPPETS_FILE))

    if isinstance(result, str):
        return RegenerateResponse(
            status="warning",
            message=result,
            snippet_count=0,
            output_file=str(SNIPPETS_FILE),
        )

    return RegenerateResponse(
        status="ok",
        message="Corpus regenerated successfully.",
        snippet_count=len(result),
        output_file=str(SNIPPETS_FILE),
    )
