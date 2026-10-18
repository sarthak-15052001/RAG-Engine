from typing import Any, List, TypedDict

from langgraph.graph import StateGraph, START, END

from src.ingestion.nodes import load_node, split_node, store_node, graph_node


class IngestionState(TypedDict, total=False):
    file: str
    job_id: str
    docs: List[Any]
    chunks: List[Any]
    stored: bool
    vectors_stored: int
    vectors_failed: int
    graph_entities_stored: int


def build_ingestion_pipeline():
    graph = StateGraph(IngestionState)

    graph.add_node('load', load_node)
    graph.add_node('split', split_node)
    graph.add_node('store', store_node)
    graph.add_node('graph', graph_node)

    graph.add_edge(START, 'load')
    graph.add_edge('load', 'split')
    # store (Weaviate) and graph (Neo4j) both only need `chunks`, and are
    # independent of each other, so they run as parallel branches.
    graph.add_edge('split', 'store')
    graph.add_edge('split', 'graph')
    graph.add_edge('store', END)
    graph.add_edge('graph', END)

    return graph.compile()
