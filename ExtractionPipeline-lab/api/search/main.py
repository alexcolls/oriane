import uvicorn
from src.app import app
from config.env_config import settings

# This is the main entry point for running the application.
# Uvicorn will use the 'app' object imported from your api.api module.
#
# To run the application, use the following command in your terminal:
# uvicorn main:app --reload
#
# - `main`: Refers to this file, main.py
# - `app`: Refers to the FastAPI instance created inside main.py
# - `--reload`: Enables hot-reloading for development, so the server
#               restarts automatically after code changes.

if __name__ == "__main__":
    # We point uvicorn to the 'app' object inside the 'api.main' module.
    # This ensures Python treats 'api' as a package.
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(settings.api_port),
        reload=True,
        reload_dirs=["api"],
    )
