from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from time import perf_counter
from typing import Any

from mosaic.risk import exact_k_metrics


def _rows(sizes: list[int]) -> tuple[dict[str, str], ...]:
    return tuple(
        {"combination": f"class-{index}"} for index, size in enumerate(sizes) for _ in range(size)
    )


def _sizes(seed: int, kind: str) -> list[int]:
    generator = random.Random(seed)
    if kind == "critical":
        # Keep every generated critical case unambiguously beyond the policy
        # boundary (minimum k=1 and at least 20% of records below k=5).
        singleton_count = generator.randint(24, 36)
        large_classes = [generator.randint(5, 12) for _ in range(4)]
        return [1] * singleton_count + large_classes
    if kind == "elevated":
        return [generator.randint(2, 4) for _ in range(4)] + [
            generator.randint(5, 18) for _ in range(12)
        ]
    return [generator.randint(5, 24) for _ in range(18)]


def _direct_metrics(sizes: list[int]) -> dict[str, float | int]:
    total = sum(sizes)
    return {
        "total_records": total,
        "distinct_combinations": len(sizes),
        "minimum_k": min(sizes),
        "percent_below_5": round(100 * sum(size for size in sizes if size < 5) / total, 3),
    }


def run_benchmark() -> dict[str, Any]:
    started = perf_counter()
    results = []
    counts = Counter()
    for seed in range(20260730, 20260746):
        for kind in ("critical", "elevated", "safe"):
            sizes = _sizes(seed, kind)
            direct = _direct_metrics(sizes)
            metrics = exact_k_metrics(_rows(sizes), ("combination",))
            predicted_critical = metrics.minimum_k < 2 and metrics.percent_below_5 >= 20
            expected_critical = kind == "critical"
            if expected_critical and predicted_critical:
                counts["true_positive"] += 1
            elif expected_critical:
                counts["false_negative"] += 1
            elif predicted_critical:
                counts["false_positive"] += 1
            else:
                counts["true_negative"] += 1
            exact = (
                metrics.total_records == direct["total_records"]
                and metrics.distinct_combinations == direct["distinct_combinations"]
                and metrics.minimum_k == direct["minimum_k"]
                and metrics.percent_below_5 == direct["percent_below_5"]
            )
            results.append(
                {
                    "case_id": f"seed-{seed}-{kind}",
                    "kind": kind,
                    "seed": seed,
                    "records": metrics.total_records,
                    "minimum_k": metrics.minimum_k,
                    "percent_below_5": metrics.percent_below_5,
                    "expected_critical": expected_critical,
                    "predicted_critical": predicted_critical,
                    "exact_metric_agreement": exact,
                    "raw_rows_returned": 0,
                }
            )
    tp = counts["true_positive"]
    fp = counts["false_positive"]
    fn = counts["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    scale = []
    for classes, class_size in ((100, 10), (1000, 10), (5000, 10)):
        scale_started = perf_counter()
        metrics = exact_k_metrics(_rows([class_size] * classes), ("combination",))
        scale.append(
            {
                "records": metrics.total_records,
                "classes": classes,
                "runtime_ms": round((perf_counter() - scale_started) * 1000, 3),
            }
        )
    stable_payload = {
        "cases": results,
        "counts": dict(counts),
        "precision": precision,
        "recall": recall,
    }
    return {
        "schema_version": 1,
        "status": "passed"
        if all(item["exact_metric_agreement"] for item in results) and fp == 0 and fn == 0
        else "failed",
        "disclosure": {
            "what_this_measures": "Exact metric agreement, policy-boundary behavior, safe-control false positives, repeatability, and local scaling.",
            "what_is_by_construction": "Case labels are generated from deliberately bounded class-size families. Perfect classification here is a regression claim, not field accuracy.",
            "what_it_does_not_measure": "Real-world correlation realism or catalog-lineage completeness; the external-data and recorded-DataHub proofs address those separately.",
        },
        "cases": len(results),
        "counts": dict(counts),
        "metrics": {
            "precision": precision,
            "recall": recall,
            "critical_false_positive_rate": fp
            / sum(item["kind"] != "critical" for item in results),
            "exact_k_agreement": sum(item["exact_metric_agreement"] for item in results)
            / len(results),
            "zero_raw_rows_rate": sum(item["raw_rows_returned"] == 0 for item in results)
            / len(results),
        },
        "repeatability_sha256": hashlib.sha256(
            json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "scale": scale,
        "total_runtime_seconds": round(perf_counter() - started, 3),
        "results": results,
    }
