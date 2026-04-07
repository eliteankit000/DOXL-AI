"""
DocXL AI - PDF Word Extractor (PyMuPDF)
Production-grade word extraction with bounding boxes
"""
import fitz  # PyMuPDF
from typing import List, Dict

def extract_words_from_pdf(pdf_path: str, page_limit: int = 10) -> List[Dict]:
    """
    Extract all words from PDF with bounding boxes using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        page_limit: Maximum pages to process
        
    Returns:
        List of word dictionaries: {text, x0, y0, x1, y1, page, width, height}
    """
    words = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(len(doc), page_limit)):
            page = doc[page_num]
            
            # Extract words with bounding boxes
            word_list = page.get_text("words")  # Returns list of (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            
            for w in word_list:
                x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
                
                words.append({
                    'text': text.strip(),
                    'x0': x0,
                    'y0': y0,
                    'x1': x1,
                    'y1': y1,
                    'page': page_num + 1,
                    'width': x1 - x0,
                    'height': y1 - y0
                })
        
        doc.close()
        return words
        
    except Exception as e:
        print(f"[EXTRACTOR ERROR] {e}")
        return []


def extract_words_from_image(image_path: str) -> List[Dict]:
    """
    Fallback for image files - convert to PDF first.
    PyMuPDF can handle images directly.
    """
    try:
        # PyMuPDF can open images directly
        doc = fitz.open(image_path)
        page = doc[0]
        
        # For images, we need OCR - use pytesseract
        # But per requirements, avoid OCR unless absolutely required
        # For now, return empty (images need OCR layer)
        
        doc.close()
        return []
        
    except Exception as e:
        print(f"[EXTRACTOR ERROR] Image extraction failed: {e}")
        return []
