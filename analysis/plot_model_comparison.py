import json
import os
from collections import defaultdict

import matplotlib.pyplot as plt


def main() -> None:
    report_path = os.path.join("reports", "benchmark_results.json")
    out_path = os.path.join("reports", "model_comparison.png")

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    model_scores = defaultdict(list)
    final_scores = []
    for item in data:
        final_scores.append(float(item.get("judge", {}).get("final_score", 0.0)))
        for model_name, score in item.get("judge", {}).get("individual_scores", {}).items():
            model_scores[model_name].append(float(score))

    if not model_scores:
        raise ValueError("No judge model scores found in reports/benchmark_results.json")

    models = sorted(model_scores.keys())
    avg_scores = [sum(model_scores[m]) / len(model_scores[m]) for m in models]
    final_avg = sum(final_scores) / len(final_scores) if final_scores else 0.0

    labels = ["final_score_avg"] + models
    scores = [final_avg] + avg_scores

    plt.figure(figsize=(10, 5))
    colors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    bars = plt.bar(labels, scores, color=colors[: len(labels)])
    plt.ylim(1, 5)
    plt.title("Final Score vs Judge Model Averages")
    plt.ylabel("Average score (1-5)")
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for bar, score in zip(bars, scores):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            score + 0.03,
            f"{score:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    os.makedirs("reports", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

    print(f"Saved: {out_path}")
    print(f"final_score_avg={final_avg:.4f}")
    for label, score in zip(models, avg_scores):
        print(f"{label}_avg={score:.4f}")


if __name__ == "__main__":
    main()
