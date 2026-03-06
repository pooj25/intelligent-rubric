from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _ocr_image_variants(img: Image.Image) -> str:
    if pytesseract is None:
        return ""

    variants = []
    base = img.convert("RGB")
    variants.append(base)

    gray = ImageOps.grayscale(base)
    variants.append(gray)

    boosted = ImageEnhance.Contrast(gray).enhance(2.2)
    variants.append(boosted)

    denoised = boosted.filter(ImageFilter.MedianFilter(size=3))
    variants.append(denoised)

    best_text = ""
    for v in variants:
        try:
            txt = pytesseract.image_to_string(v, config="--oem 3 --psm 6")
            if len(txt.strip()) > len(best_text.strip()):
                best_text = txt
        except Exception:
            continue

    return best_text


def _read_pdf(path: Path) -> str:
    text = ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    except Exception:
        pass

    if text.strip():
        return text

    # Fallback OCR for scanned PDFs.
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(path))
        chunks = []
        for img in images:
            chunks.append(_ocr_image_variants(img))
        return "\n".join(chunks)
    except Exception:
        return ""


def _read_docx(path: Path) -> str:
    try:
        import docx

        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def _read_image(path: Path) -> str:
    try:
        with Image.open(path) as img:
            return _ocr_image_variants(img)
    except Exception:
        return ""


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()

    if ext in {".txt", ".md"}:
        return _read_txt(path)
    if ext == ".pdf":
        return _read_pdf(path)
    if ext == ".docx":
        return _read_docx(path)
    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}:
        return _read_image(path)

    return ""
