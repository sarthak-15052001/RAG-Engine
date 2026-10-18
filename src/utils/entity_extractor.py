from typing import List

from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from src.core.config import CHAT_MODEL
from src.core.logging_config import get_logger

logger = get_logger('entity.extractor')


class ExtractedEntity(BaseModel):
    name: str = Field(description='The canonical name of the entity, e.g. "Marie Curie"')
    type: str = Field(
        description='The entity category, e.g. PERSON, ORGANIZATION, LOCATION, DATE, PRODUCT, EVENT, OTHER'
    )


class EntityList(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)


_llm = None
_extractor = None

_prompt = PromptTemplate.from_template(
    """Extract the distinct named entities mentioned in the text below.
For each entity, give its name and a short category (PERSON, ORGANIZATION,
LOCATION, DATE, PRODUCT, EVENT, or OTHER). Skip pronouns and generic terms.
If there are no clear named entities, return an empty list.

Text:
{text}
"""
)


def _get_extractor():
    global _llm, _extractor
    if _extractor is None:
        logger.info(f'🤖 [ENTITY EXTRACTOR] Initializing LLM entity extractor (Model: {CHAT_MODEL})...')
        _llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
        _extractor = _llm.with_structured_output(EntityList, method='function_calling')
    return _extractor


def extract_entities(text: str) -> List[ExtractedEntity]:
    """Extract named entities from a chunk of text."""
    if not text or not text.strip():
        return []

    chain = _prompt | _get_extractor()
    try:
        result: EntityList = chain.invoke({'text': text})
        return result.entities
    except Exception as exc:
        logger.warning(f'⚠️ [ENTITY EXTRACTOR] Entity extraction failed for chunk: {exc}')
        return []
