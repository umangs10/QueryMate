"""File handling — load CSV, XLSX, SQLite, PDF, and TXT uploads.

Converts uploaded files into either a SQLAlchemy engine (SQL mode)
or a list of LangChain Documents (RAG mode).
"""

import tempfile
from pathlib import Path

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


def load_to_sqlite(uploaded_file) -> sqlalchemy.Engine:
    """Convert an uploaded data file into an in-memory SQLite engine.

    Supported formats:
        - .csv  → single table named ``uploaded_data``
        - .xlsx → one table per sheet, named after the sheet
        - .db / .sqlite → used directly via file path

    Args:
        uploaded_file: A Streamlit UploadedFile or a path-like object
            with a ``.name`` attribute and readable data.

    Returns:
        A SQLAlchemy engine connected to the resulting SQLite database.

    Raises:
        ValueError: If the file extension is not supported.
    """
    name = uploaded_file.name if hasattr(uploaded_file, "name") else str(uploaded_file)
    suffix = Path(name).suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(uploaded_file)
        engine = create_engine("sqlite://", echo=False)
        df.to_sql("uploaded_data", engine, index=False, if_exists="replace")
        return engine

    if suffix == ".xlsx":
        engine = create_engine("sqlite://", echo=False)
        xls = pd.ExcelFile(uploaded_file)
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            # Sanitize sheet name for SQL table name
            table_name = sheet_name.strip().replace(" ", "_").lower()
            df.to_sql(table_name, engine, index=False, if_exists="replace")
        return engine

    if suffix in (".db", ".sqlite"):
        # Save uploaded bytes to a temp file so SQLite can open it
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        engine = create_engine(f"sqlite:///{tmp_path}", echo=False)
        return engine

    raise ValueError(
        f"Unsupported file format: '{suffix}'. "
        "SQL mode supports .csv, .xlsx, .db, and .sqlite files."
    )


def load_documents(uploaded_files: list) -> list[Document]:
    """Load uploaded PDF and TXT files into LangChain Document objects.

    Each file is saved to a temporary location for the loaders to read.
    PDF pages are tracked via metadata. TXT files are loaded as a single
    document with the source filename in metadata.

    Args:
        uploaded_files: A list of Streamlit UploadedFile objects (PDF or TXT).

    Returns:
        A flat list of Document objects from all uploaded files.

    Raises:
        ValueError: If a file has an unsupported extension.
    """
    all_docs: list[Document] = []

    for uploaded_file in uploaded_files:
        name = uploaded_file.name if hasattr(uploaded_file, "name") else str(uploaded_file)
        suffix = Path(name).suffix.lower()

        # Save to temp file so loaders can read from disk
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        if suffix == ".pdf":
            docs = PyPDFLoader(tmp_path).load()
            # Inject original filename into metadata
            for doc in docs:
                doc.metadata["source"] = name
            all_docs.extend(docs)

        elif suffix == ".txt":
            docs = TextLoader(tmp_path).load()
            for doc in docs:
                doc.metadata["source"] = name
                doc.metadata["page"] = 0
            all_docs.extend(docs)

        else:
            raise ValueError(
                f"Unsupported file format: '{suffix}'. "
                "RAG mode supports .pdf and .txt files."
            )

    return all_docs

