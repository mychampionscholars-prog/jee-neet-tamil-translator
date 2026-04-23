"""
questions_parser.py
Extracts structured questions from raw PDF text.
Handles JEE/NEET format: numbered questions + A/B/C/D options.
"""
import re
from loguru import logger


# Detect question start: "1." or "1)" or "Q1" or "Q.1"
QUESTION_START = re.compile(
    r'^\s*(?:Q\.?)?\s*(\d{1,3})[\.)\s]+',
    re.MULTILINE
)

# Detect option start: "(A)" or "A." or "A)" or "(a)"
OPTION_START = re.compile(
    r'^\s*[\(\[]?([A-Da-d])[\)\]\.\s]+',
    re.MULTILINE
)


def clean_text(text: str) -> str:
    """Remove extra whitespace and fix common OCR issues."""
    text = re.sub(r'\n{3,}', '\n\n', text)  # max 2 newlines
    text = re.sub(r' {2,}', ' ', text)      # max 1 space
    text = text.strip()
    return text


def split_into_question_blocks(full_text: str) -> list:
    """
    Split raw text into individual question blocks.
    Returns list of (q_number, q_text) tuples.
    """
    parts = QUESTION_START.split(full_text)
    # parts = [preamble, q_no1, text1, q_no2, text2, ...]
    
    blocks = []
    for i in range(1, len(parts), 2):
        try:
            q_no = parts[i].strip()
            q_text = parts[i + 1] if i + 1 < len(parts) else ""
            blocks.append((q_no, q_text))
        except IndexError:
            continue
    
    logger.info(f"Found {len(blocks)} question blocks")
    return blocks


def parse_options(text: str) -> tuple:
    """
    Extract A/B/C/D options from question text.
    Returns (question_body, options_dict)
    """
    option_parts = OPTION_START.split(text)
    
    if len(option_parts) <= 1:
        # No options found - could be paragraph question
        return text.strip(), {}
    
    question_body = option_parts[0].strip()
    options = {}
    
    for i in range(1, len(option_parts), 2):
        try:
            label = option_parts[i].upper()
            option_text = option_parts[i + 1] if i + 1 < len(option_parts) else ""
            # Clean option text - stop at next option or end
            option_text = option_text.split('\n')[0].strip()
            if label in ['A', 'B', 'C', 'D']:
                options[label] = option_text
        except IndexError:
            continue
    
    return question_body, options


def parse_paper(pages_text: list, paper_title: str = "",
                subject: str = "General") -> dict:
    """
    Main function: convert list of page texts to structured paper dict.
    
    Input:  ["Page 1 text...", "Page 2 text...", ...]
    Output: {
        "paper_title": "...",
        "subject": "...",
        "questions": [
            {
                "q_no": "1",
                "body": "Question text",
                "options": {"A": "...", "B": "...", ...}
            },
            ...
        ]
    }
    """
    full_text = "\n".join(pages_text)
    full_text = clean_text(full_text)
    
    blocks = split_into_question_blocks(full_text)
    
    questions = []
    for q_no, block_text in blocks:
        body, options = parse_options(block_text)
        
        if not body.strip():
            continue  # Skip empty questions
        
        questions.append({
            "q_no": q_no,
            "subject": subject,
            "body": body,
            "options": options,
            "explanation": ""  # filled later if answer key is available
        })
    
    logger.success(f"Parsed {len(questions)} questions from paper")
    
    return {
        "paper_title": paper_title,
        "subject": subject,
        "questions": questions
    }
