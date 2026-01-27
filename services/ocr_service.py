
import os
import google.generativeai as genai
from fastapi import HTTPException
import PIL.Image
import io

# Configure Gemini
# Expects GOOGLE_API_KEY in environment variables
def configure_genai(api_key: str):
    genai.configure(api_key=api_key)

async def extract_text_from_image(image_bytes: bytes, mime_type: str) -> str:
    """
    Extracts text from an image (or PDF converted to image) using Gemini.
    Tries 'gemini-3-flash-preview' first, falls back to 'gemini-1.5-flash'.
    """
    prompt = """Transcribe the provided document EXACTLY as it appears. 
    
    1. For header lines, addresses, and signatures: Transcribe EXACTLY line-by-line. 
    2. For the main body paragraphs: Transcribe EACH individual paragraph as its own block tagged with [PARA]. Do NOT merge separate paragraphs into one big block.
    3. CRITICAL: Separate 'நாள்' and 'இடம்' into individual lines tagged [LEFT].
    4. CRITICAL: Separate the signature block (இப்படிக்கு... and names) into individual lines tagged [RIGHT].
    
    Tagging:
    [LEFT] - Addresses, salutations, Date, Place.
    [CENTER] - Subject line, dotted lines.
    [PARA] - EACH distinct body paragraph.
    [RIGHT] - 'Yours truly' and Signature block.
    
    Language: [TAM] for Tamil, [ENG] for English.
    Return ONLY the tagged transcription."""

    content = [
        {"mime_type": mime_type, "data": image_bytes},
        prompt
    ]

    # Safety settings to allow handwriting analysis (sometimes flagged incorrectly)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    async def generate(model_name):
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(content, safety_settings=safety_settings)
        return response.text

    try:
        # Try primary advanced model
        return await generate('gemini-3-flash-preview')
    except Exception as e:
        print(f"Primary model failed: {e}. Retrying with fallback...")
        try:
            # Fallback to stable model
            return await generate('gemini-1.5-flash')
        except Exception as e2:
             print(f"Fallback model failed: {e2}")
             raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e2)}")
