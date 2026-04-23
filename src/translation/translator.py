"""
translator.py
Core translation engine for JEE/NEET English -> Tamil
Protects math equations from being translated.
"""
import re
import torch
from loguru import logger

# ── Math Protection Patterns ─────────────────────────────────
# These patterns find LaTeX math in the text
# They are MASKED before translation and RESTORED after
MATH_PATTERNS = [
    r'\\[\[\(].*?\\[\]\)]',     # \[ ... \] and \( ... \)
    r'\$\$.*?\$\$',              # $$ ... $$
    r'\$[^\$]+\$',               # $ ... $
    r'\\frac\{[^}]+\}\{[^}]+\}', # \frac{}{}
    r'\\[a-zA-Z]+\{[^}]*\}',    # \command{}
    r'\d+\.?\d*\s*[\+\-\*\/\^]\s*\d+\.?\d*',  # simple math: 2+3, x^2
    r'[A-Za-z]\s*=\s*[\d\.]+',  # A = 10
]

def mask_math_tokens(text: str) -> tuple[str, dict]:
    """
    Replace math expressions with placeholders like <M0>, <M1>...
    Returns masked text and a dictionary to restore them.
    """
    placeholders = {}
    masked = text
    counter = 0
    
    for pattern in MATH_PATTERNS:
        matches = list(re.finditer(pattern, masked, re.DOTALL))
        for match in matches:
            token = f"<M{counter}>"
            placeholders[token] = match.group(0)
            masked = masked.replace(match.group(0), token, 1)
            counter += 1
    
    return masked, placeholders


def restore_math_tokens(text: str, placeholders: dict) -> str:
    """
    Put the original math expressions back.
    """
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text


def translate_text(text: str, tokenizer, model, device: str = "cpu",
                   target_lang: str = ">>tam<<") -> str:
    """
    Translate a single piece of English text to Tamil.
    Automatically protects math expressions.
    """
    if not text or not text.strip():
        return text
    
    # Step 1: Mask math
    masked_text, placeholders = mask_math_tokens(text)
    
    # Step 2: Translate
    try:
        # Add target language prefix for opus-mt multilingual model
        input_text = f"{target_lang} {masked_text}"
        
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=600,
                num_beams=4,
                early_stopping=True
            )
        
        tamil_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
    except Exception as e:
        logger.error(f"Translation failed for text: {text[:50]}... Error: {e}")
        tamil_text = masked_text  # fallback: return original
    
    # Step 3: Restore math
    final_text = restore_math_tokens(tamil_text, placeholders)
    
    return final_text


def translate_question(question: dict, tokenizer, model,
                       device: str = "cpu") -> dict:
    """
    Translate a full question (body + all options) to Tamil.
    Returns a new question dict with Tamil text.
    """
    tamil_question = question.copy()
    
    logger.info(f"Translating Q{question.get('q_no', '?')}...")
    
    # Translate question body
    if question.get("body"):
        tamil_question["body"] = translate_text(
            question["body"], tokenizer, model, device
        )
    
    # Translate each option A, B, C, D
    if question.get("options"):
        tamil_options = {}
        for label, option_text in question["options"].items():
            tamil_options[label] = translate_text(
                option_text, tokenizer, model, device
            )
        tamil_question["options"] = tamil_options
    
    # Translate explanation if present
    if question.get("explanation"):
        tamil_question["explanation"] = translate_text(
            question["explanation"], tokenizer, model, device
        )
    
    return tamil_question


def translate_paper(paper: dict, tokenizer, model,
                    device: str = "cpu") -> dict:
    """
    Translate an entire question paper.
    """
    logger.info(f"Starting translation of: {paper.get('paper_title', 'Untitled')}")
    
    tamil_paper = {
        "paper_title": paper.get("paper_title", ""),
        "subject": paper.get("subject", ""),
        "questions": []
    }
    
    total = len(paper.get("questions", []))
    
    for i, question in enumerate(paper.get("questions", []), 1):
        logger.info(f"Progress: {i}/{total} questions")
        tamil_q = translate_question(question, tokenizer, model, device)
        tamil_paper["questions"].append(tamil_q)
    
    logger.success(f"Translation complete! {total} questions translated.")
    return tamil_paper
