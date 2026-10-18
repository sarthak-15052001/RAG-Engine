from neo4j import GraphDatabase

from src.core.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from src.core.logging_config import get_logger

logger = get_logger('neo4j.client')
_driver = None


def get_driver():
    """Lazily create and cache the Neo4j driver."""
    global _driver
    if _driver is not None:
        return _driver

    if not NEO4J_PASSWORD:
        logger.error('❌ [NEO4J] NEO4J_PASSWORD environment variable is not set!')
        raise RuntimeError(
            'NEO4J_PASSWORD is not set. Configure NEO4J_URI / NEO4J_USERNAME / '
            'NEO4J_PASSWORD in your .env to use the graph features.'
        )

    logger.info(f'🔌 [NEO4J] Connecting to Neo4j database at {NEO4J_URI} (user: {NEO4J_USERNAME})...')
    _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        logger.info('🔌 [NEO4J] Closing active Neo4j driver...')
        _driver.close()
        _driver = None


def verify_connectivity():
    """Raises if Neo4j isn't reachable."""
    logger.info('🔍 [NEO4J] Verifying connection status...')
    driver = get_driver()
    driver.verify_connectivity()
    logger.info('✅ [NEO4J] Connection verified successfully!')


def _graph_counts_tx(tx):
    documents = tx.run('MATCH (d:Document) RETURN count(d) AS n').single()['n']
    entities = tx.run('MATCH (e:Entity) RETURN count(e) AS n').single()['n']
    mentions = tx.run('MATCH ()-[r:MENTIONS]->() RETURN count(r) AS n').single()['n']
    return {'documents': documents, 'entities': entities, 'mentions': mentions}


def get_graph_counts():
    driver = get_driver()
    with driver.session() as session:
        counts = session.execute_read(_graph_counts_tx)
        logger.info(
            f'📊 [NEO4J STATS] Graph contains {counts["documents"]} Document(s), '
            f'{counts["entities"]} Entity(ies), and {counts["mentions"]} MENTIONS relation(s).'
        )
        return counts


def ensure_constraints():
    logger.info('⚙️ [NEO4J] Setting up node key and uniqueness constraints...')
    driver = get_driver()
    with driver.session() as session:
        session.run(
            'CREATE CONSTRAINT document_source_unique IF NOT EXISTS '
            'FOR (d:Document) REQUIRE d.source IS UNIQUE'
        )
        session.run(
            'CREATE CONSTRAINT entity_name_type_unique IF NOT EXISTS '
            'FOR (e:Entity) REQUIRE (e.name, e.type) IS NODE KEY'
        )
    logger.info('✅ [NEO4J] Database constraints ensured successfully.')


def _store_document_entities_tx(tx, source, entities):
    tx.run(
        'MERGE (d:Document {source: $source})',
        source=source,
    )
    for entity in entities:
        tx.run(
            '''
            MERGE (e:Entity {name: $name, type: $type})
            WITH e
            MATCH (d:Document {source: $source})
            MERGE (d)-[:MENTIONS]->(e)
            ''',
            name=entity['name'],
            type=entity['type'],
            source=source,
        )


def store_document_entities(source: str, entities: list):
    logger.info(
        f'🕸️ [NEO4J WRITE] Writing Document node ("{source}") and '
        f'{len(entities)} unique Entity relation(s) to Neo4j Knowledge Graph...'
    )
    driver = get_driver()
    with driver.session() as session:
        session.execute_write(_store_document_entities_tx, source, entities)
    logger.info(f'✅ [NEO4J WRITE] Successfully updated Knowledge Graph for source "{source}".')


def _related_entities_tx(tx, entity_name):
    result = tx.run(
        '''
        MATCH (e:Entity {name: $name})<-[:MENTIONS]-(d:Document)-[:MENTIONS]->(other:Entity)
        WHERE other.name <> $name
        RETURN DISTINCT other.name AS name, other.type AS type
        LIMIT 25
        ''',
        name=entity_name,
    )
    return [{'name': record['name'], 'type': record['type']} for record in result]


def get_related_entities(entity_name: str):
    logger.info(f'🔍 [NEO4J QUERY] Fetching entities related to "{entity_name}"...')
    driver = get_driver()
    with driver.session() as session:
        results = session.execute_read(_related_entities_tx, entity_name)
        logger.info(f'✅ [NEO4J QUERY] Found {len(results)} related entity(ies) for "{entity_name}".')
        return results


def _documents_mentioning_tx(tx, entity_name):
    result = tx.run(
        '''
        MATCH (d:Document)-[:MENTIONS]->(e:Entity {name: $name})
        RETURN DISTINCT d.source AS source
        ''',
        name=entity_name,
    )
    return [record['source'] for record in result]


def get_documents_mentioning(entity_name: str):
    logger.info(f'🔍 [NEO4J QUERY] Fetching documents mentioning entity "{entity_name}"...')
    driver = get_driver()
    with driver.session() as session:
        results = session.execute_read(_documents_mentioning_tx, entity_name)
        logger.info(f'✅ [NEO4J QUERY] Found {len(results)} document(s) mentioning "{entity_name}".')
        return results
