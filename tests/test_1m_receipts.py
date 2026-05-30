import sys
import os
import random
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.receipt_parser import (
    extract_merchant,
    extract_date,
    extract_total,
    extract_tax,
    classify_receipt_type,
)

random.seed(42)

N = 1_000_000

RETAIL_MERCHANTS = [
    ("ParknShop", "百佳", "retail"),
    ("PARKnSHOP", "百佳", "retail"),
    ("百佳", "百佳", "retail"),
    ("Wellcome", "惠康", "retail"),
    ("WELLCOME", "惠康", "retail"),
    ("惠康", "惠康", "retail"),
    ("7-Eleven", "七十一", "retail"),
    ("7-11", "七十一", "retail"),
    ("七十一", "七十一", "retail"),
    ("Circle K", "OK便利店", "retail"),
    ("OK便利店", "OK便利店", "retail"),
    ("Watsons", "屈臣氏", "retail"),
    ("WATSONS", "屈臣氏", "retail"),
    ("屈臣氏", "屈臣氏", "retail"),
    ("Mannings", "萬寧", "retail"),
    ("MANNINGS", "萬寧", "retail"),
    ("萬寧", "萬寧", "retail"),
    ("IKEA", "宜家", "retail"),
    ("宜家", "宜家", "retail"),
    ("UNIQLO", "", "retail"),
    ("H&M", "", "retail"),
    ("ZARA", "", "retail"),
    ("Muji", "無印良品", "retail"),
    ("無印良品", "無印良品", "retail"),
    ("Daiso", "大創", "retail"),
    ("大創", "大創", "retail"),
    ("Japan Home Centre", "日本城", "retail"),
    ("日本城", "日本城", "retail"),
    ("Fortress", "豐澤", "retail"),
    ("豐澤", "豐澤", "retail"),
    ("Broadway", "百老匯", "retail"),
    ("百老匯", "百老匯", "retail"),
    ("Pricerite", "實惠", "retail"),
    ("實惠", "實惠", "retail"),
    ("City Super", "", "retail"),
    ("LOG-ON", "", "retail"),
    ("Apita", "", "retail"),
    ("Yata", "一田", "retail"),
    ("一田", "一田", "retail"),
    ("SOGO", "崇光", "retail"),
    ("崇光", "崇光", "retail"),
    ("Sa Sa", "莎莎", "retail"),
]

RESTAURANT_MERCHANTS = [
    ("McDonald's", "麥當勞", "restaurant"),
    ("MCDONALD'S", "麥當勞", "restaurant"),
    ("麥當勞", "麥當勞", "restaurant"),
    ("KFC", "肯德基", "restaurant"),
    ("肯德基", "肯德基", "restaurant"),
    ("Starbucks", "星巴克", "restaurant"),
    ("STARBUCKS", "星巴克", "restaurant"),
    ("星巴克", "星巴克", "restaurant"),
    ("Maxim's", "美心", "restaurant"),
    ("美心", "美心", "restaurant"),
    ("TamJai", "譚仔", "restaurant"),
    ("譚仔", "譚仔", "restaurant"),
    ("Yoshinoya", "吉野家", "restaurant"),
    ("吉野家", "吉野家", "restaurant"),
    ("Fairwood", "大快活", "restaurant"),
    ("大快活", "大快活", "restaurant"),
    ("Cafe de Coral", "大家樂", "restaurant"),
    ("大家樂", "大家樂", "restaurant"),
    ("Tsui Wah", "翠華", "restaurant"),
    ("翠華", "翠華", "restaurant"),
    ("Pacific Coffee", "", "restaurant"),
    ("Subway", "", "restaurant"),
    ("Pizza Hut", "", "restaurant"),
    ("Domino's", "", "restaurant"),
    ("Hai Di Lao", "海底撈", "restaurant"),
    ("海底撈", "海底撈", "restaurant"),
    ("Din Tai Fung", "鼎泰豐", "restaurant"),
    ("鼎泰豐", "鼎泰豐", "restaurant"),
    ("Ichiran", "一蘭", "restaurant"),
    ("一蘭", "一蘭", "restaurant"),
    ("Pret A Manger", "", "restaurant"),
    ("Shake Shack", "", "restaurant"),
    ("Lady M", "", "restaurant"),
    ("% Arabica", "", "restaurant"),
    ("Emerald", "翠園", "restaurant"),
    ("翠園", "翠園", "restaurant"),
    ("Lei Garden", "利苑", "restaurant"),
    ("利苑", "利苑", "restaurant"),
    ("Fook Lam Moon", "福臨門", "restaurant"),
    ("福臨門", "福臨門", "restaurant"),
]

TRANSPORT_MERCHANTS = [
    ("MTR", "港鐵", "transportation"),
    ("港鐵", "港鐵", "transportation"),
    ("KMB", "九巴", "transportation"),
    ("九巴", "九巴", "transportation"),
    ("Citybus", "城巴", "transportation"),
    ("城巴", "城巴", "transportation"),
    ("NWFB", "新巴", "transportation"),
    ("新巴", "新巴", "transportation"),
    ("HK Tramways", "電車", "transportation"),
    ("電車", "電車", "transportation"),
    ("Star Ferry", "天星小輪", "transportation"),
    ("天星小輪", "天星小輪", "transportation"),
    ("New World First Ferry", "新渡輪", "transportation"),
    ("新渡輪", "新渡輪", "transportation"),
    ("Taxi", "的士", "transportation"),
    ("的士", "的士", "transportation"),
    ("Uber", "", "transportation"),
    ("Octopus", "八達通", "transportation"),
    ("八達通", "八達通", "transportation"),
    ("Airport Express", "機場快綫", "transportation"),
    ("機場快綫", "機場快綫", "transportation"),
]

UTILITY_MERCHANTS = [
    ("CLP Power", "中電", "utilities"),
    ("中電", "中電", "utilities"),
    ("HK Electric", "港燈", "utilities"),
    ("港燈", "港燈", "utilities"),
    ("Town Gas", "煤氣", "utilities"),
    ("煤氣", "煤氣", "utilities"),
    ("Water Supplies Dept", "水務署", "utilities"),
    ("水務署", "水務署", "utilities"),
    ("PCCW", "電訊盈科", "utilities"),
    ("電訊盈科", "電訊盈科", "utilities"),
    ("HKBN", "香港寬頻", "utilities"),
    ("香港寬頻", "香港寬頻", "utilities"),
    ("SmarTone", "數碼通", "utilities"),
    ("3HK", "3香港", "utilities"),
    ("China Mobile HK", "中國移動香港", "utilities"),
    ("Now TV", "", "utilities"),
]

OTHER_MERCHANTS = [
    ("HSBC", "匯豐", "other"),
    ("匯豐", "匯豐", "other"),
    ("Hang Seng Bank", "恆生", "other"),
    ("BOC", "中銀", "other"),
    ("Standard Chartered", "渣打", "other"),
    ("Post Office", "郵局", "other"),
    ("Government Dept", "政府", "other"),
    ("Hospital Authority", "醫院", "other"),
    ("ABC Store", "", "other"),
    ("XYZ Shop", "", "other"),
    ("Random Shop", "", "other"),
    ("測試店鋪", "", "other"),
    ("Hello Mart", "", "other"),
    ("Good Buy", "", "other"),
    ("Quick Shop", "", "other"),
    ("Easy Store", "", "other"),
    ("Happy Mall", "", "other"),
    ("Sunrise Ltd", "", "other"),
]

ALL_MERCHANTS = RETAIL_MERCHANTS + RESTAURANT_MERCHANTS + TRANSPORT_MERCHANTS + UTILITY_MERCHANTS + OTHER_MERCHANTS

DATE_FORMATS = [
    "chinese",
    "dd_mm_yyyy_slash",
    "yyyy_mm_dd_dash",
    "dd_mm_yyyy_dot",
    "dd_mm_yyyy_dash",
    "dd_mm_yy_slash",
    "mm_dd_yyyy_slash",
    "yyyy_mm_dd_slash",
]

TOTAL_LABELS = [
    "Total",
    "Balance Due",
    "Grand Total",
    "總計",
    "Amount Due",
]


def _replace_total_line(text, total_line):
    last_pos = -1
    for label in TOTAL_LABELS:
        for suffix in [":", " HKD "]:
            pos = text.rfind(f"{label}{suffix}")
            if pos > last_pos:
                last_pos = pos
    if last_pos >= 0:
        text = text[:last_pos] + total_line
    return text


AMOUNT_FORMATS = [
    "dollar",
    "hk_dollar",
    "hkd_space",
    "plain_decimal",
    "comma_dollar",
    "chinese_hkd",
    "hk_dot_dollar",
    "dollar_decimal",
    "comma_plain",
    "hk_comma_dollar",
    "no_symbol",
    "hkd_label",
]

LANGUAGES = ["en", "zh", "mixed"]

RECEIPT_FORMATS = [
    "thermal_en",
    "thermal_zh",
    "a4_invoice",
    "taxi_receipt",
    "utility_bill",
    "simple_receipt",
    "detailed_receipt",
    "bilingual_receipt",
    "chinese_only",
    "invoice_table",
]

RETAIL_ITEMS_EN = [
    "Apples x3", "Rice 5kg", "Milk 1L", "Bread", "Eggs x12",
    "Orange Juice", "Chips", "Noodles", "Toilet Paper", "Soap",
    "Shampoo", "Detergent", "Canned Food", "Frozen Pizza", "Cheese",
]
RETAIL_ITEMS_ZH = [
    "米 5公斤", "牛奶 1升", "麵包", "雞蛋 12隻", "橙汁",
    "薯片", "即食麵", "廁紙", "番梘", "洗頭水",
]

RESTAURANT_ITEMS_EN = [
    "Set Lunch A", "Iced Lemon Tea", "Fried Rice", "Wonton Noodle",
    "Milk Tea", "Toast", "Sandwich", "Coffee", "Soup", "Salad",
]
RESTAURANT_ITEMS_ZH = [
    "午餐肉通粉", "凍檸茶", "炒飯", "雲吞麵", "奶茶",
    "多士", "三文治", "咖啡", "湯麵", "小菜",
]

TRANSPORT_ITEMS_EN = [
    "Adult Octopus", "MTR Fare", "Bus Fare", "Taxi Fare",
    "Light Rail", "Airport Express", "Cross Harbour",
]
TRANSPORT_ITEMS_ZH = [
    "成人八達通", "港鐵車費", "巴士車費", "的士車費",
    "輕鐵", "機場快綫", "過海",
]

UTILITY_ITEMS_EN = [
    "Electricity Charge", "Water Charge", "Gas Charge",
    "Monthly Fee", "Service Charge", "Equipment Rental",
]
UTILITY_ITEMS_ZH = [
    "電費", "水費", "煤氣費", "月費", "服務費", "設備租用",
]

OTHER_ITEMS_EN = [
    "Service Fee", "Processing Charge", "Admin Fee", "Consultation",
]
OTHER_ITEMS_ZH = [
    "服務費", "手續費", "行政費", "諮詢費",
]

ITEMS_BY_TYPE = {
    "retail": (RETAIL_ITEMS_EN, RETAIL_ITEMS_ZH),
    "restaurant": (RESTAURANT_ITEMS_EN, RESTAURANT_ITEMS_ZH),
    "transportation": (TRANSPORT_ITEMS_EN, TRANSPORT_ITEMS_ZH),
    "utilities": (UTILITY_ITEMS_EN, UTILITY_ITEMS_ZH),
    "other": (OTHER_ITEMS_EN, OTHER_ITEMS_ZH),
}


def gen_amount(edge=None):
    if edge == "very_large":
        return round(random.uniform(100000, 999999.99), 2)
    elif edge == "very_small":
        return round(random.uniform(0.01, 0.99), 2)
    elif edge == "zero":
        return 0.0
    r = random.random()
    if r < 0.05:
        return round(random.uniform(0.1, 0.99), 2)
    elif r < 0.10:
        return round(random.uniform(50000, 200000), 2)
    elif r < 0.30:
        return round(random.uniform(100, 5000), 2)
    else:
        return round(random.uniform(1, 500), 2)


def gen_date():
    y = random.choice([2023, 2024, 2025, 2026])
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return y, m, d


def format_date(y, m, d, fmt):
    if fmt == "chinese":
        return f"{y}年{m:02d}月{d:02d}日", f"{y}-{m:02d}-{d:02d}"
    elif fmt == "dd_mm_yyyy_slash":
        return f"{d:02d}/{m:02d}/{y}", f"{y}-{m:02d}-{d:02d}"
    elif fmt == "yyyy_mm_dd_dash":
        return f"{y}-{m:02d}-{d:02d}", f"{y}-{m:02d}-{d:02d}"
    elif fmt == "dd_mm_yyyy_dot":
        return f"{d:02d}.{m:02d}.{y}", f"{y}-{m:02d}-{d:02d}"
    elif fmt == "dd_mm_yyyy_dash":
        return f"{d:02d}-{m:02d}-{y}", f"{y}-{m:02d}-{d:02d}"
    elif fmt == "dd_mm_yy_slash":
        return f"{d:02d}/{m:02d}/{y % 100:02d}", None
    elif fmt == "mm_dd_yyyy_slash":
        return f"{m:02d}/{d:02d}/{y}", None
    elif fmt == "yyyy_mm_dd_slash":
        return f"{y}/{m:02d}/{d:02d}", f"{y}-{m:02d}-{d:02d}"
    return f"{d:02d}/{m:02d}/{y}", f"{y}-{m:02d}-{d:02d}"


def format_amount_value(amount):
    if amount >= 1000 and random.random() < 0.3:
        return f"{amount:,.2f}"
    if amount == int(amount):
        return f"{amount:.2f}"
    return f"{amount:.2f}"


def format_total_line(label, amount, fmt):
    amt_str = format_amount_value(amount)
    if fmt == "dollar":
        return f"{label}: ${amt_str}"
    elif fmt == "hk_dollar":
        return f"{label}: HK${amt_str}"
    elif fmt == "hkd_space":
        return f"{label}: HKD {amt_str}"
    elif fmt == "plain_decimal":
        return f"{label}: {amt_str}"
    elif fmt == "comma_dollar":
        return f"{label}: ${amount:,.2f}"
    elif fmt == "chinese_hkd":
        return f"{label}: 港幣{amt_str}"
    elif fmt == "hk_dot_dollar":
        return f"{label}: H.K.${amt_str}"
    elif fmt == "dollar_decimal":
        return f"{label}: ${amt_str}"
    elif fmt == "comma_plain":
        return f"{label}: {amount:,.2f}"
    elif fmt == "hk_comma_dollar":
        return f"{label}: HK${amount:,.2f}"
    elif fmt == "no_symbol":
        return f"{label}: {amt_str}"
    elif fmt == "hkd_label":
        return f"{label} HKD {amt_str}"
    return f"{label}: ${amt_str}"


def _pick_items(receipt_type, lang, n_items):
    en_items, zh_items = ITEMS_BY_TYPE.get(receipt_type, (RETAIL_ITEMS_EN, RETAIL_ITEMS_ZH))
    if lang == "en":
        pool = en_items
    elif lang == "zh":
        pool = zh_items
    else:
        pool = en_items + zh_items
    return random.sample(pool, min(n_items, len(pool)))


def fmt_thermal_en(merchant, date_str, items, total_line, extra_lines):
    lines = [merchant, f"Date: {date_str}", "-" * 30]
    for item in items:
        price = round(random.uniform(5, 200), 2)
        lines.append(f"{item}  ${price:.2f}")
    lines.append("-" * 30)
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_thermal_zh(merchant, date_str, items, total_line, extra_lines):
    lines = [merchant, f"日期: {date_str}", "─" * 30]
    for item in items:
        price = round(random.uniform(5, 200), 2)
        lines.append(f"{item}  ${price:.2f}")
    lines.append("─" * 30)
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_a4_invoice(merchant, date_str, items, total_line, extra_lines):
    inv_no = f"INV-{random.randint(10000, 99999)}"
    lines = [
        merchant,
        f"Invoice No: {inv_no}",
        f"Date: {date_str}",
        "",
        f"{'Description':<30} {'Qty':>5} {'Price':>10} {'Amount':>10}",
        "-" * 60,
    ]
    for item in items:
        qty = random.randint(1, 5)
        price = round(random.uniform(10, 500), 2)
        amt = round(qty * price, 2)
        lines.append(f"{item:<30} {qty:>5} ${price:>9.2f} ${amt:>9.2f}")
    lines.append("-" * 60)
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_taxi_receipt(merchant, date_str, items, total_line, extra_lines):
    license_no = f"HK{random.randint(1000, 9999)}"
    route = random.choice(["Central -> TST", "Mong Kok -> Causeway Bay", "Admiralty -> North Point"])
    lines = [
        merchant,
        f"License: {license_no}",
        f"Date: {date_str}",
        f"Route: {route}",
        f"Fare: ${round(random.uniform(30, 300), 2):.2f}",
        f"Tunnel: ${random.choice([0, 20, 25, 35]):.2f}",
        f"Baggage: ${random.choice([0, 5, 10]):.2f}",
        "-" * 30,
        total_line,
        "Thank you for riding with us!",
    ]
    return "\n".join(lines)


def fmt_utility_bill(merchant, date_str, items, total_line, extra_lines):
    meter = random.randint(100000, 999999)
    consumption = random.randint(100, 5000)
    lines = [
        merchant,
        f"Bill Date: {date_str}",
        f"Account No: {random.randint(10000000, 99999999)}",
        f"Meter Reading: {meter}",
        f"Consumption: {consumption} kWh",
        "-" * 30,
    ]
    for item in items:
        price = round(random.uniform(50, 2000), 2)
        lines.append(f"{item}  ${price:.2f}")
    lines.append("-" * 30)
    lines.append(total_line)
    lines.append("Payment due by end of month")
    return "\n".join(lines)


def fmt_simple_receipt(merchant, date_str, items, total_line, extra_lines):
    lines = [merchant, f"Date: {date_str}"]
    for item in items[:2]:
        price = round(random.uniform(5, 100), 2)
        lines.append(f"{item}  ${price:.2f}")
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_detailed_receipt(merchant, date_str, items, total_line, extra_lines):
    subtotal = 0.0
    lines = [merchant, f"Date: {date_str}", "-" * 30]
    for item in items:
        price = round(random.uniform(5, 200), 2)
        subtotal += price
        lines.append(f"{item}  ${price:.2f}")
    lines.append("-" * 30)
    lines.append(f"Subtotal: ${subtotal:.2f}")
    sc = round(subtotal * 0.1, 2)
    lines.append(f"Service Charge (10%): ${sc:.2f}")
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_bilingual_receipt(merchant, date_str, items, total_line, extra_lines):
    lines = [merchant, f"Date / 日期: {date_str}", "-" * 30]
    en_items, zh_items = items[:len(items)//2], items[len(items)//2:]
    for en, zh in zip(en_items, zh_items):
        price = round(random.uniform(5, 200), 2)
        lines.append(f"{en}/{zh}  ${price:.2f}")
    if len(en_items) > len(zh_items):
        for en in en_items[len(zh_items):]:
            price = round(random.uniform(5, 200), 2)
            lines.append(f"{en}  ${price:.2f}")
    lines.append("-" * 30)
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_chinese_only(merchant, date_str, items, total_line, extra_lines):
    lines = [merchant, f"日期: {date_str}", "─" * 30]
    for item in items:
        price = round(random.uniform(5, 200), 2)
        lines.append(f"{item}  ${price:.2f}")
    lines.append("─" * 30)
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


def fmt_invoice_table(merchant, date_str, items, total_line, extra_lines):
    inv_no = f"INV-{random.randint(10000, 99999)}"
    lines = [
        merchant,
        f"Invoice No: {inv_no}",
        f"Date: {date_str}",
        "",
        "| Description | Qty | Price | Amount |",
        "|-------------|-----|-------|--------|",
    ]
    for item in items:
        qty = random.randint(1, 5)
        price = round(random.uniform(10, 500), 2)
        amt = round(qty * price, 2)
        lines.append(f"| {item} | {qty} | ${price:.2f} | ${amt:.2f} |")
    lines.append("|-------------|-----|-------|--------|")
    lines.append(total_line)
    lines.extend(extra_lines)
    return "\n".join(lines)


FORMAT_FUNCS = {
    "thermal_en": fmt_thermal_en,
    "thermal_zh": fmt_thermal_zh,
    "a4_invoice": fmt_a4_invoice,
    "taxi_receipt": fmt_taxi_receipt,
    "utility_bill": fmt_utility_bill,
    "simple_receipt": fmt_simple_receipt,
    "detailed_receipt": fmt_detailed_receipt,
    "bilingual_receipt": fmt_bilingual_receipt,
    "chinese_only": fmt_chinese_only,
    "invoice_table": fmt_invoice_table,
}

FOOTER_BY_TYPE = {
    "retail": ["Thank you for shopping!"],
    "restaurant": ["Thank you for dining with us!"],
    "transportation": ["Thank you for riding with us!"],
    "utilities": ["Payment due by end of month"],
    "other": ["Thank you!"],
}

FOOTER_ZH = {
    "retail": ["多謝惠顧！"],
    "restaurant": ["多謝光臨！"],
    "transportation": ["多謝乘搭！"],
    "utilities": ["請於月底前繳費"],
    "other": ["多謝！"],
}


def generate_standard_case():
    type_weights = [
        ("retail", 0.28),
        ("restaurant", 0.28),
        ("transportation", 0.15),
        ("utilities", 0.12),
        ("other", 0.17),
    ]
    r = random.random()
    cumulative = 0
    receipt_type = "other"
    for t, w in type_weights:
        cumulative += w
        if r < cumulative:
            receipt_type = t
            break

    if receipt_type == "retail":
        m = random.choice(RETAIL_MERCHANTS)
    elif receipt_type == "restaurant":
        m = random.choice(RESTAURANT_MERCHANTS)
    elif receipt_type == "transportation":
        m = random.choice(TRANSPORT_MERCHANTS)
    elif receipt_type == "utilities":
        m = random.choice(UTILITY_MERCHANTS)
    else:
        m = random.choice(OTHER_MERCHANTS)

    merchant_en = m[0]
    receipt_type = m[2]
    date_fmt = random.choice(DATE_FORMATS)
    amount_fmt = random.choice(AMOUNT_FORMATS)
    label = random.choice(TOTAL_LABELS)
    lang = random.choice(LANGUAGES)
    receipt_fmt = random.choice(RECEIPT_FORMATS)
    include_tax = random.random() < 0.3

    y, m_val, d = gen_date()
    date_str, expected_date = format_date(y, m_val, d, date_fmt)
    amount = gen_amount()
    total_line = format_total_line(label, amount, amount_fmt)

    n_items = random.randint(2, 6)
    items = _pick_items(receipt_type, lang, n_items)

    if lang == "zh":
        footers = FOOTER_ZH.get(receipt_type, ["多謝！"])
    elif lang == "en":
        footers = FOOTER_BY_TYPE.get(receipt_type, ["Thank you!"])
    else:
        footers = FOOTER_BY_TYPE.get(receipt_type, ["Thank you!"]) + FOOTER_ZH.get(receipt_type, ["多謝！"])

    extra_lines = list(footers)
    if include_tax:
        tax_amt = round(amount * random.uniform(0, 0.05), 2)
        extra_lines.insert(0, f"Tax: ${tax_amt:.2f}")
    else:
        tax_amt = None

    fmt_func = FORMAT_FUNCS[receipt_fmt]
    text = fmt_func(merchant_en, date_str, items, total_line, extra_lines)
    lines = text.split("\n")

    expected = {
        "merchant": merchant_en,
        "date": expected_date,
        "total": amount,
        "tax": tax_amt if include_tax else None,
        "receipt_type": receipt_type,
    }
    return receipt_type, receipt_fmt, text, lines, expected


def generate_edge_case():
    edge_type = random.choice([
        "very_large_amount",
        "very_small_amount",
        "zero_amount",
        "discount_line",
        "service_charge",
        "multiple_totals",
        "no_date",
        "no_merchant",
        "empty_lines",
        "qr_code_text",
    ])

    if edge_type == "very_large_amount":
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        amount = gen_amount(edge="very_large")
        total_line = format_total_line("Total", amount, "dollar")
        text = _replace_total_line(text, total_line)
        lines = text.split("\n")
        expected["total"] = amount
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "very_small_amount":
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        amount = gen_amount(edge="very_small")
        total_line = format_total_line("Total", amount, "dollar")
        text = _replace_total_line(text, total_line)
        lines = text.split("\n")
        expected["total"] = amount
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "zero_amount":
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        total_line = format_total_line("Total", 0.0, "dollar")
        text = _replace_total_line(text, total_line)
        lines = text.split("\n")
        expected["total"] = 0.0
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "discount_line":
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        discount = round(random.uniform(5, 50), 2)
        text += f"\nDiscount: -${discount:.2f}"
        lines = text.split("\n")
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "service_charge":
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        sc = round(expected["total"] * 0.1, 2)
        text += f"\nService Charge: ${sc:.2f}"
        lines = text.split("\n")
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "multiple_totals":
        merchant = "ParknShop"
        y, m_val, d = gen_date()
        subtotal = round(random.uniform(50, 200), 2)
        total = round(subtotal * 1.0, 2)
        text = f"{merchant}\nDate: {d:02d}/{m_val:02d}/{y}\nSubtotal: ${subtotal:.2f}\nTotal: ${total:.2f}"
        lines = text.split("\n")
        expected = {
            "merchant": merchant,
            "date": f"{y}-{m_val:02d}-{d:02d}",
            "total": total,
            "tax": None,
            "receipt_type": "retail",
        }
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "no_date":
        merchant = "McDonald's"
        amount = round(random.uniform(20, 100), 2)
        text = f"{merchant}\nCoffee  $30.00\nSandwich  $45.00\nTotal: ${amount:.2f}"
        lines = text.split("\n")
        expected = {
            "merchant": merchant,
            "date": None,
            "total": amount,
            "tax": None,
            "receipt_type": "restaurant",
        }
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "no_merchant":
        y, m_val, d = gen_date()
        amount = round(random.uniform(10, 100), 2)
        text = f"Date: {d:02d}/{m_val:02d}/{y}\nItem  $50.00\nTotal: ${amount:.2f}"
        lines = text.split("\n")
        expected = {
            "merchant": "Date: " + f"{d:02d}/{m_val:02d}/{y}",
            "date": f"{y}-{m_val:02d}-{d:02d}",
            "total": amount,
            "tax": None,
            "receipt_type": "other",
        }
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "empty_lines":
        merchant = "Wellcome"
        y, m_val, d = gen_date()
        amount = round(random.uniform(10, 100), 2)
        text = f"\n\n{merchant}\n\nDate: {d:02d}/{m_val:02d}/{y}\n\nRice  $45.00\n\nTotal: ${amount:.2f}\n\n"
        lines = text.split("\n")
        expected = {
            "merchant": merchant,
            "date": f"{y}-{m_val:02d}-{d:02d}",
            "total": amount,
            "tax": None,
            "receipt_type": "retail",
        }
        return "edge_" + edge_type, text, lines, expected

    elif edge_type == "qr_code_text":
        merchant = "7-Eleven"
        y, m_val, d = gen_date()
        amount = round(random.uniform(10, 50), 2)
        qr_data = f"QR:https://pay.7-eleven.hk/ref/{random.randint(100000,999999)}"
        text = f"{merchant}\nDate: {d:02d}/{m_val:02d}/{y}\nSnack  $15.00\nDrink  $12.00\nTotal: ${amount:.2f}\n{qr_data}"
        lines = text.split("\n")
        expected = {
            "merchant": merchant,
            "date": f"{y}-{m_val:02d}-{d:02d}",
            "total": amount,
            "tax": None,
            "receipt_type": "retail",
        }
        return "edge_" + edge_type, text, lines, expected

    return generate_standard_case() + ("edge_unknown",)


def run_tests():
    print("=" * 70)
    print("HK Receipt Parser — 1,000,000 Receipt Stress Test")
    print("=" * 70)
    print(f"Generating {N:,} test cases...\n")

    stats = {
        "total": 0,
        "passed": 0,
        "by_receipt_type": defaultdict(lambda: {"total": 0, "passed": 0}),
        "by_format": defaultdict(lambda: {"total": 0, "passed": 0}),
        "by_field": {
            "merchant": {"total": 0, "passed": 0},
            "date": {"total": 0, "passed": 0},
            "total": {"total": 0, "passed": 0},
            "tax": {"total": 0, "passed": 0},
            "receipt_type": {"total": 0, "passed": 0},
        },
        "failures": defaultdict(int),
        "edge_results": defaultdict(lambda: {"total": 0, "passed": 0}),
        "failure_examples": defaultdict(list),
    }

    n_edge = 50000
    n_standard = N - n_edge

    start = time.time()
    gen_start = time.time()

    for i in range(n_standard):
        receipt_type, receipt_fmt, text, lines, expected = generate_standard_case()
        _run_single(stats, receipt_type, receipt_fmt, text, lines, expected, i)

        if (i + 1) % 100000 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  [{i+1:>10,}/{N:,}] {rate:,.0f} cases/sec | {elapsed:.1f}s elapsed")

    for i in range(n_edge):
        result = generate_edge_case()
        if len(result) == 5:
            edge_type = "edge_unknown"
            receipt_type, receipt_fmt, text, lines, expected = result
        else:
            edge_type, text, lines, expected = result
            receipt_type = expected.get("receipt_type", "other")
            receipt_fmt = "edge"
        _run_single(stats, receipt_type, receipt_fmt, text, lines, expected, n_standard + i, edge_type=edge_type)

    elapsed = time.time() - start

    print(f"\n{'=' * 70}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total test cases:  {stats['total']:,}")
    print(f"Overall passed:    {stats['passed']:,}")
    overall_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
    print(f"Overall pass rate: {overall_rate:.2f}%")
    print(f"Time elapsed:      {elapsed:.2f}s")
    print(f"Throughput:        {stats['total']/elapsed:,.0f} cases/sec")

    print(f"\n{'─' * 60}")
    print("PASS RATE BY RECEIPT TYPE:")
    print(f"{'─' * 60}")
    for rtype in ["retail", "restaurant", "transportation", "utilities", "other"]:
        d = stats["by_receipt_type"].get(rtype, {"total": 0, "passed": 0})
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {rtype:20s}: {d['passed']:>7,}/{d['total']:>7,} ({rate:.2f}%)")

    print(f"\n{'─' * 60}")
    print("PASS RATE BY RECEIPT FORMAT:")
    print(f"{'─' * 60}")
    for fmt_name in RECEIPT_FORMATS + ["edge"]:
        d = stats["by_format"].get(fmt_name, {"total": 0, "passed": 0})
        if d["total"] > 0:
            rate = d["passed"] / d["total"] * 100
            print(f"  {fmt_name:20s}: {d['passed']:>7,}/{d['total']:>7,} ({rate:.2f}%)")

    print(f"\n{'─' * 60}")
    print("PASS RATE BY FIELD:")
    print(f"{'─' * 60}")
    for field in ["merchant", "date", "total", "tax", "receipt_type"]:
        d = stats["by_field"][field]
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {field:20s}: {d['passed']:>7,}/{d['total']:>7,} ({rate:.2f}%)")

    print(f"\n{'─' * 60}")
    print("TOP 20 FAILURE PATTERNS:")
    print(f"{'─' * 60}")
    sorted_failures = sorted(stats["failures"].items(), key=lambda x: -x[1])[:20]
    for pattern, count in sorted_failures:
        pct = count / stats["total"] * 100
        print(f"  {pattern:55s}: {count:>7,} ({pct:.2f}%)")

    print(f"\n{'─' * 60}")
    print("EDGE CASE RESULTS:")
    print(f"{'─' * 60}")
    for etype in sorted(stats["edge_results"].keys()):
        d = stats["edge_results"][etype]
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {etype:35s}: {d['passed']:>5,}/{d['total']:>5,} ({rate:.2f}%)")

    print(f"\n{'─' * 60}")
    print("FAILURE EXAMPLES (up to 3 per top pattern):")
    print(f"{'─' * 60}")
    shown = 0
    for pattern, count in sorted_failures[:10]:
        examples = stats["failure_examples"].get(pattern, [])
        for ex in examples[:3]:
            print(f"\n  [{pattern}]")
            print(f"    Expected: {ex['expected']}")
            print(f"    Got:      {ex['got']}")
            shown += 1
            if shown >= 15:
                break
        if shown >= 15:
            break

    print(f"\n{'=' * 70}")
    if overall_rate >= 95:
        print("VERDICT: EXCELLENT — Parser handles HK receipts very well")
    elif overall_rate >= 85:
        print("VERDICT: GOOD — Parser handles most HK receipts correctly")
    elif overall_rate >= 70:
        print("VERDICT: FAIR — Parser needs improvement in some areas")
    elif overall_rate >= 50:
        print("VERDICT: POOR — Parser needs significant improvement")
    else:
        print("VERDICT: CRITICAL — Parser fails on majority of receipts")
    print(f"{'=' * 70}")

    return stats


def _run_single(stats, receipt_type, receipt_fmt, text, lines, expected, idx, edge_type=None):
    stats["total"] += 1
    stats["by_receipt_type"][receipt_type]["total"] += 1
    stats["by_format"][receipt_fmt]["total"] += 1

    try:
        parsed_merchant = extract_merchant(lines)
        parsed_date = extract_date(text)
        parsed_total = extract_total(text)
        parsed_tax = extract_tax(text)
        parsed_type = classify_receipt_type(text, parsed_merchant)
    except Exception as e:
        stats["failures"][f"exception: {type(e).__name__}"] += 1
        return

    case_passed = True

    field_checks = [
        ("merchant", expected.get("merchant"), parsed_merchant),
        ("date", expected.get("date"), parsed_date),
        ("total", expected.get("total"), parsed_total),
        ("tax", expected.get("tax"), parsed_tax),
        ("receipt_type", expected.get("receipt_type"), parsed_type),
    ]

    for field, exp_val, got_val in field_checks:
        stats["by_field"][field]["total"] += 1
        passed = _check_field(field, exp_val, got_val)
        if passed:
            stats["by_field"][field]["passed"] += 1
        else:
            case_passed = False
            key = f"{field}_mismatch({receipt_type})"
            stats["failures"][key] += 1
            if len(stats["failure_examples"].get(key, [])) < 3:
                if key not in stats["failure_examples"]:
                    stats["failure_examples"][key] = []
                stats["failure_examples"][key].append({
                    "expected": exp_val,
                    "got": got_val,
                })

    if case_passed:
        stats["passed"] += 1
        stats["by_receipt_type"][receipt_type]["passed"] += 1
        stats["by_format"][receipt_fmt]["passed"] += 1

    if edge_type:
        stats["edge_results"][edge_type]["total"] += 1
        if case_passed:
            stats["edge_results"][edge_type]["passed"] += 1


def _check_field(field, expected, got):
    if field == "merchant":
        if expected and got:
            return expected.lower() in got.lower() or got.lower() in expected.lower()
        if not expected and not got:
            return True
        if expected == "" and got == "":
            return True
        return False
    elif field == "date":
        if expected is None:
            return True
        if expected and got:
            return expected == got
        return False
    elif field == "total":
        if expected is None:
            return True
        if expected is not None and got is not None:
            return abs(expected - got) < 0.02
        if expected == 0.0 and got is not None and got == 0.0:
            return True
        return False
    elif field == "tax":
        if expected is None:
            return True
        if expected is not None and got is not None:
            return abs(expected - got) < 0.02
        return True
    elif field == "receipt_type":
        return expected == got
    return True


if __name__ == "__main__":
    run_tests()
