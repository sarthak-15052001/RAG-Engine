from unittest.mock import MagicMock, patch

from src.data_stores.neo4j_graph_client import (
    store_document_entities,
    get_related_entities,
    get_documents_mentioning,
    get_graph_counts,
)


def _mock_driver_with_session():
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_driver, mock_session


def test_store_document_entities_runs_expected_queries():
    mock_driver, mock_session = _mock_driver_with_session()
    fake_tx = MagicMock()
    mock_session.execute_write.side_effect = lambda fn, *args: fn(fake_tx, *args)

    with patch('src.data_stores.neo4j_graph_client.get_driver', return_value=mock_driver):
        store_document_entities(
            'data/test.pdf',
            [{'name': 'Marie Curie', 'type': 'PERSON'}],
        )

    # one MERGE for the Document, one MERGE+MATCH+MERGE per entity
    assert fake_tx.run.call_count == 2
    first_call_query = fake_tx.run.call_args_list[0].args[0]
    assert 'MERGE (d:Document' in first_call_query


def test_store_document_entities_with_no_entities_still_creates_document():
    mock_driver, mock_session = _mock_driver_with_session()
    fake_tx = MagicMock()
    mock_session.execute_write.side_effect = lambda fn, *args: fn(fake_tx, *args)

    with patch('src.data_stores.neo4j_graph_client.get_driver', return_value=mock_driver):
        store_document_entities('data/empty.pdf', [])

    assert fake_tx.run.call_count == 1


def test_get_related_entities_parses_records():
    mock_driver, mock_session = _mock_driver_with_session()
    fake_tx = MagicMock()
    fake_tx.run.return_value = [
        {'name': 'Paris', 'type': 'LOCATION'},
    ]
    mock_session.execute_read.side_effect = lambda fn, *args: fn(fake_tx, *args)

    with patch('src.data_stores.neo4j_graph_client.get_driver', return_value=mock_driver):
        result = get_related_entities('Marie Curie')

    assert result == [{'name': 'Paris', 'type': 'LOCATION'}]


def test_get_documents_mentioning_parses_records():
    mock_driver, mock_session = _mock_driver_with_session()
    fake_tx = MagicMock()
    fake_tx.run.return_value = [{'source': 'data/test.pdf'}]
    mock_session.execute_read.side_effect = lambda fn, *args: fn(fake_tx, *args)

    with patch('src.data_stores.neo4j_graph_client.get_driver', return_value=mock_driver):
        result = get_documents_mentioning('Marie Curie')

    assert result == ['data/test.pdf']


def test_get_graph_counts_returns_document_entity_mention_totals():
    mock_driver, mock_session = _mock_driver_with_session()
    fake_tx = MagicMock()

    def fake_run(query):
        result = MagicMock()
        if 'Document' in query:
            result.single.return_value = {'n': 3}
        elif 'Entity' in query:
            result.single.return_value = {'n': 17}
        elif 'MENTIONS' in query:
            result.single.return_value = {'n': 22}
        return result

    fake_tx.run.side_effect = fake_run
    mock_session.execute_read.side_effect = lambda fn, *args: fn(fake_tx, *args)

    with patch('src.data_stores.neo4j_graph_client.get_driver', return_value=mock_driver):
        counts = get_graph_counts()

    assert counts == {'documents': 3, 'entities': 17, 'mentions': 22}
