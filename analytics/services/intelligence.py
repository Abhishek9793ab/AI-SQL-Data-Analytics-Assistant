from decimal import Decimal


def to_number(value):
    """
    Convert a value to float when possible.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value):
    """
    Format numeric values for human-readable insights.
    """
    if value is None:
        return "N/A"

    try:
        number = float(value)

        if number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.2f}"

    except (TypeError, ValueError):
        return str(value)


def generate_intelligence(columns, rows):
    """
    Generate factual analytics locally.

    IMPORTANT:
    This function does NOT call Gemini.
    """

    if not rows:
        return {
            "row_count": 0,
            "category_count": 0,
            "numeric_columns": [],
            "insights": [
                "No matching records were found."
            ],
        }

    numeric_columns = []

    for column in columns:
        values = []

        for row in rows:
            number = to_number(
                row.get(column)
            )

            if number is not None:
                values.append(number)

        if values:
            numeric_columns.append(column)

    insights = []

    # --------------------------------------------------
    # ROW COUNT
    # --------------------------------------------------

    insights.append(
        f"The analysis returned {len(rows)} result row(s)."
    )

    # --------------------------------------------------
    # CATEGORY COUNT
    # --------------------------------------------------

    category_count = 0

    if columns:
        first_column = columns[0]

        categories = set()

        for row in rows:
            value = row.get(first_column)

            if value is not None:
                categories.add(str(value))

        category_count = len(categories)

    if len(columns) == 2 and category_count > 1:
        insights.append(
            f"The result contains {category_count} categories."
        )

    # --------------------------------------------------
    # NUMERIC ANALYSIS
    # --------------------------------------------------

    for column in numeric_columns:

        values = []

        for row in rows:
            number = to_number(
                row.get(column)
            )

            if number is not None:
                values.append(number)

        if not values:
            continue

        total = sum(values)
        average = total / len(values)
        highest = max(values)
        lowest = min(values)

        insights.append(
            f"{column}: total {format_number(total)}, "
            f"average {format_number(average)}, "
            f"highest {format_number(highest)}, "
            f"lowest {format_number(lowest)}."
        )

    # --------------------------------------------------
    # CATEGORY + NUMERIC VALUE
    # --------------------------------------------------

    if len(columns) == 2:

        category_column = columns[0]
        value_column = columns[1]

        pairs = []

        for row in rows:

            category = row.get(
                category_column
            )

            value = to_number(
                row.get(value_column)
            )

            if category is not None and value is not None:
                pairs.append(
                    (
                        str(category),
                        value,
                    )
                )

        if pairs:

            highest = max(
                pairs,
                key=lambda item: item[1],
            )

            lowest = min(
                pairs,
                key=lambda item: item[1],
            )

            insights.append(
                f"The highest {value_column} is "
                f"{highest[0]} at "
                f"{format_number(highest[1])}."
            )

            insights.append(
                f"The lowest {value_column} is "
                f"{lowest[0]} at "
                f"{format_number(lowest[1])}."
            )

    return {
        "row_count": len(rows),
        "category_count": category_count,
        "numeric_columns": numeric_columns,
        "insights": insights,
    }


def build_intelligence_summary(columns, rows):
    """
    Return one concise factual summary.
    """

    data = generate_intelligence(
        columns,
        rows,
    )

    insights = data.get(
        "insights",
        [],
    )

    return " ".join(insights)
