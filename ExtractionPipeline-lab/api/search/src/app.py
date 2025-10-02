from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables before importing settings
load_dotenv(".env", override=True)

from auth.apikey import verify_api_key
from auth.basic import verify_credentials
from config.env_config import settings
from config.logging_config import configure_logging
from src.controllers.add_content import image as add_image_controller
from src.controllers.add_content import video as add_video_controller
from src.controllers.get_embeddings import embeddings as get_embeddings_controller
from src.controllers.search_by import image as search_image_controller
from src.controllers.search_by import text as search_text_controller
from src.controllers.search_by_user_content import image as search_user_image_controller
from src.controllers.search_by_user_content import video as search_user_video_controller

log = configure_logging()

app = FastAPI(
    title=settings.api_name,
    description="A modular API for adding and searching visual and sematic video content.",
    version="1.2.0",
    docs_url=None,
    openapi_url=None,
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers from Controllers ---

app.include_router(
    add_image_controller.router,
    prefix="/add-content/image",
    tags=["Add Content"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    add_video_controller.router,
    prefix="/add-content/video",
    tags=["Add Content"],
    dependencies=[Depends(verify_api_key)],
)

# Search By Routes
app.include_router(
    search_text_controller.router,
    prefix="/search-by/text",
    tags=["Search"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    search_image_controller.router,
    prefix="/search-by/image",
    tags=["Search"],
    dependencies=[Depends(verify_api_key)],
)

# Search By User Content Routes
app.include_router(
    search_user_image_controller.router,
    prefix="/search-by-user-content",
    tags=["User Content Search"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    search_user_video_controller.router,
    prefix="/search-by-user-content",
    tags=["User Content Search"],
    dependencies=[Depends(verify_api_key)],
)

# Get Embeddings Routes
app.include_router(
    get_embeddings_controller.router,
    prefix="/get-embeddings",
    tags=["Embeddings"],
    dependencies=[Depends(verify_api_key)],
)


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Visual Search API"}

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

# Debug endpoint for testing
@app.get("/debug/settings", tags=["Debug"])
def debug_settings():
    return {
        "api_username": settings.api_username,
        "api_password": "***" if settings.api_password else None,
        "api_key": "***" if settings.api_key else None,
        "api_name": settings.api_name,
    }


# Custom Swagger UI Route
@app.get("/api/docs", dependencies=[Depends(verify_credentials)])
def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title=settings.api_name + " Docs")


@app.get("/api/openapi.json", dependencies=[Depends(verify_credentials)])
def custom_openapi():
    return JSONResponse(app.openapi())
