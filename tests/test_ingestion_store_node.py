from unittest.mock import MagicMock, patch

from src.ingestion.nodes import store_node, split_node
from src.ingestion.jobs import job_store, JobStatus


def test_store_node_reports_progress_to_job():
    job = job_store.create(filename='test.pdf')

    with patch('src.ingestion.nodes.store_vectors', return_value=(80, 20)) as mock_store:
        result = store_node({'file': 'data/test.pdf', 'chunks': [MagicMock()], 'job_id': job.job_id})

    assert result == {'stored': True, 'vectors_stored': 80, 'vectors_failed': 20}
    mock_store.assert_called_once()
    # on_progress should have been wired through so the job store gets updates
    _, kwargs = mock_store.call_args
    assert 'on_progress' in kwargs


def test_store_node_progress_callback_updates_job_store():
    job = job_store.create(filename='test.pdf')

    def fake_store_vectors(chunks, batch_size, on_progress):
        on_progress(50, 0, 100)
        on_progress(100, 0, 100)
        return 100, 0

    with patch('src.ingestion.nodes.store_vectors', side_effect=fake_store_vectors):
        store_node({'file': 'data/test.pdf', 'chunks': [MagicMock()], 'job_id': job.job_id})

    updated = job_store.get(job.job_id)
    assert updated.chunks_stored == 100
    assert updated.chunks_failed == 0


def test_store_node_works_without_job_id():
    """store_node should work fine for the direct/synchronous ingest_file()
    call path too, where there's no job to report progress to."""
    with patch('src.ingestion.nodes.store_vectors', return_value=(5, 0)):
        result = store_node({'file': 'data/test.pdf', 'chunks': [MagicMock()]})

    assert result == {'stored': True, 'vectors_stored': 5, 'vectors_failed': 0}


def test_split_node_records_total_chunks_on_job():
    job = job_store.create(filename='test.pdf')
    fake_chunks = [MagicMock() for _ in range(42)]

    with patch('src.ingestion.nodes.split_documents', return_value=fake_chunks):
        result = split_node({'docs': [MagicMock()], 'job_id': job.job_id})

    assert len(result['chunks']) == 42
    updated = job_store.get(job.job_id)
    assert updated.total_chunks == 42
