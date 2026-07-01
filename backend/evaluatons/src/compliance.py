# src/compliance.py
# Advanced MDONER / NEC-style Compliance Engine 
from typing import Dict, Any, List
from src.web_search import duckduckgo_search

class ComplianceChecker:
    """
    A realistic 20-point Ministry of DoNER / NEC-style compliance engine.

    This engine does **not** perform numeric scoring from DPR text.
    Instead, it:
      • Retrieves guideline snippets using controlled web search
      • Compares DPR text qualitatively to 20 compliance checkpoints
      • Classifies each checkpoint as: "Met", "Partially Met", or "Not Observed"
      • Generates a ministry-grade compliance summary block
      • Returns a compliance score (0–10) for the Policy module
    """
 
    # 20 MDONER-STYLE GUIDELINE CHECKPOINTS 
    GUIDELINES: List[str] = [
        # TECHNICAL
        "Clear statement of objectives aligned with regional development priorities",
        "Explicit identification of project location, beneficiaries, and coverage",
        "Engineering design consistent with terrain, hydrology, and soil conditions",
        "Adequacy of drawings, technical specifications, and design assumptions",
        "Demonstration of feasibility considering monsoon and working-season constraints",

        # COSTING / FINANCIAL
        "BoQ items presented with clear rate justification",
        "No abnormal concentration of cost in single items or components",
        "Rates benchmarked against standard scheduled rates or recent departmental works",
        "Inclusion of proper contingencies and administrative overhead norms",
        "Financial phasing aligned with implementation schedule",

        # IMPLEMENTATION & INSTITUTIONAL
        "Clear implementation mechanism with defined responsibilities",
        "Identification of executing agency with demonstrated capability",
        "O&M arrangements described with financial sustainability",
        "Risk management and mitigation strategy outlined",

        # SOCIAL & ENVIRONMENTAL
        "Assessment of environmental sensitivity and safeguards",
        "Adequacy of community participation measures",
        "Gender / vulnerable group inclusion considerations",

        # POLICY ALIGNMENT
        "Alignment with NEC / MDONER programme objectives",
        "Consistency with State Government development priorities",
        "Monitoring, reporting, and evaluation arrangements clearly identified",
    ]
 
    def _keyword_match(self, text: str, guideline: str) -> str:
        """
        Light-weight qualitative heuristic:
        - If many keywords present: Met
        - If some keywords present: Partially Met
        - If almost none: Not Observed
        """
        words = [w.lower() for w in guideline.split() if len(w) > 4]
        hits = sum(1 for w in words if w in text.lower())

        if hits >= 3:
            return "Met"
        elif hits == 1 or hits == 2:
            return "Partially Met"
        return "Not Observed"
 
    def _compute_score(self, results: Dict[str, str]) -> float:
        """
        Convert compliance observations to a 0–10 policy score.
        - Met → 1 point
        - Partially Met → 0.5 point
        - Not Observed → 0
        """
        score = 0.0
        for status in results.values():
            if status == "Met":
                score += 1.0
            elif status == "Partially Met":
                score += 0.5

        # scale: 20 points → convert to 10
        return round((score / 20) * 10, 2)
 
    def check(self, text: str) -> Dict[str, Any]:
        """
        Return structured compliance assessment:
            {
                "guidelines": {
                    guideline_text: "Met" / "Partially Met" / "Not Observed",
                    ...
                },
                "compliance_score_0_10": float,
                "web_support_context": [...]
            }
        """
        # 1. Evaluate each of the 20 guideline checkpoints
        guideline_map = {
            guideline: self._keyword_match(text, guideline)
            for guideline in self.GUIDELINES
        }

        # 2. Calculate score
        score = self._compute_score(guideline_map)

        # 3. Light web assistance for contextual language only (NO NUMBERS)
        queries = [
            "MDONER DPR appraisal format",
            "NEC project evaluation criteria",
            "Government project screening note structure",
        ]
        web_results = []
        for q in queries:
            web_results.extend(duckduckgo_search(q, max_results=2))

        return {
            "guidelines": guideline_map,
            "compliance_score_0_10": score,
            "web_support_context": web_results[:6],
        }
