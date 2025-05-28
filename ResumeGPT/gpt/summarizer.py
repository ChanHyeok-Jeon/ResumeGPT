# gpt/summarizer.py

import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"[PDF 추출 오류] {str(e)}"

def summarize_resume(pdf_path: str) -> str:
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return "PDF에서 텍스트를 추출할 수 없습니다."
    
    prompt = f"다음은 한 구직자의 이력서입니다:\n\n{text}\n\n이 이력서를 간단하고 명확하게 요약해줘."
    summary = ask_gpt(prompt)
    return summary

def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    text = ""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"[이력서 읽기 오류] {str(e)}"