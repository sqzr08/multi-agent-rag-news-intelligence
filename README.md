# 🤖 AI News Intelligence Agent

A multi-agent RAG pipeline that scrapes AI news daily, analyzes each article with structured LLM outputs, and generates a clean Markdown intelligence report.

Built with **LangGraph**, **Gemini 2.0 Flash**, **SerpAPI**.

---

## Architecture

```
SerpAPI (Google News)
        │
        ▼
┌───────────────┐
│   Retriever   │  Discover URLs → scrape full text → deduplicate by URL hash
│     Agent     │
└──────┬────────┘
       │  List[RawArticle]
       ▼
┌───────────────┐
│   Analyzer    │  Gemini extracts summary, topics, entities, sentiment,
│     Agent     │  and importance score — output enforced by Pydantic
└──────┬────────┘
       │  List[AnalyzedArticle]
       ▼
┌───────────────┐
│   Insights    │  Gemini synthesizes themes, emerging topics, key players,
│     Agent     │  and an executive summary across all articles
└──────┬────────┘
       │  InsightsOutput
       ▼
┌───────────────┐
│ Report Writer │  Assembles final Markdown report and saves to /reports
│     Agent     │
└───────────────┘
```

All agents share a typed `PipelineState` (LangGraph `TypedDict`). Every model in the pipeline is a Pydantic `BaseModel` — LLM outputs are enforced via `.with_structured_output()`, so there is no manual JSON parsing anywhere.

---

## Report Output

Each run produces `reports/ai_news_YYYY-MM-DD.md` with the following sections:

- **Executive Summary** — 3–5 sentence briefing for senior readers
- **Today's Core Themes** — key topics running across all articles
- **Top Stories** — up to 15 articles ranked by importance score, each with source, date, importance bar, sentiment, summary, topics, entities, and link
- **Signals** — emerging topics and key players today

---

## Project Structure

```
news-intelligence-agent/
├── agents/
│   ├── retriever.py       # SerpAPI discovery + trafilatura scraping
│   ├── analyzer.py        # Gemini structured analysis (Pydantic enforced)
│   ├── insights.py        # Gemini insight synthesis (Pydantic enforced)
│   └── report_writer.py   # Markdown report assembly and file output
├── graph/
│   ├── state.py           # All Pydantic models + PipelineState TypedDict
│   └── pipeline.py        # LangGraph StateGraph wiring all agents
├── scheduler/
│   └── runner.py          # APScheduler daily trigger
├── reports/               # Generated Markdown reports (auto-created)
├── config.py              # All settings, loaded from .env
├── main.py                # Entry point (run once or start scheduler)
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```


### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
GEMINI_API_KEY=your_gemini_api_key_here
SERPAPI_KEY=your_serpapi_key_here
```

Get your keys here:
- Gemini API key — [Google AI Studio](https://aistudio.google.com/)
- SerpAPI key — [serpapi.com](https://serpapi.com/)

### 3. Run

**Execute once immediately:**

```bash
python main.py --mode run
```

**Run on a daily schedule (default: 8:00 AM):**

```bash
python main.py --mode schedule
```

**Custom search query:**

```bash
python main.py --mode run --query "generative AI startups"
```

---

## Configuration

All settings live in `config.py` and can be overridden via `.env`:

| Setting | Default | Description |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model used for all LLM calls |
| `SERPAPI_MAX_RESULTS` | `20` | Max articles fetched per run |
| `SERPAPI_TIME_PERIOD` | `d` | News recency: `d` = past 24h, `w` = past week |
| `SCRAPE_TIMEOUT_SECONDS` | `15` | Per-article scrape timeout |
| `SCRAPE_MAX_RETRIES` | `2` | Retry attempts per article |
| `MIN_ARTICLE_LENGTH` | `200` | Minimum character count to keep an article |
| `SCHEDULE_HOUR` | `8` | Hour of day for scheduled run (24h) |
| `SCHEDULE_MINUTE` | `0` | Minute of hour for scheduled run |
| `REPORTS_DIR` | `./reports` | Directory where reports are saved |

---

## Data Models

All models are Pydantic `BaseModel`. LLM outputs in the Analyzer and Insights agents are enforced using LangChain's `.with_structured_output()` — the LLM response schema is derived directly from the Pydantic model, and the output is validated automatically before it reaches the next agent.

```
RawArticle          — output of Retriever (url, title, source, date, raw_text, url_hash)
ArticleAnalysis     — enforced LLM output (summary, topics, entities, sentiment, importance_score)
AnalyzedArticle     — merged metadata + analysis passed downstream
InsightsOutput      — enforced LLM output (todays_themes, emerging_topics, key_entities_today, executive_summary)
```

`Sentiment` is a `str` enum (`positive` | `neutral` | `negative`) validated at the model level.
`importance_score` is a `float` with `ge=0.0, le=1.0` constraints — the LLM cannot return a value outside this range.
