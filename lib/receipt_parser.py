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

    total_patterns = [
        r'(?:總計|總金額|合計|總數|Total|TOTAL|Amount|AMOUNT|Grand\s*Total)[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?:HKD|H\.K\.D\.|hkd|HK\$)\s*([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.?\d*)',
        r'(?:合計|總計)\s*([\d,]+\.?\d*)',
        r'(?:港幣)\s*([\d,]+\.?\d*)',
    ]

    all_matches = []
    for pattern in total_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                all_matches.append(amount)
            except ValueError:
                continue

    if all_matches:
        return max(all_matches)

    return None


def extract_tax(text: str) -> Optional[float]:
    if not text:
        return None

    tax_patterns = [
        r'(?:稅款|稅|Tax|TAX|GST)[:\s]*\$?\s*([\d,]+\.?\d*)',
    ]

    for pattern in tax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                continue

    return None


def classify_receipt_type(text: str, merchant: str) -> str:
    combined = f"{merchant} {text}".lower()

    restaurant_keywords = [
        "餐廳", "茶餐廳", "restaurant", "cafe", "咖啡", "food",
        "美食", "麥當勞", "mcdonald", "肯德基", "kfc", "星巴克",
        "starbucks", "大家樂", "cafe de coral", "美心", "maxim",
        "翠華", "tsui wah", "譚仔", "tamjai", "吉野家", "yoshinoya",
        "大快活", "fairwood", "壽司", "sushi", "火鍋", "hotpot", "燒味",
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
