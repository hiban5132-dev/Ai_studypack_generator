import json
import streamlit as st

from workflow import run_workflow


st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Study Pack Generator")
st.caption(
    "A multi-stage AI workflow: Planning → Content Generation → Assessment → Review → Refinement"
)

with st.sidebar:
    st.header("🎓 Student Profile")

    subject = st.text_input("Subject", placeholder="e.g. Biology")
    topic = st.text_input("Topic", placeholder="e.g. Photosynthesis")

    level = st.selectbox(
        "Knowledge Level",
        ["Beginner", "Intermediate", "Advanced"],
    )

    learning_goal = st.text_area(
        "Learning Goal",
        placeholder="e.g. Prepare for my university exam",
    )

    study_time = st.selectbox(
        "Available Study Time",
        ["30 minutes", "60 minutes", "2 hours", "3 hours", "1 day"],
    )

    flashcard_count = st.slider(
        "Number of Flashcards",
        min_value=3,
        max_value=15,
        value=8,
    )

    mcq_count = st.slider(
        "Number of MCQs",
        min_value=3,
        max_value=15,
        value=5,
    )

st.subheader("📝 Optional Study Notes")
uploaded_file = st.file_uploader(
    "Upload TXT or Markdown notes",
    type=["txt", "md"],
)

notes = ""
if uploaded_file:
    notes = uploaded_file.read().decode("utf-8", errors="ignore")
    st.success(f"Loaded notes: {uploaded_file.name}")

st.info(
    "The workflow passes structured context between AI stages. "
    "A final validation and repair step protects the output from common formatting errors."
)

if st.button(
    "🚀 Generate Personalized Study Pack",
    type="primary",
    use_container_width=True,
):
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        status = st.status("Starting AI workflow...", expanded=True)

        def progress(stage, message):
            status.write(f"**{stage}** — {message}")

        try:
            result = run_workflow(
                subject=subject,
                topic=topic,
                level=level,
                learning_goal=learning_goal,
                study_time=study_time,
                notes=notes,
                flashcard_count=flashcard_count,
                mcq_count=mcq_count,
                progress_callback=progress,
            )

            st.session_state["workflow_result"] = result
            status.update(
                label="✅ Workflow completed successfully",
                state="complete",
                expanded=False,
            )

        except Exception as exc:
            status.update(
                label="❌ Workflow failed",
                state="error",
                expanded=True,
            )
            st.error(
                "The study pack could not be generated. "
                "Check your GROQ_API_KEY and Streamlit logs."
            )
            st.exception(exc)

if "workflow_result" in st.session_state:
    result = st.session_state["workflow_result"]
    planning = result["planning"]
    assessment = result["assessment"]
    review = result["review"]
    content = result["content"]

    st.divider()
    st.subheader("📊 Workflow Quality Report")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall", f'{assessment.get("overall_score", 0)}/100')
    c2.metric("Accuracy", f'{assessment.get("accuracy_score", 0)}/100')
    c3.metric("Coverage", f'{assessment.get("coverage_score", 0)}/100')
    c4.metric("Readability", review.get("student_readability", "—"))

    with st.expander("🧭 View Planning Stage"):
        st.write("**Learning Objectives**")
        for item in planning.get("learning_objectives", []):
            st.markdown(f"- {item}")

        st.write("**Concept Sequence**")
        for item in planning.get("concept_sequence", []):
            st.markdown(
                f"**{item.get('order', '')}. {item.get('concept', '')}** — "
                f"{item.get('reason', '')}"
            )

        st.write("**Personalization Notes**")
        for item in planning.get("personalization_notes", []):
            st.markdown(f"- {item}")

    st.subheader("📚 Study Summary")
    st.write(content.get("summary", ""))

    st.subheader("🔑 Key Points")
    for point in content.get("key_points", []):
        st.markdown(f"- {point}")

    st.subheader("🧠 Flashcards")
    for i, card in enumerate(content.get("flashcards", []), 1):
        with st.expander(f"Flashcard {i}: {card.get('question', '')}"):
            st.write(card.get("answer", ""))

    st.subheader("📝 MCQs")
    for i, mcq in enumerate(content.get("mcqs", []), 1):
        st.markdown(f"**{i}. {mcq.get('question', '')}**")

        options = mcq.get("options", [])
        answer = st.radio(
            "Select an answer:",
            options,
            index=None,
            key=f"mcq_answer_{i}",
        )

        if answer is not None:
            if answer == mcq.get("answer"):
                st.success("✅ Correct!")
            else:
                st.error("❌ Incorrect.")
                st.write(f"Correct answer: **{mcq.get('answer', '')}**")

            st.caption(
                f"Explanation: {mcq.get('explanation', '')}"
            )

    st.subheader("⏱️ Study Plan")
    for item in content.get("study_plan", []):
        st.markdown(
            f"**{item.get('time', '')}** — {item.get('task', '')}"
        )

    st.subheader("🎯 Exam Tips")
    for tip in content.get("exam_tips", []):
        st.markdown(f"- {tip}")

    with st.expander("🔍 Assessment & Review Details"):
        st.write("**Assessment Issues**")
        issues = assessment.get("issues", [])
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.write("No major issues identified.")

        st.write("**Review Strengths**")
        for strength in review.get("strengths", []):
            st.markdown(f"- {strength}")

        st.write("**Priority Fixes**")
        fixes = review.get("priority_fixes", [])
        if fixes:
            for fix in fixes:
                st.markdown(f"- {fix}")
        else:
            st.write("No priority fixes required.")

    download_data = json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    )

    st.download_button(
        "⬇️ Download Complete Study Pack",
        data=download_data,
        file_name="ai_study_pack.json",
        mime="application/json",
        use_container_width=True,
    )

st.divider()
st.caption(
    "Powered by Groq • Multi-stage AI workflow • Streamlit"
)
