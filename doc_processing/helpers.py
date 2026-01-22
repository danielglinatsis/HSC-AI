from typing import Iterable, List, Union
from langchain_core.documents import Document


def flatten(items: Iterable[Union[list, tuple, any]]) -> List:
    """
    Flattens lists
    """
    flattened = []
    for item in items or []:
        if isinstance(item, (list, tuple)):
            flattened.extend(flatten(item))
        else:
            flattened.append(item)
    return flattened

def docs_to_texts_and_meta(docs: List[Document]):
    return (
        [d.page_content for d in docs],
        [d.metadata for d in docs],
    )