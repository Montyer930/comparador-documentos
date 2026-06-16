import difflib
import re
from typing import Any


def compare_texts(text_a: str, text_b: str) -> dict[str, Any]:
    lines_a = text_a.splitlines(keepends=True)
    lines_b = text_b.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)

    diff_blocks: list[dict[str, Any]] = []
    total_similar = 0
    total_diff = 0

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        block: dict[str, Any] = {
            "tag": op,
            "a_lines": lines_a[i1:i2],
            "b_lines": lines_b[j1:j2],
            "a_start": i1,
            "a_end": i2,
            "b_start": j1,
            "b_end": j2,
        }
        diff_blocks.append(block)
        if op == "equal":
            total_similar += sum(len(l) for l in lines_a[i1:i2])
        else:
            total_diff += sum(len(l) for l in lines_a[i1:i2]) + sum(
                len(l) for l in lines_b[j1:j2]
            )

    total = total_similar + total_diff
    similarity_pct = round((total_similar / total) * 100, 2) if total else 100.0

    return {
        "similarity_percentage": similarity_pct,
        "diff_blocks": diff_blocks,
        "total_lines_a": len(lines_a),
        "total_lines_b": len(lines_b),
    }


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower().strip()


def compare_multiple_items(
    doc_items: list[list[dict[str, str]]],
) -> dict[str, Any]:
    indices: list[dict[str, dict[str, str]]] = []
    for items in doc_items:
        indices.append({i["codigo"]: i for i in items})

    all_codes: set[str] = set()
    for idx in indices:
        all_codes |= set(idx)
    code_counts: dict[str, int] = {}
    for code in all_codes:
        code_counts[code] = sum(1 for idx in indices if code in idx)

    n = len(doc_items)
    en_todos = sum(1 for c in code_counts.values() if c == n)
    en_ninguno = 0

    rows: list[dict] = []
    for code in sorted(all_codes):
        presente: list[bool] = []
        nombres: list[str | None] = []
        for idx in indices:
            item = idx.get(code)
            presente.append(item is not None)
            nombres.append(item["nombre"] if item else None)

        nombre_global = None
        nombre_coincide_en_todos: bool | None = None
        nombres_presentes = [n for n in nombres if n is not None]
        if nombres_presentes:
            nombre_global = nombres_presentes[0]
            nombre_coincide_en_todos = all(
                _normalize(n) == _normalize(nombre_global) for n in nombres_presentes
            )

        rows.append({
            "codigo": code,
            "nombres": nombres,
            "presente": presente,
            "total_presente": sum(presente),
            "nombre_global": nombre_global,
            "nombre_coincide_en_todos": nombre_coincide_en_todos,
        })

    total_por_doc = [len(items) for items in doc_items]
    solo_en_uno = sum(1 for c in code_counts.values() if c == 1)

    return {
        "cantidad_documentos": n,
        "total_por_doc": total_por_doc,
        "total_codigos_unicos": len(all_codes),
        "en_todos": en_todos,
        "solo_en_uno": solo_en_uno,
        "rows": rows,
    }


def compare_all(
    doc_a: dict[str, object],
    doc_b: dict[str, object],
) -> dict[str, object]:
    text_result = compare_texts(
        str(doc_a.get("text", "")),
        str(doc_b.get("text", "")),
    )
    items_result = compare_multiple_items([
        list(doc_a.get("items", [])),
        list(doc_b.get("items", [])),
    ])
    return {
        "text_comparison": text_result,
        "items_comparison": items_result,
    }
