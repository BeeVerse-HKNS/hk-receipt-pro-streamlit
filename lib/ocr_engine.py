import io
from PIL import Image

try:
    from paddleocr import PaddleOCR
    _PADDLEOCR_AVAILABLE = True
except ImportError:
    _PADDLEOCR_AVAILABLE = False

_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "bmp", "tiff", "tif", "webp"}
_SUPPORTED_EXTENSIONS = _IMAGE_EXTENSIONS | {"pdf", "docx", "doc", "xls", "xlsx", "csv", "txt"}


def is_image_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in _IMAGE_EXTENSIONS


def is_supported_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in _SUPPORTED_EXTENSIONS


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in _IMAGE_EXTENSIONS:
        image = Image.open(io.BytesIO(file_bytes))
        return _run_ocr(image)

    if ext == "pdf":
        text = ""
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except ImportError:
            pass
        except Exception:
            pass

        if text.strip():
            return text

        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes)
            for img in images:
                page_text = _run_ocr(img)
                if page_text:
                    text += page_text + "\n"
        except ImportError:
            pass
        except Exception:
            pass

        return text

    if ext in ("docx", "doc"):
        text = ""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    row_text = " | ".join(cells)
                    if row_text.strip("| "):
                        text += row_text + "\n"
        except ImportError:
            pass
        except Exception:
            pass
        return text

    return ""


def extract_receipt_data(file_bytes: bytes, filename: str = None) -> dict:
    result = {
        "merchant": "",
        "date": None,
        "total": 0.0,
        "tax": 0.0,
        "type": "other",
    }

    try:
        from lib.receipt_parser import extract_total, extract_date, extract_tax, classify_receipt_type, extract_merchant
        _use_receipt_parser = True
    except ImportError:
        _use_receipt_parser = False

    try:
        if filename and not is_image_file(filename):
            ocr_text = extract_text_from_file(file_bytes, filename)
        else:
            image = Image.open(io.BytesIO(file_bytes))
            ocr_text = _run_ocr(image)

        if _use_receipt_parser:
            lines = ocr_text.strip().split("\n")
            result["merchant"] = extract_merchant(lines)
            date_str = extract_date(ocr_text)
            if date_str:
                try:
                    from datetime import datetime as dt
                    result["date"] = dt.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    result["date"] = None
            else:
                result["date"] = None
            result["total"] = extract_total(ocr_text) or 0.0
            result["tax"] = extract_tax(ocr_text) or 0.0
            result["type"] = classify_receipt_type(ocr_text, result.get("merchant", ""))
        else:
            result = _parse_ocr_result(ocr_text, result)
    except Exception:
        pass

    return result


def _run_ocr(image: Image.Image) -> str:
    text = ""

    if _PADDLEOCR_AVAILABLE:
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang="ch")
            img_array = __import__("numpy").array(image)
            ocr_result = ocr.ocr(img_array, cls=True)
            for line in ocr_result:
                if line:
                    for word_info in line:
                        text += word_info[1][0] + "\n"
        except Exception:
            text = ""

    if not text.strip():
        try:
            import pytesseract
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        except ImportError:
            pass
        except Exception:
            pass

    return text


def _parse_ocr_result(text: str, result: dict) -> dict:
    import re

    lines = text.strip().split("\n")
    if lines:
        result["merchant"] = lines[0].strip()

    date_patterns = [
        r"(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})",
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            from datetime import datetime
            try:
                date_str = match.group(1)
                for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"]:
                    try:
                        result["date"] = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
            break

    total_patterns = [
        r"(?:TOTAL|Total|總計|合計|總額|Amount)[\s:]*\$?\s*([\d,]+\.?\d*)",
        r"\$\s*([\d,]+\.?\d*)\s*$",
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            try:
                result["total"] = float(match.group(1).replace(",", ""))
            except ValueError:
                pass
            break

    tax_patterns = [
        r"(?:TAX|Tax|稅|稅款|GST)[\s:]*\$?\s*([\d,]+\.?\d*)",
    ]
    for pattern in tax_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                result["tax"] = float(match.group(1).replace(",", ""))
            except ValueError:
                pass
            break

    text_lower = text.lower()
    if any(kw in text_lower for kw in ["restaurant", "餐廳", "茶餐", "酒樓", "快餐"]):
        result["type"] = "restaurant"
    elif any(kw in text_lower for kw in ["mtr", "巴士", "的士", "taxi", "transport"]):
        result["type"] = "transportation"
    elif any(kw in text_lower for kw in ["電力", "煤氣", "水費", "electricity", "gas", "water", "中電", "港燈"]):
        result["type"] = "utilities"
    elif any(kw in text_lower for kw in ["超市", "便利店", "supermarket", "7-eleven", "wellcome", "parknshop"]):
        result["type"] = "retail"

    return result
