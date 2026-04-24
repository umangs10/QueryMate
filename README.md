# README.md — QueryMate

**QueryMate** is a dual-mode AI data assistant. Upload data or documents and ask questions in natural language.

- **SQL Mode**: Upload CSV/XLSX/SQLite → LangChain SQL agent generates and executes SQL via Gemini → returns answer
- **RAG Mode**: Upload PDF/TXT → chunk + embed in FAISS → retrieve top chunks → generate answer with citations

## Quick Start

### 1. Clone and enter the directory

```bash
git clone <your-repo-url>
cd QueryMate
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
cp .env.example .env
# Edit .env and add your Google API key
# Get one at: https://aistudio.google.com/apikey
```

### 5. Run the app

```bash
streamlit run app.py
```

## Project Structure

```text
QueryMate/
├── app.py                    # Streamlit entry point
├── modes/
│   ├── sql_mode.py           # SQL agent with dual-layer guardrails
│   └── rag_mode.py           # RAG pipeline with injection defense
├── utils/
│   ├── file_handler.py       # CSV/XLSX/SQLite/PDF/TXT loading
│   ├── guardrails.py         # SQL safety + prompt injection defense
│   ├── llm_config.py         # Centralized Gemini LLM/embeddings config
│   └── response.py           # LLM response normalization utility
├── data/sample.csv           # Demo data
├── docs/sample.pdf           # Demo document
├── requirements.txt
├── .env.example
└── .gitignore
```

## Tech Stack

| Layer | Tech |
|---|---|
| Language | Python 3.10+ |
| UI | Streamlit |
| LLM Framework | LangChain |
| LLM | Google Gemini 3.1 Flash Lite |
| Embeddings | `models/embedding-001` |
| Vector DB | FAISS |
| SQL DB | SQLite + SQLAlchemy |
| Data | pandas |
| PDF | pypdf |

## Features

- **Mode Toggle**: Sidebar radio button switches between SQL and RAG modes.
- **Data Preview**: View your full uploaded data tables interactively directly inside the chat interface.
- **SQL Guardrails**: Dual-layer blocking of destructive SQL (DROP, DELETE, UPDATE, etc.).
- **Prompt Injection Defense**: Context wrapped in numbered `<context>` tags with a defensive system prompt.
- **Source Citations**: RAG answers show exactly which document chunks were used.
- **Schema Display**: SQL mode displays database tables and columns in the sidebar.
- **Rate Limit Handling**: Gracefully catches 429 API quota limit errors with user-friendly warnings.
- **Chat History**: Persists during the session, clearable via a sidebar button.

## License

MIT
