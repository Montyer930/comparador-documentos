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


def compare_tables(
    tables_a: list[list[list[str | None]]],
    tables_b: list[list[list[str | None]]],
) -> list[dict[str, Any]]:
    table_diffs = []
    max_tables = max(len(tables_a), len(tables_b))

    for i in range(max_tables):
        ta = tables_a[i] if i < len(tables_a) else []
        tb = tables_b[i] if i < len(tables_b) else []

        if not ta and not tb:
            continue

        if ta == tb:
            table_diffs.append(
                {"table_index": i, "match": True, "rows_a": len(ta), "rows_b": len(tb)}
            )
        else:
            row_diffs = []
            max_rows = max(len(ta), len(tb))
            for r in range(max_rows):
                ra = ta[r] if r < len(ta) else []
                rb = tb[r] if r < len(tb) else []
                if ra != rb:
                    row_diffs.append(
                        {
                            "row": r,
                            "a": ra,
                            "b": rb,
                        }
                    )
            table_diffs.append(
                {
                    "table_index": i,
                    "match": False,
                    "rows_a": len(ta),
                    "rows_b": len(tb),
                    "row_diffs": row_diffs,
                }
            )

    return table_diffs


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower().strip()


def compare_items(
    items_a: list[dict[str, str]],
    items_b: list[dict[str, str]],
) -> dict[str, list | int]:
    idx_a: dict[str, dict[str, str]] = {i["codigo"]: i for i in items_a}
    idx_b: dict[str, dict[str, str]] = {i["codigo"]: i for i in items_b}

    all_codes = set(idx_a) | set(idx_b)
    both: set[str] = set(idx_a) & set(idx_b)
    only_a = set(idx_a) - set(idx_b)
    only_b = set(idx_b) - set(idx_a)

    rows: list[dict] = []
    for code in sorted(all_codes):
        a = idx_a.get(code)
        b = idx_b.get(code)
        name_match = None
        if a and b:
            name_match = _normalize(a["nombre"]) == _normalize(b["nombre"])
        rows.append({
            "codigo": code,
            "nombre_a": a["nombre"] if a else None,
            "nombre_b": b["nombre"] if b else None,
            "en_a": a is not None,
            "en_b": b is not None,
            "nombre_coincide": name_match,
        })

    return {
        "total_a": len(items_a),
        "total_b": len(items_b),
        "en_ambos": len(both),
        "solo_a": len(only_a),
        "solo_b": len(only_b),
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
    tables_result = compare_tables(
        list(doc_a.get("tables", [])),
        list(doc_b.get("tables", [])),
    )
    items_result = compare_items(
        list(doc_a.get("items", [])),
        list(doc_b.get("items", [])),
    )
    return {
        "text_comparison": text_result,
        "table_comparison": tables_result,
        "items_comparison": items_result,
    }
