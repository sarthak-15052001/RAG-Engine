import threading

from src.ingestion.jobs import JobStore, JobStatus


def test_create_returns_job_with_pending_status():
    store = JobStore()
    job = store.create(filename='test.pdf')

    assert job.status == JobStatus.PENDING
    assert job.filename == 'test.pdf'
    assert job.job_id


def test_get_returns_none_for_unknown_id():
    store = JobStore()
    assert store.get('does-not-exist') is None


def test_update_modifies_fields_and_bumps_updated_at():
    store = JobStore()
    job = store.create(filename='test.pdf')
    original_updated_at = job.updated_at

    store.update(job.job_id, status=JobStatus.RUNNING, chunks_stored=10)

    updated = store.get(job.job_id)
    assert updated.status == JobStatus.RUNNING
    assert updated.chunks_stored == 10
    assert updated.updated_at >= original_updated_at


def test_update_on_unknown_job_id_does_not_raise():
    store = JobStore()
    store.update('does-not-exist', status=JobStatus.RUNNING)  # should be a no-op


def test_to_dict_contains_expected_keys():
    store = JobStore()
    job = store.create(filename='test.pdf')
    data = job.to_dict()

    assert data['job_id'] == job.job_id
    assert data['filename'] == 'test.pdf'
    assert data['status'] == 'pending'
    assert 'total_chunks' in data
    assert 'chunks_stored' in data
    assert 'chunks_failed' in data
    assert 'entities_stored' in data
    assert 'error' in data


def test_job_store_increment_is_atomic_under_concurrent_updates():
    store = JobStore()
    job = store.create(filename='test.pdf')

    def bump():
        for _ in range(100):
            store.increment(job.job_id, chunks_stored=1)

    threads = [threading.Thread(target=bump) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # increment() acquires the lock for the full read-modify-write, so this
    # must land on exactly 500 with no lost updates.
    final = store.get(job.job_id)
    assert final.chunks_stored == 500
