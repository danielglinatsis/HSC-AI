import os
import sys
import pickle
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -------------------------------------------------
# Allow importing constants from project root
# -------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
for p in (REPO_ROOT, SRC_ROOT):
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config.constants import PICKLE_PATH, SYLLABUS_DIR, PROJECT_ROOT as CONSTANTS_PROJECT_ROOT, LLM_INSTRUCTIONS, AI_MODEL


def load_syllabus(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_syllabus(text: str) -> List[Dict[str, Any]]:

    if not text:
        raise ValueError("Empty LLM response")

    cleaned = text.strip()
    # Remove fenced code blocks if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not locate JSON array in response: {cleaned[:200]}")

    payload = cleaned[start : end + 1]
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("LLM response JSON was not an array")
    # Ensure dict items
    out: List[Dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            out.append(item)
    return out


def build_question_id(exam: str, page: Any, index_in_exam: int) -> str:
    return f"{exam}::p{page}::q{index_in_exam:03d}"


def iterate_questions(data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:

    all_qs = data.get("questions", [])
    out: List[Tuple[str, Dict[str, Any]]] = []
    for exam_qs in all_qs:
        if not isinstance(exam_qs, list):
            continue
        for i, q in enumerate(exam_qs, start=1):
            if not isinstance(q, dict):
                continue
            exam = str(q.get("exam", "unknown_exam"))
            page = q.get("page", "unknown_page")
            qid = build_question_id(exam=exam, page=page, index_in_exam=i)
            out.append((qid, q))
    return out


def tag_questions_with_llm(
    data: Dict[str, Any],
    *,
    syllabus_path: Optional[Path] = None,
    batch_size: int = 8,
) -> Dict[str, Any]:
    """
    Final pre-processing step: use an LLM to assign syllabus tags to each question.

    This function mutates question dicts in-place by adding (as available):
      - `syllabus_tags`: list[dict] (controlled tag set; topic + subtopic)
      - `difficulty`: str
      - `skill_types`: list[str]

    These keys become retriever metadata automatically (see `retriever_setup.py`).
    """
    if not isinstance(data, dict):
        raise TypeError("tag_questions_with_llm expects a dict with keys: metadata/questions")

    # Resolve syllabus JSON relative to repo root (constants uses a relative string)
    if syllabus_path is None:
        syllabus_path = (CONSTANTS_PROJECT_ROOT / SYLLABUS_DIR).resolve()

    # Configure API key (safe to call multiple times)
    try:
        from setup import ai_model_setup

        ai_model_setup.google_api_setup()
    except Exception as e:
        # Continue; generate_content will fail with a clearer error if not configured
        print(f"Warning: could not configure Google API key automatically: {e}")

    # Load controlled tag set (json) once
    syllabus = load_syllabus(syllabus_path)

    # Prepare questions with stable IDs; skip any already tagged in a previous run
    flat = [
        (qid, q)
        for (qid, q) in iterate_questions(data)
        if not q.get("llm_tagged")
    ]
    if not flat:
        print("All questions already tagged; skipping LLM tagging.")
        return data
    print(f"Tagging {len(flat)} untagged question(s) with LLM...")

    # Local import so module can be imported without genai installed/configured
    import google.generativeai as genai

    model = genai.GenerativeModel(AI_MODEL)

    # Batch and tag
    for start in range(0, len(flat), batch_size):
        batch = flat[start : start + batch_size]

        batch_payload = [
            {
                "id": qid,
                "text": q.get("text", ""),
                "marks": q.get("marks"),  # often missing; included if present
                "metadata": {k: v for k, v in q.items() if k != "text"},
            }
            for (qid, q) in batch
        ]

        prompt = f"""{LLM_INSTRUCTIONS}

Input batch (JSON):
{json.dumps(batch_payload, ensure_ascii=False)}

Controlled syllabus tag set (JSON):
{json.dumps(syllabus, ensure_ascii=False)}
"""
        try:
            response = model.generate_content(prompt)
            items = extract_syllabus((response.text or "").strip())
        except Exception as e:
            print(f"Warning: LLM tagging failed for batch {start//batch_size + 1}: {e}")
            continue

        by_id: Dict[str, Dict[str, Any]] = {qid: q for (qid, q) in batch}

        for item in items:
            qid = item.get("id")
            if not qid or qid not in by_id:
                continue

            q = by_id[qid]

            # Store the model outputs as question metadata fields
            if "syllabus_tags" in item and isinstance(item["syllabus_tags"], list):
                q["syllabus_tags"] = item["syllabus_tags"]
                # Convenience: a flat string list for retrieval/filtering
                flat_tags: List[str] = []
                for t in item["syllabus_tags"]:
                    if not isinstance(t, dict):
                        continue
                    topic = t.get("topic")
                    subtopic = t.get("subtopic")
                    if isinstance(topic, str) and isinstance(subtopic, str):
                        flat_tags.append(f"{topic} / {subtopic}")
                    elif isinstance(topic, str):
                        flat_tags.append(topic)
                if flat_tags:
                    q["tags"] = flat_tags

            if "difficulty" in item and isinstance(item["difficulty"], str):
                q["difficulty"] = item["difficulty"]

            if "skill_types" in item and isinstance(item["skill_types"], list):
                q["skill_types"] = item["skill_types"]

            # Backward/alternate key compatibility if the model follows older wording
            if "topics" in item and "syllabus_tags" not in q:
                q["topics"] = item["topics"]
            if "subtopics" in item and "syllabus_tags" not in q:
                q["subtopics"] = item["subtopics"]

            q["llm_tagged"] = True

    return data


def save_questions(data: Dict[str, Any], out_path: str | Path = PICKLE_PATH) -> None:
    """
    Persists the processed questions back to disk (pickle).
    Default path matches the app's expected `PICKLE_PATH`.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


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
    tagged_data = tag_questions_with_llm(cleaned_data)
    save_questions(tagged_data)
    helpers.print_question(tagged_data, "2022-hsc-mathematics-advanced.pdf", 16)