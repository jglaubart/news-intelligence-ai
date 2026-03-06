import os
from dotenv import load_dotenv
from google import genai


load_dotenv(dotenv_path=".env")

# Modelo barato:
MODEL = "models/gemini-flash-lite-latest"


class AIQuotaError(Exception):
    pass


def _get_client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Falta GEMINI_API_KEY en .env")
    return genai.Client(api_key=key)


client = _get_client()


def generate_keywords(topic: str) -> str:
    """
    Devuelve un JSON (string) con:
    {
      "keywords_primary": [...],
      "keywords_secondary": [...],
      "search_queries": [...]
    }
    """
    prompt = f"""
Devolveme SOLO un JSON válido (sin markdown) con este formato:

{{
  "keywords_primary": ["..."],
  "keywords_secondary": ["..."],
  "search_queries": ["..."]
}}

Tema: {topic}

Reglas:
- keywords_primary: 8 a 15
- keywords_secondary: 10 a 25
- search_queries: 6 a 12, en español, estilo query de Google, SIN signos raros.
""".strip()

    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        # google-genai devuelve texto en resp.text
        return resp.text or ""
    except Exception as e:
        # si querés, acá podés detectar 429 específicamente mirando str(e)
        msg = str(e)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            raise AIQuotaError(msg)
        raise