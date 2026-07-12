"""知识文档文本解析。"""

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def parse_document(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = "、".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"暂不支持 {suffix or '无扩展名'} 文件，支持格式：{supported}")

    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8-sig", errors="ignore")
    elif suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        document = Document(BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    clean_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not clean_text:
        raise ValueError("文档未解析出有效文本，请检查文件内容")
    return clean_text
