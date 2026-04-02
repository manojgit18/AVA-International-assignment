# backend/services/ocr.py

import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_bytes: bytes, file_type: str) -> str:
    """
    Main entry point. Routes to correct extractor based on file type.
    Returns raw extracted text string.
    """
    try:
        if file_type == "pdf":
            return _extract_from_pdf(file_bytes)
        elif file_type in ("jpg", "jpeg", "png"):
            return _extract_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise

def _extract_from_image(file_bytes: bytes) -> str:
    """
    For JPG/PNG: open with Pillow, preprocess, run Tesseract.
    """
    image = Image.open(io.BytesIO(file_bytes))

    # Preprocessing improves OCR accuracy on noisy/low-quality scans
    image = image.convert("L")          # convert to grayscale
    image = image.point(lambda x: 0 if x < 140 else 255)  # binarize (sharpen text)

    # Tesseract config:
    # --oem 3  = use LSTM neural net engine (most accurate)
    # --psm 6  = assume a single uniform block of text
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(image, config=config)

    return text.strip()

def _extract_from_pdf(file_bytes: bytes) -> str:
    """
    For PDFs: convert each page to an image first, then OCR each page.
    Joins all pages with a separator.
    """
    # Convert PDF pages to PIL images at 300 DPI (higher = better quality)
    pages = convert_from_bytes(file_bytes, dpi=300)

    all_text = []
    for i, page in enumerate(pages):
        page_text = pytesseract.image_to_string(page, config="--oem 3 --psm 6")
        all_text.append(f"--- Page {i+1} ---\n{page_text.strip()}")

    return "\n\n".join(all_text)