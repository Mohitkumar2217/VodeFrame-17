import re
from typing import List, Dict, Any
import math
import numpy as np

BOQ_ITEM_PATTERNS = [
    re.compile(r'(?P<desc>[\w\W]+?)\s*-\s*(?P<qty>[\d,\.]+)\s*(?P<unit>[a-zA-Z/%]+)\s*@\s*(?P<rate>[\d,.,]+)\s*(?:=|₹)?\s*(?P<amount>[\d,.,]+)?'),
    re.compile(r'(?P<index>\d+)\.\s*(?P<desc>[\w\W]+?):\s*(?P<qty>[\d,\.]+)\s*(?P<unit>[a-zA-Z/%]+)\s*@\s*(?P<rate>[\d,.,]+)\s*(?:=|₹)?\s*(?P<amount>[\d,.,]+)?'),
    re.compile(r'(?P<desc>[A-Za-z][\w\W]+?)\s+(?P<qty>[\d,\.]+)\s+(?P<unit>[a-zA-Z/%]+)\s+(?P<rate>[\d,.,]+)\s+(?P<amount>[\d,.,]+)')
]

def _clean_num(s: str) -> float:
    if s is None:
        return math.nan
    s = s.replace(',', '').strip()
    try:
        return float(s)
    except:
        return math.nan


def parse_boq_from_text(text: str) -> List[Dict[str, Any]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items = []

    for ln in lines:
        matched = False
        for pat in BOQ_ITEM_PATTERNS:
            m = pat.search(ln)
            if m:
                gd = m.groupdict()
                item = {
                    "desc": (gd.get("desc") or "").strip(),
                    "qty": _clean_num(gd.get("qty")),
                    "unit": (gd.get("unit") or "").strip(),
                    "rate": _clean_num(gd.get("rate")),
                    "amount": _clean_num(gd.get("amount"))
                }
                if math.isnan(item["amount"]) and not math.isnan(item["qty"]) and not math.isnan(item["rate"]):
                    item["amount"] = round(item["qty"] * item["rate"], 2)

                items.append(item)
                matched = True
                break

        if not matched:
            m2 = re.match(r'(?P<desc>.+?)\s*[:\-]\s*₹?\s*(?P<amount>[\d,\.]+)', ln)
            if m2:
                gd = m2.groupdict()
                items.append({
                    "desc": gd.get("desc").strip(),
                    "qty": math.nan,
                    "unit": "",
                    "rate": math.nan,
                    "amount": _clean_num(gd.get("amount"))
                })

    return items


def boq_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    amounts = [it.get("amount") for it in items if not math.isnan(it.get("amount", math.nan))]
    rates = [it.get("rate") for it in items if not math.isnan(it.get("rate", math.nan))]

    total_cost = float(np.nansum(amounts))
    item_count = len(items)

    # Cost concentration index (HHI-like)
    if total_cost > 0:
        shares = [(amt / total_cost) ** 2 for amt in amounts]
        hhi = float(np.sum(shares))
    else:
        hhi = math.nan

    return {
        "items_count": item_count,
        "total_estimated_cost": round(total_cost, 2),

        # Missing data
        "missing_qty_count": sum(math.isnan(it["qty"]) for it in items),
        "missing_rate_count": sum(math.isnan(it["rate"]) for it in items),

        # Numeric KPIs
        "avg_rate": float(np.nanmean(rates)) if rates else math.nan,
        "median_rate": float(np.nanmedian(rates)) if rates else math.nan,
        "max_item_cost": max(amounts) if amounts else math.nan,
        "min_item_cost": min(amounts) if amounts else math.nan,
        "cost_concentration_index_hhi": hhi,

        # Percent metrics
        "pct_missing_rate": round(100 * sum(math.isnan(it["rate"]) for it in items) / item_count, 2) if item_count else 0,
        "pct_missing_qty": round(100 * sum(math.isnan(it["qty"]) for it in items) / item_count, 2) if item_count else 0,

        # Useful downstream values
        "numeric_items": items
    }


def extract_boq_sections(text: str, section_headers=None) -> str:
    if section_headers is None:
        section_headers = [
            "bill of quantities", "boq", "bill of items",
            "schedule of quantities", "bill of quantities (boq)"
        ]

    low = text.lower()
    for header in section_headers:
        idx = low.find(header)
        if idx != -1:
            return text[idx: idx + 20000]

    return text
