from pydantic import BaseModel, Field

from livegraph.models.chat import get_chat_model

TRIPLE_EXTRACTION_PROMPT = """Extract entities and relationships from the text below.

Text:
{text}
"""


class Entity(BaseModel):
    text: str = Field(description="the entity's name as it appears in the text")
    label: str = Field(description="entity type, e.g. Person, Place, Organization, Concept")


class Relation(BaseModel):
    source: Entity
    target: Entity
    text: str = Field(description="short description of the relationship")
    label: str = Field(description="relation type, e.g. LOCATED_IN, WORKS_FOR, PART_OF")


class ExtractedTriples(BaseModel):
    relations: list[Relation]


async def extract_triples(text: str) -> list[dict]:
    model = get_chat_model().with_structured_output(ExtractedTriples)
    prompt = TRIPLE_EXTRACTION_PROMPT.format(text=text)
    result = await model.ainvoke(prompt)
    if not isinstance(result, ExtractedTriples):
        return []
    return [relation.model_dump() for relation in result.relations]
