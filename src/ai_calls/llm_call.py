import sys
import json
import google.generativeai as genai
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.constants import LLM_INSTRUCTIONS, AI_MODEL
from src.doc_processing import syllabus_extractor

def analyse_syllabus(query, syllabus): 

    def read_syllabus(syllabus):
        with open(syllabus, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)

    syllabus_content = read_syllabus(syllabus)

    llm_call = f"""
    {LLM_INSTRUCTIONS}

    User query: {query}

    Syllabus: {syllabus_content}

    """
    model = genai.GenerativeModel(AI_MODEL)
    response = model.generate_content(llm_call)

    return response.text