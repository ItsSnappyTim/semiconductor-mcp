from pathlib import Path


def extract_pdf(path: str | Path) -> tuple[str, int, str]:
    """Return (title, page_count, full_text) for a PDF file."""
    import pdfplumber

    path = Path(path)
    pages_text: list[str] = []
    title = ""

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages_text.append(text)
            if i == 0 and not title:
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped:
                        title = stripped
                        break

    if not title:
        title = path.stem

    full_text = "\n\n".join(pages_text)
    return title, page_count, full_text
