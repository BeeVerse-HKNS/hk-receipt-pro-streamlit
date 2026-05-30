import re
from datetime import datetime
from typing import Optional

try:
    from paddleocr import PaddleOCR
    _PADDLEOCR_AVAILABLE = True
except ImportError:
    _PADDLEOCR_AVAILABLE = False


def parse_receipt(ocr_result: dict) -> dict:
    text = ocr_result.get("text", "")
    lines = ocr_result.get("lines", [])
    engine = ocr_result.get("engine", "none")

    merchant = extract_merchant(lines)
    date = extract_date(text)
    total = extract_total(text)
    tax = extract_tax(text)
    receipt_type = classify_receipt_type(text, merchant)
    confidence = calculate_confidence(merchant, date, total, engine)

    return {
        "merchant": merchant,
        "date": date,
        "total": total,
        "tax": tax,
        "currency": "HKD",
        "receipt_type": receipt_type,
        "confidence": confidence,
        "raw_text": text,
    }


def extract_merchant(lines: list[str]) -> str:
    if not lines:
        return ""

    known_merchants = [
        "ParknShop", "PARKnSHOP", "百佳",
        "Wellcome", "WELLCOME", "惠康",
        "7-Eleven", "7-11", "七十一",
        "McDonald's", "MCDONALD'S", "麥當勞",
        "KFC", "肯德基",
        "Starbucks", "STARBUCKS", "星巴克",
        "Circle K", "OK便利店",
        "Watsons", "WATSONS", "屈臣氏",
        "Mannings", "MANNINGS", "萬寧",
        "IKEA", "宜家",
        "Maxim's", "美心",
        "TamJai", "譚仔",
        "Yoshinoya", "吉野家",
        "Fairwood", "大快活",
        "Cafe de Coral", "大家樂",
        "Tsui Wah", "翠華",
        "UNIQLO",
        "H&M",
    ]

    top_lines = lines[:5] if len(lines) >= 5 else lines

    for line in top_lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        for merchant in known_merchants:
            if merchant.lower() in cleaned.lower():
                return merchant

    for line in top_lines:
        cleaned = line.strip()
        if not cleaned or len(cleaned) < 2:
            continue
        if re.match(r'^[A-Za-z\u4e00-\u9fff\s&\'\-\.]+$', cleaned):
            if not re.match(r'^[\d\$\@\#\%]+', cleaned):
                return cleaned

    return top_lines[0].strip() if top_lines else ""


def extract_date(text: str) -> Optional[str]:
    if not text:
        return None

    chinese_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if chinese_match:
        year, month, day = chinese_match.groups()
        try:
            datetime(int(year), int(month), int(day))
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except ValueError:
            pass

    dd_mm_yyyy = re.findall(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', text)
    if dd_mm_yyyy:
        for day, month, year in dd_mm_yyyy:
            try:
                datetime(int(year), int(month), int(day))
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue

    yyyy_mm_dd = re.findall(r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})', text)
    if yyyy_mm_dd:
        for year, month, day in yyyy_mm_dd:
            try:
                datetime(int(year), int(month), int(day))
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue

    mm_dd_yyyy = re.findall(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', text)
    if mm_dd_yyyy:
        for month, day, year in mm_dd_yyyy:
            try:
                datetime(int(year), int(month), int(day))
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue

    return None


def extract_total(text: str) -> Optional[float]:
    if not text:
        return None

    labeled_patterns = [
        r'(?:Balance\s*Due|Amount\s*Due|Total\s*Due|Net\s*Amount|Payable|應付)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?:Grand\s*Total|總計|總金額|合計|總數)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?:Invoice\s*Total|Amount\s*Payable)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?<!Sub)(?<!sub)(?:Total|TOTAL)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?:Amount|AMOUNT)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?:港幣)\s*([\d,]+\.?\d*)',
        r'(?:Subtotal|Sub\s*Total|小計)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
    ]

    for pattern in labeled_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in reversed(matches):
                try:
                    return float(match.replace(',', ''))
                except ValueError:
                    continue

    currency_patterns = [
        r'(?:HKD|H\.K\.D\.|hkd|HK\$)\s*([\d,]+\.?\d*)',
    ]

    for pattern in currency_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in reversed(matches):
                try:
                    return float(match.replace(',', ''))
                except ValueError:
                    continue

    dollar_matches = re.findall(r'\$\s*([\d,]+\.?\d*)', text)
    if dollar_matches:
        for match in reversed(dollar_matches):
            try:
                return float(match.replace(',', ''))
            except ValueError:
                continue

    decimal_matches = re.findall(r'([\d,]+\.\d{2})', text)
    if decimal_matches:
        for match in reversed(decimal_matches):
            try:
                return float(match.replace(',', ''))
            except ValueError:
                continue

    return None


def extract_tax(text: str) -> Optional[float]:
    if not text:
        return None

    tax_patterns = [
        r'(?:稅款|稅項|稅)[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
        r'(?:Tax|TAX|GST|VAT)\s*(?:\([^)]*\))?[:\s]*\$?\s*(?:HKD|HK\$|hkd)?\s*([\d,]+\.?\d*)',
    ]

    for pattern in tax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                continue

    return None


_MERCHANT_TYPE_MAP = {
    "parknshop": "retail", "百佳": "retail",
    "wellcome": "retail", "惠康": "retail",
    "7-eleven": "retail", "7-11": "retail", "七十一": "retail",
    "circle k": "retail", "ok便利店": "retail",
    "watsons": "retail", "屈臣氏": "retail",
    "mannings": "retail", "萬寧": "retail",
    "ikea": "retail", "宜家": "retail",
    "uniqlo": "retail",
    "h&m": "retail",
    "mcdonald": "restaurant", "麥當勞": "restaurant",
    "kfc": "restaurant", "肯德基": "restaurant",
    "starbucks": "restaurant", "星巴克": "restaurant",
    "maxim": "restaurant", "美心": "restaurant",
    "tamjai": "restaurant", "譚仔": "restaurant",
    "yoshinoya": "restaurant", "吉野家": "restaurant",
    "fairwood": "restaurant", "大快活": "restaurant",
    "cafe de coral": "restaurant", "大家樂": "restaurant",
    "tsui wah": "restaurant", "翠華": "restaurant",
    "mtr": "transportation", "港鐵": "transportation",
    "taxi": "transportation", "的士": "transportation",
    "kmb": "transportation", "九巴": "transportation",
    "citybus": "transportation", "城巴": "transportation",
    "nwfb": "transportation", "新巴": "transportation",
    "octopus": "transportation", "八達通": "transportation",
    "clp power": "utilities", "clp": "utilities", "中電": "utilities",
    "hk electric": "utilities", "港燈": "utilities", "hke": "utilities",
    "town gas": "utilities", "煤氣": "utilities",
    "pccw": "utilities", "電訊盈科": "utilities",
    "hkbn": "utilities", "香港寬頻": "utilities",
    "水務署": "utilities",
}


def classify_receipt_type(text: str, merchant: str) -> str:
    merchant_lower = merchant.lower()
    for key, rtype in _MERCHANT_TYPE_MAP.items():
        if key in merchant_lower:
            return rtype

    combined = f"{merchant} {text}".lower()

    restaurant_keywords = [
        "餐廳", "茶餐廳", "restaurant", "cafe", "咖啡", "food",
        "美食", "壽司", "sushi", "火鍋", "hotpot", "燒味",
        "dim sum", "點心", "麵家", "noodle",
    ]
    for kw in restaurant_keywords:
        if kw in combined:
            return "restaurant"

    transport_keywords = [
        "的士", "taxi", "mtr", "港鐵", "巴士", "bus",
        "八達通", "octopus", "九巴", "kmb", "城巴", "citybus",
        "新巴", "nwfb", "輕鐵", "light rail", "纜車", "tram",
    ]
    for kw in transport_keywords:
        if kw in combined:
            return "transportation"

    utility_keywords = [
        "電費", "水費", "煤氣", "electricity", "water", "gas",
        "中電", "clp power", "港燈", "hk electric", "水務署",
        "clp", "hke", "town gas", "pccw", "電訊盈科", "hkbn", "香港寬頻",
    ]
    for kw in utility_keywords:
        if kw in combined:
            return "utilities"

    retail_keywords = [
        "百佳", "parknshop", "wellcome", "惠康", "萬寧", "mannings",
        "7-eleven", "7-11", "屈臣氏", "watsons", "超市",
        "supermarket", "藥房", "pharmacy", "便利店", "convenience",
    ]
    for kw in retail_keywords:
        if kw in combined:
            return "retail"

    return "other"


def calculate_confidence(
    merchant: str,
    date: Optional[str],
    total: Optional[float],
    engine: str,
) -> float:
    confidence = 0.3

    if merchant:
        confidence += 0.2
    if date:
        confidence += 0.2
    if total is not None:
        confidence += 0.2

    if engine == "pytesseract":
        confidence -= 0.1

    if not _PADDLEOCR_AVAILABLE and engine != "pytesseract":
        confidence -= 0.1

    return round(min(confidence, 1.0), 2)
