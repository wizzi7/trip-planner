"""
Usage:
    python -m benchmark.runner                # run all
    python -m benchmark.runner --dry-run      # print plan without calling LLMs
    python -m benchmark.runner --scenario S1_krakow --model gemini   # single combo
"""

import asyncio
import argparse
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.models import UserInput, LLMSettings
from backend.agents.orchestrator import OrchestratorAgent
from backend.logging_config import setup_logging

setup_logging()

from benchmark.scenarios import SCENARIOS, MODELS, REPETITIONS


RESULTS_DIR = Path(__file__).parent / "results"


def _build_user_input(scenario: dict, model_cfg: dict) -> UserInput:
    params = scenario["params"].copy()
    params["llm_settings"] = LLMSettings(
        provider=model_cfg["provider"],
        model=model_cfg["model"],
    )
    return UserInput(**params)


def _serialize_plan(plan) -> dict:
    return plan.model_dump(mode="json")


async def run_single(
    scenario: dict,
    model_cfg: dict,
    run_idx: int,
) -> dict:

    scenario_id = scenario["id"]
    model_id = model_cfg["id"]
    label = f"{scenario_id} | {model_cfg['label']} | run {run_idx}"

    print(f"\n{'='*70}")
    print(f"  START: {label}")
    print(f"{'='*70}")

    user_input = _build_user_input(scenario, model_cfg)

    orchestrator = OrchestratorAgent()

    start = time.time()
    try:
        plan = await orchestrator.run(user_input)
        success = True
        error_msg = None
    except Exception as e:
        plan = None
        success = False
        error_msg = str(e)
        print(f"  ERROR: {e}")

    e2e_latency = round(time.time() - start, 3)

    agent_metrics = {}
    if plan and plan.usage_stats:
        for agent_name, stats in plan.usage_stats.items():
            if hasattr(stats, "model_dump"):
                agent_metrics[agent_name] = stats.model_dump()
            elif isinstance(stats, dict):
                agent_metrics[agent_name] = stats
            else:
                agent_metrics[agent_name] = {
                    "input_tokens": getattr(stats, "input_tokens", 0),
                    "output_tokens": getattr(stats, "output_tokens", 0),
                    "total_tokens": getattr(stats, "total_tokens", 0),
                    "cost": getattr(stats, "cost", 0.0),
                    "model": getattr(stats, "model", ""),
                    "latency_seconds": getattr(stats, "latency_seconds", None),
                }

    total_input_tokens = sum(m.get("input_tokens", 0) for m in agent_metrics.values())
    total_output_tokens = sum(m.get("output_tokens", 0) for m in agent_metrics.values())
    total_cost = sum(m.get("cost", 0.0) for m in agent_metrics.values())

    quality_auto = {}
    if plan:
        quality_auto["num_days"] = len(plan.days) if plan.days else 0
        quality_auto["total_activities"] = sum(
            len(d.activities) for d in plan.days
        ) if plan.days else 0
        quality_auto["avg_activities_per_day"] = round(
            quality_auto["total_activities"] / max(quality_auto["num_days"], 1), 1
        )
        quality_auto["has_culinary"] = plan.culinary_section is not None
        quality_auto["has_mobility"] = plan.mobility_section is not None
        quality_auto["has_city_overview"] = plan.city_overview is not None
        quality_auto["schema_valid"] = True
        quality_auto["total_cost_estimate"] = plan.total_cost
    else:
        quality_auto["schema_valid"] = False

    result = {
        "scenario_id": scenario_id,
        "scenario_label": scenario["label"],
        "model_id": model_id,
        "model_label": model_cfg["label"],
        "model_name": model_cfg["model"],
        "provider": model_cfg["provider"],
        "run": run_idx,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "error": error_msg,
        "e2e_latency_seconds": e2e_latency,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": round(total_cost, 6),
        "agent_metrics": agent_metrics,
        "quality_auto": quality_auto,
        "plan": _serialize_plan(plan) if plan else None,
    }

    print(f"  DONE: {label}  |  {e2e_latency}s  |  ${total_cost:.4f}  |  "
          f"{total_input_tokens}+{total_output_tokens} tokens")

    return result


async def run_benchmark(
    scenario_filter: str = None,
    model_filter: str = None,
    dry_run: bool = False,
):

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = SCENARIOS
    models = MODELS

    if scenario_filter:
        scenarios = [s for s in scenarios if s["id"] == scenario_filter]
        if not scenarios:
            print(f"Unknown scenario: {scenario_filter}")
            return

    if model_filter:
        models = [m for m in models if m["id"] == model_filter]
        if not models:
            print(f"Unknown model: {model_filter}")
            return

    total_runs = len(scenarios) * len(models) * REPETITIONS
    print(f"\n{'#'*70}")
    print(f"  BENCHMARK: {len(scenarios)} scenarios × {len(models)} models × {REPETITIONS} reps = {total_runs} runs")
    print(f"{'#'*70}")

    if dry_run:
        for s in scenarios:
            for m in models:
                for r in range(1, REPETITIONS + 1):
                    print(f"  [DRY-RUN] {s['id']} | {m['label']} | run {r}")
        print(f"\nDry run complete. {total_runs} runs would be executed.")
        return

    all_results = []
    run_counter = 0

    for scenario in scenarios:
        for model_cfg in models:
            for rep in range(1, REPETITIONS + 1):
                run_counter += 1
                print(f"\n  >>> Run {run_counter}/{total_runs}")

                result = await run_single(scenario, model_cfg, rep)
                all_results.append(result)

                # Save individual result
                filename = f"{scenario['id']}_{model_cfg['id']}_run{rep}.json"
                filepath = RESULTS_DIR / filename
                filepath.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"  Saved: {filepath.name}")

    summary = {
        "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(all_results),
        "successful_runs": sum(1 for r in all_results if r["success"]),
        "total_cost_usd": round(sum(r["total_cost_usd"] for r in all_results), 6),
        "total_duration_seconds": round(sum(r["e2e_latency_seconds"] for r in all_results), 1),
        "runs": [
            {
                "scenario": r["scenario_id"],
                "model": r["model_name"],
                "run": r["run"],
                "success": r["success"],
                "e2e_latency_s": r["e2e_latency_seconds"],
                "cost_usd": r["total_cost_usd"],
                "tokens": f"{r['total_input_tokens']}+{r['total_output_tokens']}",
            }
            for r in all_results
        ],
    }

    summary_path = RESULTS_DIR / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n{'#'*70}")
    print(f"  BENCHMARK COMPLETE")
    print(f"  Runs: {summary['successful_runs']}/{summary['total_runs']} successful")
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Total time: {summary['total_duration_seconds']}s")
    print(f"  Summary: {summary_path}")
    print(f"{'#'*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Trip Planner LLM Benchmark Runner")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without calling LLMs")
    parser.add_argument("--scenario", type=str, default=None, help="Run only this scenario ID (e.g. S1_krakow)")
    parser.add_argument("--model", type=str, default=None, help="Run only this model ID (e.g. gemini)")
    args = parser.parse_args()

    asyncio.run(run_benchmark(
        scenario_filter=args.scenario,
        model_filter=args.model,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
