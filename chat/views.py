import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime
from django.views.decorators.http import require_POST
from django.utils import timezone

from datasets.models import Dataset

from .models import Conversation, Message
from .services.query_pipeline import run_query_pipeline


@login_required
@require_POST
def ask_question(request, dataset_id):

    dataset = get_object_or_404(
        Dataset,
        id=dataset_id,
        owner=request.user,
        status="ready",
    )

    try:
        data = json.loads(
            request.body.decode("utf-8")
            if request.body
            else "{}"
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    question = str(
        data.get("question", "")
    ).strip()

    if not question:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Please enter a question "
                    "about your dataset."
                ),
            },
            status=400,
        )

    if len(question) > 2000:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Question is too long. "
                    "Maximum 2000 characters allowed."
                ),
            },
            status=400,
        )

    conversation_id = data.get(
        "conversation_id"
    )

    conversation = None
    new_conversation = False

    if conversation_id:

        try:
            conversation_id = int(
                conversation_id
            )

        except (
            TypeError,
            ValueError,
        ):

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid conversation ID.",
                },
                status=400,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
            dataset=dataset,
        )

    else:

        conversation = Conversation(
            user=request.user,
            dataset=dataset,
            title=question[:80],
        )

        new_conversation = True

    try:

        result = run_query_pipeline(
            user=request.user,
            dataset=dataset,
            conversation=conversation,
            question=question,
        )

    except Exception as exc:

        print("\n" + "=" * 70)
        print("AI SQL ANALYST ERROR")
        print("=" * 70)
        print(type(exc).__name__)
        print(str(exc))
        print("=" * 70 + "\n")

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    if new_conversation:
        conversation.save()

    plan = result.get(
        "plan",
        {},
    )

    if not isinstance(plan, dict):
        plan = {}

    query_result = result.get(
        "result",
        {},
    )

    if not isinstance(
        query_result,
        dict,
    ):
        query_result = {}

    sql = str(
        plan.get(
            "sql",
            "",
        )
    ).strip()

    columns = query_result.get(
        "columns",
        [],
    )

    rows = query_result.get(
        "rows",
        [],
    )

    if not isinstance(columns, list):
        columns = []

    if not isinstance(rows, list):
        rows = []

    row_count = query_result.get(
        "row_count",
        len(rows),
    )

    try:
        row_count = int(row_count)

    except (
        TypeError,
        ValueError,
    ):
        row_count = len(rows)

    execution_ms = query_result.get(
        "execution_ms",
        0,
    )

    try:
        execution_ms = round(
            float(execution_ms),
            2,
        )

    except (
        TypeError,
        ValueError,
    ):
        execution_ms = 0

    truncated = bool(
        query_result.get(
            "truncated",
            False,
        )
    )

    intent = str(
        plan.get(
            "intent",
            "Analysis completed",
        )
    ).strip()

    if not intent:
        intent = "Analysis completed"

    chart = plan.get(
        "chart",
        {},
    )

    if not isinstance(chart, dict):
        chart = {}

    chart_type = str(
        chart.get(
            "type",
            "none",
        )
    ).strip().lower()

    allowed_chart_types = {
        "bar",
        "line",
        "pie",
        "doughnut",
        "scatter",
        "none",
    }

    if chart_type not in allowed_chart_types:
        chart_type = "none"

    chart_x = str(
        chart.get(
            "x_column",
            "",
        )
    ).strip()

    chart_y = str(
        chart.get(
            "y_column",
            "",
        )
    ).strip()

    chart_title = str(
        chart.get(
            "title",
            "Analysis",
        )
    ).strip()

    if not chart_title:
        chart_title = "Analysis"

    explanation = str(
        result.get(
            "ai_insight",
            plan.get(
                "ai_insight",
                "",
            ),
        )
    ).strip()

    if not explanation:
        explanation = (
            "No additional explanation "
            "was generated."
        )

    suggestions = plan.get(
        "suggestions",
        [],
    )

    if not isinstance(
        suggestions,
        list,
    ):
        suggestions = []

    cleaned_suggestions = []

    for suggestion in suggestions:

        suggestion = str(
            suggestion
        ).strip()

        if suggestion:
            cleaned_suggestions.append(
                suggestion
            )

    cleaned_suggestions = (
        cleaned_suggestions[:5]
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.USER,
        content=question,
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.ASSISTANT,
        content=explanation,
        sql=sql,
        result_json={
            "columns": columns,
            "rows": rows[:50],
            "row_count": row_count,
            "execution_ms": execution_ms,
            "truncated": truncated,
        },
        metadata_json={
            "ai_insight": explanation,
            "intent": intent,
            "chart_type": chart_type,
            "chart_x": chart_x,
            "chart_y": chart_y,
            "chart_title": chart_title,
            "suggestions": cleaned_suggestions,
        },
    )

    conversation.save(
        update_fields=["updated_at"]
    )

    return JsonResponse(
        {
            "success": True,
            "conversation_id": conversation.id,
            "question": question,
            "dataset": dataset.name,
            "dataset_id": dataset.id,
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "execution_ms": execution_ms,
            "truncated": truncated,
            "intent": intent,
            "explanation": explanation,

            # Chart information
            "chart_type": chart_type,
            "chart_x": chart_x,
            "chart_y": chart_y,
            "chart_title": chart_title,

            "follow_up_suggestions": cleaned_suggestions,

            "intelligence": result.get("intelligence", {}),
            "intelligence_summary": result.get("intelligence_summary", ""),

            "result": {
                "columns": columns,
                "rows": rows,
                "row_count": row_count,
                "execution_ms": execution_ms,
                "truncated": truncated,
            },
        }
    )


@login_required
def conversation_history(request, dataset_id):

    dataset = get_object_or_404(
        Dataset,
        id=dataset_id,
        owner=request.user,
    )

    conversations = (
        Conversation.objects
        .filter(
            user=request.user,
            dataset=dataset,
        )
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    data = []

    for conversation in conversations:

        messages = list(
            conversation.messages.all()
        )

        last_message = (
            messages[-1]
            if messages
            else None
        )

        data.append(
            {
                "id": conversation.id,

                "title": conversation.title,

                # India time / IST
                "created_at": localtime(
                    conversation.created_at
                ).strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                # India time / IST
                "updated_at": localtime(
                    conversation.updated_at
                ).strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                "message_count": len(
                    messages
                ),

                "last_message": (
                    last_message.content[:120]
                    if last_message
                    else ""
                ),
            }
        )

    return JsonResponse(
        {
            "success": True,
            "dataset": dataset.name,
            "dataset_id": dataset.id,
            "conversations": data,
        }
    )

@login_required
def export_conversation(
    request,
    conversation_id,
):
    import csv
    import json

    from django.http import HttpResponse

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user,
    )

    messages = conversation.messages.order_by(
        "created_at"
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        f'filename="conversation_{conversation.id}.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Role",
        "Message",
        "SQL",
        "Result",
        "Created At",
    ])

    for message in messages:

        result = getattr(
            message,
            "result_json",
            {},
        )

        writer.writerow([
            message.role,
            message.content,
            message.sql,
            json.dumps(
                result,
                ensure_ascii=False,
            ),
            message.created_at,
        ])

    return response
