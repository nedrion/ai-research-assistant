import httpx


class LlmService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code == 404:
                raise RuntimeError(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Run: ollama pull {self.model}"
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
        models = self.list_models()
        if self.model in models:
            return True
        short = self.model.split(":")[0]
        return any(short == m.split(":")[0] for m in models)

    def list_models(self) -> list[str]:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []
