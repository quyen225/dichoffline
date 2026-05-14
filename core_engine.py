from typing import List, Optional
from ollama_provider import OllamaProvider
from groq_provider import GroqProvider
from azure_provider import AzureProvider
from google_provider import GoogleProvider

class TranslationEngine:
    """Cổng chuyển tiếp kết nối gọi tới các module AI Provider độc lập."""

    @staticmethod
    def call_ollama(model: str, text: str) -> str:
        return OllamaProvider.generate(model, text)

    @staticmethod
    def list_ollama_models() -> List[str]:
        return OllamaProvider.list_ollama_models()

    @staticmethod
    def fetch_groq_models(api_key: str) -> List[str]:
        return GroqProvider.fetch_models(api_key)

    @staticmethod
    def call_groq(api_key: str, model: str, text: str) -> str:
        return GroqProvider.generate(api_key, model, text)

    @staticmethod
    def call_azure(key: str, endpoint: str, region: str, text: str) -> str:
        return AzureProvider.generate(key, endpoint, region, text)

    @staticmethod
    def translate_google_free(text: str) -> Optional[str]:
        return GoogleProvider.generate_free(text)
