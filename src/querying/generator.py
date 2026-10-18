from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from src.core.config import CHAT_MODEL
from src.core.logging_config import get_logger

logger = get_logger('query.generator')

_llm = None
_prompt = PromptTemplate.from_template(
    """Answer the question using only the context below. If the context
doesn't contain the answer, say you don't know.

Context:
{context}

Question:
{question}
"""
)


def _get_llm():
    global _llm
    if _llm is None:
        logger.info(f'🤖 [GENERATOR] Initializing ChatOpenAI model ({CHAT_MODEL})...')
        _llm = ChatOpenAI(model=CHAT_MODEL)
    return _llm


def generate_answer(context, question):
    if not context.strip():
        logger.warning('⚠️ [GENERATOR] No relevant context available. Returning fallback message.')
        return "I couldn't find any relevant documents to answer that question."

    logger.info(f'🤖 [GENERATOR] Generating answer with LLM ({CHAT_MODEL}) using context ({len(context)} characters)...')
    chain = _prompt | _get_llm()
    response = chain.invoke({'context': context, 'question': question})
    answer = response.content
    logger.info(f'✅ [GENERATOR] Successfully generated answer ({len(answer)} characters).')
    return answer
