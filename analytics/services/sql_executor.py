import time

from django.conf import settings
from django.db import connection

from .sql_validator import validate_sql


def execute_safe_query(
    sql: str,
    allowed_table: str,
):
    """
    Execute only validated SELECT/WITH queries.

    Returns:
        columns
        rows
        row_count
        truncated
        execution_ms
    """

    # ---------------------------------------------------------
    # 1. Validate SQL
    # ---------------------------------------------------------
    sql = validate_sql(
        sql,
        allowed_table,
    )

    # ---------------------------------------------------------
    # 2. Maximum rows allowed for UI
    # ---------------------------------------------------------
    max_rows = int(
        getattr(
            settings,
            "MAX_QUERY_ROWS",
            1000,
        )
    )

    if max_rows < 1:
        max_rows = 1000

    # ---------------------------------------------------------
    # 3. Wrap query with LIMIT
    # ---------------------------------------------------------
    wrapped_sql = f"""
        SELECT *
        FROM (
            {sql}
        ) AS analytics_result
        LIMIT {max_rows}
    """

    # ---------------------------------------------------------
    # 4. Execute query + measure real execution time
    # ---------------------------------------------------------
    start = time.perf_counter()

    with connection.cursor() as cursor:

        cursor.execute(wrapped_sql)

        rows = cursor.fetchall()

        if cursor.description:
            columns = [
                column[0]
                for column in cursor.description
            ]
        else:
            columns = []

    elapsed_ms = (
        time.perf_counter() - start
    ) * 1000

    # ---------------------------------------------------------
    # 5. Convert database rows to JSON-friendly lists
    # ---------------------------------------------------------
    result_rows = [
        list(row)
        for row in rows
    ]

    # ---------------------------------------------------------
    # 6. Detect whether result was limited
    # ---------------------------------------------------------
    truncated = (
        len(result_rows) >= max_rows
    )

    # ---------------------------------------------------------
    # 7. Return result
    # ---------------------------------------------------------
    return {
        "columns": columns,
        "rows": result_rows,
        "row_count": len(result_rows),
        "truncated": truncated,

        # IMPORTANT:
        # result_formatter.py expects this exact key.
        "execution_ms": round(
            elapsed_ms,
            2,
        ),

        "sql": sql,
    }