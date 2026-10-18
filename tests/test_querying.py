from unittest.mock import MagicMock, patch

from src.querying import retrieve_docs, generate_answer


def test_retrieve_docs():
    fake_doc = MagicMock()
    fake_doc.page_content = 'hello world document chunk'

    fake_vectorstore = MagicMock()
    fake_vectorstore.similarity_search.return_value = [fake_doc]

    with patch('src.querying.retriever.get_vectorstore', return_value=fake_vectorstore):
        docs = retrieve_docs('hello world')

    assert docs == ['hello world document chunk']
    fake_vectorstore.similarity_search.assert_called_once_with('hello world', k=4)


def test_generate_answer_with_empty_context():
    answer = generate_answer('', 'anything?')
    assert "don't know" in answer.lower() or "couldn't find" in answer.lower()
