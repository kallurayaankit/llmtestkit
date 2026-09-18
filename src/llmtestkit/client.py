"""Unified LLM client.

Ships with Ollama. To add another provider, subclass BaseClient and
implement generate() and chat().
"""

import os
import requests
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv()


DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:3b"


class BaseClient(ABC):
    """Interface every provider must implement."""

    @abstractmethod
    def generate(self, prompt: str, timeout: int = 300, temperature: float | None = None) -> str:
        ...

    @abstractmethod
    def chat(self, turns: list[str], timeout: int = 300, temperature: float | None = None) -> str:
        ...


class OllamaClient(BaseClient):
    """Talks to a locally-running Ollama server."""

    def __init__(self, base_url: str | None = None, model: str | None = None, system: str | None = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", DEFAULT_URL)
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.system = system

    def generate(self, prompt, timeout=300, temperature=None):
        options = {}
        if temperature is not None:
            options["temperature"] = temperature

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if self.system:
            payload["system"] = self.system

        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()["response"]

    def chat(self, turns, timeout=300, temperature=None):
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})

        final_reply = ""
        for user_msg in turns:
            messages.append({"role": "user", "content": user_msg})
            options = {}
            if temperature is not None:
                options["temperature"] = temperature
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": options,
            }
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
            r.raise_for_status()
            final_reply = r.json()["message"]["content"]
            messages.append({"role": "assistant", "content": final_reply})

        return final_reply

    def is_available(self):
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=2)
            return True
        except Exception:
            return False


def get_client(provider: str = "ollama", **kwargs) -> BaseClient:
    """Factory. Add new providers here."""
    if provider == "ollama":
        return OllamaClient(**kwargs)
    raise ValueError(f"unknown provider: {provider}")
