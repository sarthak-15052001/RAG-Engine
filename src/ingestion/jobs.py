import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class JobStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


@dataclass
class IngestionJob:
    job_id: str
    filename: str
    status: JobStatus = JobStatus.PENDING
    total_chunks: int = 0
    chunks_stored: int = 0
    chunks_failed: int = 0
    entities_stored: int = 0
    error: Optional[str] = None
    graph_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'status': self.status.value,
            'total_chunks': self.total_chunks,
            'chunks_stored': self.chunks_stored,
            'chunks_failed': self.chunks_failed,
            'entities_stored': self.entities_stored,
            'error': self.error,
            'graph_error': self.graph_error,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class JobStore:
    """Thread-safe in-memory job registry.

    This is intentionally simple - a single dict guarded by a lock - which
    is sufficient for a single-process FastAPI deployment. If this app is
    ever run with multiple worker processes, swap this for a shared store
    (Redis, a DB table) - every method below is the only place that would
    need to change.
    """

    def __init__(self):
        self._jobs: Dict[str, IngestionJob] = {}
        self._lock = threading.Lock()

    def create(self, filename: str) -> IngestionJob:
        job = IngestionJob(job_id=uuid.uuid4().hex, filename=filename)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[IngestionJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in fields.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def increment(self, job_id: str, **deltas):
        """Atomically adds `deltas` to the named numeric fields, e.g.
        increment(job_id, chunks_stored=1). Use this instead of a
        get()-then-update() pair when multiple threads may be reporting
        progress concurrently - get() and update() are each individually
        atomic, but calling them separately is not (there's a race between
        reading the current value and writing the new one)."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, delta in deltas.items():
                setattr(job, key, getattr(job, key) + delta)
            job.updated_at = time.time()


job_store = JobStore()
