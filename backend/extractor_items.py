import re
from pathlib import Path

import pdfplumber


def _clean_name(raw: str) -> str:
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"\s*-+\s*$", "", raw).strip()
    raw = re.sub(r"^\s*-+\s*", "", raw).strip()
    return raw


def extract_items_from_text(text: str) -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    lines = text.splitlines()

    # --- Pass 1: Doc A "Lista Accesorios" (SCHUCO <COD> ...) ---
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Flexible: SCHUCO followed by code, then anything, ending with optional -
        m = re.match(
            r"SCHUCO\s+(\d{6}(?:-SC)?)\s+(.+)",
            s,
        )
        if not m:
            continue
        code = m.group(1)
        rest = m.group(2).strip()

        # Strip trailing dash
        rest = re.sub(r"\s*-\s*$", "", rest).strip()

        # Remove leading quantity/color/material tokens
        while rest:
            before = rest
            # Skip "-" placeholder
            rest = re.sub(r"^-\s+", "", rest).strip()
            # Skip color codes like "C0-PLATA MATE" or "R.9005"
            rest = re.sub(r"^[CR][\d.]-?[A-Za-z0-9]+\s+(?:MATE\s+)?", "", rest).strip()
            # Skip standalone "MATE" followed by number
            rest = re.sub(r"^MATE\s+\d+\s+", "", rest).strip()
            # Skip "INOX", "LACADO", "BRUN" followed by number
            rest = re.sub(r"^(INOX|LACADO|BRUN)\s+\d+\s+", "", rest).strip()
            # Skip "X 2558" style prefixes
            rest = re.sub(r"^X\s+\d+\s+", "", rest).strip()
            # Skip leading quantity: digits (with comma/period) optionally followed by "m"
            rest = re.sub(r"^[\d.,]+\s*(?:m\s+)?", "", rest).strip()
            if rest == before:
                break

        name = _clean_name(rest)
        if not name:
            continue
        if code not in seen:
            seen.add(code)
            items.append({"codigo": code, "nombre": name, "fuente": "lista_accesorios"})

    # --- Pass 2: Doc A "Optimización Barras" (Código: / Descripción:) ---
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        m = re.search(r"Código:\s*(\d{6}(?:-SC)?)", s)
        if not m:
            continue
        code = m.group(1)
        if code in seen:
            continue

        # Search forward for Descripción:
        name = ""
        for j in range(i + 1, min(i + 10, len(lines))):
            nl = lines[j].strip()
            dm = re.match(r"Descripción:\s*(.+)", nl)
            if dm:
                name = _clean_name(dm.group(1))
                break
            # Stop at next section header or code
            if re.search(r"(Código:|Serie:)", nl):
                break

        seen.add(code)
        items.append({"codigo": code, "nombre": name, "fuente": "optimizacion_barras"})

    # --- Pass 3: Doc B "Material de pedido" (<COD> <name> <price> ...) ---
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("SCHUCO "):
            continue

        # Pattern: <COD> <name> <price> <qty> ...
        # Price is a float with , or . as decimal separator
        m = re.match(
            r"(\d{6}(?:-SC)?)\s+(.+?)\s+\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2,})\s+\d",
            s,
        )
        if not m:
            continue
        code = m.group(1)
        if code in seen:
            continue

        raw_name = m.group(2).strip()
        raw_name = re.sub(r"\s{2,}", " ", raw_name)
        raw_name = re.sub(r"\s+11:\s+[A-Z]+\s*$", "", raw_name)  # "11: BRUN" suffix
        raw_name = re.sub(r"\s+9005\s*$", "", raw_name)  # color code suffix
        name = _clean_name(raw_name)
        if not name:
            continue
        seen.add(code)
        items.append({"codigo": code, "nombre": name, "fuente": "material_pedido"})

    return items


def extract_items(file_path: str | Path) -> list[dict]:
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return extract_items_from_text(text)
