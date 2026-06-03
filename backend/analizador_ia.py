import json
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
FALLBACK_MODELS = ["qwen2.5:3b", "llama3.2:3b", "llama3.1:8b"]


def build_prompt(diff_data: dict[str, Any]) -> str:
    text_comp = diff_data.get("text_comparison", {})
    table_comp = diff_data.get("table_comparison", [])

    prompt = f"""Eres un analista de documentos. Recibes la comparación entre dos documentos PDF que deberían contener la misma información pero en formatos diferentes.

## Similitud general: {text_comp.get('similarity_percentage', 'N/A')}%

### Diferencias textuales:
"""

    blocks = text_comp.get("diff_blocks", [])
    for block in blocks:
        tag = block.get("tag", "")
        if tag == "replace":
            a = "".join(block.get("a_lines", []))
            b = "".join(block.get("b_lines", []))
            prompt += f"\n- REEMPLAZO (líneas {block.get('a_start')}-{block.get('a_end')} vs {block.get('b_start')}-{block.get('b_end')}):\n  Documento A: {a[:200]}\n  Documento B: {b[:200]}\n"
        elif tag == "delete":
            a = "".join(block.get("a_lines", []))
            prompt += f"\n- ELIMINADO en Documento B (líneas {block.get('a_start')}-{block.get('a_end')}):\n  {a[:200]}\n"
        elif tag == "insert":
            b = "".join(block.get("b_lines", []))
            prompt += f"\n- INSERTADO en Documento B (líneas {block.get('b_start')}-{block.get('b_end')}):\n  {b[:200]}\n"

    prompt += "\n### Diferencias en tablas:\n"
    for tbl in table_comp:
        if not tbl.get("match", True):
            prompt += f"\n- Tabla índice {tbl.get('table_index')}: Documento A tiene {tbl.get('rows_a')} filas, Documento B tiene {tbl.get('rows_b')} filas\n"
            for row in tbl.get("row_diffs", []):
                prompt += f"  - Fila {row.get('row')}: A={row.get('a')} vs B={row.get('b')}\n"

    prompt += """
---
Analiza y responde SOLO con un JSON con esta estructura exacta:
{
  "resumen": "Resumen corto de las diferencias encontradas (máx 2 oraciones)",
  "diferencias_reales": ["lista", "de", "diferencias", "significativas"],
  "diferencias_formato": ["lista", "de", "diferencias", "solo de formato"],
  "coincidencia_porcentaje_estimado": 95,
  "recomendacion": "Recomendación breve basada en el análisis"
}
Responde ÚNICAMENTE el JSON, sin texto adicional.
"""
    return prompt


async def analyze_diff(diff_data: dict[str, Any]) -> dict[str, Any]:
    prompt = build_prompt(diff_data)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()
            raw = result.get("response", "{}")
            return json.loads(raw)
    except Exception as e:
        return {
            "resumen": f"No se pudo obtener análisis IA: {str(e)}",
            "diferencias_reales": [],
            "diferencias_formato": [],
            "coincidencia_porcentaje_estimado": None,
            "recomendacion": "Verifica que Ollama esté corriendo con el modelo adecuado.",
        }
