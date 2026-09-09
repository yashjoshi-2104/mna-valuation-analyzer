# Power BI Dashboard — Build Guide

Power BI Desktop is a Windows application, so it can't be built or run from
this environment — but the data pipeline here is fully wired to feed it.
Follow these steps in Power BI Desktop (free download) to build the
executive dashboard.

## 1. Generate the data

From the project root, with the venv active:
```bash
python -m src.ingestion.load_data        # if you haven't already
python -m src.export.powerbi_export
```
This writes three CSVs to `powerbi/data/`:
- `company_metrics.csv` — one row per company, all ratios pre-calculated
- `transactions.csv` — all 25 precedent deals
- `transaction_summary_by_industry.csv` — median/percentile multiples by industry

Re-run the export any time the underlying data or calculations change —
Power BI will pick up the new CSVs on refresh (step 6).

## 2. Connect Power BI to the data

1. Open Power BI Desktop → **Get Data** → **Folder**
2. Point it at `powerbi/data/` (use the full absolute path)
3. Choose **Combine & Transform** if prompted, or load each CSV individually
   via **Get Data > Text/CSV** — three separate queries is simpler for a
   first build
4. In Power Query Editor, confirm each column's data type: `*_musd` and
   ratio columns should be **Decimal Number**, `announce_date` should be
   **Date**
5. Click **Close & Apply**

## 3. Build relationships

Go to the **Model** view:
- `company_metrics[company_id]` isn't needed as a relationship for this
  dashboard (transactions aren't tied to a specific portfolio company in
  this dataset — they're market reference data), so no relationship is
  required between the three tables. Each visual pulls from one table.

## 4. KPI Cards (page 1 — Executive Overview)

Add **Card** visuals bound to a selected company (use a **Slicer** on
`company_metrics[name]` first, then these cards will react to the
selection):
- Revenue → `Sum of revenue_musd`
- EBITDA → `Sum of ebitda_musd`
- Market Cap → `Sum of market_cap_musd`
- Enterprise Value → `Sum of enterprise_value_musd`
- EV/Revenue → `Sum of ev_revenue`
- EV/EBITDA → `Sum of ev_ebitda`

From `transaction_summary_by_industry`:
- Median EV/Revenue (precedent deals) → `median_ev_revenue`
- Median EV/EBITDA (precedent deals) → `median_ev_ebitda`

## 5. Visualizations

- **Bar chart** — Revenue by company (`company_metrics`, axis = `name`,
  value = `revenue_musd`)
- **Bar chart** — EBITDA margin by company (`ebitda_margin_pct`)
- **Scatter chart** — Peer comparison: X = `revenue_musd`, Y = `ev_ebitda`,
  size = `market_cap_musd`, legend = `name` (this mirrors the "comps
  positioning" view from the web app)
- **Clustered bar** — EV/Revenue and EV/EBITDA by company, side by side
- **Table or bar chart** — M&A deal value by acquirer/target, from
  `transactions[deal_value_musd]`
- **Column chart** — Deal count and median multiples by industry, from
  `transaction_summary_by_industry`

## 6. Refreshing data

Power BI Desktop → **Home** → **Refresh** re-reads the CSVs in
`powerbi/data/`. There's no live connection or credential involved — it's
just re-reading files, which is why this stays ₹0 and needs no gateway
setup for local use.

## 7. Publishing (optional, still free)

Power BI has a free individual tier for publishing to app.powerbi.com if
you want a shareable link for your portfolio — File → Publish. This is
optional and not required to demo the project.
