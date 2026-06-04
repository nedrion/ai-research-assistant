import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    import uvicorn
    from src.core.config import settings

    print(f"Starting API at http://{settings.api_host}:{settings.api_port}")
    uvicorn.run("src.api.server:app", host=settings.api_host, port=settings.api_port, reload=False)


if __name__ == "__main__":
    main()
