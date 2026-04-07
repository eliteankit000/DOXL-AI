"""
DocXL AI - Image Processing Engine
Handles JPG/PNG with OCR using PaddleOCR
"""
import cv2
import numpy as np
from typing import List, Dict

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Preprocess image for better OCR accuracy.
    
    Steps:
    1. Convert to grayscale
    2. Apply thresholding
    3. Denoise
    
    Args:
        image_path: Path to image file
        
    Returns:
        Preprocessed image as numpy array
    """
    # Read image
    img = cv2.imread(image_path)
    
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Resize if too large (for performance)
    height, width = img.shape[:2]
    max_dimension = 2000
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised


def extract_text_with_paddleocr(image_path: str) -> List[Dict]:
    """
    Extract text with bounding boxes using PaddleOCR.
    
    Returns:
        List of word dictionaries: {text, x0, y0, x1, y1, page}
    """
    try:
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            show_log=False,
            use_gpu=False  # Set True if GPU available
        )
        
        # Run OCR
        result = ocr.ocr(image_path, cls=True)
        
        words = []
        
        if result and len(result) > 0:
            for line in result[0]:  # First page
                bbox = line[0]  # [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
                text = line[1][0]  # text
                confidence = line[1][1]  # confidence score
                
                # Extract coordinates
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x0 = min(x_coords)
                y0 = min(y_coords)
                x1 = max(x_coords)
                y1 = max(y_coords)
                
                # Filter low confidence
                if confidence > 0.5:
                    words.append({
                        'text': text.strip(),
                        'x0': x0,
                        'y0': y0,
                        'x1': x1,
                        'y1': y1,
                        'page': 1,
                        'width': x1 - x0,
                        'height': y1 - y0,
                        'confidence': confidence
                    })
        
        return words
        
    except ImportError:
        print("[OCR ERROR] PaddleOCR not installed. Falling back to pytesseract.")
        return extract_text_with_tesseract(image_path)


def extract_text_with_tesseract(image_path: str) -> List[Dict]:
    """
    Fallback OCR using pytesseract.
    
    Returns:
        List of word dictionaries: {text, x0, y0, x1, y1, page}
    """
    try:
        import pytesseract
        from PIL import Image
        
        # Read image
        img = Image.open(image_path)
        
        # Get OCR data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        words = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue
            
            x0 = data['left'][i]
            y0 = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            x1 = x0 + width
            y1 = y0 + height
            confidence = int(data['conf'][i])
            
            # Filter low confidence
            if confidence > 50:
                words.append({
                    'text': text,
                    'x0': float(x0),
                    'y0': float(y0),
                    'x1': float(x1),
                    'y1': float(y1),
                    'page': 1,
                    'width': float(width),
                    'height': float(height),
                    'confidence': confidence / 100.0
                })
        
        return words
        
    except ImportError:
        print("[OCR ERROR] Tesseract not installed.")
        return []


def process_image(image_path: str) -> List[Dict]:
    """
    Main image processing pipeline.
    
    Steps:
    1. Preprocess image
    2. Run OCR (PaddleOCR preferred, tesseract fallback)
    3. Return structured words
    
    Returns:
        List of word dictionaries compatible with PDF pipeline
    """
    print(f"[IMAGE_ENGINE] Processing image: {image_path}")
    
    # Step 1: Preprocess (optional, can skip for speed)
    # preprocessed = preprocess_image(image_path)
    
    # Step 2: Extract text with OCR
    words = extract_text_with_paddleocr(image_path)
    
    print(f"[IMAGE_ENGINE] Extracted {len(words)} words via OCR")
    
    return words
