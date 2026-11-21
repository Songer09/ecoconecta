"""Evalúa intenciones fuera de los ejemplos del prompt."""

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean
from time import perf_counter
from app.language import classify

HERE = Path(__file__).parent


def evaluate(predict, dataset):
    matrix = Counter()
    times = []
    domain_correct = 0
    for row in dataset:
        start = perf_counter()
        result = predict(row["text"])
        times.append((perf_counter() - start) * 1000)
        matrix[row["intent"], result.intent] += 1
        domain_correct += result.scope == row["scope"]
    labels = sorted({tag for pair in matrix for tag in pair})
    scores = {}
    for tag in labels:
        tp = matrix[tag, tag]
        support = sum(matrix[tag, predicted] for predicted in labels)
        predicted = sum(matrix[actual, tag] for actual in labels)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        scores[tag] = {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0,
            "support": support,
        }
    times.sort()
    return {
        "schema_version": 1,
        "n": len(dataset),
        "accuracy": sum(matrix[tag, tag] for tag in labels) / len(dataset),
        "scope_accuracy": domain_correct / len(dataset),
        "macro_f1": mean(s["f1"] for s in scores.values()),
        "false_collection_from_education": sum(
            matrix[i, "collection"] for i in ("compost", "recycling", "material")
        ),
        "latency_ms": {
            "p50": round(times[(len(times) - 1) // 2], 3),
            "p95": round(times[int((len(times) - 1) * 0.95)], 3),
        },
        "labels": labels,
        "per_intent": scores,
        "confusion_matrix": {
            "rows": "expected",
            "columns": "predicted",
            "values": [[matrix[a, b] for b in labels] for a in labels],
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["mock", "configured"], default="mock")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    mode = "mock"
    predict = classify
    if args.provider == "configured":
        from app.config import settings
        from app.providers import understand

        mode = settings().ai
        predict = understand
    dataset = [
        json.loads(line)
        for line in (HERE / "evaluacion_intenciones.jsonl").read_text().splitlines()
    ]
    result = evaluate(predict, dataset)
    result["provider"] = mode
    report = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    print(
        {
            k: result[k]
            for k in (
                "provider",
                "n",
                "accuracy",
                "scope_accuracy",
                "macro_f1",
                "false_collection_from_education",
                "latency_ms",
            )
        }
    )


if __name__ == "__main__":
    main()
