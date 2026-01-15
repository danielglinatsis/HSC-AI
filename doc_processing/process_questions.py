import os
import sys
import pickle
from pathlib import Path

import doc_extractor

def process_questions(all_metadata, all_qs):
    out_path = Path("doc_processing/data/all_questions.pkl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("wb") as f:
        pickle.dump(
            {
                "metadata": all_metadata,
                "questions": all_qs,
            },
            f, 
            protocol=pickle.HIGHEST_PROTOCOL
        )

if __name__ == "__main__":
    all_metadata, all_qs = doc_extractor.all_questions()
    process_questions(all_metadata, all_qs)