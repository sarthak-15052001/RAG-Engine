from src.ingestion.ingestion_pipelines import build_ingestion_pipeline


# Backwards-compatible API for existing code

def load_node(state):
    return state


def split_node(state):
    return state


def store_node(state):
    return state


def build_graph():
    return build_ingestion_pipeline()
