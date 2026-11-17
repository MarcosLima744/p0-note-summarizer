import math
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from dotenv import load_dotenv


class AppError(Exception):
    """Erro que pode ser apresentado ao usuário sem detalhes internos."""


@dataclass(frozen=True)
class Config:
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:4b-instruct"
    timeout: float = 300
    max_output_tokens: int = 6000
    context_length: int = 32768
    temperature: float = 0
    max_input_chars: int = 24000

    @classmethod
    def load(cls) -> "Config":
        # Apenas o .env do diretório de execução; variáveis exportadas prevalecem.
        load_dotenv(".env", override=False)
        try:
            timeout = float(os.getenv("OLLAMA_TIMEOUT", "300"))
            tokens = int(os.getenv("OLLAMA_MAX_OUTPUT_TOKENS", "6000"))
            context = int(os.getenv("OLLAMA_CONTEXT_LENGTH", "32768"))
            temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0"))
            chars = int(os.getenv("NOTES_MAX_INPUT_CHARS", "24000"))
        except ValueError:
            raise AppError("Timeout, temperatura e limites devem ser números válidos.") from None
        if not math.isfinite(timeout) or timeout <= 0 or min(tokens, context, chars) <= 0:
            raise AppError("Timeout e limites devem ser números positivos e finitos.")
        if not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise AppError("OLLAMA_TEMPERATURE deve estar entre 0 e 2.")
        if tokens >= context:
            raise AppError("OLLAMA_CONTEXT_LENGTH deve ser maior que OLLAMA_MAX_OUTPUT_TOKENS.")
        model = os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct").strip()
        if not model or model.endswith(":cloud") or "-cloud" in model:
            raise AppError("OLLAMA_MODEL deve indicar um modelo local, como qwen3:4b-instruct.")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
        try:
            url = urlsplit(base_url)
            port = url.port
            valid = (url.scheme in {"http", "https"}
                     and url.hostname in {"localhost", "127.0.0.1", "::1"}
                     and not (url.username or url.password or url.query or url.fragment or url.path)
                     and (port is None or port > 0))
        except ValueError:
            valid = False
        if not valid:
            raise AppError("OLLAMA_BASE_URL deve ser um endereço local válido, como http://localhost:11434.")
        return cls(base_url, model, timeout, tokens, context, temperature, chars)
