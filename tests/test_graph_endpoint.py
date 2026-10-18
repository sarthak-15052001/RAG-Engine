from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_graph_health_disabled_by_default():
    r = client.get('/v1/graph/health')
    assert r.status_code == 200
    assert r.json() == {'enabled': False, 'connected': False}


def test_graph_health_enabled_but_not_connected():
    with patch('src.api.v1.endpoints.graph.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.api.v1.endpoints.graph.verify_connectivity', side_effect=RuntimeError('Connection refused')):
        r = client.get('/v1/graph/health')

    assert r.status_code == 200
    body = r.json()
    assert body['enabled'] is True
    assert body['connected'] is False
    assert 'Connection refused' in body['detail']


def test_graph_health_connected_with_counts():
    with patch('src.api.v1.endpoints.graph.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.api.v1.endpoints.graph.verify_connectivity', return_value=None), \
         patch(
             'src.api.v1.endpoints.graph.get_graph_counts',
             return_value={'documents': 2, 'entities': 9, 'mentions': 14},
         ):
        r = client.get('/v1/graph/health')

    assert r.status_code == 200
    body = r.json()
    assert body['enabled'] is True
    assert body['connected'] is True
    assert body['counts'] == {'documents': 2, 'entities': 9, 'mentions': 14}


def test_graph_health_connected_but_counting_fails():
    with patch('src.api.v1.endpoints.graph.ENABLE_GRAPH_EXTRACTION', True), \
         patch('src.api.v1.endpoints.graph.verify_connectivity', return_value=None), \
         patch('src.api.v1.endpoints.graph.get_graph_counts', side_effect=RuntimeError('query failed')):
        r = client.get('/v1/graph/health')

    assert r.status_code == 200
    body = r.json()
    assert body['connected'] is True
    assert 'counts_error' in body
