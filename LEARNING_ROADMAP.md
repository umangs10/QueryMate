# LEARNING_ROADMAP.md — QueryMate

Study guide for the concepts behind QueryMate, grouped by priority tier.

**Total time**: 8–12 hours across all tiers, ~5 hours for Tier 1.

---

## Tier 1 — Must Know Cold
*You can't claim this project without knowing these.*

### LLM Basics
**What it is**: Large Language Models predict the next token in a sequence. They're trained on massive text corpora and can be prompted to perform tasks like Q&A, summarization, and code generation. Key concepts: tokens, context windows, temperature, sampling.
**Why it matters here**: Gemini is the core of both SQL and RAG modes.
**Resource**: [Andrej Karpathy — Intro to LLMs (YouTube, 1hr)](https://www.youtube.com/watch?v=zjkBMFhNj_g)
**You know enough when**: You can explain tokens, temperature, and context windows without notes.
**Time**: 1 hour

### Embeddings
**What it is**: Dense vector representations of text where semantically similar text has similar vectors. Used for search, clustering, and RAG retrieval.
**Why it matters here**: RAG mode embeds document chunks and queries into vectors for similarity search.
**Resource**: [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
**You know enough when**: You can explain why "king - man + woman ≈ queen" and how cosine similarity works.
**Time**: 30 minutes

### RAG Pipeline
**What it is**: Retrieval-Augmented Generation — instead of relying on the LLM's training data, you retrieve relevant documents and include them in the prompt. Steps: load → chunk → embed → index → retrieve → generate.
**Why it matters here**: This is exactly what RAG mode does.
**Resource**: [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
**You know enough when**: You can draw the RAG pipeline from memory and explain each step.
**Time**: 45 minutes

### LangChain Agents & Tool-Calling
**What it is**: Agents use LLMs to decide which tools to call and in what order. Tool-calling uses the model's native function calling API. The agent loop: observe → think → act → observe.
**Why it matters here**: The SQL agent decides when to inspect schema, run queries, or retry.
**Resource**: [LangChain Agents Docs](https://python.langchain.com/docs/how_to/#agents)
**You know enough when**: You can explain the difference between a chain (fixed steps) and an agent (dynamic tool selection).
**Time**: 45 minutes

### Vector Databases (FAISS)
**What it is**: Specialized databases for storing and searching high-dimensional vectors. FAISS (Facebook AI Similarity Search) is an in-memory library for efficient nearest-neighbor search.
**Why it matters here**: FAISS stores our document embeddings and performs similarity search.
**Resource**: [FAISS GitHub Wiki](https://github.com/facebookresearch/faiss/wiki)
**You know enough when**: You can explain approximate nearest neighbor search and why it's faster than brute force.
**Time**: 30 minutes

### Prompt Engineering Basics
**What it is**: The art of crafting inputs to get better outputs from LLMs. Techniques: system prompts, few-shot examples, chain-of-thought, structured output.
**Why it matters here**: Our RAG system prompt and SQL agent prompts are prompt engineering in action.
**Resource**: [Google Prompt Engineering Guide](https://ai.google.dev/docs/prompt_best_practices)
**You know enough when**: You can improve a bad prompt systematically, not just by guessing.
**Time**: 30 minutes

### Prompt Injection + Defenses
**What it is**: Attacks where malicious text in user input or documents hijacks the LLM's behavior. Defenses: context separation (tags), defensive system prompts, input/output filtering.
**Why it matters here**: Our `<context>` wrapping and defensive system prompt are injection defenses.
**Resource**: [OWASP LLM Top 10 — Prompt Injection](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
**You know enough when**: You can explain 3 injection attack types and 3 defense strategies.
**Time**: 30 minutes

### SQL Injection (for context)
**What it is**: Classic web security attack where malicious SQL is injected through user input. Relevant because our guardrails are conceptually similar, blocking destructive SQL operations.
**Why it matters here**: Explains why we check both user input AND generated SQL.
**Resource**: [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
**You know enough when**: You can explain parameterized queries and why string concatenation is dangerous.
**Time**: 20 minutes

---

## Tier 2 — Should Know Well
*Strong interviews probe these topics.*

### Agent Types (ReAct vs Tool-Calling vs Plan-and-Execute)
**What it is**: ReAct = text-based reasoning loop. Tool-calling = native function calling API. Plan-and-execute = plan all steps first, then execute. Each has trade-offs in reliability, latency, and model compatibility.
**Why it matters here**: We chose tool-calling over ReAct because Gemini has parsing issues with ReAct's text format.
**Resource**: [LangChain Agent Types](https://python.langchain.com/docs/how_to/agent_executor/)
**You know enough when**: You can explain when to use each type and their failure modes.
**Time**: 30 minutes

### Chunking Strategies
**What it is**: How you split documents affects retrieval quality. Strategies: fixed-size, recursive character, semantic, sentence-based, document structure-aware.
**Why it matters here**: We use `RecursiveCharacterTextSplitter(1000, 200)` — a common starting point.
**Resource**: [LangChain Text Splitters](https://python.langchain.com/docs/how_to/#text-splitters)
**You know enough when**: You can explain when recursive splitting fails and what alternatives exist.
**Time**: 30 minutes

### Retrieval Strategies
**What it is**: Beyond basic similarity search: MMR (maximal marginal relevance), re-ranking, hybrid search (dense + sparse), HyDE, multi-query retrieval.
**Why it matters here**: We use basic similarity search — knowing alternatives shows depth.
**Resource**: [LangChain Retrievers](https://python.langchain.com/docs/how_to/#retrievers)
**You know enough when**: You can propose a retrieval improvement for poor results.
**Time**: 30 minutes

### Context Window Limits
**What it is**: LLMs have a maximum input+output token limit. Gemini 1.5 Flash has 1M tokens, but performance degrades with very long contexts. Strategies: summarization, hierarchical retrieval, chunk selection.
**Why it matters here**: We retrieve only 4 chunks to stay well within limits and maintain quality.
**Resource**: [Google Gemini Model Docs](https://ai.google.dev/models/gemini)
**You know enough when**: You can calculate approximate token counts and design for context limits.
**Time**: 20 minutes

### RAGAS Evaluation
**What it is**: A framework for evaluating RAG pipelines. Metrics: faithfulness (does the answer match the context?), answer relevancy, context relevancy, context recall.
**Why it matters here**: We don't have evaluation in QueryMate, but knowing RAGAS shows maturity.
**Resource**: [RAGAS Documentation](https://docs.ragas.io/)
**You know enough when**: You can name 3 RAGAS metrics and explain what each measures.
**Time**: 30 minutes

### Streamlit Session State
**What it is**: Streamlit reruns the entire script on each interaction. `st.session_state` persists values across reruns. Key patterns: initialization, callbacks, widget state.
**Why it matters here**: Chat history, FAISS index, and SQL engine are all cached in session state.
**Resource**: [Streamlit Session State Docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
**You know enough when**: You can explain why Streamlit reruns everything and how session state solves it.
**Time**: 20 minutes

### Temperature / Sampling
**What it is**: Temperature controls randomness in token selection. 0 = deterministic (greedy), 1+ = more random. Top-k and top-p are alternative sampling strategies.
**Why it matters here**: We use temperature=0 for factual, reproducible answers.
**Resource**: [Cohere — LLM Parameters](https://docs.cohere.com/docs/temperature)
**You know enough when**: You can explain when to use temperature 0 vs 0.7 vs 1.0.
**Time**: 15 minutes

---

## Tier 3 — Nice to Know
*Bonus points in interviews.*

### Fine-Tuning vs RAG
**What it is**: Fine-tuning adjusts model weights on domain data. RAG retrieves external data at inference time. Fine-tuning is expensive and static; RAG is flexible and real-time.
**Why it matters here**: Shows you considered alternatives and chose RAG deliberately.
**Resource**: [Anyscale — Fine-tuning vs RAG](https://www.anyscale.com/blog/fine-tuning-vs-rag)
**You know enough when**: You can advise a team on which approach to use for their use case.
**Time**: 20 minutes

### LangGraph / Multi-Agent
**What it is**: LangGraph lets you build stateful, multi-agent workflows as graphs. Agents can route to other agents, maintain shared state, and handle complex multi-step tasks.
**Why it matters here**: QueryMate manually toggles modes; LangGraph could auto-route.
**Resource**: [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
**You know enough when**: You can sketch a LangGraph workflow for auto-routing SQL vs RAG.
**Time**: 30 minutes

### Re-Ranking
**What it is**: After initial retrieval, a re-ranker (e.g., Cohere Rerank, cross-encoder) rescores results for higher precision. Two-stage pipeline: fast retrieval → precise re-ranking.
**Why it matters here**: Could improve our RAG quality if initial retrieval returns noisy results.
**Resource**: [Cohere Rerank Docs](https://docs.cohere.com/docs/reranking)
**You know enough when**: You can explain the two-stage retrieval pipeline.
**Time**: 15 minutes

### Quantization
**What it is**: Reducing model weight precision (float32 → int8/int4) to decrease memory and increase speed, with minimal quality loss. Relevant for self-hosted models.
**Why it matters here**: We use an API, so this doesn't apply directly. But shows depth.
**Resource**: [Hugging Face Quantization](https://huggingface.co/docs/transformers/quantization)
**You know enough when**: You can explain the trade-offs of 4-bit vs 8-bit quantization.
**Time**: 15 minutes

### Token Cost Optimization
**What it is**: Strategies to reduce LLM API costs: caching, prompt compression, model routing (cheap model for easy tasks, expensive for hard ones), batch processing.
**Why it matters here**: We cache FAISS to avoid re-embedding. More strategies show production awareness.
**Resource**: [LangChain Caching](https://python.langchain.com/docs/how_to/llm_caching/)
**You know enough when**: You can estimate token costs and propose 3 optimization strategies.
**Time**: 15 minutes

---

## Honesty Check

If you skip certain tiers, **do not claim** these in interviews:

- Skip Tier 2 → Don't say "I deeply understand agent architectures" or "I've evaluated RAG quality"
- Skip Tier 3 → Don't say "I considered fine-tuning" or "I know how to optimize token costs" (unless you actually do)
- Never claim → "I built this entirely from scratch" (SQL mode started from a tutorial)

Honesty is a differentiator. Interviewers respect it.
