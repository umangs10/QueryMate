# CODE_WALKTHROUGH.md — QueryMate

A phase-by-phase explanation of every file and function.

---

## Phase 1: Scaffolding

**What was built**: Project skeleton — directories, config files, package inits, minimal Streamlit app, test infrastructure.

**Files**: `app.py`, `modes/`, `utils/`, `tests/`, `.env.example`, `.gitignore`, `requirements.txt`, `data/sample.csv`, `tests/fixtures/`

**Key decision**: Modular from day one. Test infrastructure first with `conftest.py` defining `requires_api_key` marker.

---

## Phase 2: LLM Config (`utils/llm_config.py`)

**What was built**: Factory functions for Gemini chat model and embeddings.

- `_resolve_api_key(api_key)` — Returns explicit key or falls back to env var. Raises `ValueError` with helpful link.
- `get_llm(api_key)` — Creates `ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)`. Temperature 0 = deterministic.
- `get_embeddings(api_key)` — Creates `GoogleGenerativeAIEmbeddings(model="models/embedding-001")`.

**Tutorial vs original**: Tutorial had inline config. We centralized it.

---

## Phase 3: SQL Mode (`modes/sql_mode.py` + `utils/file_handler.py`)

**What was built**: Upload structured data → SQLite → LangChain SQL agent → answer + SQL.

- `file_handler.load_to_sqlite(uploaded_file)` — CSV/XLSX/SQLite → SQLAlchemy Engine.
- `sql_mode.get_schema_info(engine)` — Extracts table/column metadata via `inspect()`.
- `sql_mode.handle_sql_mode(engine, question, llm)` — Creates `SQLDatabase`, runs `create_sql_agent(agent_type="tool-calling")`, extracts SQL from intermediate steps.
- `sql_mode._extract_sql_from_steps(result)` — Parses agent steps for `sql_db_query` tool.

**Key decision**: `agent_type="tool-calling"` instead of tutorial's `"zero-shot-react-description"` (parsing issues with Gemini).

---

## Phase 4: SQL Guardrails (`utils/guardrails.py`)

**What was built**: Regex-based SQL safety checker, dual-layer.

- `check_sql_safety(text)` — Scans for `DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE` with `\b` word boundaries. Returns `(True, "safe")` or `(False, "Destructive operation X detected")`.

Applied at TWO points: (1) user's raw input before agent runs, (2) agent's generated SQL after.

**Entirely original** — tutorial has no guardrails.

---

## Phase 5: RAG Mode (`modes/rag_mode.py` + `file_handler.py` extension)

**What was built**: Full RAG pipeline — document loading, chunking, FAISS indexing, retrieval, answer + citations.

- `file_handler.load_documents(uploaded_files)` — PDF via `PyPDFLoader`, TXT via `TextLoader`.
- `rag_mode.build_vector_store(documents, embeddings)` — `RecursiveCharacterTextSplitter(1000, 200)` → `FAISS.from_documents()`.
- `rag_mode.handle_rag_mode(...)` — Similarity search k=4 → wrap context → invoke LLM → return answer + sources.

**Key decisions**: Chunk 1000/overlap 200 balances precision vs coverage. FAISS index cached in session state.

**Entirely original** — tutorial has no RAG.

---

## Phase 6: Prompt Injection Defense

- `guardrails.wrap_context_safely(chunks)` — Wraps each chunk in `<context id="N">...</context>` tags.
- `guardrails.get_system_prompt_rag()` — Returns defensive prompt telling LLM to ignore instructions in context.

**Entirely original.**

---

## Phase 7: Polish

Clear chat button, schema display, source citations, SQL display, error handling (missing API key, unsupported format, LLM errors).

---

## How It All Fits Together

### SQL Mode Flow
```
Upload CSV/XLSX/SQLite → load_to_sqlite() → Engine
  → check_sql_safety(user_input) [Layer 1]
  → create_sql_agent() → agent.invoke()
  → check_sql_safety(generated_sql) [Layer 2]
  → Return answer + SQL + tables
```

### RAG Mode Flow
```
Upload PDF/TXT → load_documents() → Documents
  → build_vector_store() → FAISS (cached)
  → similarity_search(question, k=4)
  → wrap_context_safely() + get_system_prompt_rag()
  → llm.invoke(system_prompt + context + question)
  → Return answer + sources
```
