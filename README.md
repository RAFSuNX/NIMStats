<div align="center">

[![NIMStats Banner](https://capsule-render.vercel.app/api?type=waving&color=76b900&height=220&section=header&text=NIMStats&fontSize=90&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Real-Time%20NVIDIA%20NIM%20Benchmark%20Dashboard&descSize=22&descAlignY=60&descAlign=50)](https://nimstats.maurodruwel.be/)

[![CI](https://github.com/MauroDruwel/NIMStats/actions/workflows/benchmark.yml/badge.svg)](https://github.com/MauroDruwel/NIMStats/actions)
[![Live Dashboard](https://img.shields.io/badge/🌐%20live-nimstats.maurodruwel.be-76b900?style=flat-square)](https://nimstats.maurodruwel.be/)
[![Models](https://img.shields.io/badge/models-20%2B-blue?style=flat-square)](https://build.nvidia.com/models)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/MauroDruwel/NIMStats/pulls)
[![Stars](https://img.shields.io/github/stars/MauroDruwel/NIMStats?style=flat-square&color=gold)](https://github.com/MauroDruwel/NIMStats/stargazers)

<br/>

> **Community-driven benchmarking of 20+ NVIDIA NIM models — fully automated, zero infra cost, self-hostable in minutes.**

<br/>

**[🚀 View Live Dashboard](https://nimstats.maurodruwel.be/) · [📖 Docs](#-quick-start) · [🤝 Contribute](#-contributing) · [💬 Discussions](https://github.com/MauroDruwel/NIMStats/discussions)**

</div>

---

## ✨ What is NIMStats?

NIMStats automatically benchmarks **20+ NVIDIA NIM models** every hour using GitHub Actions and publishes the results to a beautiful, interactive dashboard. No servers, no subscriptions — just fork, add your API key, and go.

<div align="center">

| 🏎️ Hourly Benchmarks | 📊 Interactive Charts | 🔁 Zero Infrastructure | 🌍 Fully Open-Source |
|:---:|:---:|:---:|:---:|
| Automatic via GitHub Actions | Response time, throughput & trends | Static site + free CI/CD | Fork and self-host in minutes |

</div>

---

## ⚡ Quick Start

> Get your own benchmarking dashboard running in under 5 minutes.

### 1. Fork & Clone

```bash
git clone https://github.com/MauroDruwel/NIMStats.git
cd NIMStats
```

### 2. Get a Free API Key

Visit **[build.nvidia.com](https://build.nvidia.com)** → Create a free account → Copy your API key.

### 3. Add the Secret

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `NIM_API_KEY` | Your NVIDIA NIM API key |

### 4. Deploy the Dashboard

| Platform | Steps |
|----------|-------|
| **Cloudflare Pages** | Connect repo in [Cloudflare Pages](https://pages.cloudflare.com/) |
| **GitHub Pages** | Settings → Pages → Deploy from `main` |
| **Netlify / Vercel** | Connect repo for instant auto-deploy |

### 5. Run Your First Benchmark

**Actions → Benchmark NVIDIA NIM Models → Run workflow**

That's it — your dashboard auto-refreshes every hour. ✨

---

## 📊 Dashboard Features

<div align="center">

| Feature | Details |
|---------|---------|
| **KPI Cards** | Total runs, success rate, fastest model, best throughput |
| **Analytics** | Consistency scores, median latency, per-model stats |
| **Charts** | Response times, throughput distribution, scatter plots, trends |
| **Results Table** | Sort by speed, throughput, or name · click to read full response |
| **History** | Full audit trail with trend visualizations |
| **Live Status** | Online/offline indicator · auto-refresh every 30 s |

</div>

---

## 🤖 Benchmarked Models

<details>
<summary><b>20 models across 8 providers — click to expand</b></summary>

<br/>

| Provider | Model | Highlight |
|----------|-------|-----------|
| **DeepSeek** | `deepseek-ai/deepseek-v4-flash` | Fast MoE, optimized for speed |
| **DeepSeek** | `deepseek-ai/deepseek-v4-pro` | Professional-grade reasoning |
| **DeepSeek** | `deepseek-ai/deepseek-v3.2` | Latest with improved reasoning |
| **Z-AI** | `z-ai/glm-5.1` | Superior code understanding |
| **Z-AI** | `z-ai/glm-4.7` | Strong mathematical capabilities |
| **MiniMax** | `minimax/minimax-m2.7` | Efficient inference model |
| **MiniMax** | `minimax/minimax-m2.5` | Previous generation MiniMax |
| **NVIDIA** | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA's 120B flagship |
| **NVIDIA** | `nvidia/nemotron-4-340b-instruct` | 340B instruction-tuned |
| **NVIDIA** | `nvidia/llama-3.1-nemotron-ultra-253b-v1` | Ultra-large 253B model |
| **Moonshot** | `moonshotai/kimi-k2.5` | Context-optimized model |
| **Moonshot** | `moonshotai/kimi-k2-instruct` | Instruction-tuned Kimi |
| **GPT-OSS** | `gpt-oss/gpt-oss-120b` | Open-source 120B |
| **Google** | `google/gemma-4-31b-it` | Lightweight edge inference |
| **Qwen** | `qwen/qwen3-coder-480b-a35b-instruct` | Specialized coding (480B MoE) |
| **Qwen** | `qwen/qwen2.5-coder-32b-instruct` | Lightweight Qwen coder |
| **Qwen** | `qwen/qwen3.5-397b-a17b` | Flagship Qwen (397B) |
| **Mistral** | `mistralai/devstral-2-123b-instruct-2512` | Developer-focused (123B) |
| **Mistral** | `mistralai/mistral-large-3-675b-instruct-2512` | Largest Mistral (675B) |
| **Meta** | `meta/llama-3.1-405b-instruct` | Meta's largest Llama (405B) |

</details>

---

## 🏗️ How It Works

```
┌──────────────────────── GitHub Actions (every hour) ────────────────────────┐
│                                                                               │
│   ┌─────────────────────┐        ┌─────────────────────┐                    │
│   │  Job 1 — Group A    │        │  Job 2 — Group B    │  (run in parallel) │
│   │  10 NIM models      │        │  10 NIM models      │                    │
│   └──────────┬──────────┘        └──────────┬──────────┘                    │
│              └──────────────┬───────────────┘                               │
│                    ┌────────▼────────┐                                       │
│                    │  Merge + commit │  → history.json updated in repo       │
│                    └─────────────────┘                                       │
└───────────────────────────────────────────────────────────────────────────── ┘
                                     │
                          ┌──────────▼──────────┐
                          │  Static Dashboard   │  auto-refresh every 30 s
                          │  (Pages / Netlify)  │
                          └─────────────────────┘
```

**Parallel jobs = ~50% faster benchmarks** ⚡

---

## 🛠️ Customization

<details>
<summary><b>Change the benchmark prompt</b></summary>

Edit `PROMPT` in `scripts/test_models.py`:
```python
PROMPT = "Your custom prompt here"
```
</details>

<details>
<summary><b>Add or remove models</b></summary>

Edit the model arrays in `scripts/test_models.py`:
```python
GROUP1_MODELS = [
    "your/custom-model",
    # ...
]
```
</details>

<details>
<summary><b>Change the schedule</b></summary>

Edit `.github/workflows/benchmark.yml`:
```yaml
- cron: '0 */6 * * *'  # Every 6 hours instead of every hour
```
</details>

<details>
<summary><b>Run locally</b></summary>

```bash
# Serve the dashboard
python3 -m http.server 8000
# Open http://localhost:8000

# Run benchmarks manually (requires NIM_API_KEY env var)
export NIM_API_KEY=your_key_here
python3 scripts/test_models.py
```
</details>

---

## 📦 Data Format

`history.json` is the single source of truth persisted in the repo. `scripts/results.json` is a temporary per-job artifact only.

```jsonc
{
  "runs": [{
    "timestamp": "2026-04-28T06:49:00Z",
    "prompt": "...",
    "models": [{
      "model": "deepseek-ai/deepseek-v4-flash",
      "success": true,
      "responseTime": 2500,       // ms — request to response
      "tokensGenerated": 150,
      "totalTokens": 170,
      "throughput": 60.0,         // tokens/sec
      "response": "..."
    }],
    "summary": {
      "successCount": 20,
      "totalModels": 20,
      "fastestModel": "...",
      "fastestTime": 2500
    }
  }]
}
```

**Benchmark parameters:** `temperature: 0.7` · `top_p: 0.9` · `max_tokens: 500` · OpenAI-compatible API

---

## 🤝 Contributing

Contributions are what make the open-source community amazing. Any contribution you make is **greatly appreciated**!

1. **Fork** the repository
2. Create your feature branch: `git checkout -b feat/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feat/amazing-feature`
5. Open a **Pull Request**

**Ideas for contributions:**
- 🆕 Add new NIM models to the benchmark list
- 📊 New chart types or dashboard widgets
- 🌐 Internationalization / translations
- 🐛 Bug fixes and performance improvements
- 📖 Improve documentation

Please read through open [Issues](https://github.com/MauroDruwel/NIMStats/issues) before starting — someone might already be working on it!

---

## 🔗 Resources

- [NVIDIA NIM API Documentation](https://docs.api.nvidia.com/nim/)
- [NVIDIA Model Catalog](https://build.nvidia.com/models)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

Made with ❤️ for the ML community · [⭐ Star this repo](https://github.com/MauroDruwel/NIMStats) if you find it useful!

[![footer](https://capsule-render.vercel.app/api?type=waving&color=76b900&height=100&section=footer)](https://nimstats.maurodruwel.be/)

</div>
