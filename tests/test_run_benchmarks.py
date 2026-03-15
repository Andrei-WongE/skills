from __future__ import annotations

import json
from pathlib import Path

from run_benchmarks import _aggregate_results, _parse_json_tail, _render_markdown_report


def test_parse_json_tail_accepts_clean_json_output() -> None:
    payload = {"tables_manifest": "/tmp/example.json", "cached": False}
    assert _parse_json_tail(json.dumps(payload, indent=2)) == payload


def test_parse_json_tail_finds_trailing_json_after_logs() -> None:
    output = "starting extractor\nfinished\n" + json.dumps({"engine": "docling", "cached": True}, indent=2)
    assert _parse_json_tail(output)["engine"] == "docling"


def test_aggregate_results_computes_pass_rate() -> None:
    aggregate = _aggregate_results(
        [
            {
                "case_id": "a",
                "structure_accuracy": 0.9,
                "role_accuracy": 0.8,
                "cell_text_exact_accuracy": 0.7,
                "cell_text_normalized_accuracy": 0.75,
                "numeric_cell_accuracy": 0.8,
                "latex_exact_accuracy": 0.7,
                "coefficient_pair_accuracy": 0.6,
                "summary_row_accuracy": 0.9,
                "unresolved_false_negatives": 1,
                "near_perfect_gate": False,
            },
            {
                "case_id": "b",
                "structure_accuracy": 1.0,
                "role_accuracy": 1.0,
                "cell_text_exact_accuracy": 1.0,
                "cell_text_normalized_accuracy": 1.0,
                "numeric_cell_accuracy": 1.0,
                "latex_exact_accuracy": 1.0,
                "coefficient_pair_accuracy": 1.0,
                "summary_row_accuracy": 1.0,
                "unresolved_false_negatives": 0,
                "near_perfect_gate": True,
            },
            {"case_id": "c", "error": "boom"},
        ]
    )

    assert aggregate["case_count"] == 3
    assert aggregate["success_count"] == 2
    assert aggregate["failure_count"] == 1
    assert aggregate["near_perfect_pass_count"] == 1
    assert aggregate["near_perfect_pass_rate"] == 0.5


def test_render_markdown_report_includes_failures_and_pass_rate(tmp_path: Path) -> None:
    aggregate = {
        "case_count": 2,
        "success_count": 1,
        "failure_count": 1,
        "near_perfect_pass_count": 0,
        "near_perfect_pass_rate": 0.0,
        "avg_structure_accuracy": 0.9,
    }
    results = [
        {
            "case_id": "synthetic-a",
            "category": "regression",
            "structure_accuracy": 0.9,
            "cell_text_normalized_accuracy": 0.8,
            "numeric_cell_accuracy": 0.7,
            "latex_exact_accuracy": 0.6,
            "coefficient_pair_accuracy": 0.5,
            "near_perfect_gate": False,
        },
        {"case_id": "synthetic-b", "error": "extractor failed"},
    ]

    report = _render_markdown_report(tmp_path / "manifest.json", aggregate, results)
    assert "Near-perfect pass rate" in report
    assert "| synthetic-a | regression | 0.9000 | 0.8000 | 0.7000 | 0.6000 | 0.5000 | False |" in report
    assert "- `synthetic-b`: extractor failed" in report
