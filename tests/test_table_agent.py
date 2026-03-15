from __future__ import annotations

import json
from pathlib import Path

from table_agent import (
    _rebuild_rotated_table_from_words,
    _reconstruct_paired_group_header,
    _reconstruct_grouped_header,
    _refresh_cells,
    build_agent_table,
    cell_text_to_latex,
)
from table_cleanup import TableCleanupReport


class FakeBBox:
    def __init__(self, l: float, t: float, r: float, b: float, coord_origin: str = "TOPLEFT") -> None:
        self.l = l
        self.t = t
        self.r = r
        self.b = b
        self.coord_origin = coord_origin

    def model_dump(self, mode: str | None = None) -> dict[str, object]:
        return {
            "l": self.l,
            "t": self.t,
            "r": self.r,
            "b": self.b,
            "coord_origin": self.coord_origin,
        }


class FakeProv:
    def __init__(self, page_no: int, bbox: FakeBBox) -> None:
        self.page_no = page_no
        self.bbox = bbox


class FakeCell:
    def __init__(
        self,
        text: str,
        row_start: int,
        row_end: int,
        col_start: int,
        col_end: int,
        *,
        column_header: bool = False,
        row_header: bool = False,
        row_section: bool = False,
    ) -> None:
        self.text = text
        self.start_row_offset_idx = row_start
        self.end_row_offset_idx = row_end
        self.start_col_offset_idx = col_start
        self.end_col_offset_idx = col_end
        self.column_header = column_header
        self.row_header = row_header
        self.row_section = row_section
        self.bbox = FakeBBox(10 + (col_start * 20), 10 + (row_start * 8), 20 + (col_end * 20), 18 + (row_end * 8))


class FakeData:
    def __init__(self, table_cells: list[FakeCell]) -> None:
        self.table_cells = table_cells


class FakeTable:
    def __init__(self) -> None:
        self.data = FakeData(
            [
                FakeCell("", 0, 1, 0, 1, column_header=True),
                FakeCell("Models", 0, 1, 1, 3, column_header=True),
                FakeCell("Variable", 1, 2, 0, 1, column_header=True),
                FakeCell("(1)", 1, 2, 1, 2, column_header=True),
                FakeCell("(2)", 1, 2, 2, 3, column_header=True),
                FakeCell("Robots", 2, 3, 0, 1),
                FakeCell("-0.123***", 2, 3, 1, 2),
                FakeCell("-0.456", 2, 3, 2, 3),
                FakeCell("", 3, 4, 0, 1),
                FakeCell("(0.045)", 3, 4, 1, 2),
                FakeCell("(0.078)", 3, 4, 2, 3),
                FakeCell("Controls", 4, 5, 0, 1),
                FakeCell("Yes", 4, 5, 1, 2),
                FakeCell("No", 4, 5, 2, 3),
                FakeCell("Observations", 5, 6, 0, 1),
                FakeCell("1000", 5, 6, 1, 2),
                FakeCell("900", 5, 6, 2, 3),
            ]
        )
        self.prov = [FakeProv(1, FakeBBox(0, 0, 120, 48, "TOPLEFT"))]
        self.footnotes = [{"text": "Robust standard errors in parentheses."}]

    def caption_text(self, doc: object) -> str:
        return "Table 1: Example Regression"


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def test_cell_text_to_latex_synthesizes_significance_markers() -> None:
    latex, source, confidence = cell_text_to_latex("-0.123***")
    assert latex == "$-0.123^{***}$"
    assert source == "deterministic"
    assert confidence > 0.9


def test_build_agent_table_matches_regression_fixture() -> None:
    table = FakeTable()
    report = TableCleanupReport(verification_required=False, reasons=[])
    agent_table, full_latex = build_agent_table(
        table=table,
        doc=object(),
        pdf_path=Path("/tmp/example.pdf"),
        table_index=1,
        raw_markdown="",
        cleaned_markdown="| Variable | (1) | (2) |",
        cleaned_report=report,
        html=None,
        otsl=None,
        crop_path=None,
        table_image=None,
        plumber_pdf=None,
    )

    expected_semantics = json.loads((FIXTURE_DIR / "example_regression_semantics.json").read_text(encoding="utf-8"))
    expected_full_latex = (FIXTURE_DIR / "example_table.tex").read_text(encoding="utf-8")
    expected_tabular = (FIXTURE_DIR / "example_tabular.tex").read_text(encoding="utf-8")

    assert agent_table["title"] == "Table 1: Example Regression"
    assert agent_table["regression_semantics"] == expected_semantics
    assert agent_table["renderings"]["latex_tabular"] == expected_tabular
    assert full_latex == expected_full_latex

    cells_by_id = {cell["cell_id"]: cell for cell in agent_table["cells"]}
    assert cells_by_id["r2_c1"]["latex"] == "$-0.123^{***}$"
    assert cells_by_id["r4_c1"]["text_normalized"] == "Yes"


def test_reconstruct_grouped_header_splits_summary_stats_header() -> None:
    cells = [
        {"row_start": 0, "row_end": 1, "col_start": 0, "col_end": 1, "role": "column_header", "text_normalized": "Variable", "text_raw": "Variable"},
        {"row_start": 0, "row_end": 1, "col_start": 1, "col_end": 2, "role": "data", "text_normalized": "Mean", "text_raw": "Mean"},
        {"row_start": 0, "row_end": 1, "col_start": 2, "col_end": 3, "role": "column_header", "text_normalized": "SD", "text_raw": "SD"},
        {"row_start": 0, "row_end": 1, "col_start": 3, "col_end": 4, "role": "column_header", "text_normalized": "Moments P25", "text_raw": "Moments P25"},
        {"row_start": 0, "row_end": 1, "col_start": 4, "col_end": 5, "role": "column_header", "text_normalized": "P50", "text_raw": "P50"},
        {"row_start": 0, "row_end": 1, "col_start": 5, "col_end": 6, "role": "column_header", "text_normalized": "P75", "text_raw": "P75"},
        {"row_start": 1, "row_end": 2, "col_start": 0, "col_end": 1, "role": "row_header", "text_normalized": "Employment growth", "text_raw": "Employment growth"},
        {"row_start": 1, "row_end": 2, "col_start": 1, "col_end": 2, "role": "data", "text_normalized": "0.014", "text_raw": "0.014"},
    ]

    rebuilt, n_rows = _reconstruct_grouped_header(cells, 3, 6)
    refreshed = _refresh_cells(rebuilt)
    by_position = {(cell["row_start"], cell["col_start"]): cell for cell in refreshed}

    assert n_rows == 4
    assert by_position[(0, 1)]["text_normalized"] == "Moments"
    assert by_position[(0, 1)]["col_end"] == 6
    assert by_position[(1, 3)]["text_normalized"] == "P25"
    assert by_position[(2, 0)]["text_normalized"] == "Employment growth"


def test_rebuild_rotated_table_from_words_recovers_landscape_structure() -> None:
    words = [
        {"text": "elbaT", "x0": 10.0, "top": 10.0, "upright": False},
        {"text": ":1", "x0": 10.0, "top": 20.0, "upright": False},
        {"text": "IIIV", "x0": 10.0, "top": 30.0, "upright": False},
        {"text": "rotceS-yb-rotceS", "x0": 10.0, "top": 40.0, "upright": False},
        {"text": "stneiciffeoC", "x0": 10.0, "top": 50.0, "upright": False},
        {"text": "rotceS", "x0": 20.0, "top": 100.0, "upright": False},
        {"text": ")1(", "x0": 20.0, "top": 90.0, "upright": False},
        {"text": ")2(", "x0": 20.0, "top": 80.0, "upright": False},
        {"text": ")3(", "x0": 20.0, "top": 70.0, "upright": False},
        {"text": "toboR", "x0": 30.0, "top": 100.0, "upright": False},
        {"text": "erusopxe", "x0": 30.0, "top": 90.0, "upright": False},
        {"text": "11.0-", "x0": 30.0, "top": 80.0, "upright": False},
        {"text": "90.0-", "x0": 30.0, "top": 70.0, "upright": False},
        {"text": "70.0-", "x0": 30.0, "top": 60.0, "upright": False},
        {"text": "dradnatS", "x0": 40.0, "top": 100.0, "upright": False},
        {"text": "rorre", "x0": 40.0, "top": 90.0, "upright": False},
        {"text": ")40.0(", "x0": 40.0, "top": 80.0, "upright": False},
        {"text": ")30.0(", "x0": 40.0, "top": 70.0, "upright": False},
        {"text": ")30.0(", "x0": 40.0, "top": 60.0, "upright": False},
    ]

    rebuilt, n_rows, n_cols, title, notes = _rebuild_rotated_table_from_words(
        words,
        current_n_rows=12,
        current_n_cols=2,
        title=None,
        notes=[],
    )

    assert rebuilt is not None
    assert n_rows == 3
    assert n_cols == 4
    assert title == "Coefficients Sector-by-Sector VIII 1: Table"
    assert notes == []
    refreshed = _refresh_cells(rebuilt)
    by_position = {(cell["row_start"], cell["col_start"]): cell for cell in refreshed}
    assert by_position[(0, 0)]["text_normalized"] == "Sector"
    assert by_position[(1, 0)]["text_normalized"] == "Robot exposure"
    assert by_position[(2, 0)]["text_normalized"] == "Standard error"
    assert by_position[(1, 1)]["text_normalized"] == "-0.11"
    assert by_position[(2, 1)]["text_normalized"] == "(0.04)"


def test_refresh_cells_maps_math_aliases() -> None:
    refreshed = _refresh_cells(
        [
            {"row_start": 0, "row_end": 1, "col_start": 1, "col_end": 2, "role": "column_header", "text_normalized": "βˆ", "text_raw": "βˆ"},
            {"row_start": 1, "row_end": 2, "col_start": 0, "col_end": 1, "role": "stub", "text_normalized": "ϵ L", "text_raw": "ϵ L"},
        ]
    )
    by_position = {(cell["row_start"], cell["col_start"]): cell for cell in refreshed}
    assert by_position[(0, 1)]["text_normalized"] == "Estimate"
    assert by_position[(0, 1)]["latex"] == r"$\hat{\beta}$"
    assert by_position[(1, 0)]["text_normalized"] == "Labor elasticity"
    assert by_position[(1, 0)]["latex"] == r"$\epsilon_L$"


def test_reconstruct_paired_group_header_splits_compound_row() -> None:
    cells = [
        {"row_start": 0, "row_end": 1, "col_start": 0, "col_end": 1, "role": "column_header", "text_normalized": "Outcome Men Mean", "text_raw": "Outcome Men Mean"},
        {"row_start": 0, "row_end": 1, "col_start": 1, "col_end": 2, "role": "column_header", "text_normalized": "SD", "text_raw": "SD"},
        {"row_start": 0, "row_end": 1, "col_start": 2, "col_end": 3, "role": "column_header", "text_normalized": "Mean", "text_raw": "Mean"},
        {"row_start": 0, "row_end": 1, "col_start": 3, "col_end": 4, "role": "column_header", "text_normalized": "Women SD", "text_raw": "Women SD"},
        {"row_start": 0, "row_end": 1, "col_start": 4, "col_end": 5, "role": "column_header", "text_normalized": "", "text_raw": ""},
        {"row_start": 1, "row_end": 2, "col_start": 0, "col_end": 1, "role": "row_header", "text_normalized": "Employment", "text_raw": "Employment"},
        {"row_start": 1, "row_end": 2, "col_start": 1, "col_end": 2, "role": "data", "text_normalized": "0.82", "text_raw": "0.82"},
    ]

    rebuilt, n_rows = _reconstruct_paired_group_header(cells, 2, 5)
    refreshed = _refresh_cells(rebuilt)
    by_position = {(cell["row_start"], cell["col_start"]): cell for cell in refreshed}

    assert n_rows == 3
    assert by_position[(0, 0)]["text_normalized"] == "Outcome"
    assert by_position[(0, 1)]["text_normalized"] == "Men"
    assert by_position[(0, 3)]["text_normalized"] == "Women"
    assert by_position[(1, 1)]["text_normalized"] == "Mean"
    assert by_position[(1, 2)]["text_normalized"] == "SD"
    assert by_position[(1, 3)]["text_normalized"] == "Mean"
    assert by_position[(1, 4)]["text_normalized"] == "SD"
