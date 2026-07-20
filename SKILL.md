---
name: call-flow-deep-dive
description: Generate multi-tab Excel reports and HTML dashboards with charts from call flow CSV data. Self-contained skill — scripts are bundled as reference files for instant restoration on any system.
tags:
  - data-science
  - reporting
  - excel
  - html
  - call-center
---

# Call Flow Deep-Dive Report Skill

## What it does
Generates multi-tab Excel reports and HTML dashboards (with matplotlib charts) analyzing call flow data from raw CSV exports. All time data displays in MM:SS format. Call flow paths are extracted from a specified column (e.g., "Queue") in the raw CSV files.

## Installation / Portability
This skill is fully self-contained. To install on any system:

```bash
# Option 1: From the package zip (if available)
mkdir -p ~/.hermes/skills/data-science/call-flow-deep-dive
cd ~/.hermes/skills/data-science/call-flow-deep-dive
unzip -o skill-call-flow-deep-dive.zip

# Option 2: Copy from another system
# Transfer the entire call-flow-deep-dive directory and place it at:
# ~/.hermes/skills/data-science/call-flow-deep-dive/

# Option 3: Ask me to recreate it
# Just say "set up call-flow-deep-dive skill" and I'll reconstruct everything
```

After installation, verify with:
```bash
ls ~/.hermes/skills/data-science/call-flow-deep-dive/
# Should show: SKILL.md, references/, scripts/
```

## Quick setup (project from scratch)
If you're starting on a new system and need a fresh project:

```bash
# 1. Create the project directory structure
mkdir -p /path/to/project/scripts
mkdir -p "/path/to/project/CSV Files"
mkdir -p /path/to/project/Reports/Charts
mkdir -p /path/to/project/Output
mkdir -p /path/to/project/Reports_HTML/charts

# 2. Copy scripts from the skill reference files
cp ~/.hermes/skills/data-science/call-flow-deep-dive/references/extract_html_data.py /path/to/project/scripts/
cp ~/.hermes/skills/data-science/call-flow-deep-dive/references/generate_report.py /path/to/project/scripts/
cp ~/.hermes/skills/data-science/call-flow-deep-dive/references/generate_html_report.py /path/to/project/scripts/

# 3. Drop your raw CSV exports into CSV Files/
#    (one file per month, any of these patterns work)
```

Now the project is ready. See "Step-by-step process" below to generate reports.

## Project layout
```
Project Root/
├── scripts/
│   ├── extract_html_data.py      ← extracts KPI/duration/hourly/outcomes CSVs + call paths
│   ├── generate_report.py        ← main Excel generator (data-only, multi-tab)
│   └── generate_html_report.py   ← generates HTML dashboard with matplotlib charts (reads CSVs)
├── CSV Files/                    ← raw CSV exports, one per month
│   ├── doc_xxx_Switchboard-April.csv          (hyphen separator)
│   ├── doc_xxx_Switchboard June.csv           (space separator)
│   └── doc_xxx_LRS Spanish April.csv          (multi-word category)
├── Reports/Charts/               ← extracted CSV data + path counts
│   ├── <category>_outcomes.csv       Month,Total,Successful,Failed,Abandoned,Success%,Fail%,Abandon%
│   ├── <category>_duration.csv       Month,Avg Duration (s),P50 Duration (s),P95 Duration (s),Max Duration (s),Valid Samples
│   ├── <category>_hourly.csv         Hour,April,May,June,All
│   ├── <category>_transfers.csv      Month,Total Transfers,Blind Transfers,Consult Transfers,Transfer Rate (%)
│   ├── <category>_flow_paths.csv     Path,Count (all months aggregated)
│   ├── <category>_flow_paths_april.csv   (per month)
│   ├── <category>_disconnect_types.csv   Disconnect Type,April,May,June,Total
│   └── <category>_summary.csv          Metric,April,May,June,Total
├── Reports_HTML/
│   ├── report_<category>.html
│   └── charts/*.png
└── Output/
    └── <Category>_DeepDive_Apr-May-Jun_2026.xlsx
```

## Step-by-step process

### 1. Extract data from raw CSVs
Run the extraction script from the `scripts/` directory:
```bash
cd scripts
python3 extract_html_data.py                # processes ALL categories found in CSV Files/
python3 extract_html_data.py Switchboard    # processes a single category
```

This script:
- Reads raw CSVs from `CSV Files/`
- Classifies outcomes: `Outcome Success == "1"` AND `Abandoned != "YES"` → successful; `Abandoned == "YES"` → abandoned; else failed
- Parses durations (`' 00:04:12.710'` → total seconds), filters outliers >86400s (24h)
- Extracts call paths from the **Queue column** (semicolon-separated → joined with ` → `)
- Produces summary CSVs in `Reports/Charts/` for each category:
  - `outcomes.csv` — Month,Total,Successful,Failed,Abandoned,Success%,Fail%,Abandon%
  - `duration.csv` — Month,Avg Duration (s),P50 Duration (s),P95 Duration (s),Max Duration (s),Valid Samples
  - `hourly.csv` — Hour,April,May,June,All
  - `transfers.csv` — Month,Total Transfers,Blind Transfers,Consult Transfers,Transfer Rate (%)
  - `flow_paths.csv` — Path,Count (aggregated) + per-month files
  - `disconnect_types.csv` — Disconnect Type,April,May,June,Total
  - `summary.csv` — Metric,April,May,June,Total

### 2. Generate Excel report (data-only, multi-tab)
```bash
python3 generate_report.py                # auto-detects category
python3 generate_report.py Switchboard    # single category
```

The script reads extracted CSVs and generates `Output/<Category>_DeepDive_Apr-May-Jun_2026.xlsx` with tabs:
- **Summary** — KPI cards (Total Calls, Abandonment Rate, Success Rate, Avg Duration) + monthly summary table
- **{Month Name}** — Key Metrics (MM:SS format) + Top 10 call flow paths
- **Transfers** — transfer counts and rates per month
- **Disconnect Types** — top 15 disconnect types
- **Hourly** — call distribution by hour
- **Duration** — Avg, P50, P95, Max Duration in MM:SS
- **Outcomes Stacked** — total/successful/failed/abandoned per month
- **Flow Paths** — all unique paths with total counts

### 3. Generate HTML report (with charts)
```bash
python3 generate_html_report.py Switchboard   # reads CSVs from Reports/Charts/
```

**IMPORTANT:** `generate_html_report.py` reads directly from `Reports/Charts/*.csv` files, NOT from the Excel workbook. The HTML generation was rewritten to parse CSVs because:
- Hardcoded row numbers in the old version didn't match the Excel structure produced by `generate_report.py`
- The HTML generator reads outcomes, duration, hourly, transfers, disconnect_types, and flow_paths CSVs
- Charts are saved to `Reports_HTML/charts/` as PNGs
- The HTML dashboard is saved to `Reports_HTML/report_<category>.html`

To create a complete report for one category:
```bash
python3 extract_html_data.py Switchboard        # Step 1: generate CSVs
python3 generate_report.py Switchboard           # Step 2: generate Excel
python3 generate_html_report.py Switchboard      # Step 3: generate HTML dashboard
```

## Chart output
The HTML dashboard references PNG charts via `./charts/` relative paths. When sharing or delivering:
- Always include the HTML file and the `charts/` directory together
- The recommended format is a zip with the HTML at root and `charts/` as a sibling folder

## Key constraints & conventions
- **Time formatting:** All duration metrics use `format_duration()` — converts seconds to `f"{m:02d}:{s:02d}"` (e.g., 386s → "06:26")
- **Path source:** Call flow paths come ONLY from the specified path column of raw CSV files — never from other columns
- **Pitfall — column naming:** In Inbound.log exports, "Queue Segments" contains a numeric COUNT of segments, NOT the paths. The actual queue destinations are in the "Queue" column (semicolon-separated). Always verify the column contains paths, not counts.
- **Filename separator detection:** Scripts must handle both space-separated (`Switchboard June.csv`) and hyphen-separated (`Switchboard-April.csv`) filenames. **Space-split is tried first** since hyphens can appear in category names (e.g., `Non-ATTY`). For `doc_xxx_Switchboard-April.csv`: split on `-` to get month=`April`, category=`Switchboard`. For `doc_xxx_Non-ATTY June.csv`: split on space to get month=`June`, category=`Non-ATTY`.
- **Relative paths:** All scripts resolve directories via `PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`.
- **No hardcoded sys.path entries:** Scripts do NOT inject any `sys.path.insert()` for a specific Python installation. They rely on the active Python environment/venv. This is a hard rule discovered during audit.
- **No charts in Excel:** The Excel output is strictly tabular — no charts, images, or embedding.
- **Month isolation:** Each monthly tab uses only that month's raw CSV data.
- **Top N:** Monthly tabs show top 10 paths; the Flow Paths tab shows all unique paths.
- **CSV-based HTML generation:** `generate_html_report.py` reads CSV files directly from `Reports/Charts/`. Do NOT rely on Excel structure for HTML generation — the Excel file may change, but the CSV schemas are stable.

## Chart generation requirements
When generating the HTML dashboard with `generate_html_report.py`:
- **Hourly distribution chart** must filter to business hours only (6 AM to 6 PM, i.e., hour 6–18). Do NOT show all 24 hours.
- **Duration Statistics chart** must display MM:SS format on bar labels AND the y-axis. The y-axis uses `plt.FuncFormatter` to convert raw-second bar heights to MM:SS tick labels. Both `create_monthly_charts` and `create_duration_stats_charts` implement this.

## When NOT to Use This Skill

This skill handles the full extraction → Excel → HTML pipeline. If you only need outcome classification patterns and chart XML templates (documentation), use the **call-flow-analysis** skill instead.

## Troubleshooting

### Paths showing fewer than expected
The legacy aggregated path CSV may have been truncated. Always extract fresh paths from the raw CSV files using `extract_html_data.py`. Check the path column name — don't confuse it with a count column (e.g., "Queue Segments" contains counts, not paths).

### Excel won't open
Ensure no `openpyxl` image embedding code exists. The script is pure data generation.

### "Total" row appearing as a month
The outcomes CSV includes a "Total" summary row. Always filter `Month == 'Total'` before treating rows as months. This applies to both `extract_html_data.py` and `generate_report.py`.

### Scripts lost from project
All three scripts are bundled as reference files in the skill directory:
- `references/extract_html_data.py`
- `references/generate_report.py`
- `references/generate_html_report.py`

If the project `scripts/` directory is deleted, copy them back using the commands in "Quick setup (project from scratch)" above. Each reference file is an exact copy of the corresponding script. No reconstruction from scratch is needed.

## Extending to other projects

To apply this skill to a different dataset:
1. **Identify the path column** — find the column containing the sequential path data (semicolon-separated or similar)
2. **Adjust file names** — update CSV file names in the extraction and generation scripts
3. **Adjust KPIs** — modify the KPI extraction to match your data schema
4. **Customize tabs** — add/remove tabs as needed for your analysis
5. **Verify relative paths** — ensure `PROJECT_DIR` correctly resolves to your project root

## Auditing other skills for self-containment

When checking any skill for portability (or making a skill self-contained), verify these four things:

1. **Hardcoded paths**: Scripts should use relative paths or configurable arguments (e.g., `argparse` with `--project-dir`). Never hardcode `/Users/trey/...` paths.
2. **Install instructions**: SKILL.md must have an "Installation / Portability" section with clear steps for installing the skill on a new system.
3. **Package zips**: Each skill should have a zip file (e.g., `skill-{name}.zip`) in its own directory for easy transfer.
4. **Reference files**: All scripts and supporting files should be saved in the skill's `references/` directory so they can be restored if the project files are deleted.

If any of these are missing, add them before considering the skill "self-contained."

## Post-Audit Notes (2026-07-17)

The following issues were discovered and fixed during a reference file audit:

- **`generate_html_report.py` was incomplete**: The HTML template was cut off mid-f-string at line 500. The script never wrote any output file and had no `if __name__ == '__main__'` block. Fixed: complete HTML template, proper file write, auto-detect + CLI entry point (`main()`).
- **Duration chart y-axis mismatch**: Two duration charts stated the y-axis was "MM:SS" but displayed raw seconds as bar heights. Fixed by adding `plt.FuncFormatter` to format y-axis ticks in MM:SS while keeping bar data in raw seconds.
- **`extract_html_data.py` duplicate output**: Wrote `{prefix}_outcomes.csv` and an identical `{prefix}_call_outcomes.csv`. Removed the duplicate write — only `_outcomes.csv` is produced.
- **All three scripts had hardcoded `/Library/Python/3.9/...` sys.path**: This resolves only on the machine that created the scripts. Removed all three hardcoded path inserts — scripts now rely on the active Python environment/venv.