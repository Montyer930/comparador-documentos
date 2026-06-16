import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from analizador_ia import analyze_diff
from comparador import compare_multiple_items, compare_texts
from extractor_items import extract_items

app = FastAPI(title="Comparador de Documentos", version="2.0.0")

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
async def compare_documents(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        return JSONResponse(
            {"error": "Debes subir al menos 2 documentos"}, status_code=400
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        docs_raw: list[dict] = []
        filenames: list[str] = []

        for f in files:
            content = await f.read()
            if not content:
                continue
            path = Path(tmpdir) / (f.filename or "documento.pdf")
            path.write_bytes(content)
            items = extract_items(path)
            docs_raw.append(items)
            filenames.append(f.filename or "documento.pdf")

        items_comp = compare_multiple_items(docs_raw)

        text_comps = []
        if len(docs_raw) == 2:
            text_a = "\n".join(i.get("nombre", "") for i in docs_raw[0])
            text_b = "\n".join(i.get("nombre", "") for i in docs_raw[1])
            text_comps.append(compare_texts(text_a, text_b))

        ia_analysis = await analyze_diff(items_comp)

    return {
        "documentos": filenames,
        "diff": {
            "text_comparisons": text_comps,
            "items_comparison": items_comp,
        },
        "ia_analysis": ia_analysis,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
