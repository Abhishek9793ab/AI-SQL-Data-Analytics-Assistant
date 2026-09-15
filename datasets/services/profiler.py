import json

import numpy as np
import pandas as pd


def detect_column_type(series):

    non_null = series.dropna()

    if non_null.empty:
        return "text"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_integer_dtype(series):
        return "integer"

    if pd.api.types.is_float_dtype(series):
        return "float"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        return "float"

    # Try date detection for object/string columns
    if pd.api.types.is_object_dtype(series):

        sample = non_null.astype(str).head(100)

        converted = pd.to_datetime(
            sample,
            errors="coerce",
        )

        if len(sample) > 0:

            success_rate = (
                converted.notna().mean()
            )

            if success_rate >= 0.8:
                return "date"

    return "text"


def make_json_safe(value):

    if pd.isna(value):
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    return value


def profile_dataset(df):

    missing_cells = int(
        df.isna().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    numeric_columns = 0
    categorical_columns = 0
    date_columns = 0

    columns = []

    for position, column in enumerate(df.columns):

        series = df[column]

        data_type = detect_column_type(
            series
        )

        if data_type in ("integer", "float"):
            numeric_columns += 1

        elif data_type == "date" or data_type == "datetime":
            date_columns += 1

        else:
            categorical_columns += 1

        sample_values = [
            make_json_safe(value)
            for value in series.dropna()
            .head(5)
            .tolist()
        ]

        columns.append(
            {
                "name": str(column),
                "data_type": data_type,
                "nullable": bool(series.isna().any()),
                "null_count": int(series.isna().sum()),
                "unique_values": int(
                    series.nunique(
                        dropna=True
                    )
                ),
                "sample_values": sample_values,
            }
        )

    profile = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_columns": date_columns,
        "memory_usage_bytes": int(
            df.memory_usage(
                deep=True
            ).sum()
        ),
        "columns": columns,
    }

    return profile