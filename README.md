# Comparador de Documentos

Plataforma para comparar dos documentos PDF y analizar sus diferencias usando IA local (Ollama).

## Stack

- **Backend:** Python + FastAPI
- **Extracción:** pdfplumber
- **Análisis IA:** Ollama (qwen2.5)
- **Frontend:** HTML/CSS/JS vanilla

## Requisitos

- Python 3.10+
- Ollama instalado y corriendo con el modelo `qwen2.5:7b`

## Instalación

```bash
pip install -r backend/requirements.txt
```

## Ejecución

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abrir `http://localhost:8000`

## Uso

1. Subir dos PDFs
2. La plataforma extrae y compara el contenido
3. Muestra diferencias lado a lado
4. Envía automáticamente las diferencias a Ollama para análisis IA
