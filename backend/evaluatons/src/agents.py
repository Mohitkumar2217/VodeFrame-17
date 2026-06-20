import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.web_search import duckduckgo_search

load_dotenv()

DEFAULT_AGENT_MODEL = os.getenv("AGENT_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("Groq_API_KEY")

def _trim(text:str, chars: int = 1400) -> str:
    """Trim text safely for token limits (preserve start & end if large)."""
    if not text:
        return ""
    if len(text) <= chars:
        return text
    # keep first 1000 and last 400 chars for context continuity
    return text[:1000] + "\n\n...[TRIMMED]...\n\n" + text[-400:]

class MultiAgentSystem:
    """
    Multi-agent DPR evaluation system with optionalstrong_mode.

    - strong_mode=true -> each agent performs web-validated reasoning,
      deeper prompts, and returns more structured, numeric output.
    - strong_mode=False -> lighter, faster outputs (still LLM-based).
    """

    def __init__(self, strong_mode: bool = False, model: str= DEFAULT_AGENT_MODEL, max_tokens: int = 900):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment.")
        self.strong_mode = strong_mode
        self.model = model
        self.llm = ChatGroq(
            model=self.model,
            groq_api_key = GROQ_API_KEY,
            max_tokens=max_tokens
        )

    # Engineer Agent
    def engineer_agent(self, dpr_context: str) -> str:
        ctx = _trim(dpr_context)
        if self.strong_mode:
            # fetch web evidence for engineering standards ()
            web = duckduckgo_search(
                "MDONER DoR DPR engineering design guidelines North Eastern Region NEC rural infrastructure standards",
                max_results=4
            )
            web_ctx = "\n".join(web)[:900]
            pompt = f"""
            You are a Senior Civil/Structural Engineer evaluating a DPR for a project
            in the India.
            DPR excerpt (trimmed):
            {ctx}
            Web evidence (authoritative sources, trimmed):
            {web_ctx}
            Tasks (STRONG MODE — NUMERIC OUTPUT REQUIRED):
            1. Identify major engineering issues and quantify them wherever possible, e.g.:
               - slopes in %
               - rainfall / runoff values
               - soil loss (t/ha/year)
               - percentage shortfall/excess in design parameters
            2. For each concern, give:
               - what the DPR implies (numeric)
               - what a typical MDONER/DoR/NEC norm would be (range/number)
               - deviation in percentage terms (e.g. +40%, -25%).
            3. Count missing or weak elements:
               - number of missing drawings / sections / design details
               - number of unclear or unreferenced specifications.
            4. Provide top 5 technical concerns (each with at least one numeric detail).
            5. Provide 3 practical mitigation suggestions with ESTIMATED IMPACT in % terms
               (e.g. “expected to reduce soil loss by ~30%”, “improves stability margin by ~15%”).
            6. Give:
               - Technical Score (1–10, numeric)
               - Confidence: low / medium / high
               - A short numeric summary: at least 5 key numeric bullets.
            STRICT OUTPUT FORMAT (no JSON):
            Engineer Agent Analysis:
            Technical Concerns:
            - Concern 1: <text with numbers and %>
            - Concern 2: ...
            - Concern 3: ...
            - Concern 4: ...
            - Concern 5: ...
            Mitigations:
            - Mitigation 1: <text, includes estimated % impact>
            - Mitigation 2: ...
            - Mitigation 3: ...
            Scores:
            - Technical Score: X/10
            - Confidence: <low|medium|high>
            Numeric Summary:
            - metric_1: <value or %>
            - metric_2: <value or %>
            - metric_3: <value or %>
            - metric_4: <value or %>
            - metric_5: <value or %>
            """
        else:
            prompt = f"""
            You are a Civil/Structural Engineer evaluating a DPR section.
            DPR excerpt:
            {ctx}
            Tasks:
            - List up to 5 technical concerns (bullets).
            - Provide 1–2 numeric or percentage details if visible (e.g. slopes, areas, lengths).
            - Give 1–2 mitigation suggestions.
            - Provide a Technical Score (1–10) in one line at the end.
            Output format:
            Technical Concerns:
            - ...
            Mitigations:
            - ...
            Technical Score: X/10
            """
        resp = self.llm.invoke([prompt]).content.strip()
        return f"Finance Agent Output:\n{resp}"
    
    # Risk Agent
    def risk_agent(self, dpr_context:str, monte_carlo_summary:Dict[str, Any] | None = None) -> str:
        ctx = _trim(dpr_context)
        mc_snip = ""
        if monte_carlo_summary:
            # present a short human-readable summary of risk sim
            mc_snip = (
                f"Monte Carlo summary (median cost {monte_carlo_summary.get('cost', {}).get('p50', 'N/A')}, "
                f"p90 cost overrun % {monte_carlo_summary.get('cost_overrun_distribution_pct', {}).get('p90', 'N/A')}, "
                f"p90 schedule overrun % {monte_carlo_summary.get('schedule_overrun_distribution_pct', {}).get('p90', 'N/A')})"
            )
        if self.strong_mode:
            web = duckduckgo_search(
                "Mera Sathi Infrastructure DPR common risks cost overrun delays",
                max_results=3
            )
            web_ctx = '\n'.join(web)[:700]
            prompt = f"""
                You are a DPR Risk Analyst for MDONER/DoR projects.
                DPR excerpt:
                {ctx}
                Monte Carlo summary:
                {mc_snip}
                Relevant web insights (trimmed):
                {web_ctx}
                Tasks (STRONG MODE — MUST BE NUMERIC):
                1. Identify TOP 6 RISKS of any type (technical, financial, environmental, social, institutional).
                2. For each risk, give:
                   - likelihood on a 0–1 scale (e.g. 0.7)
                   - impact on a 0–1 scale (e.g. 0.6)
                   - risk_value = likelihood × impact (0–1).
                3. Rank risks by risk_value (descending).
                4. Provide mitigation measures with estimated % reduction in risk_value.
                5. Provide overall:
                   - Risk Score (1–10)
                   - Risk Index = mean risk_value × 10 (0–10 scale)
                   - Overall Risk Level: Low / Medium / High.
                STRICT OUTPUT FORMAT (no JSON):
                Risk Agent Analysis:
                Risks Table:
                - Risk 1: <name> | Likelihood: L1 | Impact: I1 | Risk Value: R1
                - Risk 2: ...
                - Risk 3: ...
                - Risk 4: ...
                - Risk 5: ...
                - Risk 6: ...
                Mitigations:
                - Mitigation 1: <text, reduces risk by ~X%>
                - Mitigation 2: ...
                - Mitigation 3: ...
                Scores:
                - Risk Score: X/10
                - Risk Index: Y.YY/10
                - Overall Risk Level: <Low|Medium|High>
                Numeric Summary:
                - avg_likelihood: <value>
                - avg_impact: <value>
                - max_risk_value: <value>
                - min_risk_value: <value>
                - mitigated_risk_reduction_estimate: <value %>
                """
        else:
            prompt = f"""
                You are a Risk Analyst reviewing a DPR.
                DPR excerpt:
                {ctx}
                Tasks:
                - List top 4 risks briefly.
                - Optionally assign each risk a qualitative likelihood (low/medium/high)
                  and impact (low/medium/high).
                - Provide an overall Risk Score (1–10).
                Output format:
                Risks:
                - Risk 1: ...
                - Risk 2: ...
                - Risk 3: ...
                - Risk 4: ...
                Risk Score: X/10
                """
        resp = self.llm.invoke([prompt]).content.strip()
        return f"Risk Agent Output:\n{resp}"

    # Policy Agent 
    def policy_agent(self, dpr_context: str) -> str:
        ctx = _trim(dpr_context)
        if self.strong_mode:
            # probe scheme-specific checks (MDONER / DoR + related central schemes)
            web = duckduckgo_search(
                "MDONER DPR guidelines DoR NEC checklist tourism infrastructure IWMP PMKSY North Eastern Region",
                max_results=5
            )
            web_ctx = "\n".join(web)[:900]
            prompt = f"""
                You are a Government Policy & Compliance Specialist for MDONER/DoR/NEC projects.
                DPR excerpt:
                {ctx}
                Scheme references and guidelines (trimmed):
                {web_ctx}
                Tasks (STRONG MODE — NUMERIC COMPLIANCE ANALYSIS):
                1. Evaluate DPR compliance against at least 4 relevant frameworks, for example:
                   - MDONER DPR format / guidelines
                   - DoR (roads/infra) norms
                   - NEC/State-specific DPR guidelines
                   - Relevant central schemes (e.g., IWMP, PMKSY, NHM, tourism-specific norms)
                   Adjust based on the content actually present.
                2. For each relevant scheme/framework, estimate:
                   - total_clauses_considered (approximate, e.g. 10–15 key points)
                   - clauses_matched
                   - clauses_missing/weak
                   - compliance_percentage = clauses_matched / total_clauses_considered × 100.
                3. Highlight 3–5 critical missing approvals/documents (if any).
                4. Provide:
                   - Compliance Score (1–10)
                   - Numeric summary of compliance percentages.
                STRICT OUTPUT FORMAT (no JSON):
                Policy Agent Analysis:
                Compliance Table:
                - Scheme 1: <name> | Matched: a | Missing/Weak: b | Compliance: c%
                - Scheme 2: ...
                - Scheme 3: ...
                - Scheme 4: ...
                Critical Gaps:
                - Gap 1: <text, preferably with some numeric reference>
                - Gap 2: ...
                - Gap 3: ...
                Recommendations:
                - Recommendation 1: <text, possible impact in %>
                - Recommendation 2: ...
                - Recommendation 3: ...
                Scores:
                - Compliance Score: X/10
                Numeric Summary:
                - scheme_1_compliance_pct: <value %>
                - scheme_2_compliance_pct: <value %>
                - scheme_3_compliance_pct: <value %>
                - scheme_4_compliance_pct: <value %>
                - avg_compliance_pct: <value %>
                """
        else:
            prompt = f"""
                You are a Policy Analyst.
                DPR excerpt:
                {ctx}
                Tasks:
                - Identify any obvious policy/compliance gaps.
                - Mention any important approvals or documents that seem missing.
                - Give a Compliance Score (1–10) in one line at the end.
                Output format:
                Compliance Observations:
                - ...
                Compliance Score: X/10
                """
        resp = self.llm.invoke([prompt]).content.strip()
        return f"Policy Agent Output:\n{resp}"

    # Reviewer / Aggregator Agent 
    def reviewer_agent(self, engineer_out: str, finance_out: str, risk_out: str, policy_out: str) -> str:
        """
        Combine agent outputs into a short consolidated evaluation.
        """
        # Trim inputs to stay token-safe
        e = _trim(engineer_out, chars=1200)
        f = _trim(finance_out, chars=1200)
        r = _trim(risk_out, chars=1200)
        p = _trim(policy_out, chars=1200)

        prompt = f"""
            You are the Final DPR Reviewer for an MDONER/DoR-style evaluation.
            Below are the specialist agent outputs (already structured):
            Engineer:
            {e}
            Finance:
            {f}
            Risk:
            {r}
            Policy:
            {p}
            Tasks (MUST BE NUMERIC + SYNTHESIZED):
            1. Infer or approximate the following from the text:
               - technical_score (0–10)
               - finance_score (0–10)
               - risk_score (0–10)
               - compliance_score (0–10)
            2. Derive at least 6 quantitative insights, such as:
               - estimated cost overrun/underrun %
               - typical risk index or average risk value
               - overall compliance percentage
               - count of major/critical issues vs minor issues.
            3. Provide:
               - 3 numeric strengths (each with some number or %)
               - 3 numeric weaknesses (each with some number or %).
            4. Build a combined scorecard:
               - Technical / Finance / Risk / Compliance (each 0–10).
            5. Give a final Recommendation: Go / Revise / No-Go,
               backed by 2–3 numeric reasons.
            STRICT OUTPUT FORMAT (no JSON):
            Reviewer Agent Analysis:
            Executive Summary (numeric):
            - Point 1: <text with numbers/%>
            - Point 2: <text with numbers/%>
            - Point 3: <text with numbers/%>
            - Point 4: <text with numbers/%>
            - Point 5: <text with numbers/%>
            Strengths:
            - Strength 1: <text with numeric element>
            - Strength 2: ...
            - Strength 3: ...
            Weaknesses:
            - Weakness 1: <text with numeric element>
            - Weakness 2: ...
            - Weakness 3: ...
            Scorecard:
            - Technical: X/10
            - Finance: Y/10
            - Risk: Z/10
            - Compliance: W/10
            Overall Indices (approximate):
            - Avg Score: S.S/10
            - Estimated Cost Deviation: C% (over/under)
            - Approximate Compliance: P%
            Recommendation:
            - <Go|Revise|No-Go> with brief numeric justification
            """ 
    # High-level helper: run all agents and return consolidated result 
    def run_full_evaluation(self, dpr_text: str, monte_carlo_summary: Dict[str, Any] | None = None) -> str:
        """
        Runs all agents sequentially (engineer, finance, risk, policy) and then the reviewer.
        Returns a combined textual summary.
        """
        # Use trimmed full context for speed
        context = _trim(dpr_text, chars=3000)

        # Run agents
        eng = self.engineer_agent(context)
        fin = self.finance_agent(context)
        risk = self.risk_agent(context, monte_carlo_summary=monte_carlo_summary)
        pol = self.policy_agent(context)

        # Final aggregate
        review = self.reviewer_agent(eng, fin, risk, pol)

        # Return a composite structure (still as text for the final LLM synthesiser)
        out = {
            "engineer": eng,
            "finance": fin,
            "risk": risk,
            "policy": pol,
            "reviewer": review
        }

        # Format compactly for insertion into final prompt
        formatted = "\n\n--- AGENT PANEL ---\n"
        formatted += f"Engineer:\n{eng}\n\n"
        formatted += f"Finance:\n{fin}\n\n"
        formatted += f"Risk:\n{risk}\n\n"
        formatted += f"Policy:\n{pol}\n\n"
        formatted += f"Reviewer:\n{review}\n"
        return formatted