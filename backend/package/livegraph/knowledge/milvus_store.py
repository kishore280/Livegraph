import asyncio
import uuid

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from livegraph.models.embed import get_embedding_model

_CONNECTION_ALIAS = "default"
_COLLECTION_NAME = "livegraph_chunks"
_VECTOR_METRIC_TYPE = "COSINE"


def _connect() -> None:
    from livegraph.config import settings
    connections.connect(alias=_CONNECTION_ALIAS, uri=settings.milvus_uri, token=settings.milvus_token)


def get_or_create_collection() -> Collection:
    _connect()
    if utility.has_collection(_COLLECTION_NAME, using=_CONNECTION_ALIAS):
        collection = Collection(name=_COLLECTION_NAME, using=_CONNECTION_ALIAS)
    else:
        embed_model = get_embedding_model()
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embed_model.dimension),
        ]
        schema = CollectionSchema(fields=fields, description="livegraph session chunks")
        collection = Collection(name=_COLLECTION_NAME, schema=schema, using=_CONNECTION_ALIAS)
        collection.create_index(  # pyright: ignore[reportUnusedCoroutine]
            "embedding",
            {"metric_type": _VECTOR_METRIC_TYPE, "index_type": "IVF_FLAT", "params": {"nlist": 1024}},
        )
        collection.create_index("session_id", {"index_type": "INVERTED"})  # pyright: ignore[reportUnusedCoroutine]
    collection.load()
    return collection


async def add_chunks(session_id: str, chunks: list[str]) -> list[dict]:
    if not chunks:
        return []

    embed_model = get_embedding_model()
    ids = [uuid.uuid4().hex for _ in chunks]
    session_ids = [session_id for _ in chunks]
    vectors = await asyncio.to_thread(embed_model.encode, chunks)

    collection = await asyncio.to_thread(get_or_create_collection)
    await asyncio.to_thread(collection.insert, [ids, session_ids, chunks, vectors])
    await asyncio.to_thread(collection.flush)

    return [{"chunk_id": chunk_id, "content": content} for chunk_id, content in zip(ids, chunks, strict=True)]


async def search(session_id: str, query_text: str, top_k: int = 5) -> list[dict]:
    embed_model = get_embedding_model()
    query_vector = (await asyncio.to_thread(embed_model.encode, query_text))[0]

    collection = await asyncio.to_thread(get_or_create_collection)
    results = await asyncio.to_thread(
        collection.search,
        data=[query_vector],
        anns_field="embedding",
        param={"metric_type": _VECTOR_METRIC_TYPE, "params": {"nprobe": 10}},
        limit=top_k,
        expr=f'session_id == "{session_id}"',
        output_fields=["content"],
    )
    hits = results[0]  # pyright: ignore[reportIndexIssue]
    return [{"chunk_id": hit.id, "content": hit.entity.get("content"), "score": hit.distance} for hit in hits]


async def get_sample_chunks(session_id: str, limit: int = 5) -> list[dict]:
    collection = await asyncio.to_thread(get_or_create_collection)
    rows = await asyncio.to_thread(
        collection.query,
        expr=f'session_id == "{session_id}"',
        limit=limit,
        output_fields=["id", "content"],
    )
    return [
        {"chunk_id": row["id"], "content": row["content"]}
        for row in rows  # pyright: ignore[reportGeneralTypeIssues]
    ]
