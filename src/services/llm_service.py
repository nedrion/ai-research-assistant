import asyncio
import time

import httpx


class LlmService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, system: str = "", model: str | None = None) -> str:
        model = model or self.model
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code == 404:
                raise RuntimeError(
                    f"Model '{model}' not found in Ollama. "
                    f"Run: ollama pull {model}"
                )
            resp.raise_for_status()
            return resp.json()["response"]

    def is_server_running(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def has_model(self) -> bool:
        return self.model in self.list_models()

    def list_models(self) -> list[str]:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

    def ensure_model(self, model: str | None = None) -> None:
        from src.core.logging import get_logger

        log = get_logger(__name__)
        target = model or self.model

        for attempt in range(30):
            if self.is_server_running():
                break
            log.info("Waiting for Ollama to be ready (attempt %d/30)...", attempt + 1)
            time.sleep(2)
        else:
            log.warning("Ollama not reachable — skipping model pull")
            return

        if target in self.list_models():
            return

        log.info("Model '%s' not found locally — pulling from Ollama...", target)
        try:
            with httpx.Client(timeout=600) as client:
                payload = {"name": target, "stream": False}
                resp = client.post(f"{self.base_url}/api/pull", json=payload)
                resp.raise_for_status()
            log.info("Model '%s' pulled successfully", target)
        except Exception as exc:
            log.warning("Failed to pull model '%s': %s", target, exc)

    async def ensure_model_async(self, model: str | None = None) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.ensure_model, model)
