"""QueryMate — Dual-Mode AI Data Assistant.

Main Streamlit application entry point. Provides a sidebar toggle
to switch between SQL Mode (structured data queries) and RAG Mode
(document Q&A with citations).
"""

import streamlit as st

from utils.llm_config import get_llm


def init_session_state() -> None:
    """Initialize all session state keys with defaults."""
    defaults = {
        "messages": [],
        "sql_engine": None,
        "faiss_index": None,
        "uploaded_file_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_chat() -> None:
    """Clear chat history and cached data."""
    st.session_state.messages = []
    st.session_state.sql_engine = None
    st.session_state.faiss_index = None
    st.session_state.uploaded_file_name = None


def display_chat_history() -> None:
    """Render all messages from session state."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sql"):
                with st.expander("🔍 Generated SQL"):
                    st.code(msg["sql"], language="sql")
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"**{src.get('source', 'Unknown')}** "
                            f"(page {src.get('page', 'N/A')})"
                        )
                        st.caption(src.get("content", "")[:300])
                        st.divider()


def main() -> None:
    """Initialize and run the QueryMate Streamlit application."""
    st.set_page_config(
        page_title="QueryMate",
        page_icon="🔍",
        layout="wide",
    )

    init_session_state()

    # ── Sidebar ──────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🔍 QueryMate")
        mode = st.radio("Select Mode", ["SQL Mode", "RAG Mode"], key="mode")
        st.divider()

        if st.button("🗑️ Clear Chat"):
            clear_chat()
            st.rerun()

    # ── Main Area ────────────────────────────────────────────────────
    st.title("🔍 QueryMate")
    st.caption("Your dual-mode AI data assistant — ask questions about data or documents.")

    # ── SQL Mode ─────────────────────────────────────────────────────
    if mode == "SQL Mode":
        _run_sql_mode()
    else:
        _run_rag_mode()

    # ── Chat History ─────────────────────────────────────────────────
    display_chat_history()


def _run_sql_mode() -> None:
    """Handle the SQL Mode UI and logic."""
    from utils.file_handler import load_to_sqlite
    from modes.sql_mode import handle_sql_mode, get_schema_info

    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=["csv", "xlsx", "db", "sqlite"],
        key="sql_uploader",
    )

    if uploaded_file:
        try:
            # Only reload if the file changed
            if st.session_state.uploaded_file_name != uploaded_file.name:
                with st.spinner("Loading data..."):
                    engine = load_to_sqlite(uploaded_file)
                    st.session_state.sql_engine = engine
                    st.session_state.uploaded_file_name = uploaded_file.name
                st.success(f"✅ Loaded **{uploaded_file.name}**")

            engine = st.session_state.sql_engine

            # Show schema in sidebar + data preview in main area
            if engine:
                import pandas as pd
                import sqlalchemy

                schema = get_schema_info(engine)
                with st.sidebar:
                    with st.expander("📊 Database Schema"):
                        for table in schema:
                            st.markdown(f"**{table['table']}**")
                            for col in table["columns"]:
                                st.markdown(f"  - `{col}`")

                # Data preview in main area
                for table in schema:
                    table_name = table["table"]
                    with st.expander(f"👀 Preview: **{table_name}**"):
                        try:
                            df = pd.read_sql(
                                sqlalchemy.text(f"SELECT * FROM {table_name}"),
                                engine,
                            )
                            st.dataframe(df, use_container_width=True)
                            # Show total row count
                            count = len(df)
                            st.caption(f"Showing all {count} rows")
                        except Exception as e:
                            st.error(f"Could not preview table: {e}")

            # Chat input
            if question := st.chat_input("Ask a question about your data..."):
                st.session_state.messages.append(
                    {"role": "user", "content": question}
                )

                with st.chat_message("user"):
                    st.markdown(question)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            llm = get_llm()
                            result = handle_sql_mode(engine, question, llm)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result["answer"],
                                "sql": result.get("sql", ""),
                            })
                        except Exception as e:
                            error_msg = str(e)
                            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                                error_msg = "⚠️ Rate limit hit. Switch to a paid plan or try again in some time."
                            else:
                                error_msg = f"❌ Error: {e}"
                            st.session_state.messages.append(
                                {"role": "assistant", "content": error_msg}
                            )
                st.rerun()

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"❌ Failed to load file: {e}")
    else:
        st.info("👆 Upload a CSV, XLSX, or SQLite file to get started with SQL Mode.")


def _run_rag_mode() -> None:
    """Handle the RAG Mode UI and logic."""
    from utils.file_handler import load_documents
    from modes.rag_mode import handle_rag_mode
    from utils.llm_config import get_llm, get_embeddings

    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="rag_uploader",
    )

    if uploaded_files:
        try:
            # Load documents
            file_names = [f.name for f in uploaded_files]
            current_names = "_".join(sorted(file_names))

            if st.session_state.uploaded_file_name != current_names:
                with st.spinner("Processing documents..."):
                    documents = load_documents(uploaded_files)
                    embeddings = get_embeddings()
                    from modes.rag_mode import build_vector_store
                    faiss_index = build_vector_store(documents, embeddings)
                    st.session_state.faiss_index = faiss_index
                    st.session_state.uploaded_file_name = current_names
                st.success(f"✅ Indexed **{len(file_names)}** document(s)")

            # Chat input
            if question := st.chat_input("Ask a question about your documents..."):
                st.session_state.messages.append(
                    {"role": "user", "content": question}
                )

                with st.chat_message("user"):
                    st.markdown(question)

                with st.chat_message("assistant"):
                    with st.spinner("Searching documents..."):
                        try:
                            llm = get_llm()
                            embeddings = get_embeddings()
                            result = handle_rag_mode(
                                documents=[],  # Not needed if index cached
                                user_question=question,
                                llm=llm,
                                embeddings=embeddings,
                                faiss_index=st.session_state.faiss_index,
                            )
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result["answer"],
                                "sources": result.get("sources", []),
                            })
                        except Exception as e:
                            error_msg = str(e)
                            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                                error_msg = "⚠️ Rate limit hit. Switch to a paid plan or try again in some time."
                            else:
                                error_msg = f"❌ Error: {e}"
                            st.session_state.messages.append(
                                {"role": "assistant", "content": error_msg}
                            )
                st.rerun()

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"❌ Failed to process documents: {e}")
    else:
        st.info("👆 Upload PDF or TXT files to get started with RAG Mode.")


if __name__ == "__main__":
    main()
