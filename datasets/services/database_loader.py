import re

import pandas as pd
from django.db import connection


SQLITE_TYPE_MAP = {
    "integer": "INTEGER",
    "float": "REAL",
    "boolean": "INTEGER",
    "date": "TEXT",
    "datetime": "TEXT",
    "text": "TEXT",
}


def quote_identifier(identifier):

    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*",
        identifier,
    ):
        raise ValueError(
            f"Unsafe SQLite identifier: {identifier}"
        )

    return f'"{identifier}"'


def create_dataset_table(
    table_name,
    column_definitions,
):

    table_sql = quote_identifier(
        table_name
    )

    column_sql = []

    for column in column_definitions:

        database_name = column[
            "database_name"
        ]

        data_type = column[
            "data_type"
        ]

        sqlite_type = SQLITE_TYPE_MAP[
            data_type
        ]

        column_sql.append(
            f"{quote_identifier(database_name)} "
            f"{sqlite_type}"
        )

    sql = (
        f"CREATE TABLE {table_sql} "
        f"({', '.join(column_sql)})"
    )

    with connection.cursor() as cursor:

        cursor.execute(sql)


def insert_dataframe(
    table_name,
    df,
    database_columns,
    batch_size=500,
):

    renamed = df.copy()

    mapping = {
        item["original_name"]:
        item["database_name"]
        for item in database_columns
    }

    renamed = renamed.rename(
        columns=mapping
    )

    # SQLite does not have native datetime/date types
    for column in renamed.columns:

        if pd.api.types.is_datetime64_any_dtype(
            renamed[column]
        ):

            renamed[column] = (
                renamed[column]
                .dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

    renamed = renamed.where(
        pd.notna(renamed),
        None,
    )

    columns = list(
        renamed.columns
    )

    quoted_columns = ", ".join(
        quote_identifier(column)
        for column in columns
    )

    placeholders = ", ".join(
        ["?"] * len(columns)
    )

    sql = (
        f"INSERT INTO "
        f"{quote_identifier(table_name)} "
        f"({quoted_columns}) "
        f"VALUES ({placeholders})"
    )

    rows = [
        tuple(row)
        for row in renamed.itertuples(
            index=False,
            name=None,
        )
    ]

    with connection.cursor() as cursor:

        for start in range(
            0,
            len(rows),
            batch_size,
        ):

            batch = rows[
                start:start + batch_size
            ]

            cursor.executemany(
                sql,
                batch,
            )