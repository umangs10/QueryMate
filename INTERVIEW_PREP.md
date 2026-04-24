# INTERVIEW_PREP.md — QueryMate

## Honesty Statement

> You built on a Medium tutorial for SQL mode. When asked "did you build this from scratch", the honest answer is: "I used a Medium tutorial as the starting point for the SQL agent pattern, then extended it with RAG, guardrails, injection defenses, and tests." Never claim 100% original work.

---

## A. Architecture & Design

### 1. Walk me through the project.
QueryMate is a dual-mode AI data assistant built with Streamlit, LangChain, and Google Gemini. SQL Mode lets users upload CSV/XLSX/SQLite files, converts them to SQLite, and uses a LangChain SQL agent to answer natural language questions. RAG Mode lets users upload PDFs/TXT, chunks and embeds them into FAISS, retrieves relevant context, and generates answers with citations. Both modes share a chat UI with session persistence.

**Follow-up**: Why two modes? → Structured vs unstructured data need different retrieval strategies.

### 2. How does the SQL agent work?
LangChain's `create_sql_agent` wraps the LLM with SQL tools (schema inspection, query execution). It receives a natural language question, inspects the schema, generates SQL, executes it against SQLite, and returns a natural language answer. We use `agent_type="tool-calling"` which leverages the model's native function calling.

**Follow-up**: Why not just generate SQL directly? → The agent can self-correct, inspect schema, and handle multi-step reasoning.

### 3. How does the RAG pipeline work?
Documents are loaded, split into 1000-char chunks with 200-char overlap, embedded using Google's embedding model, and stored in a FAISS vector index. At query time, we retrieve the top 4 most similar chunks, wrap them in defensive context tags, and pass them with a system prompt to Gemini for answer generation.

**Follow-up**: Why top 4? → Balances enough context for accuracy without overwhelming the model or hitting token limits.

### 4. How do the modes share state?
Both modes use `st.session_state` — Streamlit's built-in per-session dictionary. Chat history (`messages`), the SQL engine, and the FAISS index are all stored there. A mode toggle via `st.sidebar.radio` conditionally renders the appropriate UI.

**Follow-up**: What happens to state on mode switch? → Chat history persists (shared list), but the file uploaders are mode-specific widgets.

---

## B. Gen AI Fundamentals

### 5. RAG vs fine-tuning — when would you use each?
RAG is best when you need to query changing documents or private data without model retraining. Fine-tuning is for teaching the model new behaviors or domain-specific language. QueryMate uses RAG because documents change per session and fine-tuning would be overkill.

**Follow-up**: Can you combine them? → Yes — fine-tune for domain language, RAG for specific document retrieval.

### 6. What's the difference between agents and chains?
Chains are fixed sequences of steps. Agents decide which tools to use at runtime based on the input. Our SQL agent dynamically chooses to inspect schema, run queries, or retry — a chain would need all steps predefined.

**Follow-up**: What agent type do you use? → `tool-calling`, which uses the model's native function calling API.

### 7. How do embeddings work?
Embeddings convert text into high-dimensional vectors where semantically similar text has closer vectors (high cosine similarity). We use Google's `models/embedding-001` to embed both document chunks and queries, then find the closest chunks via FAISS.

**Follow-up**: What dimension? → Google's embedding-001 produces 768-dimensional vectors.

### 8. What is prompt injection and how do you defend against it?
Prompt injection is when malicious text in user input or documents tries to override the LLM's instructions. We defend with: (1) wrapping context in numbered `<context>` tags to structurally separate data from instructions, and (2) a system prompt that explicitly tells the model to ignore any instructions within context tags.

**Follow-up**: Is this 100% reliable? → No. LLMs can't perfectly distinguish data from instructions. Defense-in-depth is key.

---

## C. Why This Over That

### 9. Why Gemini over OpenAI?
Free tier availability for portfolio projects, native tool-calling support, and good performance on structured tasks. For production, the choice depends on cost, latency, and specific model strengths.

**Follow-up**: Would the code work with OpenAI? → Yes, swap `ChatGoogleGenerativeAI` for `ChatOpenAI` — LangChain abstracts the provider.

### 10. Why FAISS over Chroma?
FAISS is lightweight, in-memory, zero-config — perfect for a single-session demo. Chroma adds persistence and metadata filtering, which we don't need since everything resets per session.

**Follow-up**: When would you switch? → Multi-user persistence, metadata filtering, or hybrid search needs.

### 11. Why SQLite over Postgres?
In-memory SQLite requires no server setup. Users upload files that become temporary databases. Postgres would be appropriate for persistent multi-user data.

**Follow-up**: Can you connect to external databases? → Not in this version, but `SQLDatabase` supports any SQLAlchemy-compatible connection string.

### 12. Why Streamlit over Flask?
Streamlit is purpose-built for data/ML apps — file uploaders, session state, chat UI all built-in. Flask would require building all of that from scratch. For a portfolio project, Streamlit gets to "demoable" faster.

**Follow-up**: Downsides? → Limited customization, no authentication built-in, single-threaded.

### 13. Why tool-calling over ReAct?
ReAct (`zero-shot-react-description`) requires the model to output specific text formats that Gemini doesn't follow reliably, causing parsing errors. `tool-calling` uses the model's native function calling API, which is more robust.

**Follow-up**: Does this change behavior? → Same capabilities, just different communication protocol between the model and LangChain.

---

## D. Production Concerns

### 14. How would you scale this?
Replace in-memory SQLite with a managed database, FAISS with a managed vector DB (Pinecone, Weaviate), add authentication, rate limiting, and deploy behind a load balancer. Streamlit can be containerized but isn't ideal for high-concurrency.

**Follow-up**: What about cost? → LLM API calls are the main cost. Implement caching, batch embeddings, and set token limits.

### 15. How would you add authentication?
Streamlit has `st.experimental_user` for basic auth. For production: OAuth2 via an API gateway, or switch to a framework like FastAPI + React with proper session management.

**Follow-up**: Multi-tenancy? → Each user needs isolated session state. Current architecture already does this per Streamlit session, but databases would need per-user isolation.

---

## E. Failure Modes

### 16. What if the LLM hallucinates?
In SQL mode, the agent can generate incorrect SQL — but it executes against real data, so wrong SQL usually fails or returns wrong numbers rather than fabricating data. In RAG mode, the model might misinterpret chunks — citations let users verify.

**Follow-up**: How do you detect hallucinations? → Compare answers against source chunks (RAGAS evaluation), or run SQL results back through a validator.

### 17. What if retrieval returns irrelevant chunks?
If the top-4 chunks don't contain the answer, the system prompt instructs the model to say "I don't have enough information." This is better than guessing. Improving retrieval: try re-ranking, HyDE, or hybrid search.

**Follow-up**: What's HyDE? → Hypothetical Document Embeddings — generate a hypothetical answer, embed it, and use that to retrieve similar real chunks.

### 18. How robust are your injection defenses?
They reduce risk but aren't bulletproof. Context wrapping makes structural injection harder. The system prompt is a "soft" defense — LLMs don't 100% follow instructions. Production systems should add output filtering, input sanitization, and human review for sensitive operations.

**Follow-up**: What would a stronger defense look like? → Input classifiers, output guardrails, sandboxed execution, and allowlisting of permitted operations.
