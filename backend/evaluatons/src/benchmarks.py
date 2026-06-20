# src/benchmarks.py
from typing import Dict, Any
from src.web_search import duckduckgo_search

class CostBenchmarkEngine:
    """
    Lightweight web-assisted benchmark helper.

    Currently: fetches DPR/NEC-related snippets for the given project_type
    and returns them along with the DPR's own cost figure.
    """

    def benchmark(self, project_type: str, dpr_cost: float) -> Dict[str, Any]:
        query = f"{project_type} DPR MDONER DoR NEC schedule of rates North Eastern Region"
        results = duckduckgo_search(query, max_results=3)
        return {
            "project_type": project_type,
            "dpr_cost": dpr_cost,
            "web_benchmarks": results,
        }
