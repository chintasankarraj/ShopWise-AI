# ShopWise AI

AI-assisted buying-decision tool for Amazon smartphones and laptops — paste a product URL and get a rule-based score, an AI-generated summary, real customer-review analysis, and verified alternatives, all in one place.

## Demo

No live deployment is currently linked in this repository. `render.yaml` defines a Render Blueprint for the backend, and the frontend is intended for Vercel, but no deployed URL is committed anywhere in the codebase. Add one here once a live instance exists.

## Screenshots

_No screenshots currently exist in this repository — `frontend/public/` only contains the default Next.js starter icons. Add real screenshots of the landing page, the loading state, and a full analysis result here (e.g. under `docs/screenshots/`) before publishing this README publicly._

---

## The problem

Amazon product listings bury the information a buyer actually needs — the real processor behind a vague "Others" spec field, whether the reviews are genuine or absent, whether a competing model is a better deal — inside walls of marketing copy and inconsistent structured data. Comparing two listings by hand means opening a dozen tabs and reading past the noise every time.

## How ShopWise works

Paste an Amazon smartphone or laptop URL. ShopWise extracts the listing's real specifications, scores it against a transparent, rule-based model tuned specifically for that product category, reads whatever genuine customer reviews are available, and — when its AI provider is available — writes a plain-English summary and looks for currently-purchasable alternatives worth considering instead. Every one of these steps is designed to degrade honestly: if a spec is missing, a review can't be found, or the AI call fails, ShopWise says so rather than guessing.

## V1 features

- **Product extraction** from a real Amazon listing: title, brand, price, rating, review count, image, availability, and full specifications — normalized and de-duplicated for display
- **Automatic category detection** (smartphone vs. laptop vs. other)
- **Rule-based scoring engine** producing a 0–100 score and a **BUY / CONSIDER / AVOID** verdict with human-readable reasons, computed independently of any AI provider
- **AI-generated executive summary and pros/cons** (Gemini) when available, with an explicit, non-fabricating fallback when it isn't
- **Review intelligence** — sentiment, top pros/cons, and common complaints derived from real scraped review text (never from the star rating alone)
- **Verified alternatives** — AI-discovered candidate products, each independently re-checked against its own live Amazon listing before being shown; never shown if unverifiable
- **Results dashboard** with sticky section navigation, a live-feeling loading state (elapsed timer, rotating status messages), and honest empty states throughout
- Responsive layout, tested at desktop (1440px) and mobile (390px) widths

## Supported products — V1 scope

**ShopWise V1 supports Amazon smartphones and laptops only.** This is enforced in the product itself — the landing page states it directly, and only these two categories receive tuned scoring logic. The category detector can technically recognize a few other product types (tablets, headphones, TVs, cameras, smartwatches), but they fall through to a minimal generic scorer and are **not** a supported use case. Other online retailers (Flipkart, eBay, etc.) are not supported.

The URL validator technically accepts several regional Amazon domains (`amazon.in`, `.com`, `.co.uk`, `.de`, `.ca`, `.com.au`, plus `amzn.in`/`amzn.to` short links) as an SSRF safeguard, but every stage of this project — extraction, scoring, and testing — has been built and verified exclusively against **amazon.in**. Treat other Amazon regions as untested.

## Scoring & recommendation

Scoring is entirely rule-based (no LLM involved) and fully deterministic — the same input specifications always produce the same score. Each category has its own weighted dimensions:

**Smartphone** (sums to 100): Performance 25 · Display 20 · Battery 15 · Camera 10 · RAM + Storage 10 · Charging 10 · Durability 5 · Connectivity 5

**Laptop** (capped at 100): Processor 30 · RAM 20 · Display 18 · GPU up to 12 · Storage 15 · Battery 10

The final score maps to a verdict:

| Score | Verdict |
|---|---|
| ≥ 80 | **BUY** |
| 60–79 | **CONSIDER** |
| < 60 | **AVOID** |

Every point awarded comes with a plain-English reason ("High Performance Processor", "Good Battery", etc.), so the verdict is always explainable. When a structured spec field is missing or a known non-answer (Amazon itself sometimes literally states "Unknown" or "Others"), ShopWise falls back to parsing the product title for the same information — and if neither source has real evidence, that dimension contributes nothing rather than guessing.

## AI-generated insights — what's actually AI, and what isn't

This distinction matters, so it's stated explicitly:

- **The score and verdict are never AI-generated.** They come entirely from the rule-based engine above.
- **The executive summary, pros/cons, and review sentiment analysis** are generated by **Google Gemini** (`gemini-3.5-flash`), grounded with a small retrieval-augmented-generation (RAG) knowledge base (ChromaDB + Gemini embeddings) and, when available, real scraped customer review text.
- **When Gemini is unavailable** — quota exhaustion, timeout, or any other API failure — ShopWise automatically falls back to a **deterministic, template-based summary** built from the rule-based score and reasons. This fallback never invents review sentiment, pros, or cons that aren't already known; it's clearly a lesser experience than the AI path, and the project treats that honestly rather than hiding it.
- **Alternative products** are discovered via Gemini with Google Search grounding first, with a free DuckDuckGo web-search fallback if that fails. Every candidate — from either source — is independently re-verified against its own real Amazon listing before it's ever shown; nothing is shown as "available" unless that was actually confirmed.

## System architecture / pipeline

```
Amazon product URL
      │
      ▼
1. Extract product           product_extractor.py (direct scrape)
                              → falls back to ScraperAPI's Amazon
                                Product API if Amazon blocks/redirects
      │
      ▼
2. Detect category           category_detector.py
      │
      ▼
3. Score & verdict           recommendation_agent.py  (rule-based, no AI)
      │
      ▼
4. Find alternatives         alternative_agent.py
                              Gemini + Google Search → verify →
                              DuckDuckGo fallback → verify
                              (runs exactly once per request)
      │
      ▼
5. Generate AI insights      insights_agent.py
                              Gemini + RAG + real review text
                              → deterministic fallback on any failure
      │
      ▼
6. Unified JSON response  →  Next.js results dashboard
```

## Tech stack

**Frontend** — Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind CSS v4, Framer Motion, `react-circular-progressbar` + `react-countup` (score gauge), `sonner` (toasts), `lucide-react` (icons)

**Backend** — FastAPI, Uvicorn, Pydantic, BeautifulSoup4 + lxml (HTML parsing), `google-genai` (Gemini SDK), ChromaDB (RAG vector store)

**External services** — Amazon.in (primary extraction target), ScraperAPI (fallback product provider), Google Gemini API (insights, alternatives, embeddings), DuckDuckGo HTML search (free alternatives fallback)

## Project structure

```
ShopWise-AI/
├── render.yaml                    # Render Blueprint (backend deployment)
├── frontend/                      # Next.js app
│   ├── .env.example
│   └── src/
│       ├── app/                   # layout, root page, global styles
│       ├── components/            # Dashboard + 13 result-section cards
│       ├── services/api.ts        # backend API client
│       └── types/product.ts
└── backend/                       # FastAPI app
    ├── requirements.txt
    ├── .env.example
    ├── test_*.py                  # manual/offline verification scripts
    └── app/
        ├── main.py                # FastAPI app, CORS
        ├── routes/analyze.py      # POST /analyze — the entire pipeline
        ├── schemas/product.py     # request/response models, URL validation
        ├── services/              # extraction, category detection, parsing
        ├── agents/                # recommendation, insights, alternatives
        └── rag/                   # ChromaDB + Gemini embeddings, knowledge base
```

## Local setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m app.rag.ingest        # builds the ChromaDB vector store
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. By default the frontend talks to a backend at `http://localhost:8000`.

## Environment variables

Copy each `.env.example` to `.env` and fill in real values — **never commit the `.env` files themselves.**

**`backend/.env`** (from `backend/.env.example`):

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key — powers AI insights and alternatives discovery |
| `SCRAPERAPI_KEY` | ScraperAPI key — fallback Amazon product provider when direct scraping is blocked |
| `FRONTEND_URL` | Allowed CORS origin(s) for the deployed frontend, comma-separated. Defaults to `http://localhost:3000` |

**`frontend/.env` **(from `frontend/.env.example`):

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the deployed FastAPI backend. Falls back to `http://localhost:8000` if unset |

## Testing & verification

The backend has **23 test scripts under `backend/test_*.py`**, but this is not a `pytest`-style automated suite — none of them use `pytest`-discoverable test functions. They fall into two groups:

- **15 offline, assertion-based scripts** exercise scoring, extraction, and parsing logic with no network calls, and can be run directly (`python test_score.py`, etc.) — all currently pass.
- **8 scripts require live external services** (Gemini, DuckDuckGo, ScraperAPI, or live Amazon pages) and are meant for manual verification, not CI.

There is currently no CI pipeline configured in this repository. Frontend correctness is checked via `npx tsc --noEmit` and `npm run build`, both of which are clean on the current codebase.

## Known limitations

- **Gemini's free-tier quota (20 requests/day) is easily exhausted** under normal use — every request makes two Gemini calls (insights + alternatives), so this can trigger after roughly 10 analyses in a day. When it does, ShopWise falls back to the deterministic, honest behavior described above rather than failing — but the AI-generated experience won't be what most users see without a paid plan.
- **The DuckDuckGo alternatives fallback has been unreachable** (connection timeout) from every environment this project has been tested in so far. Its parsing logic exists and is unit-tested, but has not been verified against a live response.
- **Many real Amazon listings — especially newly launched products — carry very few customer reviews** (sometimes single digits), which limits how often genuine review-based insights are available. This is a property of the listings themselves, not a scraping failure.
- **No historical price tracking.** `expected_sale_price` is always reported as unavailable; there is no price-history feature.
- **RAG context is smartphone-only.** The retrieval knowledge base currently has no equivalent laptop-focused document.
- **No automated CI test suite**, as noted above.

## Future roadmap

_Not implemented — listed here only as potential future work, not current functionality._

- Automated CI test suite (wrapping the existing offline scripts in real `pytest` tests)
- Support for additional product categories beyond smartphones and laptops
- Real historical price tracking
- Re-verifying and fixing the DuckDuckGo alternatives fallback once reachable
- Laptop-specific RAG knowledge base content
- A deployed live demo
