import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    import uvicorn
    from src.core.config import settings

    logger.info("Starting API at http://%s:%s", settings.api_host, settings.api_port)
    uvicorn.run("src.api.server:app", host=settings.api_host, port=settings.api_port, reload=False, lifespan_timeout=600)


if __name__ == "__main__":
    main()
