from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_root():
    r = client.get('/')
    assert r.status_code == 200
    assert r.json()['status'] == 'running'


def test_upload_rejects_non_pdf():
    files = {'file': ('notes.txt', b'just some text', 'text/plain')}
    r = client.post('/v1/file/upload', files=files)
    assert r.status_code == 400
    assert 'PDF' in r.json()['detail']


def test_upload_rejects_empty_file():
    files = {'file': ('empty.pdf', b'', 'application/pdf')}
    r = client.post('/v1/file/upload', files=files)
    assert r.status_code == 400
    assert 'empty' in r.json()['detail'].lower()
