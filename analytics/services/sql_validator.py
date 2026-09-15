import re


# =========================================================
# FORBIDDEN SQL KEYWORDS
# =========================================================

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "UPSERT",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "ANALYZE",
    "TRIGGER",
    "GRANT",
    "REVOKE",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE",
}


# =========================================================
# IDENTIFIER HELPERS
# =========================================================

def normalize_identifier(identifier):
    """
    Normalize a SQLite identifier for comparison.
    """

    identifier = identifier.strip()

    if (
        identifier.startswith('"')
        and identifier.endswith('"')
    ):
        identifier = identifier[1:-1]

    if (
        identifier.startswith("`")
        and identifier.endswith("`")
    ):
        identifier = identifier[1:-1]

    if (
        identifier.startswith("[")
        and identifier.endswith("]")
    ):
        identifier = identifier[1:-1]

    return identifier.lower()


# =========================================================
# REMOVE SQL COMMENTS
# =========================================================

def remove_sql_comments(sql):
    """
    Remove SQL comments before validation.
    """

    sql = re.sub(
        r"--[^\n]*",
        " ",
        sql
    )

    sql = re.sub(
        r"/\*.*?\*/",
        " ",
        sql,
        flags=re.DOTALL
    )

    return sql


# =========================================================
# CHECK FOR FORBIDDEN KEYWORDS
# =========================================================

def check_forbidden_keywords(sql):
    """
    Reject dangerous SQL operations.
    """

    for keyword in FORBIDDEN_KEYWORDS:

        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                f"Unsafe SQL operation detected: {keyword}"
            )


# =========================================================
# CHECK STATEMENT TYPE
# =========================================================

def check_statement_type(sql):
    """
    Only SELECT and WITH queries are allowed.
    """

    stripped = sql.strip()

    if not stripped:
        raise ValueError(
            "SQL query cannot be empty."
        )

    first_token_match = re.match(
        r"^\s*([A-Za-z]+)",
        stripped
    )

    if not first_token_match:
        raise ValueError(
            "Invalid SQL query."
        )

    first_token = (
        first_token_match
        .group(1)
        .upper()
    )

    if first_token not in {
        "SELECT",
        "WITH",
    }:
        raise ValueError(
            "Only SELECT queries are allowed."
        )


# =========================================================
# CHECK MULTIPLE STATEMENTS
# =========================================================

def check_multiple_statements(sql):
    """
    Multiple SQL statements are not allowed.

    Example blocked:

        SELECT * FROM table;
        DROP TABLE table
    """

    if ";" in sql:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )


# =========================================================
# CHECK SYSTEM TABLE ACCESS
# =========================================================

def check_system_tables(sql):
    """
    Prevent access to SQLite internal tables.
    """

    forbidden_tables = {
        "sqlite_master",
        "sqlite_schema",
        "sqlite_temp_master",
        "sqlite_sequence",
    }

    for table in forbidden_tables:

        pattern = (
            rf"\b{re.escape(table)}\b"
        )

        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                "Access to SQLite system tables is not allowed."
            )


# =========================================================
# FIND TABLE REFERENCES
# =========================================================

def extract_table_references(sql):
    """
    Extract tables used after FROM and JOIN.

    Supports normal SQLite identifiers.
    """

    pattern = (
        r"\b(?:FROM|JOIN)\s+"
        r"(?:"
        r'"([^"]+)"'
        r"|`([^`]+)`"
        r"|\[([^\]]+)\]"
        r"|([A-Za-z_][A-Za-z0-9_]*)"
        r")"
    )

    matches = re.findall(
        pattern,
        sql,
        flags=re.IGNORECASE
    )

    tables = []

    for match in matches:

        table = next(
            (
                item
                for item in match
                if item
            ),
            None
        )

        if table:
            tables.append(
                normalize_identifier(table)
            )

    return tables


# =========================================================
# DATASET TABLE ALLOWLIST
# =========================================================

def check_table_allowlist(
    sql,
    allowed_table
):
    """
    Ensure the query only accesses
    the currently selected dataset.
    """

    allowed_table = normalize_identifier(
        allowed_table
    )

    tables = extract_table_references(
        sql
    )

    for table in tables:

        # Ignore SQL subquery patterns that
        # don't represent a real table.
        if table in {
            "select",
        }:
            continue

        if table != allowed_table:

            raise ValueError(
                "Query attempted to access a "
                f"table outside the selected dataset: {table}"
            )


# =========================================================
# CHECK DANGEROUS FUNCTIONS
# =========================================================

def check_dangerous_functions(sql):
    """
    Block SQLite functions/features that should
    not be exposed to generated SQL.
    """

    dangerous_functions = {
        "load_extension",
    }

    for function_name in dangerous_functions:

        pattern = (
            rf"\b{re.escape(function_name)}\s*\("
        )

        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                f"Unsafe SQLite function detected: "
                f"{function_name}"
            )


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_sql(
    sql,
    allowed_table
):
    """
    Validate AI-generated SQL before execution.

    Pipeline:

        Gemini SQL
             ↓
        remove comments
             ↓
        SELECT/WITH check
             ↓
        forbidden operation check
             ↓
        multiple statement check
             ↓
        system table check
             ↓
        dangerous function check
             ↓
        dataset table allowlist
             ↓
        safe SQL
    """

    if not isinstance(sql, str):
        raise ValueError(
            "Generated SQL must be a string."
        )

    # Remove leading/trailing whitespace
    sql = sql.strip()

    # Remove comments
    sql = remove_sql_comments(sql)

    # Normalize whitespace
    sql = re.sub(
        r"\s+",
        " ",
        sql
    ).strip()

    # Security checks
    check_statement_type(sql)

    check_multiple_statements(sql)

    check_forbidden_keywords(sql)

    check_system_tables(sql)

    check_dangerous_functions(sql)

    check_table_allowlist(
        sql,
        allowed_table
    )

    return sql