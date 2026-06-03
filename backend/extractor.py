from pathlib import Path
from typing import Any

import pdfplumber


def extract_text(file_path: str | Path) -> str:
    with pdfplumber.open(file_path) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n--- PAGE BREAK ---\n\n".join(pages)


def extract_tables(file_path: str | Path) -> list[list[list[str | None]]]:
    tables: list[list[list[str | None]]] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def extract_all(file_path: str | Path) -> dict[str, Any]:
    return {
        "text": extract_text(file_path),
        "tables": extract_tables(file_path),
    }
