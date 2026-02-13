import re
from typing import Iterable, List, Union
from langchain_core.documents import Document


def flatten(items: Iterable[Union[list, tuple, any]]) -> List:
    '''
    Flattens lists
    '''
    flattened = []
    for item in items or []:
        if isinstance(item, (list, tuple)):
            flattened.extend(flatten(item))
        else:
            flattened.append(item)
    return flattened

def docs_to_texts_and_meta(docs: List[Document]):
    '''Splits a list of Documents into a (texts, metadatas) tuple'''
    return (
        [d.page_content for d in docs],
        [d.metadata for d in docs],
    )


def print_question(data, exam_name, question_number):
    '''
    Prints the specified printed question (e.g. Question 29)
    '''
    if isinstance(data, dict):
        all_qs = data.get("questions", [])
    else:
        all_qs = data

    pattern = None
    if question_number is not None:
        pattern = re.compile(rf"\bQuestion\s+{question_number}\b", re.IGNORECASE)

    for item in all_qs:
        questions = item if isinstance(item, list) else [item]

        for q in questions:
            if not isinstance(q, dict):
                continue
            if q.get("exam") != exam_name:
                continue

            if pattern:
                if pattern.search(q.get("text", "")):
                    print(f"Exam: {exam_name}")
                    print(f"Page: {q.get('page')}\n")
                    print(q.get("text"))
                    return 
            else:
                print(f"Exam: {exam_name}")
                print(f"Page: {q.get('page')}\n")
                print(q.get("text"))