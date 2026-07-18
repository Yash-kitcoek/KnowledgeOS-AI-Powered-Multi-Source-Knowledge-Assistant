# KnowledgeOS Architecture

KnowledgeOS is evolving from a single-purpose video transcript script into a
modular, local-first knowledge assistant. The application is deliberately split
into independently testable layers so that adding a new source type does not
change retrieval, prompting, or API code.

## Target request flow

```text
Client -> FastAPI router -> ingestion service -> processor -> chunks
       -> embeddings -> vector store + metadata store -> hybrid retriever
       -> prompt builder -> local LLM -> cited answer
```

## Initial backend layout

```text
backend/
  app/
    api/                 HTTP routers and request/response schemas
    config/              validated application settings
    models/              domain models and source-type definitions
    services/            orchestration and application use cases
    main.py              FastAPI composition root
  tests/                 unit and API tests
```

## Design decisions

- **Local-first:** Ollama, Whisper, and local vector storage remain the default;
  no paid API is required.
- **Source processors are adapters:** each processor converts one source type
  into a common chunk model with source metadata and optional timestamps.
- **Metadata is separate from vectors:** SQLite/PostgreSQL owns document,
  workspace, job, and citation records; a vector store owns embeddings.
- **Indexing is asynchronous:** uploads are staged quickly and a background
  worker performs expensive OCR, transcription, and embedding work.
- **Citations are data:** every retrieved chunk must retain an immutable source
  reference, page/slide/timestamp, and character offsets when available.

## Delivery sequence

1. Service foundation, configuration, and safe upload staging.
2. Text/PDF/DOCX/PPTX processors and normalized chunk persistence.
3. Embedding/vector-store adapter and hybrid retrieval.
4. Ollama answers with structured citations and conversation storage.
5. OCR, speech/video, websites, YouTube, analytics, authentication, and workers.

This sequence keeps the system demonstrable at every stage while avoiding a
large, hard-to-test rewrite.

## Run the current application

KnowledgeOS now provides a complete local MVP for text-based sources:

1. Create and activate a Python 3.11+ virtual environment.
2. Install the backend: `python -m pip install -e ".[dev,documents]"`.
   The `documents` extra enables PDF, DOCX, and PPTX extraction. Plain-text and
   Markdown files work with the base installation.
3. Optionally install [Ollama](https://ollama.com) and run
   `ollama pull llama3.2`. Without Ollama, KnowledgeOS still retrieves and
   displays the most relevant source passages with citations.
4. Copy `.env.example` to `.env` if you want to customize the data location or
   local model settings.
5. Start the app with `uvicorn backend.app.main:app --reload` and open
   `http://127.0.0.1:8000`.

The browser interface lets you upload a source, see its indexing status, and
ask questions. API documentation is available at `/docs`.

### Supported sources

| Type | Status | Requirement |
| --- | --- | --- |
| TXT, Markdown | Indexed locally | Base installation |
| PDF, DOCX, PPTX | Indexed locally | `documents` extra |
| Images | OCR adapter included | `ocr` extra plus Tesseract installed |
| Audio and video | Transcription adapter included | Whisper and FFmpeg installed |
