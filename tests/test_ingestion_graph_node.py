from unittest.mock import MagicMock, patch

from src.ingestion.nodes import graph_node
from src.ingestion.jobs import job_store
from src.utils.entity_extractor import ExtractedEntity


def _fake_state(num_chunks=1):
    chunks = []
    for i in range(num_chunks):
        chunk = MagicMock()
        chunk.page_content = f'Marie Curie discovered radium in Paris. (chunk {i})'
        chunks.append(chunk)
    return {'file': 'data/test.pdf', 'chunks': chunks}


def test_graph_node_skips_when_disabled():
    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', False), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        result = graph_node(_fake_state())

    assert result == {'graph_entities_stored': 0}
    mock_extract.assert_not_called()
    mock_store.assert_not_called()


def test_graph_node_extracts_and_stores_when_enabled():
    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        mock_extract.return_value = [
            ExtractedEntity(name='Marie Curie', type='PERSON'),
            ExtractedEntity(name='Paris', type='LOCATION'),
        ]

        result = graph_node(_fake_state())

    assert result == {'graph_entities_stored': 2}
    mock_store.assert_called_once()
    call_args = mock_store.call_args.args
    assert call_args[0] == 'data/test.pdf'
    assert sorted(call_args[1], key=lambda e: e['name']) == sorted(
        [
            {'name': 'Marie Curie', 'type': 'PERSON'},
            {'name': 'Paris', 'type': 'LOCATION'},
        ],
        key=lambda e: e['name'],
    )


def test_graph_node_never_raises_if_storage_fails():
    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        mock_extract.return_value = [ExtractedEntity(name='Marie Curie', type='PERSON')]
        mock_store.side_effect = RuntimeError('neo4j unreachable')

        result = graph_node(_fake_state())

    assert result == {'graph_entities_stored': 0}


def test_graph_node_deduplicates_entities_across_many_chunks():
    """Simulates a large document where the same entity appears in many
    chunks - confirms dedup works correctly under concurrent extraction,
    not just with a single chunk."""
    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        # every chunk "finds" the same two entities - real documents often
        # repeat entity mentions across many chunks
        mock_extract.return_value = [
            ExtractedEntity(name='Marie Curie', type='PERSON'),
            ExtractedEntity(name='Paris', type='LOCATION'),
        ]

        result = graph_node(_fake_state(num_chunks=50))

    assert result == {'graph_entities_stored': 2}
    assert mock_extract.call_count == 50
    mock_store.assert_called_once()


def test_graph_node_continues_when_some_chunks_fail_extraction():
    """If extraction raises for some chunks (rate limit, transient error),
    the rest should still succeed rather than failing the whole job."""
    call_count = {'n': 0}

    def flaky_extract(text):
        call_count['n'] += 1
        if call_count['n'] % 3 == 0:
            raise RuntimeError('simulated rate limit')
        return [ExtractedEntity(name='Marie Curie', type='PERSON')]

    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities', side_effect=flaky_extract), \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        result = graph_node(_fake_state(num_chunks=10))

    # some calls failed, but the ones that succeeded still get stored
    assert result == {'graph_entities_stored': 1}
    mock_store.assert_called_once()


def test_graph_node_surfaces_storage_error_on_job_for_debugging():
    """When store_document_entities fails (e.g. Neo4j unreachable), the
    real error should be visible via the job's graph_error field, not
    silently swallowed - this is what lets you actually diagnose why
    nothing showed up in Neo4j."""
    job = job_store.create(filename='test.pdf')

    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities') as mock_store:
        mock_extract.return_value = [ExtractedEntity(name='Marie Curie', type='PERSON')]
        mock_store.side_effect = RuntimeError('Could not connect to Neo4j - Connection refused')

        state = _fake_state()
        state['job_id'] = job.job_id
        result = graph_node(state)

    assert result == {'graph_entities_stored': 0}
    updated = job_store.get(job.job_id)
    assert updated.graph_error is not None
    assert 'Connection refused' in updated.graph_error


def test_graph_node_clears_graph_error_on_success():
    """A previous failed attempt's error shouldn't linger after a
    successful run."""
    job = job_store.create(filename='test.pdf')
    job_store.update(job.job_id, graph_error='stale error from a previous attempt')

    with patch('src.ingestion.nodes.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.ingestion.nodes.extract_entities') as mock_extract, \
         patch('src.ingestion.nodes.store_document_entities'):
        mock_extract.return_value = [ExtractedEntity(name='Marie Curie', type='PERSON')]

        state = _fake_state()
        state['job_id'] = job.job_id
        graph_node(state)

    updated = job_store.get(job.job_id)
    assert updated.graph_error is None
