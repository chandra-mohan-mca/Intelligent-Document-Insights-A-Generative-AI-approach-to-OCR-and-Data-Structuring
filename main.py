
import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from services.ocr_service import extract_text_from_image, configure_genai
from services.document_service import create_word_document
import uvicorn
from contextlib import asynccontextmanager

# Load API Key from environment variable for security
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not GOOGLE_API_KEY:
        print("WARNING: GOOGLE_API_KEY not found in environment variables. OCR will fail.")
    else:
        configure_genai(GOOGLE_API_KEY)
    yield

app = FastAPI(lifespan=lifespan)

# Serve static files handling
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to handle file upload and return transcribed text.
    """
    if not GOOGLE_API_KEY:
         raise HTTPException(status_code=500, detail="Server Configuration Error: API Key missing.")

    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and PDF are supported.")
    
    try:
        content = await file.read()
        text = await extract_text_from_image(content, file.content_type)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-docx")
async def download_docx(text: str = Form(...)):
    """
    Endpoint to generate and download Word document.
    """
    try:
        docx_stream = create_word_document(text)
        return StreamingResponse(
            docx_stream, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=transcription.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
