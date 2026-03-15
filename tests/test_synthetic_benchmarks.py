from __future__ import annotations

from synthetic_benchmarks import build_case_artifacts, build_default_cases


def test_build_default_cases_covers_many_latex_table_variants() -> None:
    cases = build_default_cases()
    case_ids = {case.case_id for case in cases}
    assert len(cases) >= 10
    assert "synthetic-regression-booktabs" in case_ids
    assert "synthetic-longtable-appendix" in case_ids
    assert "synthetic-sidewaystable" in case_ids
    assert "synthetic-tabularx-wrapped-stubs" in case_ids


def test_build_case_artifacts_generates_gold_agent_table_and_tex() -> None:
    case = next(case for case in build_default_cases() if case.case_id == "synthetic-regression-booktabs")
    artifacts = build_case_artifacts(case, source_pdf="/tmp/source.pdf")

    assert artifacts["agent_table"]["table_id"] == "synthetic-regression-booktabs"
    assert artifacts["agent_table"]["source_pdf"] == "/tmp/source.pdf"
    assert artifacts["agent_table"]["regression_semantics"]["coefficient_cells"]
    assert r"\begin{table}" in artifacts["table_tex"]
    assert r"\begin{tabular}" in artifacts["table_tex"]
    assert r"\begin{document}" in artifacts["document_tex"]
