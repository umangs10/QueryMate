"""RAG mode — document Q&A with FAISS retrieval and citations.

Loads documents, chunks them, embeds into a FAISS vector store,
retrieves relevant context, and generates answers with source citations.
"""

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_vector_store(
    documents: list[Document],
    embeddings: GoogleGenerativeAIEmbeddings,
) -> FAISS:
    """Chunk documents and build a FAISS vector store.

    Uses a recursive character text splitter with 1000-char chunks and
    200-char overlap to balance retrieval precision and context coverage.

    Args:
        documents: A list of LangChain Document objects to index.
        embeddings: A configured GoogleGenerativeAIEmbeddings instance.

    Returns:
        A FAISS vector store containing the embedded chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


def handle_rag_mode(
    documents: list[Document],
    user_question: str,
    llm: ChatGoogleGenerativeAI,
    embeddings: GoogleGenerativeAIEmbeddings,
    faiss_index: FAISS | None = None,
) -> dict:
    """Answer a question using RAG over the provided documents.

    If a FAISS index is provided (cached from a previous call), it is
    reused. Otherwise, a new index is built from the documents.

    Args:
        documents: A list of LangChain Document objects.
        user_question: The natural-language question to answer.
        llm: A configured ChatGoogleGenerativeAI instance.
        embeddings: A configured GoogleGenerativeAIEmbeddings instance.
        faiss_index: An optional pre-built FAISS index to reuse.

    Returns:
        A dict with keys:
            - ``answer`` (str): The generated answer.
            - ``sources`` (list[dict]): Retrieved chunks with content, page, source.
            - ``faiss_index`` (FAISS): The vector store (for caching).
    """
    # Build or reuse vector store
    if faiss_index is None:
        faiss_index = build_vector_store(documents, embeddings)

    # Retrieve top 4 chunks
    retrieved_chunks = faiss_index.similarity_search(user_question, k=4)

    # Wrap context with injection defense
    from utils.guardrails import wrap_context_safely, get_system_prompt_rag

    wrapped_context = wrap_context_safely(retrieved_chunks)
    system_prompt = get_system_prompt_rag()

    # Build prompt with defensive system instructions
    prompt = (
        f"{system_prompt}\n\n"
        f"{wrapped_context}\n\n"
        f"Question: {user_question}"
    )

    response = llm.invoke(prompt)

    from utils.response import extract_text
    answer = extract_text(response.content)

    # Extract source info from retrieved chunks
    sources = []
    for chunk in retrieved_chunks:
        sources.append({
            "content": chunk.page_content,
            "page": chunk.metadata.get("page", "N/A"),
            "source": chunk.metadata.get("source", "Unknown"),
        })

    return {
        "answer": answer,
        "sources": sources,
        "faiss_index": faiss_index,
    }
