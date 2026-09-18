from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def get_chat_model(temperature: float=0.0) -> ChatOpenAI:
    from livegraph.config import settings
    if settings.cerebras_api_key:
        return ChatOpenAI(
            model=settings.cerebras_model,
            temperature=temperature,
            api_key=SecretStr(settings.cerebras_api_key),
            max_completion_tokens=4096,
            reasoning_effort="low",
            base_url="https://api.cerebras.ai/v1",
        )
    return ChatOpenAI(
        model=settings.groq_model,
        temperature=temperature,
        api_key=SecretStr(settings.groq_api_key),
        max_completion_tokens=4096,
        reasoning_effort="low",
        base_url="https://api.groq.com/openai/v1"
    )