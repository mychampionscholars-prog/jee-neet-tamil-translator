"""
download_models.py
Run this once to download the translation model.
After this, the tool works 100% offline.
"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

MODEL_NAME = "Helsinki-NLP/opus-mt-en-mul"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "models_cache")

print("="*60)
print("JEE/NEET Tamil Translator - Model Download")
print("="*60)
print(f"Downloading model: {MODEL_NAME}")
print("This is a ONE-TIME download (~300 MB).")
print("After this, everything works offline.")
print("-"*60)

os.makedirs(CACHE_DIR, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    cache_dir=CACHE_DIR
)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    cache_dir=CACHE_DIR
)

print("-"*60)
print("Model downloaded successfully!")
print(f"Saved to: {os.path.abspath(CACHE_DIR)}")
print("You can now use the translator offline.")
print("="*60)
