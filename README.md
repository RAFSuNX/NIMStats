# NIMStats - AI Model Benchmark Dashboard

A community-driven benchmarking dashboard for NVIDIA NIM and OpenRouter free models. Automated hourly benchmarks run via GitHub Actions and publish results to a static, interactive dashboard with zero infrastructure cost.

**Live dashboard:** [nimstats.maurodruwel.be](https://nimstats.maurodruwel.be/)

---

## What it does

NIMStats tests AI model API endpoints every hour and records response time, throughput, and reliability. Results are stored in a SQLite database committed to the repository and queried client-side via WebAssembly. No server required.

**Models tested:**
- 20 NVIDIA NIM models across providers including DeepSeek, Qwen, Mistral, Meta, Google, NVIDIA, and others
- All free-tier OpenRouter models, fetched dynamically at benchmark time

**Metrics collected per model per run:**
- Response time in milliseconds
- Tokens generated and total tokens
- Success or failure with error classification
- Throughput in tokens per second

---

## Dashboard tabs

**Overview** - Hero cards showing the current fastest model, highest throughput model, and most reliable model. Includes a NIM vs OpenRouter face-off panel, live status grid from the latest run, and success rate trend chart. All sections filterable by provider source.

**Leaderboard** - All models ranked by composite score. Sortable by any column. Filterable by source (NIM or OpenRouter) and by minimum run count to exclude models with insufficient data. Coverage-weighted scoring prevents models with a single lucky run from ranking highly.

**Explorer** - Deep dive into a single model. Shows response time history chart, error breakdown donut chart, availability heatmap, and a run history table with links to view raw responses.

**Timeline** - Full history of benchmark runs in reverse chronological order. Filter by last 24h, 48h, or 7d. Expand any run to see per-model results.

**Compare** - Head-to-head comparison of any two models. Overlay chart of response times, win-rate statistics, and side-by-side metric table.

---

## Quick start

Get your own benchmarking dashboard running in under 5 minutes.

### 1. Fork and clone

```bash
git clone https://github.com/your-username/NIMStats.git
cd NIMStats
```

### 2. Get API keys

- **NVIDIA NIM:** Create a free account at [build.nvidia.com](https://build.nvidia.com) and copy your API key.
- **OpenRouter:** Create a free account at [openrouter.ai](https://openrouter.ai) and copy your API key.

### 3. Add repository secrets

Go to your fork: **Settings - Secrets and variables - Actions - New repository secret**

| Secret name | Value |
|---|---|
| `NIM_API_KEY` | Your NVIDIA NIM API key |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

### 4. Deploy the dashboard

| Platform | Steps |
|---|---|
| GitHub Pages | Settings - Pages - Deploy from branch `main` |
| Cloudflare Pages | Connect repo at [pages.cloudflare.com](https://pages.cloudflare.com) |
| Netlify or Vercel | Connect repo for automatic deploys |

### 5. Run your first benchmark

Go to **Actions - Benchmark NIM + OpenRouter Models - Run workflow**

The dashboard auto-updates on each push. The workflow also runs automatically every hour.

---

## Architecture

```
GitHub Actions (hourly)
  |
  +-- Job: test_nim_group1     (NIM models 1-10)  --+
  |                                                   |
  +-- Job: test_nim_group2     (NIM models 11-20) --+-- merge_and_update --> history.db committed
  |                                                   |
  +-- Job: test_openrouter_group1 (OR free, half) --+
  |                                                   |
  +-- Job: test_openrouter_group2 (OR free, half) --+

Static site (GitHub Pages / Cloudflare / Netlify)
  Serves index.html + history.db
  Browser loads history.db via sql.js (WebAssembly)
  All queries run client-side
```

Four jobs run in parallel, cutting wall-clock time roughly in half. The merge job waits for all four, combines results into a single run entry, and commits `history.db`.

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/test_models.py` | Benchmarks NVIDIA NIM models. Reads `NIM_API_KEY` and `MODEL_GROUP` env vars. Writes `scripts/results.json`. |
| `scripts/test_openrouter.py` | Fetches all free OpenRouter models dynamically via the `/models` endpoint, then benchmarks them. Reads `OPENROUTER_API_KEY` and `MODEL_GROUP`. Writes `scripts/results.json`. |
| `scripts/merge_results.py` | Merges the four parallel result files into one run and writes to `history.db`. |
| `scripts/db_utils.py` | Shared SQLite utilities used by both benchmark and merge scripts. |

### Run locally

```bash
# Serve the dashboard
python3 -m http.server 8080
# Open http://localhost:8080

# Run NIM benchmarks (requires NIM_API_KEY)
export NIM_API_KEY=your_key_here
python3 scripts/test_models.py

# Run OpenRouter benchmarks (requires OPENROUTER_API_KEY)
export OPENROUTER_API_KEY=your_key_here
python3 scripts/test_openrouter.py

# Merge results manually into history.db
python3 scripts/merge_results.py
```

---

## Database schema

`history.db` is a SQLite file committed to the repository. The browser loads it via [sql.js](https://sql.js.org) and queries it entirely client-side.

```sql
CREATE TABLE runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL,
    prompt        TEXT,
    success_count INTEGER,
    total_models  INTEGER,
    fastest_model TEXT,
    fastest_time  INTEGER
);

CREATE TABLE model_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    model            TEXT    NOT NULL,
    success          INTEGER NOT NULL DEFAULT 0,
    error            TEXT,
    response_time    INTEGER,
    tokens_generated INTEGER,
    total_tokens     INTEGER,
    response         TEXT
);
```

Benchmark parameters: `temperature: 0.7`, `top_p: 0.9`, `max_tokens: 500`, OpenAI-compatible API format.

The database is capped at 720 runs (30 days of hourly benchmarks). Older runs are pruned automatically on each write.

---

## Customization

**Change the benchmark prompt** - Edit `PROMPT` in `scripts/test_models.py` and `scripts/test_openrouter.py`.

**Add or remove NIM models** - Edit `ALL_MODELS` in `scripts/test_models.py`.

**Change the benchmark schedule** - Edit the cron expression in `.github/workflows/benchmark.yml`:
```yaml
- cron: '0 */6 * * *'  # every 6 hours
```

**Disable OpenRouter benchmarks** - Remove the `test_openrouter_group1`, `test_openrouter_group2` jobs from the workflow and their entries in the `needs` list of `merge_and_update`.

---

## Scoring

Each model is assigned a composite score from 0 to 100:

- Uptime contributes 40 points
- Speed score (relative to fastest model) contributes up to 30 points
- Throughput score (relative to highest tok/s) contributes up to 30 points

A coverage weight is applied based on how many runs a model has participated in relative to the runs since it was first seen. Models with fewer than 5 runs are penalised to prevent newly-added models from ranking highly on limited data.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m 'feat: describe your change'`
4. Push and open a pull request

Ideas for contributions:
- Add new NIM or OpenRouter models
- New chart types or dashboard widgets
- Bug fixes and performance improvements
- Documentation improvements

---

## License

MIT License. See `LICENSE` for details.
