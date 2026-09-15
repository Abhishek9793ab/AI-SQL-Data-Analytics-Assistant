from datasets.models import Dataset, DatasetColumn


def build_schema_context(dataset: Dataset) -> str:
    """
    Build a schema description for Gemini.

    IMPORTANT:
    Dataset.columns is the integer count of columns.
    Actual column definitions are stored in DatasetColumn.
    """

    # =========================================================
    # 1. BASIC DATASET INFORMATION
    # =========================================================

    dataset_name = str(
        getattr(dataset, "name", "")
    )

    table_name = str(
        getattr(dataset, "database_table", "")
    )

    row_count = int(
        getattr(dataset, "rows", 0) or 0
    )

    column_count = int(
        getattr(dataset, "columns", 0) or 0
    )

    # =========================================================
    # 2. GET ACTUAL DATASET COLUMNS
    # =========================================================

    columns = (
        DatasetColumn.objects
        .filter(dataset=dataset)
        .order_by("position")
    )

    # =========================================================
    # 3. BUILD COLUMN INFORMATION
    # =========================================================

    column_lines = []

    for column in columns:

        database_name = str(
            getattr(
                column,
                "database_name",
                "",
            )
        )

        original_name = str(
            getattr(
                column,
                "original_name",
                database_name,
            )
        )

        data_type = str(
            getattr(
                column,
                "data_type",
                "text",
            )
        )

        nullable = bool(
            getattr(
                column,
                "nullable",
                True,
            )
        )

        null_count = int(
            getattr(
                column,
                "null_count",
                0,
            )
            or 0
        )

        unique_values = int(
            getattr(
                column,
                "unique_values",
                0,
            )
            or 0
        )

        sample_values = getattr(
            column,
            "sample_values",
            [],
        )

        # -----------------------------------------------------
        # Sample values
        # -----------------------------------------------------

        if sample_values is None:
            sample_values = []

        if not isinstance(
            sample_values,
            list,
        ):
            sample_values = [sample_values]

        sample_text = ", ".join(
            str(value)
            for value in sample_values[:5]
        )

        if not sample_text:
            sample_text = "No sample values available"

        # -----------------------------------------------------
        # Column description
        # -----------------------------------------------------

        column_lines.append(
            (
                f"- Database field: {database_name}\n"
                f"  Original column: {original_name}\n"
                f"  Data type: {data_type}\n"
                f"  Nullable: {nullable}\n"
                f"  Null count: {null_count}\n"
                f"  Unique values: {unique_values}\n"
                f"  Sample values: {sample_text}"
            )
        )

    # =========================================================
    # 4. HANDLE EMPTY SCHEMA
    # =========================================================

    if column_lines:

        columns_text = "\n".join(
            column_lines
        )

    else:

        columns_text = (
            "No DatasetColumn records were found."
        )

    # =========================================================
    # 5. FINAL GEMINI SCHEMA CONTEXT
    # =========================================================

    schema_context = f"""
DATASET INFORMATION
===================

Dataset name:
{dataset_name}

SQLite table name:
{table_name}

Total rows:
{row_count}

Total columns:
{column_count}


AVAILABLE COLUMNS
=================

{columns_text}


SQL GENERATION RULES
====================

1. Generate SQL only for this dataset.

2. Use ONLY the SQLite table:
   {table_name}

3. Use ONLY database field names listed above.

4. Do NOT use original display names when they differ from
   database field names.

5. Generate SELECT queries only.

6. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, REPLACE, ATTACH, DETACH or other write operations.

7. Do not access SQLite system tables.

8. Do not invent columns.

9. Use SQLite-compatible SQL syntax.

10. For averages use AVG().

11. For totals use SUM().

12. For counting records use COUNT().

13. For highest value use ORDER BY ... DESC.

14. For lowest value use ORDER BY ... ASC.

15. For grouped analysis use GROUP BY.

16. When comparing categories, return the category field
    together with the calculated metric.

17. Keep result sets reasonably small unless the user
    explicitly asks for detailed rows.

18. Never explain or invent a result that is not returned
    by the SQL query.
"""

    return schema_context.strip()