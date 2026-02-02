import os
import sys
import pickle
from pathlib import Path

# -------------------------------------------------
# Allow importing constants from project root
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.constants import PICKLE_PATH

def process_questions(all_metadata, all_qs):
    out_path = Path("doc_processing/data/all_questions.pkl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "metadata": all_metadata,
        "questions": all_qs,
    }

    with out_path.open("wb") as f:
        pickle.dump(
            data,
            f, 
            protocol=pickle.HIGHEST_PROTOCOL
        )
    return data

def load_questions():
    with open(PICKLE_PATH, "rb") as f:
        data = pickle.load(f)
    return data


if __name__ == "__main__":
    data = load_questions()
    from doc_processing import clean_symbols, helpers

    cleaned_data = clean_symbols.clean_math(data)
    helpers.print_question(cleaned_data, "2024-hsc-maths-adv.pdf", 27)