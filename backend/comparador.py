import difflib
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
    return {
        "text_comparison": text_result,
        "table_comparison": tables_result,
    }
