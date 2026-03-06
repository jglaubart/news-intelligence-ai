from dotenv import load_dotenv
load_dotenv()

from app.services.cache import init_cache
init_cache()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as news_router

app = FastAPI()

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

app.include_router(news_router)

@app.get("/")
def home():
    return FileResponse("frontend/news_report_ui.html")