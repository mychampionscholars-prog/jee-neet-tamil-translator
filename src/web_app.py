"""
web_app.py
FastAPI web interface for JEE/NEET Tamil translator.
Simple UI for uploading PDF and downloading Tamil Word file.
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from datetime import datetime
from loguru import logger

# Import our modules
from src.pdf_ingest.extract_text import extract_pdf
from src.structuring.questions_parser import parse_paper
from src.translation.model_loader import load_model
from src.translation.translator import translate_paper
from src.docx_gen.builder import build_docx

app = FastAPI(title="JEE/NEET Tamil Translator")

# ── Load model once at startup ────────────────────────────────────
logger.info("Loading translation model...")
tokenizer, model = load_model()
device = "cpu"  # Change to "cuda" if you have GPU
logger.success("Model loaded. Ready to translate.")


@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Main page: simple upload form.
    """
    html = """
    <!DOCTYPE html>
    <html lang="ta">
    <head>
        <meta charset="UTF-8">
        <title>JEE/NEET தமிழ் மோழிப்பெயர்ப்பு</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 50px auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a5c8a; text-align: center; font-size: 28px; margin-bottom: 10px; }
            .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
            label { font-weight: bold; display: block; margin-top: 15px; color: #333; }
            input[type=file], select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; }
            button { background: #1a5c8a; color: white; padding: 12px 30px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }
            button:hover { background: #14486c; }
            .footer { text-align: center; margin-top: 30px; color: #999; font-size: 13px; }
            #progress { display: none; text-align: center; margin-top: 20px; color: #1a5c8a; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📖 JEE/NEET தமிழ் மோழிப்பெயர்ப்பு</h1>
            <p class="subtitle">இன்தியா கலைக்கல்கான AI கருவி</p>
            
            <form action="/translate" method="POST" enctype="multipart/form-data" onsubmit="showProgress()">
                <label for="file">📄 PDF பைலை தேர்ந்தெடுக்கவும்</label>
                <input type="file" name="file" id="file" accept=".pdf" required>
                
                <label for="subject">📚 புலம் / Subject</label>
                <select name="subject" id="subject" required>
                    <option value="">-- தேர்வு செய்யவும் --</option>
                    <option value="Physics">இயக்கவியல் (Physics)</option>
                    <option value="Chemistry">வெள்ளியியல் (Chemistry)</option>
                    <option value="Biology">உயிரியல் (Biology)</option>
                    <option value="Math">கணிதம் (Math)</option>
                </select>
                
                <button type="submit">✅ மோழிபெயர்க்க (Translate)</button>
            </form>
            
            <div id="progress">
                <p>⌛ மோழிபெயர்க்கப்படுகிறது... தயவு செய்து காத்திருக்கவும்...</p>
            </div>
            
            <div class="footer">
                Powered by AI4Bharat IndicTrans • Offline Translation Tool<br>
                Built for Tamil Nadu coaching institutes
            </div>
        </div>
        
        <script>
            function showProgress() {
                document.getElementById('progress').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return html


@app.post("/translate")
async def translate_endpoint(
    file: UploadFile = File(...),
    subject: str = Form(...)
):
    """
    Main translation endpoint.
    1. Save uploaded PDF
    2. Extract text
    3. Parse questions
    4. Translate to Tamil
    5. Generate DOCX
    6. Return download link
    """
    logger.info(f"New translation request: {file.filename} | Subject: {subject}")
    
    # Step 1: Save uploaded PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"data/input_pdfs/{timestamp}_{file.filename}"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    logger.info(f"PDF saved: {pdf_path}")
    
    # Step 2: Extract text
    pages_text = extract_pdf(pdf_path)
    
    # Step 3: Parse into structured questions
    paper_title = file.filename.replace(".pdf", "")
    english_paper = parse_paper(pages_text, paper_title=paper_title, subject=subject)
    
    # Step 4: Translate to Tamil
    tamil_paper = translate_paper(english_paper, tokenizer, model, device)
    
    # Step 5: Generate DOCX
    output_filename = f"{timestamp}_{subject}_Tamil.docx"
    output_path = f"data/output_docx/{output_filename}"
    build_docx(tamil_paper, output_path)
    
    logger.success(f"Translation complete! File ready: {output_path}")
    
    # Step 6: Return file for download
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=output_filename
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": "loaded", "device": device}
