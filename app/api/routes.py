import json
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.topic_request import TopicRequest
from app.services.ai_service import generate_keywords, AIQuotaError
from app.services.news_discovery import discover_news
from app.services.news_postprocess import dedupe_articles, rank_and_limit
from app.services.news_enrich import enrich_articles_with_text
from app.services.summary_service import summarize_topic
from app.services.report_service import build_pdf_report

router = APIRouter()


def _parse_keywords_json(keywords_json: str) -> dict:
    start = keywords_json.find("{")
    end = keywords_json.rfind("}")
    clean = keywords_json[start:end + 1] if start != -1 and end != -1 else keywords_json
    return json.loads(clean)


def _get_queries_and_keywords(req: TopicRequest):
    if getattr(req, "queries_used", None) and len(req.queries_used) > 0:
        return req.queries_used, None

    keywords_json = generate_keywords(req.topic)
    keywords = _parse_keywords_json(keywords_json)

    queries = keywords.get("search_queries") or keywords.get("queries")
    if not queries:
        raise ValueError("Gemini no devolvió 'search_queries' (o 'queries') en el JSON.")

    return queries, keywords


@router.post("/analyze-topic")
def analyze_topic(req: TopicRequest):
    try:
        queries, keywords = _get_queries_and_keywords(req)
    except AIQuotaError:
        raise HTTPException(
            status_code=503,
            detail="Gemini quota/billing error. Pasá queries_used para modo barato, o arreglá tu plan."
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="No se pudo parsear el JSON devuelto por Gemini."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparando queries: {e}")

    try:
        news_raw = discover_news(queries, max_per_query=15, days_back=req.days_back)
        news_deduped = dedupe_articles(news_raw)
        news_ranked = rank_and_limit(
            news_deduped,
            req.topic,
            (keywords or {}).get("keywords_primary", []),
            limit=40
        )

        max_enrich = getattr(req, "max_articles_enrich", 25)
        news_enriched = enrich_articles_with_text(news_ranked, max_articles=max_enrich)

        summary = summarize_topic(req.topic, news_enriched, req.days_back)
        report_path = build_pdf_report(req.topic, req.days_back, summary)

        report_filename = os.path.basename(report_path)
        download_url = f"/download-report?filename={report_filename}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando noticias: {e}")

    return {
        "topic": req.topic,
        "days_back": req.days_back,
        "queries_used": queries,
        "articles_found_raw": len(news_raw),
        "articles_found_deduped": len(news_deduped),
        "articles_found_final": len(news_enriched),
        "articles": news_enriched,
        "keywords_plan": keywords,
        "summary": summary,
        "report_path": report_path,
        "download_url": download_url,
    }


@router.get("/download-report")
def download_report(filename: str = Query(..., description="Nombre del archivo PDF")):
    file_path = os.path.join("generated_reports", filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )