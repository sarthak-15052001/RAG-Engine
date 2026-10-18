from unittest.mock import MagicMock, patch

from src.utils.entity_extractor import extract_entities, EntityList, ExtractedEntity


def test_extract_entities_empty_text_returns_empty_list():
    assert extract_entities('') == []
    assert extract_entities('   ') == []


def test_extract_entities_returns_parsed_entities():
    fake_result = EntityList(entities=[
        ExtractedEntity(name='Marie Curie', type='PERSON'),
        ExtractedEntity(name='Paris', type='LOCATION'),
    ])

    with patch('src.utils.entity_extractor._get_extractor', return_value=MagicMock()), \
         patch('src.utils.entity_extractor._prompt') as mock_prompt:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = fake_result
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        entities = extract_entities('Marie Curie worked in Paris.')

    assert len(entities) == 2
    assert entities[0].name == 'Marie Curie'
    assert entities[0].type == 'PERSON'


def test_extract_entities_returns_empty_list_on_llm_failure():
    with patch('src.utils.entity_extractor._get_extractor', return_value=MagicMock()), \
         patch('src.utils.entity_extractor._prompt') as mock_prompt:
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = RuntimeError('API error')
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        entities = extract_entities('some text')

    assert entities == []
