import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from analizador_ia import analyze_diff
from comparador import compare_all
from extractor import extract_all

app = FastAPI(title="Comparador de Documentos", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    file_path = FRONTEND_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.post("/compare")
async def compare_documents(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        path_a = Path(tmpdir) / file_a.filename or "doc_a.pdf"
        path_b = Path(tmpdir) / file_b.filename or "doc_b.pdf"

        content_a = await file_a.read()
        content_b = await file_b.read()

        path_a.write_bytes(content_a)
        path_b.write_bytes(content_b)

        doc_a = extract_all(path_a)
        doc_b = extract_all(path_b)

        diff = compare_all(doc_a, doc_b)
        ia_analysis = await analyze_diff(diff)

    return {
        "filename_a": file_a.filename or "doc_a.pdf",
        "filename_b": file_b.filename or "doc_b.pdf",
        "diff": diff,
        "ia_analysis": ia_analysis,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
