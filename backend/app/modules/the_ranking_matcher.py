from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd


THE_RANKING_PATH = os.getenv(
    "THE_RANKING_PATH",
    str(Path(__file__).resolve().parents[2] / "the_rankings" / "THE World University Rankings 2026.xlsx"),
)


@lru_cache(maxsize=1)
def _load_the_dataframe() -> pd.DataFrame | None:
    if not os.path.exists(THE_RANKING_PATH):
        return None

    try:
        return pd.read_excel(THE_RANKING_PATH)
    except Exception:
        return None


def _clean_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def get_the_ranking(uni_name: str | None) -> tuple[str | None, int | None]:
    if not uni_name:
        return None, None

    df = _load_the_dataframe()
    if df is None or df.empty:
        return uni_name, None

    columns = {column.lower(): column for column in df.columns}
    name_column = columns.get("name") or columns.get("institution") or columns.get("university")
    rank_column = columns.get("rank") or columns.get("the rank") or columns.get("world rank")

    if not name_column or not rank_column:
        return uni_name, None

    search_value = _clean_name(uni_name)
    if not search_value:
        return uni_name, None

    for _, row in df.iterrows():
        row_name = row.get(name_column)
        if not isinstance(row_name, str):
            continue

        cleaned_row = _clean_name(row_name)
        if search_value == cleaned_row or search_value in cleaned_row or cleaned_row in search_value:
            rank_value = row.get(rank_column)
            if isinstance(rank_value, str):
                digits = re.findall(r"\d+", rank_value)
                if digits:
                    return row_name, int(digits[0])
            if isinstance(rank_value, (int, float)):
                return row_name, int(rank_value)

    return uni_name, None