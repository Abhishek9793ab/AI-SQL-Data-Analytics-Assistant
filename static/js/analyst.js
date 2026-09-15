document.addEventListener("DOMContentLoaded", function () {

    "use strict";

    /* =========================================================
       CONFIG
    ========================================================= */

    const config = window.ANALYST_CONFIG || {};

    let conversationId = config.conversationId || null;
    let currentChart = null;


    /* =========================================================
       DOM
    ========================================================= */

    const questionInput = document.getElementById("questionInput");
    const askButton = document.getElementById("askButton");
    const askText = document.getElementById("askText");
    const askLoader = document.getElementById("askLoader");

    const loadingPanel = document.getElementById("loadingPanel");
    const resultPanel = document.getElementById("resultPanel");
    const errorPanel = document.getElementById("errorPanel");
    const errorMessage = document.getElementById("errorMessage");

    const resultTitle = document.getElementById("resultTitle");
    const executionTime = document.getElementById("executionTime");
    const rowCount = document.getElementById("rowCount");

    const resultTable = document.getElementById("resultTable");
    const generatedSQL = document.getElementById("generatedSQL");
    const aiExplanation = document.getElementById("aiExplanation");

    const chartContainer = document.getElementById("chartContainer");
    const chartTitle = document.getElementById("chartTitle");
    const resultChart = document.getElementById("resultChart");

    const followupSection = document.getElementById("followupSection");
    const followupSuggestions =
        document.getElementById("followupSuggestions");

    const conversationHistory =
        document.getElementById("conversationHistory");

    const newAnalysisButton =
        document.getElementById("newAnalysisButton");

    const refreshHistoryButton =
        document.getElementById("refreshHistoryButton");


    /* =========================================================
       CSRF
    ========================================================= */

    function getCookie(name) {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {

                return decodeURIComponent(
                    cookie.substring(name.length + 1)
                );

            }

        }

        return "";

    }


    const csrfToken =
        config.csrfToken ||
        getCookie("csrftoken");


    /* =========================================================
       FORMAT VALUE
    ========================================================= */

    function formatValue(value) {

        if (value === null || value === undefined) {
            return "—";
        }

        if (typeof value === "number") {

            if (!Number.isFinite(value)) {
                return String(value);
            }

            if (Number.isInteger(value)) {
                return value.toLocaleString();
            }

            return value.toLocaleString(
                undefined,
                {
                    maximumFractionDigits: 2
                }
            );
        }

        return String(value);
    }


    /* =========================================================
       FORMAT INSIGHT
    ========================================================= */

    function formatInsight(text) {

        if (!text) {
            return "No AI insight available.";
        }

        return String(text)
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");
    }


    /* =========================================================
       RENDER TABLE
    ========================================================= */

    function renderTable(columns, rows) {

        if (!resultTable) {
            return;
        }

        const thead = resultTable.querySelector("thead");
        const tbody = resultTable.querySelector("tbody");

        if (!thead || !tbody) {
            return;
        }

        thead.innerHTML = "";
        tbody.innerHTML = "";

        if (!columns || columns.length === 0) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="1">
                        No columns returned.
                    </td>
                </tr>
            `;

            return;
        }


        /* Header */

        const headerRow = document.createElement("tr");

        columns.forEach(function (column) {

            const th = document.createElement("th");

            th.textContent = column;

            headerRow.appendChild(th);

        });

        thead.appendChild(headerRow);


        /* Rows */

        if (!rows || rows.length === 0) {

            const emptyRow = document.createElement("tr");

            const emptyCell = document.createElement("td");

            emptyCell.colSpan = columns.length;

            emptyCell.textContent = "No rows returned.";

            emptyRow.appendChild(emptyCell);

            tbody.appendChild(emptyRow);

            return;
        }


        rows.forEach(function (row) {

            const tr = document.createElement("tr");

            columns.forEach(function (column) {

                const td = document.createElement("td");

                let value = "";

                if (
                    row !== null &&
                    typeof row === "object"
                ) {
                    value = row[column];
                }

                td.textContent = formatValue(value);

                tr.appendChild(td);

            });

            tbody.appendChild(tr);

        });

    }


    /* =========================================================
       RENDER CHART
    ========================================================= */

    function renderChart(data) {

        if (!chartContainer || !resultChart) {
            return;
        }

        if (currentChart) {

            currentChart.destroy();

            currentChart = null;
        }

        chartContainer.style.display = "none";

        if (!data) {
            return;
        }

        let labels = data.labels || [];
        let values = data.values || [];

        if (
            !Array.isArray(labels) ||
            !Array.isArray(values) ||
            labels.length === 0 ||
            values.length === 0
        ) {
            return;
        }


        if (typeof Chart === "undefined") {
            return;
        }


        chartContainer.style.display = "block";

        if (chartTitle) {
            chartTitle.textContent =
                data.title || "Analysis Chart";
        }


        currentChart = new Chart(
            resultChart.getContext("2d"),
            {
                type: data.type || "bar",

                data: {
                    labels: labels,

                    datasets: [
                        {
                            label: data.label || "Value",
                            data: values,

                            borderWidth: 1
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: true
                        }
                    },

                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );

    }


    /* =========================================================
       RENDER FOLLOW UPS
    ========================================================= */

    function renderFollowups(suggestions) {

        if (!followupSection || !followupSuggestions) {
            return;
        }

        followupSuggestions.innerHTML = "";

        if (
            !Array.isArray(suggestions) ||
            suggestions.length === 0
        ) {
            followupSection.style.display = "none";
            return;
        }

        suggestions.forEach(function (question) {

            if (!question) {
                return;
            }

            const button = document.createElement("button");

            button.type = "button";

            button.className = "suggestion";

            button.textContent = question;

            button.dataset.question = question;

            button.addEventListener(
                "click",
                function () {

                    if (questionInput) {
                        questionInput.value = question;
                        questionInput.focus();
                    }

                }
            );

            followupSuggestions.appendChild(button);

        });

        followupSection.style.display = "block";

    }


    /* =========================================================
       RENDER RESULT
    ========================================================= */

    function renderResult(data) {

        if (!resultPanel) {
            return;
        }

        loadingPanel.style.display = "none";
        errorPanel.style.display = "none";

        resultPanel.style.display = "block";


        /* Conversation */

        if (
            data.conversation_id !== undefined &&
            data.conversation_id !== null
        ) {
            conversationId = data.conversation_id;
        }


        /* Title */

        if (resultTitle) {

            resultTitle.textContent =
                data.question ||
                "Query Result";

        }


        /* Execution */

        if (executionTime) {

            const ms =
                data.execution_ms ??
                data.execution_time ??
                0;

            executionTime.textContent =
                `${ms} ms`;

        }


        /* Row count */

        if (rowCount) {

            const count =
                data.row_count ??
                (Array.isArray(data.rows)
                    ? data.rows.length
                    : 0);

            rowCount.textContent =
                `${count} ${count === 1 ? "row" : "rows"}`;

        }


        /* Table */

        renderTable(
            data.columns || [],
            data.rows || []
        );


        /* SQL */

        if (generatedSQL) {

            generatedSQL.textContent =
                data.sql ||
                "No SQL generated.";

        }


        /* Explanation */

        if (aiExplanation) {

            const explanation =
                data.explanation ||
                data.insight ||
                "No AI insight available.";

            aiExplanation.innerHTML =
                formatInsight(explanation);

        }


        /* Chart */

        let chartData = data.chart || data.chart_data || null;

        if (
            !chartData &&
            data.chart_type &&
            data.chart_type !== "none" &&
            Array.isArray(data.rows) &&
            data.rows.length > 0 &&
            data.chart_x &&
            data.chart_y
        ) {
            const labels = data.rows.map(function (row) {
                return row[data.chart_x];
            });

            const values = data.rows.map(function (row) {
                const value = Number(row[data.chart_y]);
                return Number.isFinite(value) ? value : 0;
            });

            chartData = {
                type: data.chart_type,
                title: data.chart_title || "Analysis Chart",
                label: data.chart_y,
                labels: labels,
                values: values
            };
        }

        renderChart(chartData);


        /* Follow ups */

        renderFollowups(
            data.follow_up_suggestions ||
            data.followup_suggestions ||
            data.followups ||
            []
        );


        /* Refresh history */

        loadHistory();

    }


    /* =========================================================
       ERROR
    ========================================================= */

    function showError(message) {

        if (loadingPanel) {
            loadingPanel.style.display = "none";
        }

        if (resultPanel) {
            resultPanel.style.display = "none";
        }

        if (errorPanel) {
            errorPanel.style.display = "flex";
        }

        if (errorMessage) {
            errorMessage.textContent =
                message || "Something went wrong.";
        }

    }


    /* =========================================================
       LOADING
    ========================================================= */

    function setLoading(isLoading) {

        if (askButton) {
            askButton.disabled = isLoading;
        }

        if (askText) {
            askText.textContent =
                isLoading ? "Analyzing..." : "Analyze data";
        }

        if (askLoader) {
            askLoader.style.display =
                isLoading ? "inline-block" : "none";
        }

        if (loadingPanel) {
            loadingPanel.style.display =
                isLoading ? "block" : "none";
        }

        if (isLoading) {

            if (resultPanel) {
                resultPanel.style.display = "none";
            }

            if (errorPanel) {
                errorPanel.style.display = "none";
            }

        }

    }


    /* =========================================================
       ASK QUESTION
    ========================================================= */

    async function askQuestion(questionOverride = null) {

        const question =
            questionOverride !== null
                ? questionOverride
                : questionInput
                    ? questionInput.value.trim()
                    : "";

        if (!question) {

            showError("Please enter a question.");

            if (questionInput) {
                questionInput.focus();
            }

            return;
        }


        if (question.length > 2000) {

            showError(
                "Question must be 2000 characters or less."
            );

            return;
        }


        setLoading(true);


        try {

            const response = await fetch(
                config.askUrl,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            csrfToken,

                        "X-Requested-With":
                            "XMLHttpRequest"
                    },

                    body: JSON.stringify({
                        question: question,

                        conversation_id:
                            conversationId
                    })
                }
            );


            let data = null;

            try {
                data = await response.json();
            } catch (jsonError) {

                throw new Error(
                    "Server returned an invalid response."
                );

            }


            if (!response.ok || data.success === false) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "Analysis failed."
                );

            }


            renderResult(data);

        } catch (error) {

            console.error(
                "AI SQL Analyst error:",
                error
            );

            showError(
                error.message ||
                "Unable to analyze the data."
            );

        } finally {

            setLoading(false);

        }

    }


    /* =========================================================
       LOAD QUERY HISTORY
    ========================================================= */

    async function loadHistory() {

        if (!conversationHistory) {
            return;
        }

        conversationHistory.innerHTML = `
            <div class="history-loading">
                Loading history...
            </div>
        `;


        try {

            const response = await fetch(
                config.historyUrl,
                {
                    method: "GET",

                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest"
                    },

                    credentials: "same-origin"
                }
            );


            const data = await response.json();


            if (!response.ok || data.success === false) {

                throw new Error(
                    data.error ||
                    "Unable to load query history."
                );

            }


            renderHistory(
                data.conversations || []
            );


        } catch (error) {

            console.error(
                "History error:",
                error
            );

            conversationHistory.innerHTML = `
                <div class="history-empty">
                    <div class="history-empty-icon">!</div>
                    <div>
                        Unable to load history
                    </div>
                </div>
            `;

        }

    }


    /* =========================================================
       RENDER HISTORY
    ========================================================= */

    function renderHistory(conversations) {

        if (!conversationHistory) {
            return;
        }

        conversationHistory.innerHTML = "";


        if (
            !Array.isArray(conversations) ||
            conversations.length === 0
        ) {

            conversationHistory.innerHTML = `
                <div class="history-empty">
                    <div class="history-empty-icon">⌁</div>
                    <div>No previous analysis</div>
                    <small>
                        Your queries will appear here.
                    </small>
                </div>
            `;

            return;
        }


        conversations.forEach(function (conversation) {

            const item =
                document.createElement("button");

            item.type = "button";

            item.className =
                "conversation-item";


            if (
                conversationId !== null &&
                Number(conversation.id) ===
                Number(conversationId)
            ) {
                item.classList.add("active");
            }


            const title =
                conversation.title ||
                "New Analysis";

            const lastMessage =
                conversation.last_message ||
                "No messages yet.";

            const count =
                conversation.message_count || 0;


            item.innerHTML = `
                <div class="conversation-item-top">

                    <span class="conversation-title">
                        ${escapeHtml(title)}
                    </span>

                    <span class="conversation-count">
                        ${count}
                    </span>

                </div>

                <div class="conversation-preview">
                    ${escapeHtml(lastMessage)}
                </div>

                <div class="conversation-date">
                    ${escapeHtml(
                        conversation.updated_at || ""
                    )}
                </div>
            `;


            item.addEventListener(
                "click",
                function () {

                    selectConversation(
                        conversation.id,
                        title
                    );

                }
            );


            conversationHistory.appendChild(item);

        });

    }


    /* =========================================================
       ESCAPE HTML
    ========================================================= */

    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /* =========================================================
       SELECT CONVERSATION
    ========================================================= */

    function selectConversation(id, title) {

        conversationId = id;


        if (questionInput) {

            questionInput.value = "";

            questionInput.focus();

        }


        if (resultPanel) {
            resultPanel.style.display = "none";
        }

        if (errorPanel) {
            errorPanel.style.display = "none";
        }

        if (loadingPanel) {
            loadingPanel.style.display = "none";
        }


        renderHistoryFromSelection();


        /*
         * Existing backend history endpoint currently returns
         * conversation summary. The next question sent with this
         * conversation_id continues that conversation.
         */

        console.log(
            "Selected conversation:",
            conversationId,
            title
        );

    }


    /* =========================================================
       REFRESH ACTIVE HISTORY
    ========================================================= */

    function renderHistoryFromSelection() {

        const items =
            conversationHistory
                ? conversationHistory.querySelectorAll(
                    ".conversation-item"
                )
                : [];


        items.forEach(function (item) {

            item.classList.remove("active");

        });

    }


    /* =========================================================
       NEW ANALYSIS
    ========================================================= */

    function startNewAnalysis() {

        conversationId = null;


        if (questionInput) {

            questionInput.value = "";

            questionInput.focus();

        }


        if (resultPanel) {
            resultPanel.style.display = "none";
        }

        if (errorPanel) {
            errorPanel.style.display = "none";
        }

        if (loadingPanel) {
            loadingPanel.style.display = "none";
        }

        if (followupSection) {
            followupSection.style.display = "none";
        }


        if (currentChart) {

            currentChart.destroy();

            currentChart = null;

        }


        loadHistory();

    }


    /* =========================================================
       SUGGESTIONS
    ========================================================= */

    document
        .querySelectorAll(".suggestion[data-question]")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    const question =
                        button.dataset.question;

                    if (!questionInput) {
                        return;
                    }

                    questionInput.value =
                        question;

                    questionInput.focus();

                }
            );

        });


    /* =========================================================
       BUTTON EVENTS
    ========================================================= */

    if (askButton) {

        askButton.addEventListener(
            "click",
            function () {

                askQuestion();

            }
        );

    }


    if (newAnalysisButton) {

        newAnalysisButton.addEventListener(
            "click",
            startNewAnalysis
        );

    }


    if (refreshHistoryButton) {

        refreshHistoryButton.addEventListener(
            "click",
            loadHistory
        );

    }


    /* =========================================================
       ENTER KEY
    ========================================================= */

    if (questionInput) {

        questionInput.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    askQuestion();

                }

            }
        );

    }


    /* =========================================================
       INITIAL LOAD
    ========================================================= */

    loadHistory();

});