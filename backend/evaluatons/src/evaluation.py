import os
import json
import re

import fitz
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.web_search import duckduckgo_search
from src.agents import MultiAgentSystem
from src.compliance import ComplianceChecker
from src.benchmarks import CostBenchmarkEngine
from src.boq_parser import extract_boq_sections, parse_boq_from_text, boq_summary
from src.gis_engine import advanced_gis_analysis
from src.risk_simulator import run_monte_carlo
from src.pdf_annotator import annotate_pdf

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# GOVERNMENT-LIKE POLICY NORMS 
GOVERNMENT_NORMS = {
    "technical": [
        "As per standard practices referenced in Ministry-level screening frameworks for infrastructure and watershed projects.",
        "Slope stability considerations should align with broadly accepted terrain management principles in hilly and high-rainfall regions.",
        "Drainage and hydrological provisions are expected to follow common watershed planning norms to avoid erosion and waterlogging.",
        "Cut-and-fill operations should minimise ecological disturbance and long-term erosion risks."
    ],
    "financial": [
        "Cost reasonableness is examined with reference to general government scrutiny principles for centrally supported projects.",
        "Expenditure patterns are expected to reflect prudent budgeting and internal consistency across BoQ items.",
        "BoQ rates should not indicate abnormal overpricing or underestimation of major work components."
    ],
    "timeline": [
        "Project timelines should consider monsoon downtime, viable working seasons, and terrain-related productivity in hilly and semi-hilly areas.",
        "Duration needs to be realistic given local access, material logistics, and availability of labour."
    ],
    "policy": [
        "DPRs are expected to be in line with overarching objectives of sustainable regional development and inclusive growth.",
        "Administrative approvals usually require clarity in institutional arrangements, monitoring structure, and expected benefit coverage.",
        "Environmental safeguards and community participation are essential expectations for long-term sustainability of public investments."
    ],
    "risk": [
        "Risk buffers must realistically account for terrain unpredictability, weather disruptions, and material supply variations.",
        "Reasonableness of projected cost and time variability is critical for responsible utilisation of public funds."
    ]
}


def gov_norms_text() -> str:
    """Flatten pseudo-government norms for prompt injection."""
    lines = []
    for _, values in GOVERNMENT_NORMS.items():
        for item in values:
            lines.append(f"- {item}")
    return "\n".join(lines)

# TOKEN-SAFE TEXT CLEANING UTILITIES 
def compress_text(text: str, max_words: int = 250) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Za-z0-9.,:/%-]", " ", text)
    words = text.split()
    return " ".join(words[:max_words])


def extract_project_name_and_location(dpr_text: str):
    """
    Best-effort extraction of project name & location phrase
    to give the LLM more context for ministry-style writing.
    """
    project_name = None
    location_hint = None

    for line in dpr_text.splitlines():
        lower = line.lower()
        if not project_name and ("project" in lower or "scheme" in lower):
            project_name = line.strip()
        if not location_hint and (
            "village" in lower or "block" in lower or "district" in lower
        ):
            location_hint = line.strip()
        if project_name and location_hint:
            break

    return project_name, location_hint


class DPRAssistant:

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self.llm = ChatGroq(
            model=model,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=1400  
        )

        self.agents = MultiAgentSystem(strong_mode=True)
        self.compliance_checker = ComplianceChecker()
        self.benchmarks = CostBenchmarkEngine()
        # MUST be set by caller, e.g. app.py, before evaluate()
        self.input_pdf_path: str | None = None
 
    # TEXT CHUNKING 
    def _chunk(self, text: str, size: int = 1500):
        return [text[i:i + size] for i in range(0, len(text), size)]
 
    # ISSUE NORMALIZER (for annotator safety) 
    def _safe_issue(self, issue):
        """
        Ensure every issue dict has a proper `meta` dict with:
          - severity
          - issue
          - note
          - snippet
        This does NOT change core logic, only guards against
        malformed / partial issue objects so pdf_annotator never crashes.
        """
        # If it's not even a dict, coerce to a minimal structure
        if not isinstance(issue, dict):
            text = str(issue)
            return {
                "snippet": text,
                "issue_type": "general",
                "severity": "low",
                "note": text,
                "issue": text,
                "meta": {
                    "severity": "low",
                    "issue": text,
                    "note": text,
                },
            }

        # Ensure snippet exists
        if not issue.get("snippet"):
            issue["snippet"] = compress_text(
                json.dumps(issue, ensure_ascii=False),
                max_words=40,
            )

        # Ensure base fields
        issue.setdefault("issue_type", "general")
        issue.setdefault("severity", "medium")
        issue.setdefault("note", "")

        # Build combined human-readable issue text
        issue_type = issue.get("issue_type", "general")
        note = issue.get("note", "")
        if note:
            combined_issue = f"{issue_type.upper()}: {note}"
        else:
            combined_issue = issue_type.upper()
        issue["issue"] = issue.get("issue", combined_issue)

        # Build / normalize meta
        meta = issue.get("meta")
        if not isinstance(meta, dict):
            meta = {}

        meta.setdefault("severity", issue.get("severity", "medium"))
        meta.setdefault("issue", issue["issue"])
        meta.setdefault("note", issue.get("note", ""))

        issue["meta"] = meta
        return issue
 
    # PAGE ISSUE DETECTION  (NO GRAMMAR / LANGUAGE ISSUES) 
    def detect_page_issues(self, page_text: str, page_num: int):
        clean_text = compress_text(page_text, max_words=250)

        prompt = f"""
            You are an MDONER/DoR Senior Technical Auditor reviewing a Detailed Project Report (DPR).
            
            IMPORTANT – STRICTLY AVOID LANGUAGE / GRAMMAR ISSUES:
            ❌ DO NOT report grammar errors  
            ❌ DO NOT report vague writing  
            ❌ DO NOT report unclear English  
            ❌ DO NOT report formatting, typos, or sentence-structure issues  
            ❌ DO NOT generate any linguistic critique  
            
            ONLY identify issues related to:
            - Engineering feasibility
            - GIS relevance (terrain, slope, hydrology, connectivity, elevation)
            - BOQ & costing anomalies
            - Financial deviations vs generally applied norms in public works
            - Timeline realism (monsoon, terrain difficulty)
            - Construction risks (landslide, flood, steep slope)
            - Environmental sensitivity
            - Policy compliance gaps (DoR/MDONER-style rules)
            - O&M sustainability gaps
            
            STRICT RULES:
            - Return ONLY a valid JSON LIST.
            - Max 4 issues per page.
            - "snippet" must be 10–40 words, quoting exact risky content.
            - severity ∈ {{low, medium, high}}
            - If no DPR-relevant issues: return [].
            - NEVER output language/grammar-based issues.
            
            JSON object format:
            {{
              "snippet": "...",
              "issue_type": "GIS|Risk|BOQ|Technical|Financial|Policy|Timeline|Sustainability",
              "severity": "low|medium|high",
              "note": "Short technical explanation of the issue tied to norms or risks"
            }}
            
            PAGE NUMBER: {page_num}
            
            PAGE TEXT:
            \"\"\"{clean_text}\"\"\"
            
            Return JSON ONLY.
            """
            
        try:
            resp_msg = self.llm.invoke(prompt)
            resp = resp_msg.content.strip()
            data = json.loads(resp)
        except Exception:
            return []

        # Normalize output:
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return []

        normalized = []
        for item in data:
            if isinstance(item, dict):
                if not item.get("snippet"):
                    item["snippet"] = compress_text(
                        json.dumps(item, ensure_ascii=False),
                        max_words=40,
                    )
                item.setdefault("issue_type", "Technical")
                item.setdefault("severity", "medium")
                item.setdefault("note", "")
                normalized.append(item)
            elif isinstance(item, str):
                snippet = compress_text(item, max_words=40)
                normalized.append(
                    {
                        "snippet": snippet,
                        "issue_type": "Technical",
                        "severity": "medium",
                        "note": item,
                    }
                )
        return normalized
 
    # MAIN DPR EVALUATION PIPELINE 
    def evaluate(self, dpr_text: str):

        if not self.input_pdf_path:
            raise ValueError(
                "DPRAssistant.input_pdf_path is not set. "
                "Set it to the uploaded PDF path before calling evaluate()."
            )

        # Extract some basic context for nicer ministry wording
        project_name, location_hint = extract_project_name_and_location(dpr_text)
 
        # PAGE-LEVEL ISSUES + PDF TEXT 
        print("[INFO] Detecting page-level issues...")
        pdf = fitz.open(self.input_pdf_path)
        issues_for_pdf = []

        for p, page in enumerate(pdf):
            raw_text = page.get_text("text") or page.get_text()
            page_issues = self.detect_page_issues(raw_text, p)

            for issue in page_issues:
                safe_issue = self._safe_issue(issue)
                snippet = safe_issue.get("snippet", "")

                issues_for_pdf.append(
                    {
                        "page": p,
                        "snippet": snippet,
                        "meta": safe_issue.get("meta", {}),
                    }
                )

        pdf.close()
 
        # DPR CHUNKING 
        chunks = self._chunk(dpr_text)
        global_context = compress_text("\n".join(chunks[:3]), max_words=300)
 
        # BOQ / GIS / RISK  (NUMERIC FACT SOURCES FIRST) 
        print("[INFO] Running BOQ, GIS, and Risk models...")

        boq_text = extract_boq_sections(dpr_text)
        boq_items = parse_boq_from_text(boq_text)
        boq_stats = boq_summary(boq_items)

        # LOCATION DETECTION FOR GIS
        loc_line = next(
            (l for l in dpr_text.splitlines() if "location" in l.lower()), None
        )
        location = (
            loc_line.split(":", 1)[-1].strip()
            if loc_line and ":" in loc_line
            else (loc_line.strip() if loc_line else "North East India")
        )

        # ADVANCED GIS MODEL
        gis_data = advanced_gis_analysis(location, project_text=dpr_text)

        # Fallback if GIS failed
        if isinstance(gis_data, dict) and gis_data.get("error"):
            gis_data = {
                "location": location,
                "coordinates": {},
                "elevation_m": 0.0,
                "alignment_score_0_100": 50.0,
                "terrain_risk_classification": {
                    "terrain_risk_tier": "Unknown",
                    "terrain_risk_score_0_100": 50.0,
                    "terrain_risk_explanation": "GIS engine failed or location not found.",
                },
                "officer_summary": "GIS data unavailable; risk scores assumed neutral.",
                "connectivity_score_0_10": 5.0,
            }

        # Risk engine uses BOQ cost as input – explicit, deterministic model
        base_cost = boq_stats.get("total_estimated_cost", 0.0)
        risk_summary = run_monte_carlo(
            base_cost if base_cost else 1.0,  # avoid zero issues
            base_duration_days=365,
            n_sims=3000,
        )

        print("[INFO] Running multi-agent panel...")
        agent_panel = self.agents.run_full_evaluation(
            dpr_text,
            monte_carlo_summary=risk_summary,
        )
 
        # COMPLIANCE CHECK (20-POINT MDONER-STYLE) 
        print("[INFO] Running compliance checker...")
        compliance_result = self.compliance_checker.check(dpr_text)
        compliance_score = compliance_result.get("compliance_score_0_10", 0.0)

        # compress heavy JSON for prompt to avoid wasting tokens (but keep full numeric fidelity)
        boq_compact = json.dumps(boq_stats, ensure_ascii=False)
        risk_compact = json.dumps(risk_summary, ensure_ascii=False)
 
        # BUILD AUTHORITATIVE NUMERIC FACT REGISTRY 
        landslide = (gis_data.get("landslide_risk") or {}) if isinstance(gis_data, dict) else {}
        flood = (gis_data.get("flood_risk") or {}) if isinstance(gis_data, dict) else {}
        terrain_cls = (gis_data.get("terrain_risk_classification") or {}) if isinstance(gis_data, dict) else {}
        cutfill = (gis_data.get("cut_fill_estimation") or {}) if isinstance(gis_data, dict) else {}
        hydro = (gis_data.get("hydrology_analysis") or {}) if isinstance(gis_data, dict) else {}

        numeric_facts = {
            "boq": {
                "total_estimated_cost_inr": boq_stats.get("total_estimated_cost"),
                "total_items": boq_stats.get("total_items"),
                "average_item_rate": boq_stats.get("avg_item_rate"),
            },
            "gis": {
                "location": gis_data.get("location"),
                "coordinates": gis_data.get("coordinates"),
                "elevation_m": gis_data.get("elevation_m"),
                "alignment_score_0_100": gis_data.get("alignment_score_0_100"),
                "terrain_risk_tier": terrain_cls.get("terrain_risk_tier"),
                "terrain_risk_score_0_100": terrain_cls.get("terrain_risk_score_0_100"),
                "landslide_risk_percent": landslide.get("landslide_risk_percent"),
                "flood_risk_index_0_100": flood.get("flood_risk_index_0_100"),
                "drainage_density_index": hydro.get("drainage_density_index"),
                "mean_corridor_elevation_m": cutfill.get("mean_elevation_m"),
                "terrain_roughness_index": cutfill.get("roughness_index"),
                "estimated_cut_fill_volume_m3_per_km": cutfill.get("estimated_cut_fill_volume_m3_per_km"),
                "connectivity_score_0_10": gis_data.get("connectivity_score_0_10"),
                "road_count_within_2km": gis_data.get("road_count"),
            },
            "risk": risk_summary,
            "compliance": {
                "compliance_score_0_10": compliance_score
            },
        }

        numeric_facts_json = json.dumps(numeric_facts, ensure_ascii=False)
 
        # Extract a few explicit risk metrics for our own debug 
        cost_stats = risk_summary.get("cost", {})
        dur_stats = risk_summary.get("duration", {})
        cost_p90 = cost_stats.get("p90")
        cost_overrun_mean = cost_stats.get("overrun_pct_mean")
        dur_overrun_mean = dur_stats.get("overrun_pct_mean")

        risk_numbers_line = (
            f"p90 cost (INR): {cost_p90}, "
            f"mean cost overrun %: {cost_overrun_mean}, "
            f"mean duration overrun %: {dur_overrun_mean}"
            if cost_p90 is not None
            else "Not available from risk engine."
        )
 
        # MODULE ANALYSIS (QUALITATIVE + SCORED; INCLUDES COMPLIANCE) 
        print("[INFO] Running module-wise qualitative+scored assessment...")

        modules = {
            "Objectives": "Evaluate clarity, justification and NEED.",
            "Technical Quality": "Engineering feasibility, terrain suitability and design soundness.",
            "Financials": "Cost structure, BoQ realism and concentration.",
            "Timeline": "Duration realism vs terrain and working season.",
            "Risks": "Clarity of cost/time risks and mitigation.",
            "Policy Fit": "Fit with regional development, programme objectives and governance.",
            "Sustainability": "O&M arrangements, long-term viability and community aspects.",
        }

        # Map specific numeric slices to modules for more grounded scoring
        module_numeric_context = {
            "Objectives": {},
            "Technical Quality": {"gis": numeric_facts.get("gis", {})},
            "Financials": {
                "boq": numeric_facts.get("boq", {}),
                "risk_cost": numeric_facts.get("risk", {}).get("cost", {}),
            },
            "Timeline": {
                "risk_duration": numeric_facts.get("risk", {}).get("duration", {}),
            },
            "Risks": {
                "risk": numeric_facts.get("risk", {}),
            },
            "Policy Fit": {
                "compliance": numeric_facts.get("compliance", {}),
            },
            "Sustainability": {},
        }

        module_summaries: list[str] = []

        for title, question in modules.items():

            selected_chunk = global_context
            for ch in chunks:
                if any(w in ch.lower() for w in question.lower().split()):
                    selected_chunk = compress_text(ch, max_words=250)
                    break

            # Web search used ONLY for qualitative narrative cues
            web_results = duckduckgo_search(
                f"{title} appraisal DPR watershed public investment India",
                max_results=5,
            )
            web_ctx = compress_text("\n".join(web_results), max_words=80)

            module_numeric_json = json.dumps(
                module_numeric_context.get(title, {}),
                ensure_ascii=False
            )

            mod_prompt = f"""
                You are preparing an **internal module-level appraisal note** for a DPR
                being examined by the Ministry of DoNER / NEC-type body.

                MODULE: {title}

                TEXT INPUT:
                - DPR Extract (local text): {selected_chunk}

                NUMERIC CONTEXT FOR THIS MODULE (ONLY SOURCE OF NUMBERS FOR THIS ANSWER):
                {module_numeric_json}

                You also have generic web wording cues (NO NUMBERS TO BE USED FROM HERE):
                {web_ctx}

                SCORING RUBRIC (MANDATORY):
                - 9–10  : Very strong; DPR is clear, well-structured, and supported by relevant data.
                - 7–8   : Adequate to good; broadly acceptable with some gaps.
                - 5–6   : Average; important aspects present but require strengthening/clarification.
                - 3–4   : Weak; major gaps in clarity, data, or justification.
                - 0–2   : Very weak; not adequate for Ministry-level appraisal.

                TASK:
                1. Write a short, professional paragraph (3–6 lines) describing how this module
                   would be viewed during Ministry scrutiny (clarity, sufficiency, gaps).
                2. Where possible, refer to numeric cues ONLY from NUMERIC CONTEXT
                   (e.g. GIS scores, BoQ totals, risk parameters, or compliance score)
                   with simple labels like "(Source: GIS Engine)", "(Source: Risk Engine)",
                   "(Source: DPR-BOQ)", or "(Source: Compliance Engine)".
                3. Choose a **Module Score: X/10** consistent with the rubric above.

                RULES:
                - DO NOT invent any numbers; if NUMERIC CONTEXT has no numbers, give a purely qualitative view.
                - DO NOT refer to external benchmarks like "10% higher than norms" unless it is explicit in NUMERIC CONTEXT.
                - Tone must be formal, concise, and Ministry-style – no casual wording.

                Return markdown with:
                - One short paragraph.
                - A bullet list titled "Key Observations:" (2–4 bullets).
                - One line at the end: "Module Score: X/10".
                """

            resp_msg = self.llm.invoke(mod_prompt)
            resp = resp_msg.content.strip()
            module_summaries.append(f"## {title}\n{resp}\n")

        compressed_modules = [
            compress_text(m, max_words=220) for m in module_summaries
        ]
        module_text = "\n".join(compressed_modules)
 
        # OPTIONAL CONTEXTUAL WEB SEARCH FOR FINAL NARRATIVE (NO NUMBERS) 
        location_for_web = location_hint or location or "North East India watershed project"
        web_context_for_ministry = duckduckgo_search(
            f"language used in Government of India DPR appraisal notes for watershed or road projects {location_for_web}",
            max_results=5,
        )
        web_context_for_ministry = compress_text(
            "\n".join(web_context_for_ministry),
            max_words=120,
        )
 
        # FINAL SYNTHESIS — GOVT-GRADE, EXECUTIVE + TECHNICAL HYBRID 
        gov_norm_block = gov_norms_text()

        final_prompt = f"""
            You are drafting a **MINISTRY-LEVEL DPR APPRAISAL NOTE** for senior officers
            of a central Ministry / NEC-type body (e.g. Secretary, Additional Secretary, Joint Secretary).

            PROJECT CONTEXT:
            - Project (best-effort text from DPR): {project_name or "Name not clearly specified in DPR extract"}
            - Location hint (from DPR, if any): {location_hint or "Not clearly specified; GIS-based location used."}

            Your tone must reflect:
            - Formal ministry scrutiny style (note-writing for file circulation).
            - Realistic engineering, financial and policy reasoning.
            - Clear sanction recommendation language.
            - Executive-summary clarity plus technical depth where needed.
            - NO invented numbers — use ONLY numbers from NUMERIC_FACTS_JSON.

            ====================================================================
            ### 1. AUTHORITATIVE NUMERIC FACTS (ONLY SOURCE FOR NUMBERS)

            NUMERIC_FACTS_JSON:
            {numeric_facts_json}

            RULES FOR NUMBERS:
            1. You are FORBIDDEN to invent or guess any numeric values
               (costs, %, scores, km, population, days, etc.) that are not in NUMERIC_FACTS_JSON.
            2. You may perform simple arithmetic on these numbers (e.g. rounding) but you MUST NOT
               bring in numbers from outside this JSON.
            3. If a quantity is not present, write clearly: "Not specified in DPR/analysis."
            4. For numeric statements, use simple source hints like:
               (Source: DPR-BOQ), (Source: GIS Engine), (Source: Risk Engine), (Source: Compliance Engine).

            ====================================================================
            ### 2. QUALITATIVE NORMS FOR REALISTIC GOVERNMENT TONE

            These are purely qualitative references (NO numbers to be taken from here):

            {gov_norm_block}

            Additional contextual wording cues from web search
            (ONLY for language style, NOT for numbers):
            {web_context_for_ministry}

            ====================================================================
            ### 3. ADDITIONAL QUALITATIVE INPUTS (NO NUMBERS TO BE TRUSTED)

            Module-wise assessments (compressed; each contains "Module Score: X/10"):
            {module_text}

            Multi-agent technical panel (compressed):
            {compress_text(agent_panel, max_words=250)}

            BOQ summary (for context; numeric truth is from NUMERIC_FACTS_JSON only):
            {boq_compact}

            GIS summary (for context):
            Location (GIS): {gis_data.get('location')}
            Coordinates: {gis_data.get('coordinates')}
            Officer GIS Summary: {gis_data.get('officer_summary','')}

            Risk simulation summary (for context; numeric truth is from NUMERIC_FACTS_JSON only):
            {risk_compact}

            Additional risk metrics (debug text; numbers already included in NUMERIC_FACTS_JSON):
            {risk_numbers_line}

            ====================================================================
            ### 4. TASK — PRODUCE A MINISTRY-FRIENDLY DPR APPRAISAL NOTE

            VERY IMPORTANT – USE MODULE SCORES CONSISTENTLY:
            - For **Technical Score**, use the "Module Score" from module "Technical Quality" as the primary anchor.
            - For **Financial Score**, use the "Module Score" from module "Financials".
            - For **Risk Score**, use the "Module Score" from module "Risks".
            - For **Compliance Score**, use the "Module Score" from module "Policy Fit".
            You may adjust by at most ±1 point in each case if you explicitly justify in the text.

            STYLE GUIDELINES:
            - Write as if this note will be placed on a Ministry file for approval.
            - Keep paragraphs short and clear; avoid generic filler text.
            - Do NOT repeat the same numeric fact in multiple sections unless needed.
            - Always tag numbers with their source in brackets.
            - Avoid dramatic language; stay neutral, administrative and precise.

            STRUCTURE (FOLLOW EXACTLY):

            ## 1. Executive Summary

            - 10–15 lines in simple, clear Ministry language.
            - Explain project purpose, location, terrain context, and overall feasibility.
            - Include 4–8 key numeric indicators ONLY from NUMERIC_FACTS_JSON with simple source tags.
            - Mention BOQ, GIS, risk, and compliance insights in a balanced way.
            - Do not over-explain methodology; focus on what matters for sanction.

            ## 2. Project Need & Strategic Importance (Score X/10)

            - Explain how the project aligns with regional development / connectivity / livelihood needs.
            - Draw on DPR narrative and module assessments.
            - Do NOT invent numeric benchmarks or population figures.
            - X/10 should be consistent with the "Objectives" module score (±1 allowed).

            ## 3. Technical & Terrain Assessment (Score X/10)

            - Describe terrain behaviour, elevation and susceptibility to flood/landslide using GIS numbers ONLY from NUMERIC_FACTS_JSON.
            - Convert technical ideas to simple language (e.g. “moderate terrain with some slope-related constraints”).
            - X/10 should be consistent with the "Technical Quality" module score (±1 allowed).

            ## 4. Financial Assessment (Score X/10)

            - Discuss cost realism using BoQ-derived numbers and risk-cost metrics only.
            - DO NOT use statements like "10% higher than typical norms" unless such % explicitly exists in NUMERIC_FACTS_JSON.
            - Comment on total cost, item spread, and risk of overrun, using Risk Engine fields only.
            - X/10 should be consistent with the "Financials" module score (±1 allowed).

            ## 5. Implementation Timeline & Practicality (Score X/10)

            - Use duration-related fields from the risk summary when present (e.g. p50 and p90 duration).
            - Discuss in plain terms whether the indicated time appears adequate, considering generic monsoon and terrain realities (qualitative only).
            - X/10 should align with the "Timeline" module score (±1 allowed).

            ## 6. Risk & Uncertainty (Score X/10)

            - Use cost and duration risk metrics ONLY from NUMERIC_FACTS_JSON (Risk Engine).
            - Explain p50/p90/overrun % in simple administrative language.
            - Clarify whether overall risk is low / moderate / high based on these values.
            - X/10 should be consistent with the "Risks" module score (±1 allowed).

            ## 7. Policy Compliance & Governance Fit (Score X/10)

            - Comment on alignment with general government priorities (sustainability, inclusion, monitoring, community participation).
            - Use the compliance score from the Compliance Engine as a numeric anchor where needed.
            - DO NOT invent any "% compliance" figures.
            - Identify specific areas where institutional or documentation clarity is required.
            - X/10 should be consistent with the "Policy Fit" module score (±1 allowed).

            ## 8. Final Recommendation for Ministry

            - Clearly state recommendation:
              - "The proposal may be approved",
              - "The proposal may be approved with conditions", or
              - "The proposal may be returned for revision."
            - Conditions (if any) should be practical and directly linked to gaps identified above.
            - Use clear, file-ready language (e.g. “Subject to the following conditions, the project may be considered for sanction.”).

            ## 9. Final Composite Score

            - Using your final section scores (Technical, Financial, Risk, Compliance), compute:
              - Technical weight: 30%
              - Financial weight: 25%
              - Risk weight: 25%
              - Compliance weight: 20%
            - Derive a 0–100 composite score using this formula.
            - This composite score is allowed because it is derived from your own section scores.
            - Mark it clearly as "(Derived from section scores)".
            - Present the final composite score and a one-line interpretation (e.g. "Overall composite score: 68/100 – suitable for consideration with safeguards.").

            ====================================================================
            REMINDERS:
            - DO NOT invent any new numeric values.
            - Use only NUMERIC_FACTS_JSON for numbers.
            - Keep the language professional, concise and relevant to decision-making.
            """

        final_msg = self.llm.invoke(final_prompt)
        final_report = final_msg.content.strip()
 
        # PDF ANNOTATION (with project title in header) 
        project_title = None
        for line in dpr_text.splitlines():
            if "project" in line.lower():
                project_title = line.strip()
                break

        highlighted_pdf = None
        try:
            highlighted_pdf = annotate_pdf(
                input_path=self.input_pdf_path,
                issues=issues_for_pdf,
                project_title=project_title or "DPR AUTOMATED REVIEW",
            )
        except Exception as e:
            # Don't kill the whole pipeline if annotation fails
            print("[WARN] PDF annotation failed:", e)
            highlighted_pdf = None

        return {
            "report": final_report,
            "highlighted_pdf": highlighted_pdf,
            "issues": issues_for_pdf,
            "modules": module_summaries,
            "boq_stats": boq_stats,
            "gis_data": gis_data,
            "risk_summary": risk_summary,
            "compliance": compliance_result,
            "agent_panel": agent_panel,
        }
