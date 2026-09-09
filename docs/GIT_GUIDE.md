# Git / GitHub Setup Guide

## 1. Initialize the repo

```bash
cd mna-valuation-analyzer
git init
git add .
git commit -m "chore: initial project scaffold"
```

`.gitignore` already excludes `data/processed/` (the generated DuckDB file),
`frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `.env`, and
venv folders — nothing generated or secret gets committed.

## 2. Create the GitHub repo

```bash
gh repo create mna-valuation-analyzer --public --source=. --remote=origin
git push -u origin main
```
(Or create it manually on github.com and `git remote add origin <url>`.)

## 3. Branching strategy

Simple trunk-based flow, appropriate for a solo portfolio project:
- `main` — always working/demoable
- Feature branches: `feat/valuation-engine`, `feat/react-frontend`,
  `feat/powerbi-export`, etc. — merge back to `main` via PR (even solo, PRs
  give you a clean history and a place to write "what/why" for your own
  future reference or an interviewer skimming the repo)

```bash
git checkout -b feat/ai-analyst-tab
# ...work...
git add .
git commit -m "feat: add optional Ollama-backed AI analyst tab"
git push -u origin feat/ai-analyst-tab
gh pr create --fill
```

## 4. Commit message convention

Conventional Commits — readable history, and it's a real signal to
interviewers that you work the way teams do:

```
feat: add financial data ingestion
feat: implement comparable company similarity engine
feat: add trading comps + precedent transaction valuation engine
feat: build FastAPI backend with companies/comps/transactions/valuation routes
feat: build React frontend with comps and valuation range visualization
feat: add optional Ollama AI analyst layer
feat: add Power BI data export script
test: add pytest suite for financials, comps, valuation
docs: write README, Power BI guide, Git guide
chore: initial project scaffold
```

Prefixes: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.

## 5. Never commit

- `.env` (already gitignored — this project has no secrets today, but keep
  the habit for when you add the optional `OLLAMA_HOST` override or any
  future API key)
- `data/processed/mna.duckdb` (generated — anyone cloning the repo
  regenerates it with `python -m src.ingestion.load_data`)
- `frontend/node_modules/`, `frontend/dist/`

## 6. Suggested README badges (optional polish)

Once pushed, you can add a GitHub Actions badge if you set up CI (`pytest`
on push) — a natural next step beyond this project's current scope, worth
mentioning as a "future enhancement" in interviews even if you don't build
it now.
