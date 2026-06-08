from __future__ import annotations

import re
from typing import Final


_POSTGRES_IDENTIFIER: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def safe_postgres_identifier(value: str) -> str:
    normalized = value.strip()
    if _POSTGRES_IDENTIFIER.fullmatch(normalized) is None:
        raise ValueError(f"safe Postgres identifier required: {value}")
    return normalized


def postgres_table(schema: str, table: str) -> str:
    return f"{safe_postgres_identifier(schema)}.{safe_postgres_identifier(table)}"
