import os
import sys 

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def extract_text(file_path: str) -> str:
    """Extract text from a PDF or image resume.

    Supports PDF via PyMuPDF and JPEG/PNG via pytesseract + Pillow.
    Returns stripped plain text. Prints which mode was used.
    Raises FileNotFoundError for missing files and ValueError for unsupported types.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    text = ""

    try:
        if ext == ".pdf":
            print("[Parser] Using PDF mode")
            with fitz.open(file_path) as doc:
                for page in doc:
                    # Using the default text extractor; "text" preserves layout reasonably
                    text += page.get_text("text")
        elif ext in [".png", ".jpg", ".jpeg"]:
            print("[Parser] Using Image mode")
            with Image.open(file_path) as img:
                text = pytesseract.image_to_string(img)
        else:
            raise ValueError("Unsupported file type.")
    except Exception as e:
        # Graceful error handling; surface minimal info and return empty string
        print(f"[Parser error] {e}")
        return ""

    return text.strip()


if __name__ == "__main__":
    # Example usage; update path as needed
    print(extract_text("sample.pdf"))


