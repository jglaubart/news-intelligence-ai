import json
import os
from google import genai

MODEL = "models/gemini-flash-lite-latest"


def summarize_topic(topic: str, articles: list[dict], days_back: int) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Nos quedamos solo con artículos útiles
    useful_articles = []
    for a in articles:
        content = (a.get("content", "") or "").strip()

        useful_articles.append(
            {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "published": a.get("published", ""),
                "link": a.get("link", ""),
                "score": a.get("score", 0),
                "content": content[:1800],
            }
        )

    prompt = f"""
Sos un analista profesional de noticias económicas.

Tema del informe: {topic}
Ventana temporal: últimos {days_back} días.

Tu tarea es producir un informe ejecutivo profesional, claro y breve.
No escribas texto innecesario ni introducciones largas.
Debe ser entendible, estructurado y apto para convertirse en un PDF profesional.

Devolvé ÚNICAMENTE un JSON válido con esta estructura exacta:

{{
  "executive_summary": "string",
  "key_points": ["string", "string", "string"],
  "repeated_trends": ["string", "string", "string"],
  "relevant_articles": [
    {{
      "title": "string",
      "source": "string",
      "published": "string",
      "link": "string",
      "why_relevant": "string"
    }}
  ]
}}

Reglas:
- executive_summary: 1 solo bloque, profesional, concreto, entre 8 y 12 líneas aprox.
- key_points: entre 4 y 6 bullets.
- repeated_trends: entre 3 y 5 bullets.
- relevant_articles: exactamente 5 artículos.
- Elegí los artículos más relevantes para entender el tema central, no derivados laterales.
- Priorizá artículos realmente vinculados al tema principal.
- Si hay ruido temático, descartalo.
- No pongas markdown.
- No pongas texto fuera del JSON.

Evidencia disponible:
{json.dumps(useful_articles, ensure_ascii=False)}
"""

    resp = client.models.generate_content(model=MODEL, contents=prompt)
    text = resp.text.strip()

    start = text.find("{")
    end = text.rfind("}")
    clean = text[start:end + 1] if start != -1 and end != -1 else text

    return json.loads(clean)