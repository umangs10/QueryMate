"""SQL mode — LangChain SQL agent for structured data queries.

Uses the ``tool-calling`` agent type with Gemini to translate natural
language questions into SQL, execute them, and return answers.
"""

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import Engine, inspect

from utils.response import extract_text


def get_schema_info(engine: Engine) -> list[dict]:
    """Extract table and column metadata from a SQLAlchemy engine.

    Args:
        engine: A SQLAlchemy engine connected to a database.

    Returns:
        A list of dicts, each with ``table`` (str) and ``columns`` (list[str]).
    """
    inspector = inspect(engine)
    schema = []
    for table_name in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        schema.append({"table": table_name, "columns": columns})
    return schema


def handle_sql_mode(
    engine: Engine,
    user_question: str,
    llm: ChatGoogleGenerativeAI,
) -> dict:
    """Run a natural-language question against a SQL database via an agent.

    Applies dual-layer SQL safety checks:
    1. Before invocation — on the user's raw input.
    2. After invocation — on the agent's generated SQL.

    Args:
        engine: A SQLAlchemy engine with the user's data loaded.
        user_question: The natural-language question to answer.
        llm: A configured ChatGoogleGenerativeAI instance.

    Returns:
        A dict with keys:
            - ``answer`` (str): The agent's natural-language answer.
            - ``sql`` (str): The generated SQL query (if extractable).
            - ``tables`` (list[str]): Table names in the database.
    """
    from utils.guardrails import check_sql_safety

    # ── Layer 1: Check user input ────────────────────────────────────
    is_safe, message = check_sql_safety(user_question)
    if not is_safe:
        return {
            "answer": f"⚠️ Query blocked: {message}. Only read-only queries are allowed.",
            "sql": "",
            "tables": [],
        }

    db = SQLDatabase(engine)
    tables = db.get_usable_table_names()

    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        verbose=True,
        handle_parsing_errors=True,
    )

    result = agent_executor.invoke({"input": user_question})

    # Extract the answer
    answer = extract_text(result.get("output", "No answer generated."))

    # Try to extract generated SQL from intermediate steps
    sql = _extract_sql_from_steps(result)

    # ── Layer 2: Check generated SQL ─────────────────────────────────
    if sql:
        is_safe, message = check_sql_safety(sql)
        if not is_safe:
            return {
                "answer": f"⚠️ Generated SQL blocked: {message}. The agent attempted a destructive operation.",
                "sql": sql,
                "tables": list(tables),
            }

    return {"answer": answer, "sql": sql, "tables": list(tables)}


def _extract_sql_from_steps(result: dict) -> str:
    """Pull the SQL query string from the agent's intermediate steps.

    Args:
        result: The full result dict from agent_executor.invoke().

    Returns:
        The SQL string if found, otherwise an empty string.
    """
    steps = result.get("intermediate_steps", [])
    for action, _observation in steps:
        # The SQL agent uses sql_db_query tool — the input is the SQL
        if hasattr(action, "tool") and action.tool == "sql_db_query":
            return action.tool_input if isinstance(action.tool_input, str) else str(action.tool_input)
    return ""
