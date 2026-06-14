# Smart Automation Lab — Reference Information

A self-contained reference web app for Microsoft AI, licensing, product roadmap, and agent stack information. Built as a single HTML file with no framework or build step, deployed to Azure Static Web Apps.

---

## Features

### Microsoft Licensing
SKU and pricing reference cards for the Microsoft products most relevant to Power Platform and AI automation projects. Organised by product family with feature breakdowns, pricing tiers, and licence comparisons.

**Products covered:**
- Power Automate (Free, Premium, Process, Hosted Process, Per Flow)
- Power Apps (Developer, Per App, Per User, Pay-as-you-go)
- Copilot Studio (per tenant and per session)
- M365 Copilot (E3/E5 add-on, Frontline)
- Agent 365
- Microsoft 365 E7
- Dynamics 365 Business Central, Customer Engagement, Sales Enterprise

### Copilot Usage Statistics
Visual dashboard showing adoption metrics, usage patterns, and ROI indicators for Microsoft Copilot deployments.

### Product Roadmap
Interactive horizontal timeline of upcoming features across four Microsoft AI products — filterable by product and status (Rolling Out / In Development).

**Data sources (refreshed automatically every 6 hours via GitHub Actions):**
| Source | Products |
|--------|----------|
| [Microsoft 365 Release Communications API](https://www.microsoft.com/releasecommunications/api/v2/m365) | M365 Copilot, Copilot Studio, Power Automate |
| [Power Platform 2026 Wave 1 — Power Apps](https://learn.microsoft.com/en-us/power-platform/release-plan/2026wave1/power-apps/planned-features) | Power Apps |
| [Power Platform 2026 Wave 1 — Copilot Studio](https://learn.microsoft.com/en-us/power-platform/release-plan/2026wave1/microsoft-copilot-studio/planned-features) | Copilot Studio (supplemental) |

Roadmap items are filtered to:
- Status: **Rolling Out** or **In Development** only
- Platform: **Desktop** or **Web**
- Date window: −2 months to +4 months from today

### AI Agent Stack Comparison
Side-by-side comparison of the four Microsoft AI agent tools across eight dimensions: Primary Purpose, Best For, How It Works, Where It Operates, Level of Autonomy, Integrations, Security & Governance, and In Simple Terms.

**Products compared:** M365 Copilot · Copilot Cowork · Microsoft Scout · Copilot Studio

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML / CSS / JavaScript (no framework) |
| Icons | [Tabler Icons](https://tabler.io/icons) (CDN) |
| Hosting | Azure Static Web Apps |
| CI/CD | GitHub Actions (OIDC auth) |
| Data pipeline | Python 3 (`parse_roadmap.py`) |

---

## Project Structure

```
├── index.html                  # Entire application (single file)
├── parse_roadmap.py            # Fetches & parses roadmap data
├── roadmap-data.json           # Processed roadmap data (auto-updated)
├── serve.json                  # Local dev server config (npx serve)
└── .github/
    └── workflows/
        ├── azure-static-web-apps-*.yml   # Azure SWA deploy workflow
        └── update-roadmap.yml            # Roadmap auto-refresh (every 6 h)
```

> `roadmap.csv` is downloaded during CI runs and is not committed to the repository.

---

## Local Development

Requires Node.js (for `serve`) and Python 3.

```bash
# Start local dev server on port 3400
npx serve -p 3400 .
```

Open [http://localhost:3400/index.html](http://localhost:3400/index.html).

To manually refresh the roadmap data locally:

```bash
# Download latest CSV from Microsoft
curl -fsSL "https://www.microsoft.com/releasecommunications/api/v2/m365?responseFormat=csv" -o roadmap.csv

# Parse and write roadmap-data.json
python parse_roadmap.py
```

---

## Roadmap Data Pipeline

The roadmap data pipeline runs automatically via GitHub Actions every 6 hours (and can be triggered manually from the Actions tab).

```
Microsoft M365 CSV API  ──┐
Power Apps release plan ──┤──▶ parse_roadmap.py ──▶ roadmap-data.json ──▶ committed to main
Copilot Studio rel. plan ─┘
```

`parse_roadmap.py` handles:
- CSV parsing with full RFC 4180 support (quoted fields, embedded commas)
- HTML table scraping from Microsoft Learn release plan pages
- Priority-based product matching (Copilot Studio takes precedence over M365 Copilot on dual-tagged items)
- Date parsing for `"June CY2026"`, `"Jul 2026"`, and ISO `YYYY-MM-DD` formats
- Status inference for Power Platform items (future GA date → In Development; current month → Rolling Out)
- Deduplication across sources

The browser Refresh button simply fetches `/roadmap-data.json` from the same origin — no CORS issues.

---

## Deployment

Deployed automatically to Azure Static Web Apps on every push to `main` via the included GitHub Actions workflow. The workflow uses OIDC authentication (no stored secrets) and sets `skip_app_build: true` since there is no build step.

```
push to main ──▶ GitHub Actions ──▶ Azure Static Web Apps
```

The roadmap auto-update workflow commits `roadmap-data.json` with `[skip ci]` in the commit message to avoid triggering a re-deploy on data-only updates.

---

## Theming

The app supports light and dark modes, toggled via the button in the top-right header. The theme is implemented entirely with CSS custom properties (`var(--bg-page)`, `var(--text-primary)`, etc.) on the `html[data-theme]` attribute — no JavaScript frameworks required.
