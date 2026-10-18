import importlib
from unittest.mock import MagicMock, patch

import src.data_stores.weaviate_client as weaviate_client


def _reload():
    importlib.reload(weaviate_client)
    return weaviate_client


def test_connects_to_weaviate_cloud_when_url_is_cloud():
    with patch('src.core.config.WEAVIATE_URL', 'https://abc123.c0.us-west3.gcp.weaviate.cloud'), \
         patch('src.core.config.WEAVIATE_API_KEY', 'fake-key'):
        wc = _reload()
        wc._client = None
        with patch.object(wc, 'weaviate') as mock_weaviate:
            mock_weaviate.connect_to_weaviate_cloud.return_value = MagicMock()
            wc.get_weaviate_client()

        assert mock_weaviate.connect_to_weaviate_cloud.called
        assert not mock_weaviate.connect_to_local.called
        kwargs = mock_weaviate.connect_to_weaviate_cloud.call_args.kwargs
        assert kwargs['cluster_url'] == 'https://abc123.c0.us-west3.gcp.weaviate.cloud'


def test_raises_clear_error_when_cloud_url_missing_api_key():
    with patch('src.core.config.WEAVIATE_URL', 'https://abc123.c0.us-west3.gcp.weaviate.cloud'), \
         patch('src.core.config.WEAVIATE_API_KEY', ''):
        wc = _reload()
        wc._client = None

        try:
            wc.get_weaviate_client()
            assert False, 'expected RuntimeError'
        except RuntimeError as exc:
            assert 'WEAVIATE_API_KEY' in str(exc)


def test_connects_to_local_when_url_is_plain_http():
    with patch('src.core.config.WEAVIATE_URL', 'http://localhost:8080'), \
         patch('src.core.config.WEAVIATE_API_KEY', None):
        wc = _reload()
        wc._client = None
        with patch.object(wc, 'weaviate') as mock_weaviate:
            mock_weaviate.connect_to_local.return_value = MagicMock()
            wc.get_weaviate_client()

        assert mock_weaviate.connect_to_local.called
        assert not mock_weaviate.connect_to_weaviate_cloud.called
        kwargs = mock_weaviate.connect_to_local.call_args.kwargs
        assert kwargs == {'host': 'localhost', 'port': 8080}


def test_raises_clear_error_when_weaviate_client_is_old_v3():
    wc = _reload()
    wc._client = None
    with patch.object(wc, '_weaviate_v4', False), \
         patch.object(wc, '_weaviate_available', True):
        try:
            wc.get_weaviate_client()
            assert False, 'expected RuntimeError'
        except RuntimeError as exc:
            assert 'v3 client' in str(exc)
            assert 'pip install --upgrade' in str(exc)
