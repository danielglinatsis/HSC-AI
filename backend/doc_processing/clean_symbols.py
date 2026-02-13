# TODO: Implement "mapping" of math characters to text

import re

integral_mapping = {
    'dx' : 'dx (integration)',
    'dt' : 'dt (integration)'
    }

def clean_math(data):
    '''
    Cleans all math symbols and 'interprets' symbols to improve retrieval results
    Expects a dictionary with 'metadata' and 'questions'
    '''
    if not isinstance(data, dict):
        all_qs = data
        metadata = []
    else:
        all_qs = data.get('questions', [])
        metadata = data.get('metadata', [])

    cleaned_questions = []

    for exam_qs in all_qs:
        cleaned_exam_qs = []
        for q in exam_qs:
            text = q.get('text', '')
            for key, replacement in integral_mapping.items():
                text = re.sub(rf'(?<![a-zA-Z]){key}(?![a-zA-Z])', replacement, text)
            cleaned_exam_qs.append({
                **q,
                'text': text
            })
        cleaned_questions.append(cleaned_exam_qs)

    result = {
        "metadata": metadata,
        "questions": cleaned_questions
    }
    return result
