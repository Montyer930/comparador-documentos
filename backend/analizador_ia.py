import json
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def build_prompt(items_comp: dict[str, Any]) -> str:
    n = items_comp.get("cantidad_documentos", 2)
    rows = items_comp.get("rows", [])

    prompt = f"""Eres un analista de documentos de arquitectura. Recibes la comparación entre {n} listas de materiales/artículos (PDFs) que DEBERÍAN contener los mismos ítems.

## Resumen de la comparación:
"""

    for i, total in enumerate(items_comp.get("total_por_doc", [])):
        prompt += f"- Documento {chr(65 + i)}: {total} ítems\n"

    prompt += f"""- Total códigos únicos: {items_comp.get('total_codigos_unicos', '?')}
- Ítems presentes en TODOS los documentos: {items_comp.get('en_todos', '?')}
- Ítems presentes en SOLO UN documento: {items_comp.get('solo_en_uno', '?')}

### Ítems faltantes por documento (presentes en algunos pero no en todos):
"""

    for row in rows:
        if not all(row.get("presente", [])):
            docs_faltantes = [
                chr(65 + i)
                for i, p in enumerate(row.get("presente", []))
                if not p
            ]
            prompt += f"- {row['codigo']} -> falta en: {', '.join(docs_faltantes)} (nombre: {row.get('nombre_global', 'N/A')})\n"

    prompt += "\n### Ítems con nombre diferente entre documentos:\n"
    for row in rows:
        if row.get("nombre_coincide_en_todos") is False:
            nombres_str = "; ".join(
                f"{chr(65+i)}={row['nombres'][i] or 'N/A'}"
                for i in range(n)
            )
            prompt += f"- {row['codigo']}: {nombres_str}\n"

    prompt += """---
Analiza y responde SOLO con un JSON con esta estructura exacta:
{
  "resumen": "Resumen en 1-2 oraciones del resultado.",
  "items_en_todos": 0,
  "items_faltantes": ["código - descripción - documentos donde falta"],
  "items_nombre_diferente": ["código - diferencias de nombre entre documentos"],
  "recomendacion": "Recomendación breve basada en el análisis."
}
Responde ÚNICAMENTE el JSON, sin texto adicional.
"""
    return prompt


async def analyze_diff(diff_data: dict[str, Any]) -> dict[str, Any]:
    items_comp = diff_data.get("items_comparison") or diff_data
    prompt = build_prompt(items_comp)
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
            # try to extract JSON from response
            import re as re_m
            m = re_m.search(r"\{.*\}", raw, re_m.DOTALL)
            if m:
                return json.loads(m.group())
            return json.loads(raw)
    except Exception as e:
        return {
            "resumen": f"No se pudo obtener análisis IA: {str(e)}",
            "items_en_todos": 0,
            "items_faltantes": [],
            "items_nombre_diferente": [],
            "recomendacion": "Verifica que Ollama esté corriendo con el modelo adecuado.",
        }
