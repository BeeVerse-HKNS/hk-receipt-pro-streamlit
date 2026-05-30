import sys
import os
import random
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.receipt_parser import (
    parse_receipt,
    extract_merchant,
    extract_date,
    extract_total,
    extract_tax,
    classify_receipt_type,
    calculate_confidence,
)

random.seed(42)

RETAIL_MERCHANTS = [
    ("ParknShop", "retail"), ("PARKnSHOP", "retail"), ("百佳", "retail"),
    ("Wellcome", "retail"), ("WELLCOME", "retail"), ("惠康", "retail"),
    ("7-Eleven", "retail"), ("7-11", "retail"), ("七十一", "retail"),
    ("Circle K", "retail"), ("OK便利店", "retail"),
    ("Watsons", "retail"), ("WATSONS", "retail"), ("屈臣氏", "retail"),
    ("Mannings", "retail"), ("MANNINGS", "retail"), ("萬寧", "retail"),
    ("IKEA", "retail"), ("宜家", "retail"),
    ("UNIQLO", "retail"), ("H&M", "retail"),
]

RESTAURANT_MERCHANTS = [
    ("McDonald's", "restaurant"), ("MCDONALD'S", "restaurant"), ("麥當勞", "restaurant"),
    ("KFC", "restaurant"), ("肯德基", "restaurant"),
    ("Starbucks", "restaurant"), ("STARBUCKS", "restaurant"), ("星巴克", "restaurant"),
    ("Maxim's", "restaurant"), ("美心", "restaurant"),
    ("TamJai", "restaurant"), ("譚仔", "restaurant"),
    ("Yoshinoya", "restaurant"), ("吉野家", "restaurant"),
    ("Fairwood", "restaurant"), ("大快活", "restaurant"),
    ("Cafe de Coral", "restaurant"), ("大家樂", "restaurant"),
    ("Tsui Wah", "restaurant"), ("翠華", "restaurant"),
]

TRANSPORT_MERCHANTS = [
    ("MTR", "transportation"), ("港鐵", "transportation"),
    ("Taxi", "transportation"), ("的士", "transportation"),
    ("KMB", "transportation"), ("九巴", "transportation"),
    ("CityBus", "transportation"), ("城巴", "transportation"),
    ("NWFB", "transportation"), ("新巴", "transportation"),
    ("Octopus", "transportation"), ("八達通", "transportation"),
]

UTILITY_MERCHANTS = [
    ("CLP Power", "utilities"), ("中電", "utilities"),
    ("HK Electric", "utilities"), ("港燈", "utilities"),
    ("Town Gas", "utilities"), ("煤氣", "utilities"),
    ("PCCW", "utilities"), ("電訊盈科", "utilities"),
    ("HKBN", "utilities"), ("香港寬頻", "utilities"),
    ("Water Supplies Dept", "utilities"), ("水務署", "utilities"),
]

OTHER_MERCHANTS = [
    ("ABC Store", "other"), ("XYZ Shop", "other"),
    ("Random Shop", "other"), ("測試店鋪", "other"),
    ("Hello Mart", "other"), ("Good Buy", "other"),
    ("Quick Shop", "other"), ("Easy Store", "other"),
    ("Happy Mall", "other"), ("Sunrise Ltd", "other"),
]

ALL_MERCHANTS = RETAIL_MERCHANTS + RESTAURANT_MERCHANTS + TRANSPORT_MERCHANTS + UTILITY_MERCHANTS + OTHER_MERCHANTS

DATE_TEMPLATES = [
    ("chinese", "{y}年{m}月{d}日"),
    ("dd_mm_yyyy", "{d}/{m}/{y}"),
    ("yyyy_mm_dd", "{y}-{m}-{d}"),
    ("dd_mm_yyyy_dot", "{d}.{m}.{y}"),
    ("dd_mm_yyyy_dash", "{d}-{m}-{y}"),
]

AMOUNT_TEMPLATES = [
    ("dollar", "${amount}"),
    ("hkd", "HKD {amount}"),
    ("hkdollar", "HK${amount}"),
    ("chinese_hkd", "港幣{amount}"),
    ("total_dollar", "總計: ${amount}"),
    ("total_eng", "Total HKD {amount}"),
    ("grand_total", "Grand Total: ${amount}"),
    ("amount_due", "Amount Due: HK${amount}"),
]

TAX_TEMPLATES = [
    ("tax_eng", "Tax: ${amount}"),
    ("tax_chi", "稅款: ${amount}"),
    ("gst", "GST: ${amount}"),
]

RETAIL_ITEMS = [
    "Apples x3", "Rice 5kg", "Milk 1L", "Bread", "Eggs x12",
    "Orange Juice", "Chips", "Noodles", "Toilet Paper", "Soap",
    "米 5公斤", "牛奶 1升", "麵包", "雞蛋 12隻", "橙汁",
]

RESTAURANT_ITEMS = [
    "Set Lunch A", "Iced Lemon Tea", "Fried Rice", "Wonton Noodle",
    "Milk Tea", "Toast", "Sandwich", "Coffee",
    "午餐肉通粉", "凍檸茶", "炒飯", "雲吞麵", "奶茶", "多士",
]

TRANSPORT_ITEMS = [
    "Adult Octopus", "MTR Fare", "Bus Fare", "Taxi Fare",
    "成人八達通", "港鐵車費", "巴士車費", "的士車費",
]

UTILITY_ITEMS = [
    "Electricity Charge", "Water Charge", "Gas Charge",
    "電費", "水費", "煤氣費",
]


def gen_amount():
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


def format_amount(amount):
    if amount >= 1000 and random.random() < 0.3:
        return f"{amount:,.2f}"
    return f"{amount:.2f}"


def generate_receipt_text(merchant, receipt_type, date_fmt, amount_fmt, include_tax, lang):
    y, m, d = gen_date()
    amount = gen_amount()
    tax_amount = round(amount * 0.0, 2) if receipt_type == "utilities" else round(amount * random.uniform(0, 0.05), 2)

    lines = [merchant]

    if date_fmt == "chinese":
        lines.append(f"日期: {y}年{m:02d}月{d:02d}日")
    elif date_fmt == "dd_mm_yyyy":
        lines.append(f"Date: {d:02d}/{m:02d}/{y}")
    elif date_fmt == "yyyy_mm_dd":
        lines.append(f"Date: {y}-{m:02d}-{d:02d}")
    elif date_fmt == "dd_mm_yyyy_dot":
        lines.append(f"Date: {d:02d}.{m:02d}.{y}")
    elif date_fmt == "dd_mm_yyyy_dash":
        lines.append(f"Date: {d:02d}-{m:02d}-{y}")

    if receipt_type == "retail":
        items = random.sample(RETAIL_ITEMS, min(random.randint(2, 5), len(RETAIL_ITEMS)))
    elif receipt_type == "restaurant":
        items = random.sample(RESTAURANT_ITEMS, min(random.randint(2, 5), len(RESTAURANT_ITEMS)))
    elif receipt_type == "transportation":
        items = random.sample(TRANSPORT_ITEMS, min(random.randint(1, 3), len(TRANSPORT_ITEMS)))
    elif receipt_type == "utilities":
        items = random.sample(UTILITY_ITEMS, min(random.randint(1, 3), len(UTILITY_ITEMS)))
    else:
        items = random.sample(RETAIL_ITEMS + RESTAURANT_ITEMS, min(random.randint(2, 4), 8))

    for item in items:
        item_price = round(random.uniform(5, 200), 2)
        lines.append(f"{item}  ${item_price:.2f}")

    formatted_amt = format_amount(amount)
    if amount_fmt == "dollar":
        lines.append(f"Total: ${formatted_amt}")
    elif amount_fmt == "hkd":
        lines.append(f"Total: HKD {formatted_amt}")
    elif amount_fmt == "hkdollar":
        lines.append(f"Total: HK${formatted_amt}")
    elif amount_fmt == "chinese_hkd":
        lines.append(f"總計: 港幣{formatted_amt}")
    elif amount_fmt == "total_dollar":
        lines.append(f"總計: ${formatted_amt}")
    elif amount_fmt == "total_eng":
        lines.append(f"Total HKD {formatted_amt}")
    elif amount_fmt == "grand_total":
        lines.append(f"Grand Total: ${formatted_amt}")
    elif amount_fmt == "amount_due":
        lines.append(f"Amount Due: HK${formatted_amt}")

    if include_tax and tax_amount > 0:
        tax_fmt = random.choice(TAX_TEMPLATES)
        formatted_tax = format_amount(tax_amount)
        if tax_fmt[0] == "tax_eng":
            lines.append(f"Tax: ${formatted_tax}")
        elif tax_fmt[0] == "tax_chi":
            lines.append(f"稅款: ${formatted_tax}")
        elif tax_fmt[0] == "gst":
            lines.append(f"GST: ${formatted_tax}")

    if receipt_type == "retail":
        lines.append("Thank you for shopping!")
    elif receipt_type == "restaurant":
        lines.append("Thank you for dining with us!")
    elif receipt_type == "transportation":
        lines.append("Thank you for riding with us!")
    elif receipt_type == "utilities":
        lines.append("Payment due by end of month")

    text = "\n".join(lines)
    expected = {
        "merchant": merchant,
        "date": f"{y}-{m:02d}-{d:02d}",
        "total": amount,
        "tax": tax_amount if include_tax else None,
        "receipt_type": receipt_type,
    }
    return text, lines, expected


def generate_edge_cases():
    cases = []
    for _ in range(200):
        edge_type = random.choice([
            "empty", "no_date", "no_amount", "large_amount",
            "tiny_amount", "comma_amount", "multiple_amounts",
            "malformed_date", "unknown_merchant", "long_merchant",
        ])
        if edge_type == "empty":
            text, lines = "", []
            expected = {"merchant": "", "date": None, "total": None, "tax": None, "receipt_type": "other"}
        elif edge_type == "no_date":
            text, lines, base = generate_receipt_text("ParknShop", "retail", "dd_mm_yyyy", "dollar", False, "en")
            text = text.split("\n")
            text = "\n".join([l for l in text if not l.startswith("Date:")])
            lines = text.split("\n")
            expected = {**base, "date": None}
        elif edge_type == "no_amount":
            text, lines, base = generate_receipt_text("McDonald's", "restaurant", "dd_mm_yyyy", "dollar", False, "en")
            text = text.split("\n")
            text = "\n".join([l for l in text if "Total" not in l and "$" not in l and "HKD" not in l and "總計" not in l])
            lines = text.split("\n")
            expected = {**base, "total": None}
        elif edge_type == "large_amount":
            text, lines, base = generate_receipt_text("CLP Power", "utilities", "yyyy_mm_dd", "hkd", False, "en")
            expected = {**base, "total": base["total"]}
        elif edge_type == "tiny_amount":
            text, lines, base = generate_receipt_text("7-Eleven", "retail", "dd_mm_yyyy", "dollar", False, "en")
            expected = {**base, "total": base["total"]}
        elif edge_type == "comma_amount":
            text = "Wellcome\nDate: 15/03/2024\nRice 5kg  $45.00\nTotal: $1,234.56"
            lines = text.split("\n")
            expected = {"merchant": "Wellcome", "date": "2024-03-15", "total": 1234.56, "tax": None, "receipt_type": "retail"}
        elif edge_type == "multiple_amounts":
            text = "ParknShop\nDate: 15/03/2024\nSubtotal: $100.00\nTax: $5.00\nTotal: $105.00"
            lines = text.split("\n")
            expected = {"merchant": "ParknShop", "date": "2024-03-15", "total": 105.00, "tax": 5.00, "receipt_type": "retail"}
        elif edge_type == "malformed_date":
            text = "Starbucks\nDate: 99/99/9999\nCoffee  $45.00\nTotal: $45.00"
            lines = text.split("\n")
            expected = {"merchant": "Starbucks", "date": None, "total": 45.00, "tax": None, "receipt_type": "restaurant"}
        elif edge_type == "unknown_merchant":
            text = "ABC Random Shop 123\nDate: 15/03/2024\nItem  $50.00\nTotal: $50.00"
            lines = text.split("\n")
            expected = {"merchant": "ABC Random Shop 123", "date": "2024-03-15", "total": 50.00, "tax": None, "receipt_type": "other"}
        elif edge_type == "long_merchant":
            text = "Hong Kong Super Department Store & Co. Ltd.\nDate: 15/03/2024\nItem  $88.00\nTotal: $88.00"
            lines = text.split("\n")
            expected = {"merchant": "Hong Kong Super Department Store & Co. Ltd.", "date": "2024-03-15", "total": 88.00, "tax": None, "receipt_type": "other"}
        else:
            continue
        cases.append(("edge_" + edge_type, text, lines, expected))
    return cases


def generate_test_cases(n=10000):
    cases = []
    type_weights = {"retail": 0.30, "restaurant": 0.30, "transportation": 0.15, "utilities": 0.10, "other": 0.15}

    for i in range(n - 200):
        r = random.random()
        cumulative = 0
        receipt_type = "other"
        for t, w in type_weights.items():
            cumulative += w
            if r < cumulative:
                receipt_type = t
                break

        if receipt_type == "retail":
            merchant, _ = random.choice(RETAIL_MERCHANTS)
        elif receipt_type == "restaurant":
            merchant, _ = random.choice(RESTAURANT_MERCHANTS)
        elif receipt_type == "transportation":
            merchant, _ = random.choice(TRANSPORT_MERCHANTS)
        elif receipt_type == "utilities":
            merchant, _ = random.choice(UTILITY_MERCHANTS)
        else:
            merchant, _ = random.choice(OTHER_MERCHANTS)

        date_fmt = random.choice(["chinese", "dd_mm_yyyy", "yyyy_mm_dd", "dd_mm_yyyy_dot", "dd_mm_yyyy_dash"])
        amount_fmt = random.choice(["dollar", "hkd", "hkdollar", "chinese_hkd", "total_dollar", "total_eng", "grand_total", "amount_due"])
        include_tax = random.random() < 0.3
        lang = random.choice(["en", "zh", "mixed"])

        text, lines, expected = generate_receipt_text(merchant, receipt_type, date_fmt, amount_fmt, include_tax, lang)
        cases.append((receipt_type, text, lines, expected))

    cases.extend(generate_edge_cases())
    return cases


def run_tests():
    print("=" * 70)
    print("HK Receipt Parser — 10,000 Receipt Stress Test")
    print("=" * 70)

    cases = generate_test_cases(10000)
    print(f"\nGenerated {len(cases)} test cases\n")

    results = {
        "total": 0,
        "passed": 0,
        "by_type": defaultdict(lambda: {"total": 0, "passed": 0}),
        "by_field": defaultdict(lambda: {"total": 0, "passed": 0}),
        "failures": defaultdict(int),
        "edge_results": defaultdict(lambda: {"total": 0, "passed": 0}),
    }

    start = time.time()

    for case_type, text, lines, expected in cases:
        results["total"] += 1
        results["by_type"][case_type]["total"] += 1

        ocr_result = {"text": text, "lines": lines, "engine": "pytesseract"}
        try:
            parsed = parse_receipt(ocr_result)
        except Exception as e:
            results["failures"][f"exception: {e}"] += 1
            continue

        case_passed = True

        for field in ["merchant", "date", "total", "tax", "receipt_type"]:
            results["by_field"][field]["total"] += 1
            expected_val = expected.get(field)
            parsed_val = parsed.get(field)

            field_passed = False
            if field == "merchant":
                if expected_val and parsed_val:
                    field_passed = expected_val.lower() in parsed_val.lower() or parsed_val.lower() in expected_val.lower()
                elif not expected_val and not parsed_val:
                    field_passed = True
            elif field == "date":
                if expected_val and parsed_val:
                    field_passed = expected_val == parsed_val
                elif not expected_val:
                    field_passed = True
            elif field == "total":
                if expected_val is not None and parsed_val is not None:
                    field_passed = abs(expected_val - parsed_val) < 0.01
                elif expected_val is None:
                    field_passed = True
            elif field == "tax":
                if expected_val is not None and parsed_val is not None:
                    field_passed = abs(expected_val - parsed_val) < 0.01
                else:
                    field_passed = True
            elif field == "receipt_type":
                field_passed = expected_val == parsed_val

            if field_passed:
                results["by_field"][field]["passed"] += 1
            else:
                case_passed = False
                results["failures"][f"{field}_mismatch({case_type})"] += 1

        if case_passed:
            results["passed"] += 1
            results["by_type"][case_type]["passed"] += 1

        if case_type.startswith("edge_"):
            results["edge_results"][case_type]["total"] += 1
            if case_passed:
                results["edge_results"][case_type]["passed"] += 1

    elapsed = time.time() - start

    print(f"\n{'=' * 70}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total test cases: {results['total']}")
    print(f"Overall pass rate: {results['passed']}/{results['total']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"Time elapsed: {elapsed:.2f}s")
    print(f"Throughput: {results['total']/elapsed:.0f} cases/sec")

    print(f"\n{'─' * 50}")
    print("PASS RATE BY RECEIPT TYPE:")
    print(f"{'─' * 50}")
    for rtype in ["retail", "restaurant", "transportation", "utilities", "other"]:
        d = results["by_type"].get(rtype, {"total": 0, "passed": 0})
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {rtype:20s}: {d['passed']:5d}/{d['total']:5d} ({rate:.1f}%)")

    print(f"\n{'─' * 50}")
    print("PASS RATE BY FIELD:")
    print(f"{'─' * 50}")
    for field in ["merchant", "date", "total", "tax", "receipt_type"]:
        d = results["by_field"][field]
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {field:20s}: {d['passed']:5d}/{d['total']:5d} ({rate:.1f}%)")

    print(f"\n{'─' * 50}")
    print("TOP 10 FAILURE PATTERNS:")
    print(f"{'─' * 50}")
    sorted_failures = sorted(results["failures"].items(), key=lambda x: -x[1])[:10]
    for pattern, count in sorted_failures:
        print(f"  {pattern:50s}: {count}")

    print(f"\n{'─' * 50}")
    print("EDGE CASE RESULTS:")
    print(f"{'─' * 50}")
    for etype, d in sorted(results["edge_results"].items()):
        rate = d["passed"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"  {etype:30s}: {d['passed']:3d}/{d['total']:3d} ({rate:.1f}%)")

    print(f"\n{'=' * 70}")
    overall_rate = results['passed'] / results['total'] * 100
    if overall_rate >= 90:
        print("VERDICT: EXCELLENT — Parser handles HK receipts well")
    elif overall_rate >= 75:
        print("VERDICT: GOOD — Parser handles most HK receipts correctly")
    elif overall_rate >= 60:
        print("VERDICT: FAIR — Parser needs improvement in some areas")
    else:
        print("VERDICT: POOR — Parser needs significant improvement")
    print(f"{'=' * 70}")

    return results


if __name__ == "__main__":
    run_tests()
