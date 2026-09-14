from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def get_chat_model(temperature: float=0.0) -> ChatOpenAI:
    from livegraph.config import settings
    return ChatOpenAI(
        model=settings.groq_model,
        temperature=temperature,
        api_key=SecretStr(settings.groq_api_key),
        base_url="https://api.groq.com/openai/v1"
    )