import os
import numpy as np
from typing import Dict, Any


def run_monte_carlo(
    base_cost: float,
    cost_cv: float = 0.2,
    base_duration_days: float = 365,
    duration_cv: float = 0.25,
    n_sims: int = 5000,
    random_seed: int = 42,
) -> Dict[str, Any]:

    rng = np.random.default_rng(random_seed)

    # Helper to compute lognormal params
    def lognorm_params(mean: float, cv: float):
        sigma = np.sqrt(np.log(1 + cv**2))
        mu = np.log(mean) - 0.5 * sigma**2
        return mu, sigma

    mu_c, sigma_c = lognorm_params(base_cost, cost_cv)
    mu_d, sigma_d = lognorm_params(base_duration_days, duration_cv)

    # Generate simulations
    costs = rng.lognormal(mu_c, sigma_c, n_sims)
    durations = rng.lognormal(mu_d, sigma_d, n_sims)

    cost_over = (costs - base_cost) / base_cost * 100
    dur_over = (durations - base_duration_days) / base_duration_days * 100

    def pct(x, p): return float(np.percentile(x, p))

    return {
        "n_sims": n_sims,
        "cost": {
            "mean": float(np.mean(costs)),
            "std": float(np.std(costs)),
            "p10": pct(costs, 10),
            "p50": pct(costs, 50),
            "p90": pct(costs, 90),
            "overrun_pct_mean": float(np.mean(cost_over)),
        },
        "duration": {
            "mean_days": float(np.mean(durations)),
            "std_days": float(np.std(durations)),
            "p10_days": pct(durations, 10),
            "p50_days": pct(durations, 50),
            "p90_days": pct(durations, 90),
            "overrun_pct_mean": float(np.mean(dur_over)),
        }
    }
