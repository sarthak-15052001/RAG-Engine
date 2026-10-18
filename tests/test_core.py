import pytest
from src.core.config import EMBEDDING_MODEL
from src.core.security import verify_token


def test_embedding_model():
    assert EMBEDDING_MODEL == 'text-embedding-ada-002'


def test_verify_token_empty():
    with pytest.raises(ValueError):
        verify_token('')
