import json
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def build_prompt(diff_data: dict[str, Any]) -> str:
    items_comp = diff_data.get("items_comparison", {})

    rows = items_comp.get("rows", [])

    prompt = f"""Eres un analista de documentos de arquitectura. Recibes la comparación entre dos listas de materiales/artículos (PDFs) que DEBERÍAN contener los mismos ítems pero pueden tener diferencias.

## Resumen de la comparación:
- Total ítems Documento A: {items_comp.get('total_a', '?')}
- Total ítems Documento B: {items_comp.get('total_b', '?')}
- Ítems que aparecen en AMBOS: {items_comp.get('en_ambos', '?')}
- Ítems SOLO en A: {items_comp.get('solo_a', '?')}
- Ítems SOLO en B: {items_comp.get('solo_b', '?')}

### Ítems solo en Documento A:
"""
    for row in rows:
        if row.get("en_a") and not row.get("en_b"):
            prompt += f"- {row['codigo']} -> {row['nombre_a']}\n"

    prompt += "\n### Ítems solo en Documento B:\n"
    for row in rows:
        if not row.get("en_a") and row.get("en_b"):
            prompt += f"- {row['codigo']} -> {row['nombre_b']}\n"

    prompt += "\n### Ítems en ambos pero con NOMBRE DIFERENTE (código igual, nombre distinto):\n"
    for row in rows:
        if row.get("en_a") and row.get("en_b") and row.get("nombre_coincide") is False:
            prompt += f"- {row['codigo']}: A=\"{row['nombre_a']}\" vs B=\"{row['nombre_b']}\"\n"

    prompt += """---
Analiza y responde SOLO con un JSON con esta estructura exacta:
{
  "resumen": "Resumen en 1-2 oraciones del resultado de la comparación: cuántos items coinciden, cuántos faltan, etc.",
  "items_solo_en_a": ["código1 - nombre1", "código2 - nombre2"],
  "items_solo_en_b": ["código1 - nombre1", "código2 - nombre2"],
  "items_nombre_diferente": ["código1: A='nombre' vs B='nombre'"],
  "items_coincidentes": 0,
  "recomendacion": "Recomendación breve basada en el análisis: ¿se puede considerar que los documentos son equivalentes o hay diferencias importantes que revisar?"
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
            "items_solo_en_a": [],
            "items_solo_en_b": [],
            "items_nombre_diferente": [],
            "items_coincidentes": 0,
            "recomendacion": "Verifica que Ollama esté corriendo con el modelo adecuado.",
        }
