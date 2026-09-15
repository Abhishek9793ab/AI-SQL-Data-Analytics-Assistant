import random
import time

from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ============================================================
# CHART SPEC
# ============================================================

class ChartSpec(BaseModel):
    type: str = Field(
        default="none",
        description="Chart type: bar, line, pie, doughnut, scatter, or none",
    )
    x_column: str = Field(
        default="",
        description="Column used for X axis/category",
    )
    y_column: str = Field(
        default="",
        description="Column used for Y axis/value",
    )
    title: str = Field(
        default="Analysis",
        description="Short chart title",
    )


# ============================================================
# SQL PLAN
# ============================================================

class SQLPlan(BaseModel):
    sql: str = Field(
        description="One safe SQLite SELECT or WITH query",
    )
    intent: str = Field(
        default="Analysis completed",
        description="Short description of what the query answers",
    )
    chart: ChartSpec = Field(
        default_factory=ChartSpec,
    )
    explanation_focus: str = Field(
        default="Explain the returned data using only actual results",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Useful follow-up questions",
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are an expert AI Data Analyst and SQL generation engine.

Your job is to convert a user's natural-language question into ONE
safe SQLite SQL query using ONLY the supplied dataset schema.

IMPORTANT:
The conversation context may contain previous user questions,
previous SQL queries, previous actual query results, and previous
AI insights.

You MUST use that conversation context when the current question
is a follow-up.

FOLLOW-UP / REFERENCE RESOLUTION
================================

Resolve references such as:

- there
- they
- them
- their
- that
- that department
- this department
- those employees
- those people
- the same group
- the same employees
- it
- its
- above
- below
- highest one
- lowest one
- the previous result
- the selected department

using the MOST RECENT relevant conversation context.

Example:

Previous question:
Which department has the highest average salary?

Previous actual result:
IT | 80600
Finance | 73250
Marketing | 72000
HR | 61250
Sales | 61000

Current question:
How many employees work there?

Correct interpretation:
"there" refers to IT.

Therefore generate a query equivalent to:

SELECT COUNT(*)
FROM dataset
WHERE department = 'IT'

Do NOT interpret the current question as a standalone question
when previous context clearly determines its meaning.

Another example:

Previous result:
IT | 80600

Current:
What about their average experience?

Interpret "their" as employees in IT.

Another example:

Previous result:
IT | 4 employees

Current:
What is their average age?

Interpret "their" as the employees belonging to IT.

CONVERSATION PRIORITY
=====================

1. Current question
2. Most recent relevant actual result
3. Previous question
4. Previous SQL
5. Older conversation context

Never invent context.

If a reference is genuinely ambiguous and cannot be resolved
from the available conversation, make the safest reasonable
interpretation using the dataset schema.

DATASET RULES
=============

1. Generate SQL ONLY for the supplied dataset.
2. Use ONLY the supplied SQLite table.
3. Use ONLY database column names from the supplied schema.
4. Never invent columns.
5. Never use original display names when database names differ.
6. SQLite syntax only.
7. Generate exactly ONE SQL statement.
8. SQL must start with SELECT or WITH.
9. Never generate INSERT.
10. Never generate UPDATE.
11. Never generate DELETE.
12. Never generate DROP.
13. Never generate ALTER.
14. Never generate CREATE.
15. Never generate REPLACE.
16. Never generate ATTACH.
17. Never generate DETACH.
18. Never access SQLite system tables.
19. Never use PRAGMA.
20. Never use load_extension.
21. Never modify the dataset.
22. For totals use SUM().
23. For averages use AVG().
24. For counts use COUNT().
25. For highest values use ORDER BY ... DESC.
26. For lowest values use ORDER BY ... ASC.
27. For grouped analysis use GROUP BY.
28. For category comparisons return the category plus metric.
29. Keep result sets reasonably small.
30. Never fabricate a result.

CHART RULES
===========

Suggest a chart only when it makes sense.

Use:
- bar for category comparisons
- line for ordered/time trends
- pie or doughnut for simple category distributions
- scatter for two numeric variables
- none for single-value results or unsuitable data

Return valid structured JSON matching the requested schema.
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    api_key = getattr(settings, "GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=api_key,
    )


# ============================================================
# MODEL CANDIDATES
# ============================================================

def get_model_candidates():
    primary = getattr(
        settings,
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    fallback = getattr(
        settings,
        "GEMINI_FALLBACK_MODEL",
        "gemini-3.7-flash",
    )

    models = []

    for model in [primary, fallback]:
        model = str(model).strip()

        if model and model not in models:
            models.append(model)

    return models


# ============================================================
# TRANSIENT ERROR CHECK
# ============================================================

def is_transient_error(exc):
    text = str(exc).lower()

    transient_words = [
        "503",
        "429",
        "500",
        "502",
        "504",
        "unavailable",
        "overloaded",
        "timeout",
        "timed out",
        "temporarily",
        "deadline exceeded",
        "resource exhausted",
    ]

    return any(
        word in text
        for word in transient_words
    )


# ============================================================
# GEMINI CALL
# ============================================================

def call_gemini(
    *,
    client,
    model,
    prompt,
):
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=SQLPlan,
            temperature=0.1,
        ),
    )

    if not response:
        raise ValueError(
            "Gemini returned an empty response."
        )

    parsed = response.parsed

    if parsed is not None:
        if isinstance(parsed, SQLPlan):
            return parsed

        return SQLPlan.model_validate(parsed)

    text = getattr(
        response,
        "text",
        "",
    )

    if not text:
        raise ValueError(
            "Gemini returned no structured response."
        )

    return SQLPlan.model_validate_json(text)


# ============================================================
# GENERATE SQL PLAN
# ============================================================

def generate_sql_plan(
    *,
    question,
    schema_context,
    conversation_context="",
):
    question = str(question).strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    schema_context = str(
        schema_context or ""
    ).strip()

    conversation_context = str(
        conversation_context or ""
    ).strip()

    if conversation_context:
        conversation_section = f"""
PREVIOUS CONVERSATION CONTEXT
=============================

The following is real conversation history from this dataset.

Use it to resolve follow-up references.

{conversation_context}

END PREVIOUS CONVERSATION CONTEXT
"""
    else:
        conversation_section = """
PREVIOUS CONVERSATION CONTEXT
=============================

No previous conversation is available.

Treat the current question as a new question.

END PREVIOUS CONVERSATION CONTEXT
"""

    prompt = f"""
DATASET SCHEMA
==============

{schema_context}


{conversation_section}


CURRENT USER QUESTION
=====================

{question}


TASK
====

Generate the SQL plan for the CURRENT USER QUESTION.

Before generating SQL:

1. Determine whether this is a standalone question or a follow-up.
2. If it is a follow-up, resolve pronouns and references using the
   previous conversation.
3. Pay special attention to the MOST RECENT actual result.
4. Do not ignore previous actual results.
5. Do not convert a contextual follow-up into an unrelated
   whole-dataset query.
6. Generate SQL only after understanding the conversation context.

Return ONLY the structured SQL plan.
"""

    client = get_gemini_client()
    models = get_model_candidates()

    last_error = None

    for model in models:

        for attempt in range(3):

            try:
                return call_gemini(
                    client=client,
                    model=model,
                    prompt=prompt,
                )

            except Exception as exc:
                last_error = exc

                print(
                    f"\n[GEMINI SQL ERROR]"
                )
                print(
                    f"Model: {model}"
                )
                print(
                    f"Attempt: {attempt + 1}/3"
                )
                print(
                    f"{type(exc).__name__}: {exc}"
                )

                if not is_transient_error(exc):
                    break

                delay = (
                    1.5 * (2 ** attempt)
                    + random.uniform(0, 0.5)
                )

                time.sleep(delay)

    if last_error:
        raise last_error

    raise ValueError(
        "Gemini could not generate a SQL plan."
    )


# ============================================================
# DATA INSIGHT
# ============================================================

def generate_data_insight(
    *,
    question,
    sql,
    columns,
    rows,
):
    columns = columns or []
    rows = rows or []

    if not columns:
        return (
            "The query did not return any columns."
        )

    if not rows:
        return (
            "No matching records were found."
        )

    # Keep AI prompt small and grounded in actual results.
    limited_rows = rows[:50]

    prompt = f"""
You are an AI data analyst.

Answer the user's question using ONLY the actual query result
provided below.

Do not invent numbers.

Do not mention Gemini.

Do not mention SQL.

Do not say "the query".

Do not use information that is not present in the actual result.

Use Indian currency formatting when the result represents salary,
revenue, cost, price, or another monetary value.

For Indian monetary values use ₹ instead of $.

Be concise but useful.

USER QUESTION:
{question}

GENERATED SQL:
{sql}

RESULT COLUMNS:
{columns}

ACTUAL RESULT:
{limited_rows}

Write a natural-language explanation of the result.
"""

    client = get_gemini_client()
    models = get_model_candidates()

    last_error = None

    for model in models:

        for attempt in range(3):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                    ),
                )

                text = getattr(
                    response,
                    "text",
                    "",
                )

                if text:
                    return text.strip()

                raise ValueError(
                    "Gemini returned an empty insight."
                )

            except Exception as exc:
                last_error = exc

                print(
                    f"\n[AI INSIGHT ERROR]"
                )
                print(
                    f"Model: {model}"
                )
                print(
                    f"Attempt: {attempt + 1}/3"
                )
                print(
                    f"{type(exc).__name__}: {exc}"
                )

                if not is_transient_error(exc):
                    break

                delay = (
                    1.5 * (2 ** attempt)
                    + random.uniform(0, 0.5)
                )

                time.sleep(delay)

    if last_error:
        raise last_error

    return (
        f"The result contains {len(rows)} row(s)."
    )