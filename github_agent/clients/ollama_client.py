# clients/ollama_client.py
# All communication with the local Ollama LLM

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from config.settings import Config


class OllamaClient:
    """
    Wraps the Ollama REST API with:
      - Retry logic
      - Token / context management
      - Multiple convenience methods for agents
    """

    def __init__(self):
        self.logger    = logging.getLogger("clients.ollama")
        self.base_url  = Config.OLLAMA_BASE_URL
        self.model     = Config.OLLAMA_MODEL
        self.timeout   = Config.OLLAMA_TIMEOUT
        self._verify_connection()

    # ──────────────────────────────────────────────────────────
    # CONNECTION
    # ──────────────────────────────────────────────────────────

    def _verify_connection(self):
        """Check Ollama is running and the model is available."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags", timeout=5
            )
            models = [m["name"] for m in resp.json().get("models", [])]
            if self.model not in models and not any(
                self.model in m for m in models
            ):
                self.logger.warning(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available: {models}. Run: ollama pull {self.model}"
                )
            else:
                self.logger.info(
                    f"Ollama ready | Model: {self.model} | URL: {self.base_url}"
                )
        except Exception as e:
            self.logger.error(
                f"Cannot reach Ollama at {self.base_url}: {e}\n"
                f"Make sure Ollama is running: ollama serve"
            )

    # ──────────────────────────────────────────────────────────
    # CORE CHAT
    # ──────────────────────────────────────────────────────────

    def chat(
        self,
        messages:    List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens:  int   = 4096,
        model:       Optional[str] = None,
        retries:     int   = 3,
    ) -> Optional[str]:
        """
        Send a chat-completion request to Ollama.

        Args:
            messages:    List of {"role": "...", "content": "..."} dicts
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens:  Maximum tokens to generate
            model:       Override default model for this call
            retries:     Number of retry attempts on failure

        Returns:
            The assistant's reply as a string, or None on failure.
        """
        url     = f"{self.base_url}/api/chat"
        payload = {
            "model":    model or self.model,
            "messages": messages,
            "stream":   False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx":     8192,
            },
        }

        for attempt in range(1, retries + 1):
            try:
                t0   = time.time()
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                elapsed = time.time() - t0

                data    = resp.json()
                content = data.get("message", {}).get("content", "")

                self.logger.debug(
                    f"LLM call | model={model or self.model} "
                    f"| temp={temperature} | {elapsed:.1f}s "
                    f"| {len(content)} chars"
                )
                return content

            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Ollama timeout (attempt {attempt}/{retries})"
                )
                time.sleep(3 * attempt)

            except requests.exceptions.RequestException as e:
                self.logger.error(
                    f"Ollama request error (attempt {attempt}/{retries}): {e}"
                )
                time.sleep(3 * attempt)

        self.logger.error("Ollama chat failed after all retries")
        return None

    # ──────────────────────────────────────────────────────────
    # CONVENIENCE WRAPPERS
    # ──────────────────────────────────────────────────────────

    def complete(
        self,
        prompt:      str,
        system:      str   = "You are a helpful assistant.",
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Simple single-prompt helper."""
        return self.chat(
            messages=[
                {"role": "system",  "content": system},
                {"role": "user",    "content": prompt},
            ],
            temperature=temperature,
        )

    def json_complete(
        self,
        prompt:      str,
        system:      str   = "Respond with valid JSON only.",
        temperature: float = 0.1,
    ) -> Optional[Dict]:
        """
        Ask for a JSON response and parse it automatically.
        Returns a dict or None.
        """
        import re

        raw = self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=temperature,
        )

        if not raw:
            return None

        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Find first JSON object in response
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass

        # Find first JSON array in response
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass

        self.logger.warning("json_complete: could not parse response as JSON")
        return None

    def code_complete(
        self,
        prompt:   str,
        language: str   = "",
        temp:     float = 0.15,
    ) -> Optional[str]:
        """
        Code-generation helper.
        Strips markdown fences automatically.
        """
        import re

        system = (
            f"You are an expert {language} developer. "
            "Return ONLY code. No markdown fences, no explanations."
        )
        raw = self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=temp,
        )

        if not raw:
            return None

        # Strip markdown code fences
        raw = re.sub(r"```\w*\n?", "", raw)
        raw = re.sub(r"```", "", raw)
        return raw.strip()

    # ──────────────────────────────────────────────────────────
    # MODEL MANAGEMENT
    # ──────────────────────────────────────────────────────────

    def list_models(self) -> List[str]:
        """Return names of all locally available Ollama models."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags", timeout=5
            )
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model if it's not already available."""
        self.logger.info(f"Pulling model: {model_name}")
        try:
            resp = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600,            # large models take time
                stream=True,
            )
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if "error" in data:
                        self.logger.error(f"Pull error: {data['error']}")
                        return False
                    self.logger.debug(f"Pull: {status}")
            self.logger.info(f"Model '{model_name}' ready")
            return True
        except Exception as e:
            self.logger.error(f"pull_model failed: {e}")
            return False

    def is_healthy(self) -> bool:
        """Quick health check — is Ollama responding?"""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags", timeout=3
            )
            return resp.status_code == 200
        except Exception:
            return False