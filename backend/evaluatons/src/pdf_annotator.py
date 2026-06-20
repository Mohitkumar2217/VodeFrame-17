import fitz
import os
import uuid
from collections import defaultdict, Counter

 
# SAFE PAGE PARSER 
def safe_page_index(page_raw):
    """Convert any page value to a valid integer index or return None."""
    try:
        p = int(str(page_raw).strip())
        if p >= 0:
            return p
    except Exception:
        return None
    return None

# Compute stats + proper grouping 
def compute_issue_stats(issues):
    """
    Returns:
        total_issues: int
        per_severity: dict
        per_page_counts: {page -> count}
        issues_by_page: {page -> list of issue dicts}
    """

    per_page_counts = defaultdict(int)
    per_severity = Counter()
    issues_by_page = defaultdict(list)
    total = 0

    for issue in issues or []:

        # --- robust page extraction ---
        page_index = safe_page_index(issue.get("page"))
        if page_index is None:
            continue

        # Group per page
        per_page_counts[page_index] += 1
        issues_by_page[page_index].append(issue)

        # Severity
        meta = issue.get("meta") or {}
        severity = str(meta.get("severity", "low")).lower()
        per_severity[severity] += 1
        total += 1

    # Normalize severity counts
    normalized = {
        "high": per_severity.get("high", 0),
        "medium": per_severity.get("medium", 0),
        "low": per_severity.get("low", 0),
        "other": total
        - (
            per_severity.get("high", 0)
            + per_severity.get("medium", 0)
            + per_severity.get("low", 0)
        ),
    }

    return total, normalized, per_page_counts, issues_by_page
 
# Highlight text on PDF page 
def highlight_issue_on_page(page, snippet, severity, comment_text):

    if not snippet or not isinstance(snippet, str):
        return

    color_map = {
        "high": (0.90, 0.10, 0.10),
        "medium": (0.98, 0.58, 0.08),
        "low": (0.10, 0.45, 0.85)
    }

    sev = str(severity).lower()
    color = color_map.get(sev, color_map["low"])

    safe_comment = comment_text or "AI Detected Issue"
    safe_comment = f"[{sev.upper()}] {safe_comment}"

    try:
        rects = page.search_for(snippet)
        if not rects:
            rects = page.search_for(snippet.strip())
    except Exception:
        return

    for rect in rects:
        try:
            annot = page.add_highlight_annot(rect)
            annot.set_colors({"stroke": color})
            annot.set_opacity(0.35)
            annot.set_info({"content": safe_comment, "title": "AI Review"})
            annot.update()
        except Exception:
            continue

 
# Header Banner (works on all PyMuPDF builds) 
def add_header_banner(page, project_title):

    FONT = "helv"   # built-in Helvetica (safe on all builds)

    TITLE = "DIGITAL DPR REVIEW – AI ANNOTATED REPORT"

    rect = page.rect
    banner_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + 55)

    # Banner
    page.draw_rect(banner_rect, fill=(0.05, 0.18, 0.40))

    # Title text
    page.insert_text(
        fitz.Point(30, 18),
        TITLE,
        fontname=FONT,
        fontsize=14,
        color=(1, 1, 1),
    )

    # Subtitle
    subtitle = (
        "Internal Technical Review • Automatically Detected Issues\n"
        f"PROJECT: {project_title[:90] if project_title else 'N/A'}"
    )

    page.insert_text(
        fitz.Point(30, 38),
        subtitle,
        fontname=FONT,
        fontsize=9,
        color=(0.90, 0.95, 1),
    )

 
# Legend + Summary Block 
def add_legend_and_summary(page, total_issues, per_severity):

    FONT = "helv"

    legend_rect = fitz.Rect(page.rect.width - 260, 65, page.rect.width - 28, 200)
    summary_rect = fitz.Rect(30, 65, 260, 200)

    # --- Legend box ---
    page.draw_rect(legend_rect, fill=(0, 0, 0, 0.80))

    page.insert_textbox(
        legend_rect,
        "AI ISSUE SEVERITY LEGEND",
        fontname=FONT,
        fontsize=10,
        color=(1, 1, 1),
        align=0
    )

    entries = [
        ("HIGH", "Critical non-compliance or major risk", (0.90, 0.10, 0.10)),
        ("MEDIUM", "Important revision required", (0.98, 0.58, 0.08)),
        ("LOW", "Advisory improvement", (0.10, 0.45, 0.85))
    ]

    y = legend_rect.y0 + 28
    for label, desc, color in entries:
        box = fitz.Rect(legend_rect.x0 + 10, y, legend_rect.x0 + 24, y + 13)
        page.draw_rect(box, fill=color)

        page.insert_text(
            fitz.Point(box.x1 + 8, y + 2),
            f"{label} – {desc}",
            fontname=FONT,
            fontsize=8.5,
            color=(1, 1, 1),
        )
        y += 18

    # --- Summary box ---
    page.draw_rect(summary_rect, fill=(1, 1, 1, 0.96))

    page.insert_text(
        fitz.Point(summary_rect.x0 + 10, summary_rect.y0 + 10),
        "SUMMARY OF FINDINGS",
        fontname=FONT,
        fontsize=10,
        color=(0, 0, 0),
    )

    lines = [
        f"Total Issues: {total_issues}",
        f"High Severity: {per_severity['high']}",
        f"Medium Severity: {per_severity['medium']}",
        f"Low Severity: {per_severity['low']}",
    ]

    y = summary_rect.y0 + 30
    for line in lines:
        page.insert_text(
            fitz.Point(summary_rect.x0 + 10, y),
            line,
            fontname=FONT,
            fontsize=9,
            color=(0, 0, 0),
        )
        y += 14

 
# Sidebar Severity Bar (per page) 
def add_page_severity_sidebar(page, page_issues):

    if not isinstance(page_issues, list) or not page_issues:
        return

    severities = {
        str((i.get("meta") or {}).get("severity", "low")).lower()
        for i in page_issues
    }

    if "high" in severities:
        color = (0.90, 0.10, 0.10)
    elif "medium" in severities:
        color = (0.98, 0.58, 0.08)
    else:
        color = (0.10, 0.45, 0.85)

    bar = fitz.Rect(
        page.rect.width - 12,
        55,
        page.rect.width - 6,
        page.rect.height - 40
    )

    page.draw_rect(bar, fill=color)

 
# Footer 
def add_page_footer(page, p, total_pages, issue_count):
    FONT = "helv"

    text = (
        f"AI Review • Issues on this page: {issue_count} "
        f"• Page {p+1}/{total_pages}"
    )

    page.insert_text(
        fitz.Point(30, page.rect.height - 20),
        text,
        fontname=FONT,
        fontsize=8,
        color=(0.25, 0.25, 0.25)
    )

 
# MASTER FUNCTION 
def annotate_pdf(input_path, issues, project_title=None):

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"PDF not found: {input_path}")

    doc = fitz.open(input_path)

    (
        total_issues,
        per_severity,
        per_page_counts,
        issues_by_page
    ) = compute_issue_stats(issues)

    total_pages = len(doc)

    # --- Page 1 Banner + Summary ---
    page0 = doc[0]
    add_header_banner(page0, project_title)
    add_legend_and_summary(page0, total_issues, per_severity)

    # --- Iterate all pages ---
    for p in range(total_pages):
        page = doc[p]
        page_issues = issues_by_page.get(p, [])
        count = per_page_counts.get(p, 0)

        add_page_severity_sidebar(page, page_issues)

        for issue in page_issues:
            meta = issue.get("meta") or {}
            highlight_issue_on_page(
                page,
                issue.get("snippet", ""),
                meta.get("severity", "low"),
                meta.get("issue") or meta.get("note")
            )

        add_page_footer(page, p, total_pages, count)

    # --- SAVE OUTPUT FILE ---
    os.makedirs("annotated", exist_ok=True)
    out_path = f"annotated/DPR_Reviewed_{uuid.uuid4().hex}.pdf"
    doc.save(out_path, deflate=True, clean=True)
    doc.close()

    return out_path
