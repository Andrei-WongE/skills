# Table Benchmarks

Store gold cases here for regression-first table extraction evaluation.

## Synthetic generation

You can generate a local synthetic benchmark corpus directly from built-in LaTeX table specs:

```bash
python3 scripts/synthetic_benchmarks.py
```

This writes:

- `benchmarks/cases/<case_id>/source.tex`
- `benchmarks/cases/<case_id>/source.pdf`
- `benchmarks/cases/<case_id>/crop.png`
- `benchmarks/cases/<case_id>/agent_table.json`
- `benchmarks/cases/<case_id>/table.tex`
- `benchmarks/cases/<case_id>/qa.json`
- `benchmarks/cases/<case_id>/metadata.json`
- `benchmarks/manifest.synthetic.json`

The built-in synthetic corpus covers multiple LaTeX styles and structures, including:

- booktabs regression tables
- multi-panel regression tables
- siunitx summary-stat tables
- wide resizebox appendix tables
- multirow and multicolumn headers
- control rows with checkmarks
- math-heavy cells and headers
- tabularx wrapped stubs
- longtable appendix layouts
- sidewaystable landscape layouts
- classic vertical-rule tables

## Recommended layout

Each case should live in its own folder:

```text
benchmarks/
  manifest.example.json
  cases/
    autor-levy-murnane-table-i/
      metadata.json
      source.pdf
      crop.png
      agent_table.json
      table.tex
      qa.json
```

## Minimum gold artifacts per case

- `metadata.json`: case id, source citation, page number, and table label
- `crop.png`: reference crop used for human verification
- `agent_table.json`: gold cell/span schema for the table
- `table.tex`: canonical LaTeX rendering for the gold table
- `qa.json`: 3-5 downstream QA prompts with exact answers

## Suggested case mix

- clean born-digital regression table
- corrupted text-layer regression table
- multi-panel table
- notes-heavy table
- summary-statistics table
- wide appendix table
- scanned or OCR-degraded case

## Evaluation

Use the evaluator to compare a predicted `agent_table.json` against a gold case:

```bash
python3 scripts/evaluate_tables.py \
  /path/to/predicted.agent.json \
  benchmarks/cases/example/agent_table.json \
  --predicted-latex /path/to/predicted.tex \
  --gold-latex benchmarks/cases/example/table.tex
```
