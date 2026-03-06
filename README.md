# AI News Intelligence Report Generator

AI-powered system that discovers news about a topic, analyzes them using a language model, and generates a professional PDF intelligence report.

The application automatically collects recent news, extracts article content, detects key narratives and trends, and produces an executive-style report ready to download.

---

# Live Demo

If deployed, you can try the application here:

https://your-project-url.vercel.app

---

# Features

- Discover news using Google News RSS
- Scrape article content automatically
- Filter articles by time window
- Deduplicate and clean news results
- AI-powered analysis of news narratives
- Extraction of key events and trends
- Executive summary generation
- Professional PDF report generation
- Simple web interface for running analysis
- Local article caching system

---

# Example Workflow

1. Enter a topic in the UI
2. Choose the time window for the analysis
3. Generate the news analysis
4. Review the AI-generated summary and insights
5. Download a professional PDF report

---

# Architecture

The project is organized into modular services:

| Service | Responsibility |
|------|------|
| news_discovery | Discover news articles using Google News RSS |
| article_scraper | Extract article content from websites |
| article_enrichment | Attach scraped content to article metadata |
| news_postprocess | Deduplicate and clean article sets |
| time_filter | Filter articles by time window |
| summary_service | Generate AI analysis of the news set |
| report_service | Generate the final PDF intelligence report |
| cache | Store article content locally to avoid re-scraping |
| ai_service | Wrapper around the Gemini AI model |

---

# Project Structure
ai-news-report
│
├── app
│ ├── models
│ │
│ ├── services
│ │ ├── ai_service.py
│ │ ├── article_enrichment.py
│ │ ├── article_scraper.py
│ │ ├── cache.py
│ │ ├── news_discovery.py
│ │ ├── news_enrich.py
│ │ ├── news_postprocess.py
│ │ ├── report_service.py
│ │ ├── summary_service.py
│ │ └── time_filter.py
│ │
│ └── main.py
│
├── frontend
│ └── news_report_ui.html
│
├── generated_reports
│
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example


---

# Technology Stack

Backend
- Python
- FastAPI

AI
- Google Gemini API

Data Processing
- BeautifulSoup
- Feedparser
- Requests

Reporting
- ReportLab (PDF generation)

Frontend
- HTML
- CSS
- JavaScript

Storage
- SQLite (article caching)

---

# Installation

Clone the repository:
git clone https://github.com/jglaubart/ai-news-report.git
cd ai-news-report

Install dependencies:
pip install -r requirements.txt

Create environment variables:
cp .env.example .env

Add your API key inside `.env`:
GEMINI_API_KEY=your_api_key_here

Run the server:
uvicorn app.main:app --reload

Open the application:
http://127.0.0.1:8000


---

# API Endpoint

Generate analysis:
POST /analyze-topic


Example request:
{
"topic": "inflación argentina",
"days_back": 30
}


Response includes:

- analyzed articles
- AI summary
- detected trends
- generated PDF report
- download link

---

# Example Use Cases

- Economic intelligence
- Media monitoring
- Policy tracking
- Market analysis
- Competitive intelligence
- Automated news briefings

---

# Future Improvements

- scheduled automated reports
- email delivery
- improved article extraction
- multi-language support
- vector search over articles
- advanced topic clustering
- dashboard analytics

---

# Security Notes

The following files are ignored from the repository:

- `.env`
- generated reports
- local database cache

Environment variables must be configured locally.

---

# License

MIT License

