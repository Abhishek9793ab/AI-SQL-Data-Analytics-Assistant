from datasets.models import Dataset

from analytics.services.llm_service import generate_sql_plan
from analytics.services.result_formatter import format_result
from analytics.services.schema_context import build_schema_context
from analytics.services.sql_executor import execute_safe_query


def build_conversation_context(conversation, limit=8):

    if conversation is None:
        return ""

    try:
        messages = list(
            conversation.messages
            .order_by("-created_at")[:limit]
        )
    except AttributeError:
        return ""

    messages.reverse()

    context_blocks = []

    for index, message in enumerate(messages, start=1):

        role = str(
            getattr(message, "role", "")
        ).upper()

        content = str(
            getattr(message, "content", "")
        ).strip()

        if not content:
            continue

        block = [
            f"MESSAGE {index}",
            f"ROLE: {role}",
            f"CONTENT: {content}",
        ]

        sql = str(
            getattr(message, "sql", "")
        ).strip()

        if sql:
            block.extend([
                "",
                "PREVIOUS SQL:",
                sql,
            ])

        result_json = getattr(
            message,
            "result_json",
            {},
        )

        if isinstance(result_json, dict):

            columns = result_json.get(
                "columns",
                [],
            )

            rows = result_json.get(
                "rows",
                [],
            )

            if columns:
                block.extend([
                    "",
                    "ACTUAL RESULT COLUMNS:",
                    str(columns),
                ])

            if rows:
                block.extend([
                    "",
                    "ACTUAL RESULT ROWS:",
                    str(rows[:20]),
                ])

        metadata_json = getattr(
            message,
            "metadata_json",
            {},
        )

        if isinstance(metadata_json, dict):

            insight = str(
                metadata_json.get(
                    "ai_insight",
                    "",
                )
            ).strip()

            if insight:
                block.extend([
                    "",
                    "PREVIOUS INSIGHT:",
                    insight,
                ])

        context_blocks.append(
            "\n".join(block)
        )

    return "\n\n".join(context_blocks)


def generate_local_insight(
    question,
    columns,
    rows,
):

    if not rows:
        return "No matching records were found."

    if not columns:
        return (
            f"The analysis returned "
            f"{len(rows)} result row(s)."
        )

    if len(rows) == 1 and len(columns) == 1:

        value = rows[0].get(
            columns[0]
        )

        return f"The result is {value}."

    if len(columns) == 2:

        category_column = columns[0]
        value_column = columns[1]

        valid_rows = []

        for row in rows:

            category = row.get(
                category_column
            )

            value = row.get(
                value_column
            )

            if category is not None:
                valid_rows.append(
                    (category, value)
                )

        numeric_rows = []

        for category, value in valid_rows:

            try:
                numeric_value = float(value)

                numeric_rows.append(
                    (
                        category,
                        numeric_value,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

        if numeric_rows:

            highest = max(
                numeric_rows,
                key=lambda item: item[1],
            )

            lowest = min(
                numeric_rows,
                key=lambda item: item[1],
            )

            def format_number(value):

                if float(value).is_integer():
                    return f"{int(value):,}"

                return f"{value:,.2f}"

            return (
                f"The analysis returned "
                f"{len(valid_rows)} categories. "
                f"The highest value is "
                f"{highest[0]} at "
                f"{format_number(highest[1])}, "
                f"while the lowest is "
                f"{lowest[0]} at "
                f"{format_number(lowest[1])}."
            )

    return (
        f"The analysis returned "
        f"{len(rows)} result row(s)."
    )


def run_query_pipeline(
    *,
    user,
    dataset: Dataset,
    conversation=None,
    question: str,
):

    question = str(question).strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    schema_context = build_schema_context(
        dataset
    )

    if not schema_context:
        raise ValueError(
            "Dataset schema could not be generated."
        )

    conversation_context = (
        build_conversation_context(
            conversation,
            limit=8,
        )
    )

    plan = generate_sql_plan(
        question=question,
        schema_context=schema_context,
        conversation_context=conversation_context,
    )

    if plan is None:
        raise ValueError(
            "Gemini did not return a SQL plan."
        )

    sql = str(
        getattr(plan, "sql", "")
    ).strip()

    if not sql:
        raise ValueError(
            "Gemini did not generate SQL."
        )

    query_result = execute_safe_query(
        sql=sql,
        allowed_table=dataset.database_table,
    )

    formatted_result = format_result(
        query_result
    )

    columns = formatted_result.get(
        "columns",
        [],
    )

    rows = formatted_result.get(
        "rows",
        [],
    )

    ai_insight = generate_local_insight(
        question=question,
        columns=columns,
        rows=rows,
    )

    plan_data = plan.model_dump()

    plan_data["ai_insight"] = ai_insight

    return {
        "plan": plan_data,
        "result": formatted_result,
        "ai_insight": ai_insight,
    }