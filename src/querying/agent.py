from src.querying.retriever import retrieve_docs
from src.querying.generator import generate_answer


def ask(question):
    docs = retrieve_docs(question)
    context = '\n'.join(docs)
    return generate_answer(context, question)
