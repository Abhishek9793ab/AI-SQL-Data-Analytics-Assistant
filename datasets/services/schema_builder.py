import re
import unicodedata


def normalize_identifier(value):

    value = str(value).strip()

    value = unicodedata.normalize(
        "NFKD",
        value
    ).encode(
        "ascii",
        "ignore"
    ).decode()

    value = re.sub(
        r"[^a-zA-Z0-9_]+",
        "_",
        value
    )

    value = re.sub(
        r"_+",
        "_",
        value
    )

    value = value.strip("_").lower()

    if not value:
        value = "column"

    if value[0].isdigit():
        value = f"col_{value}"

    return value


def build_database_columns(columns):

    used = set()
    result = []

    for original in columns:

        base = normalize_identifier(
            original
        )

        name = base
        counter = 1

        while name in used:

            counter += 1

            name = f"{base}_{counter}"

        used.add(name)

        result.append(
            {
                "original_name": original,
                "database_name": name,
            }
        )

    return result