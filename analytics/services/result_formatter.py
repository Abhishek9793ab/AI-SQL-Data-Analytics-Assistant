from datetime import date, datetime
from decimal import Decimal

import math


def make_json_safe(value):
    """
    Convert SQLite/Python values into JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def format_result(result):
    """
    Format SQL execution result into a clean JSON-safe structure.

    Expected input:

    {
        "columns": [...],
        "rows": [...],
        "row_count": 10,
        "truncated": False,
        "execution_ms": 12.5
    }
    """

    if not result:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "execution_ms": 0,
        }

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    safe_rows = []

    for row in rows:
        safe_row = {}

        if isinstance(row, dict):

            for column, value in row.items():
                safe_row[str(column)] = make_json_safe(value)

        else:

            for index, value in enumerate(row):

                if index < len(columns):
                    column_name = columns[index]
                else:
                    column_name = f"column_{index + 1}"

                safe_row[str(column_name)] = make_json_safe(
                    value
                )

        safe_rows.append(safe_row)

    return {
        "columns": [
            str(column)
            for column in columns
        ],

        "rows": safe_rows,

        "row_count": int(
            result.get(
                "row_count",
                len(safe_rows)
            )
        ),

        "truncated": bool(
            result.get(
                "truncated",
                False
            )
        ),

        "execution_ms": round(
            float(
                result.get(
                    "execution_ms",
                    0
                )
            ),
            2
        ),
    }