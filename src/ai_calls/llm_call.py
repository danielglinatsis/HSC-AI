import sys
import json
import google.generativeai as genai
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.constants import LLM_INSTRUCTIONS, AI_MODEL

def analyse_syllabus(questions, syllabus): 

    def read_syllabus(syllabus):
        with open(syllabus, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data)

    syllabus_content = read_syllabus(syllabus)

    llm_call = f"""
    {LLM_INSTRUCTIONS}

    Exam questions: {questions}

    Syllabus tags: {syllabus_content}
"""

    model = genai.GenerativeModel(AI_MODEL)
    response = model.generate_content(llm_call)

    return response.text.strip()