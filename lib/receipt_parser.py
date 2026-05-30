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
    description = extract_description(lines)
    payment_method = extract_payment_method(text)
    confidence = calculate_confidence(merchant, date, total, engine)

    return {
        "merchant": merchant,
        "date": date,
        "total": total,
        "tax": tax,
        "currency": "HKD",
        "receipt_type": receipt_type,
        "description": description,
        "payment_method": payment_method,
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
        "3HK", "3香港",
        "% Arabica",
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

    _CUR = r'(?:H\.K\.\$|H\.K\.D\.|HKD|HK\$|hkd|港幣)?\s*\$?'

    labeled_patterns = [
        rf'(?:Balance\s*Due|Amount\s*Due|Total\s*Due|Net\s*Amount|Payable|應付)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
        rf'(?:Grand\s*Total|總計|總金額|合計|總數)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
        rf'(?:Invoice\s*Total|Amount\s*Payable)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
        rf'(?<!Sub)(?<!sub)(?:Total|TOTAL)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
        rf'(?:Amount|AMOUNT)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
        r'(?:港幣)\s*([\d,]+\.?\d*)',
        rf'(?:Subtotal|Sub\s*Total|小計)[:\s]*{_CUR}\s*([\d,]+\.?\d*)',
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

    standalone_amount = re.search(r'^\s*([\d,]+\.?\d*)\s*$', text, re.MULTILINE)
    if standalone_amount:
        try:
            val = float(standalone_amount.group(1).replace(',', ''))
            if val > 0:
                return val
        except ValueError:
            pass

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


def extract_description(lines: list[str]) -> str:
    if not lines or len(lines) < 2:
        return ""

    _DATE_PATTERNS = [
        r'^\d{4}[/.-]\d{1,2}[/.-]\d{1,2}$',
        r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{4}$',
        r'^\d{4}年\d{1,2}月\d{1,2}日$',
    ]
    _AMOUNT_PATTERN = r'^[\$]?[\d,]+\.?\d*$'

    for line in lines[1:]:
        cleaned = line.strip()
        if not cleaned:
            continue
        is_date = any(re.match(p, cleaned) for p in _DATE_PATTERNS)
        if is_date:
            continue
        if re.match(_AMOUNT_PATTERN, cleaned):
            continue
        if len(cleaned) < 2:
            continue
        return cleaned

    return ""


def extract_payment_method(text: str) -> str:
    if not text:
        return "N/A"

    payment_methods = [
        (r'\bAmerican\s*Express\b|\bAE\b', "American Express"),
        (r'\bVisa\b', "Visa"),
        (r'\bMastercard\b|\bMaster\s*Card\b', "Mastercard"),
        (r'八達通|\bOctopus\b', "Octopus"),
        (r'現金|\bCash\b', "Cash"),
        (r'信用卡|\bCredit\s*Card\b', "Credit Card"),
        (r'易辦事|\bEPS\b', "EPS"),
        (r'\bPayMe\b', "PayMe"),
        (r'支付寶|\bAlipay\b', "Alipay"),
        (r'微信支付|\bWeChat\s*Pay\b', "WeChat Pay"),
        (r'轉數快|\bFPS\b', "FPS"),
    ]

    for pattern, label in payment_methods:
        if re.search(pattern, text, re.IGNORECASE):
            return label

    return "N/A"


_MERCHANT_TYPE_MAP = {
    "daiso": "office_supplies", "大創": "office_supplies",
    "japan home": "office_supplies", "日本城": "office_supplies", "jhc": "office_supplies",
    "muji": "office_supplies", "無印良品": "office_supplies",
    "fortress": "office_supplies", "豐澤": "office_supplies",
    "broadway": "office_supplies", "百老匯": "office_supplies",
    "pricerite": "office_supplies", "實惠": "office_supplies",
    "parknshop": "miscellaneous", "百佳": "miscellaneous",
    "wellcome": "miscellaneous", "惠康": "miscellaneous",
    "7-eleven": "miscellaneous", "7-11": "miscellaneous", "七十一": "miscellaneous",
    "circle k": "miscellaneous", "ok便利店": "miscellaneous",
    "watsons": "miscellaneous", "屈臣氏": "miscellaneous",
    "mannings": "miscellaneous", "萬寧": "miscellaneous",
    "ikea": "miscellaneous", "宜家": "miscellaneous",
    "uniqlo": "miscellaneous",
    "h&m": "miscellaneous",
    "zara": "miscellaneous",
    "sa sa": "miscellaneous", "莎莎": "miscellaneous",
    "city super": "miscellaneous", "city'super": "miscellaneous",
    "log-on": "miscellaneous", "logon": "miscellaneous",
    "apita": "miscellaneous",
    "yata": "miscellaneous", "一田": "miscellaneous",
    "sogo": "miscellaneous", "崇光": "miscellaneous",
    "mcdonald": "meals_entertainment", "麥當勞": "meals_entertainment",
    "kfc": "meals_entertainment", "肯德基": "meals_entertainment",
    "starbucks": "meals_entertainment", "星巴克": "meals_entertainment",
    "maxim": "meals_entertainment", "美心": "meals_entertainment",
    "tamjai": "meals_entertainment", "譚仔": "meals_entertainment",
    "yoshinoya": "meals_entertainment", "吉野家": "meals_entertainment",
    "fairwood": "meals_entertainment", "大快活": "meals_entertainment",
    "cafe de coral": "meals_entertainment", "大家樂": "meals_entertainment",
    "tsui wah": "meals_entertainment", "翠華": "meals_entertainment",
    "pacific coffee": "meals_entertainment", "太平洋咖啡": "meals_entertainment",
    "subway": "meals_entertainment", "賽百味": "meals_entertainment",
    "pizza hut": "meals_entertainment", "必勝客": "meals_entertainment",
    "domino": "meals_entertainment", "達美樂": "meals_entertainment",
    "hai di lao": "meals_entertainment", "海底撈": "meals_entertainment",
    "din tai fung": "meals_entertainment", "鼎泰豐": "meals_entertainment",
    "ichiran": "meals_entertainment", "一蘭": "meals_entertainment",
    "pret": "meals_entertainment",
    "shake shack": "meals_entertainment",
    "lady m": "meals_entertainment",
    "arabica": "meals_entertainment", "%arabica": "meals_entertainment",
    "emerald": "meals_entertainment", "翠園": "meals_entertainment",
    "lei garden": "meals_entertainment", "利苑": "meals_entertainment",
    "fook lam moon": "meals_entertainment", "福臨門": "meals_entertainment",
    "mtr": "transportation", "港鐵": "transportation",
    "taxi": "transportation", "的士": "transportation",
    "kmb": "transportation", "九巴": "transportation",
    "citybus": "transportation", "城巴": "transportation",
    "nwfb": "transportation", "新巴": "transportation",
    "octopus": "transportation", "八達通": "transportation",
    "tram": "transportation", "電車": "transportation",
    "star ferry": "transportation", "天星小輪": "transportation", "天星": "transportation",
    "first ferry": "transportation", "新渡輪": "transportation", "nwff": "transportation",
    "uber": "transportation",
    "cross harbour": "transportation", "海底隧道": "transportation",
    "eastern harbour": "transportation", "東區海底": "transportation",
    "airport express": "transportation", "機場快綫": "transportation", "機場快線": "transportation",
    "clp power": "utilities", "clp": "utilities", "中電": "utilities",
    "hk electric": "utilities", "港燈": "utilities", "hke": "utilities",
    "town gas": "utilities", "煤氣": "utilities",
    "pccw": "utilities", "電訊盈科": "utilities",
    "hkbn": "utilities", "香港寬頻": "utilities",
    "水務署": "utilities",
    "smartone": "utilities", "數碼通": "utilities",
    "3hk": "utilities", "3香港": "utilities",
    "china mobile": "utilities", "中國移動": "utilities", "cmhk": "utilities",
    "now tv": "utilities", "now寬頻": "utilities",
    "hsbc": "professional_fees", "匯豐": "professional_fees",
    "hang seng": "professional_fees", "恆生": "professional_fees",
    "boc": "professional_fees", "中銀": "professional_fees",
    "standard chartered": "professional_fees", "渣打": "professional_fees",
    "post office": "professional_fees", "郵局": "professional_fees",
    "government": "professional_fees", "政府": "professional_fees",
    "hospital": "professional_fees", "醫院": "professional_fees",
    "clinic": "professional_fees", "診所": "professional_fees",
    "bupa": "insurance", "保柏": "insurance",
    "aia": "insurance", "友邦": "insurance",
    "manulife": "insurance", "宏利": "insurance",
    "prudential": "insurance", "保誠": "insurance",
}


def classify_receipt_type(text: str, merchant: str) -> str:
    merchant_lower = merchant.lower()
    for key, rtype in _MERCHANT_TYPE_MAP.items():
        if key in merchant_lower:
            return rtype

    combined = f"{merchant} {text}".lower()

    office_supplies_keywords = [
        "辦公", "文具", "stationery", "office supplies",
        "傢俬", "furniture", "電器", "electronics",
    ]
    for kw in office_supplies_keywords:
        if kw in combined:
            return "office_supplies"

    meals_entertainment_keywords = [
        "餐廳", "茶餐廳", "restaurant", "cafe", "咖啡", "coffee",
        "food", "美食", "壽司", "sushi", "火鍋", "hotpot", "燒味",
        "dim sum", "點心", "麵家", "noodle",
        "bakery", "麵包", "蛋糕", "cake", "tea house",
        "麵", "快餐", "fast food", "bistro", "酒吧", "pub restaurant",
        "酒家", "酒樓",
    ]
    for kw in meals_entertainment_keywords:
        if kw in combined:
            return "meals_entertainment"

    transportation_keywords = [
        "的士", "taxi", "mtr", "港鐵", "巴士", "bus",
        "八達通", "octopus", "九巴", "kmb", "城巴", "citybus",
        "新巴", "nwfb", "輕鐵", "light rail", "纜車", "tram",
        "車費", "票價", "車票", "月票",
        "渡輪", "ferry", "cable car", "taxi fare",
    ]
    for kw in transportation_keywords:
        if kw in combined:
            return "transportation"

    utility_keywords = [
        "電費", "水費", "煤氣", "electricity", "water", "gas",
        "中電", "clp power", "港燈", "hk electric", "水務署",
        "clp", "hke", "town gas", "pccw", "電訊盈科", "hkbn", "香港寬頻",
        "煤氣費", "寬頻", "broadband", "流動電話", "mobile",
        "月費", "monthly fee", "賬單", "錶",
    ]
    for kw in utility_keywords:
        if kw in combined:
            return "utilities"

    rent_rates_keywords = [
        "租金", "差餉", "rent", "rates",
        "物業管理", "management fee",
    ]
    for kw in rent_rates_keywords:
        if kw in combined:
            return "rent_rates"

    professional_fees_keywords = [
        "專業", "professional", "法律", "legal",
        "會計", "accounting", "顧問", "consulting",
        "audit", "核數",
    ]
    for kw in professional_fees_keywords:
        if kw in combined:
            return "professional_fees"

    insurance_keywords = [
        "保險", "insurance", "premium", "保費",
    ]
    for kw in insurance_keywords:
        if kw in combined:
            return "insurance"

    repairs_maintenance_keywords = [
        "維修", "repair", "保養", "maintenance",
        "裝修", "renovation",
    ]
    for kw in repairs_maintenance_keywords:
        if kw in combined:
            return "repairs_maintenance"

    travel_keywords = [
        "機票", "air ticket", "flight", "酒店", "hotel",
        "住宿", "accommodation", "出差",
    ]
    for kw in travel_keywords:
        if kw in combined:
            return "travel"

    marketing_keywords = [
        "廣告", "advertising", "推廣", "promotion",
        "市場", "marketing",
    ]
    for kw in marketing_keywords:
        if kw in combined:
            return "marketing"

    depreciation_keywords = [
        "折舊", "depreciation", "攤銷", "amortization",
    ]
    for kw in depreciation_keywords:
        if kw in combined:
            return "depreciation"

    if "invoice" in combined or "發票" in combined or "invoice" in text.lower():
        invoice_type_hints = [
            (["office supplies", "辦公用品", "stationery", "文具"], "office_supplies"),
            (["meals", "entertainment", "膳食", "餐飲", "catering"], "meals_entertainment"),
            (["transport", "travel", "交通", "車資", "旅費"], "transportation"),
            (["rent", "utilities", "租金", "水電"], "utilities"),
            (["professional", "legal", "accounting", "專業", "法律", "會計"], "professional_fees"),
            (["insurance", "保險"], "insurance"),
            (["repair", "maintenance", "維修", "保養"], "repairs_maintenance"),
            (["hotel", "flight", "酒店", "機票"], "travel"),
            (["advertising", "marketing", "廣告", "推廣"], "marketing"),
        ]
        for keywords, hint_type in invoice_type_hints:
            if any(kw in combined for kw in keywords):
                return hint_type

    return "miscellaneous"


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
