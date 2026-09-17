import httpx
import requests


class EmbeddingModel:
    def __init__(self, model: str, base_url: str, api_key: str, dimension: int):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.dimension = dimension
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def encode(self, message: list[str] | str) -> list[list[float]]:
        payload = {"model": self.model, "input": message}
        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=60)
        response.raise_for_status()
        return self._extract_embeddings(response.json())

    async def aencode(self, message: list[str] | str) -> list[list[float]]:
        payload = {"model": self.model, "input": message}
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status()
            return self._extract_embeddings(response.json())

    @staticmethod
    def _extract_embeddings(result: dict) -> list[list[float]]:
        if not isinstance(result, dict) or "data" not in result:
            raise ValueError(f"Embedding failed: Invalid response format {result}")
        return [item["embedding"] for item in result["data"]]


def get_embedding_model() -> EmbeddingModel:
    from livegraph.config import settings

    return EmbeddingModel(
        model=settings.embed_model,
        base_url=settings.embed_base_url,
        api_key=settings.embed_api_key,
        dimension=settings.embed_dimension,
    )
