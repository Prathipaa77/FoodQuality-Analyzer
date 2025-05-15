def clean_text(text):
    """Clean OCR-extracted text by removing extra whitespace and special characters."""
    import re
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'[^\w\s,.]', '', text)
    return text