import json
import re
from typing import Any, Callable, Dict, Optional

from groq import Groq

from prompts import (
    PLANNING_SYSTEM,
    PLANNING_USER,
    CONTENT_SYSTEM,
    CONTENT_USER,
    ASSESSMENT_SYSTEM,
    ASSESSMENT_USER,
    REVIEW_SYSTEM,
    REVIEW_USER,
    REFINEMENT_SYSTEM,
    REFINEMENT_USER,
    REPAIR_SYSTEM,
    REPAIR_USER,
)


MODEL = "openai/gpt-oss-120b"


def get_api_key() -> Optional[str]:
    """Get Groq API key from Streamlit secrets or environment."""
    try:
        import streamlit as st

        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass

    import os
    return os.getenv("GROQ_API_KEY")


def get_client() -> Groq:
    key = get_api_key()

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit Community Cloud "
            "Secrets as GROQ_API_KEY."
        )

    return Groq(api_key=key)


def parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON and recover from accidental Markdown code fences."""
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise ValueError(
            "The AI returned an invalid JSON response."
        )


def call_ai(
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Centralized Groq call used by every workflow stage."""
    client = get_client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return parse_json(
        response.choices[0].message.content
    )


def validate_pack(
    pack: Dict[str, Any],
    flashcard_count: int,
    mcq_count: int,
) -> None:
    """Deterministic validation before the result reaches the user."""

    required = [
        "summary",
        "key_points",
        "flashcards",
        "mcqs",
        "study_plan",
        "exam_tips",
    ]

    missing = [
        field for field in required
        if field not in pack
    ]

    if missing:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(missing)
        )

    if len(pack["flashcards"]) != flashcard_count:
        raise ValueError(
            f"Expected {flashcard_count} flashcards, "
            f"got {len(pack['flashcards'])}."
        )

    if len(pack["mcqs"]) != mcq_count:
        raise ValueError(
            f"Expected {mcq_count} MCQs, "
            f"got {len(pack['mcqs'])}."
        )

    for number, mcq in enumerate(pack["mcqs"], start=1):
        options = mcq.get("options", [])

        if len(options) != 4:
            raise ValueError(
                f"MCQ {number} must have exactly 4 options."
            )

        if mcq.get("answer") not in options:
            raise ValueError(
                f"MCQ {number} answer does not match "
                "one of its options."
            )


def stage_planning(
    subject: str,
    topic: str,
    level: str,
    learning_goal: str,
    study_time: str,
    notes: str,
) -> Dict[str, Any]:
    user_prompt = PLANNING_USER.format(
        subject=subject or "General",
        topic=topic,
        level=level,
        learning_goal=learning_goal or "Understand the topic and prepare for assessment.",
        study_time=study_time,
        notes=notes[:12000] if notes else "No notes provided.",
    )

    return call_ai(
        PLANNING_SYSTEM,
        user_prompt,
    )


def stage_content(
    profile: Dict[str, Any],
    planning: Dict[str, Any],
    flashcard_count: int,
    mcq_count: int,
) -> Dict[str, Any]:
    user_prompt = CONTENT_USER.format(
        profile=json.dumps(
            profile,
            ensure_ascii=False,
        ),
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    return call_ai(
        CONTENT_SYSTEM,
        user_prompt,
    )


def stage_assessment(
    planning: Dict[str, Any],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = ASSESSMENT_USER.format(
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        ASSESSMENT_SYSTEM,
        user_prompt,
    )


def stage_review(
    profile: Dict[str, Any],
    planning: Dict[str, Any],
    content: Dict[str, Any],
    assessment: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = REVIEW_USER.format(
        profile=json.dumps(
            profile,
            ensure_ascii=False,
        ),
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        REVIEW_SYSTEM,
        user_prompt,
    )


def stage_refinement(
    planning: Dict[str, Any],
    content: Dict[str, Any],
    assessment: Dict[str, Any],
    review: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = REFINEMENT_USER.format(
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
        ),
        review=json.dumps(
            review,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        REFINEMENT_SYSTEM,
        user_prompt,
    )


def repair_pack(
    pack: Dict[str, Any],
    error: str,
    flashcard_count: int,
    mcq_count: int,
) -> Dict[str, Any]:
    user_prompt = REPAIR_USER.format(
        pack=json.dumps(
            pack,
            ensure_ascii=False,
        ),
        error=error,
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    return call_ai(
        REPAIR_SYSTEM,
        user_prompt,
    )


def run_workflow(
    subject: str,
    topic: str,
    level: str,
    learning_goal: str,
    study_time: str,
    notes: str,
    flashcard_count: int,
    mcq_count: int,
    progress_callback: Optional[
        Callable[[str, str], None]
    ] = None,
) -> Dict[str, Any]:
    """Run the complete multi-stage AI workflow."""

    def progress(stage: str, message: str):
        if progress_callback:
            progress_callback(stage, message)

    profile = {
        "subject": subject or "General",
        "topic": topic,
        "level": level,
        "learning_goal": learning_goal,
        "study_time": study_time,
    }

    # Stage 1 — Planning
    progress(
        "① Planning",
        "Creating personalized learning objectives and concept sequence...",
    )

    planning = stage_planning(
        subject=subject,
        topic=topic,
        level=level,
        learning_goal=learning_goal,
        study_time=study_time,
        notes=notes,
    )

    # Stage 2 — Content
    progress(
        "② Content Generation",
        "Generating summary, key points, flashcards, MCQs and study plan...",
    )

    content = stage_content(
        profile=profile,
        planning=planning,
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    # Stage 3 — Assessment
    progress(
        "③ Assessment",
        "Evaluating accuracy, coverage, difficulty and consistency...",
    )

    assessment = stage_assessment(
        planning=planning,
        content=content,
    )

    # Stage 4 — Review
    progress(
        "④ Review",
        "Performing an editorial review and identifying priority fixes...",
    )

    review = stage_review(
        profile=profile,
        planning=planning,
        content=content,
        assessment=assessment,
    )

    # Stage 5 — Refinement
    progress(
        "⑤ Refinement",
        "Applying review feedback while preserving correct content...",
    )

    refined = stage_refinement(
        planning=planning,
        content=content,
        assessment=assessment,
        review=review,
    )

    # Validation + one automated repair attempt
    progress(
        "⑥ Validation",
        "Checking output structure and MCQ/flashcard requirements...",
    )

    try:
        validate_pack(
            refined,
            flashcard_count,
            mcq_count,
        )
    except ValueError as validation_error:
        progress(
            "⑦ Error Recovery",
            "Validation found a problem. Running one automated repair pass...",
        )

        repaired = repair_pack(
            pack=refined,
            error=str(validation_error),
            flashcard_count=flashcard_count,
            mcq_count=mcq_count,
        )

        validate_pack(
            repaired,
            flashcard_count,
            mcq_count,
        )

        refined = repaired

    progress(
        "⑧ Complete",
        "Final study pack passed validation.",
    )

    return {
        "profile": profile,
        "planning": planning,
        "content": refined,
        "assessment": assessment,
        "review": review,
    }
    import os
    return os.getenv("GROQ_API_KEY")


def get_client() -> Groq:
    key = get_api_key()

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit Community Cloud "
            "Secrets as GROQ_API_KEY."
        )

    return Groq(api_key=key)


def parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON and recover from accidental Markdown code fences."""
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise ValueError(
            "The AI returned an invalid JSON response."
        )


def call_ai(
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Centralized Groq call used by every workflow stage."""
    client = get_client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.3,
    )

    return parse_json(
        response.choices[0].message.content
    )


def validate_pack(
    pack: Dict[str, Any],
    flashcard_count: int,
    mcq_count: int,
) -> None:
    """Deterministic validation before the result reaches the user."""

    required = [
        "summary",
        "key_points",
        "flashcards",
        "mcqs",
        "study_plan",
        "exam_tips",
    ]

    missing = [
        field for field in required
        if field not in pack
    ]

    if missing:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(missing)
        )

    if len(pack["flashcards"]) != flashcard_count:
        raise ValueError(
            f"Expected {flashcard_count} flashcards, "
            f"got {len(pack['flashcards'])}."
        )

    if len(pack["mcqs"]) != mcq_count:
        raise ValueError(
            f"Expected {mcq_count} MCQs, "
            f"got {len(pack['mcqs'])}."
        )

    for number, mcq in enumerate(pack["mcqs"], start=1):
        options = mcq.get("options", [])

        if len(options) != 4:
            raise ValueError(
                f"MCQ {number} must have exactly 4 options."
            )

        if mcq.get("answer") not in options:
            raise ValueError(
                f"MCQ {number} answer does not match "
                "one of its options."
            )


def stage_planning(
    subject: str,
    topic: str,
    level: str,
    learning_goal: str,
    study_time: str,
    notes: str,
) -> Dict[str, Any]:
    user_prompt = PLANNING_USER.format(
        subject=subject or "General",
        topic=topic,
        level=level,
        learning_goal=learning_goal or "Understand the topic and prepare for assessment.",
        study_time=study_time,
        notes=notes[:12000] if notes else "No notes provided.",
    )

    return call_ai(
        PLANNING_SYSTEM,
        user_prompt,
    )


def stage_content(
    profile: Dict[str, Any],
    planning: Dict[str, Any],
    flashcard_count: int,
    mcq_count: int,
) -> Dict[str, Any]:
    user_prompt = CONTENT_USER.format(
        profile=json.dumps(
            profile,
            ensure_ascii=False,
        ),
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    return call_ai(
        CONTENT_SYSTEM,
        user_prompt,
    )


def stage_assessment(
    planning: Dict[str, Any],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = ASSESSMENT_USER.format(
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        ASSESSMENT_SYSTEM,
        user_prompt,
    )


def stage_review(
    profile: Dict[str, Any],
    planning: Dict[str, Any],
    content: Dict[str, Any],
    assessment: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = REVIEW_USER.format(
        profile=json.dumps(
            profile,
            ensure_ascii=False,
        ),
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        REVIEW_SYSTEM,
        user_prompt,
    )


def stage_refinement(
    planning: Dict[str, Any],
    content: Dict[str, Any],
    assessment: Dict[str, Any],
    review: Dict[str, Any],
) -> Dict[str, Any]:
    user_prompt = REFINEMENT_USER.format(
        planning=json.dumps(
            planning,
            ensure_ascii=False,
        ),
        content=json.dumps(
            content,
            ensure_ascii=False,
        ),
        assessment=json.dumps(
            assessment,
            ensure_ascii=False,
        ),
        review=json.dumps(
            review,
            ensure_ascii=False,
        ),
    )

    return call_ai(
        REFINEMENT_SYSTEM,
        user_prompt,
    )


def repair_pack(
    pack: Dict[str, Any],
    error: str,
    flashcard_count: int,
    mcq_count: int,
) -> Dict[str, Any]:
    user_prompt = REPAIR_USER.format(
        pack=json.dumps(
            pack,
            ensure_ascii=False,
        ),
        error=error,
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    return call_ai(
        REPAIR_SYSTEM,
        user_prompt,
    )


def run_workflow(
    subject: str,
    topic: str,
    level: str,
    learning_goal: str,
    study_time: str,
    notes: str,
    flashcard_count: int,
    mcq_count: int,
    progress_callback: Optional[
        Callable[[str, str], None]
    ] = None,
) -> Dict[str, Any]:
    """Run the complete multi-stage AI workflow."""

    def progress(stage: str, message: str):
        if progress_callback:
            progress_callback(stage, message)

    profile = {
        "subject": subject or "General",
        "topic": topic,
        "level": level,
        "learning_goal": learning_goal,
        "study_time": study_time,
    }

    # Stage 1 — Planning
    progress(
        "① Planning",
        "Creating personalized learning objectives and concept sequence...",
    )

    planning = stage_planning(
        subject=subject,
        topic=topic,
        level=level,
        learning_goal=learning_goal,
        study_time=study_time,
        notes=notes,
    )

    # Stage 2 — Content
    progress(
        "② Content Generation",
        "Generating summary, key points, flashcards, MCQs and study plan...",
    )

    content = stage_content(
        profile=profile,
        planning=planning,
        flashcard_count=flashcard_count,
        mcq_count=mcq_count,
    )

    # Stage 3 — Assessment
    progress(
        "③ Assessment",
        "Evaluating accuracy, coverage, difficulty and consistency...",
    )

    assessment = stage_assessment(
        planning=planning,
        content=content,
    )

    # Stage 4 — Review
    progress(
        "④ Review",
        "Performing an editorial review and identifying priority fixes...",
    )

    review = stage_review(
        profile=profile,
        planning=planning,
        content=content,
        assessment=assessment,
    )

    # Stage 5 — Refinement
    progress(
        "⑤ Refinement",
        "Applying review feedback while preserving correct content...",
    )

    refined = stage_refinement(
        planning=planning,
        content=content,
        assessment=assessment,
        review=review,
    )

    # Validation + one automated repair attempt
    progress(
        "⑥ Validation",
        "Checking output structure and MCQ/flashcard requirements...",
    )

    try:
        validate_pack(
            refined,
            flashcard_count,
            mcq_count,
        )
    except ValueError as validation_error:
        progress(
            "⑦ Error Recovery",
            "Validation found a problem. Running one automated repair pass...",
        )

        repaired = repair_pack(
            pack=refined,
            error=str(validation_error),
            flashcard_count=flashcard_count,
            mcq_count=mcq_count,
        )

        validate_pack(
            repaired,
            flashcard_count,
            mcq_count,
        )

        refined = repaired

    progress(
        "⑧ Complete",
        "Final study pack passed validation.",
    )

    return {
        "profile": profile,
        "planning": planning,
        "content": refined,
        "assessment": assessment,
        "review": review,
    }
