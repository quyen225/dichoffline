# model/config.py

AVAILABLE_MODELS = {
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini"
    ],
    "azure": [
        "gpt-4o",
        "gpt-4-turbo"
    ],
    "google_free": [
        "default-public-model"
    ]
}

def get_models_by_provider(provider_name: str) -> list:
    return AVAILABLE_MODELS.get(provider_name.lower(), [])
