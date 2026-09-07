# All AI prompts are kept in one file so they can be edited
# without changing the workflow or Streamlit UI.

PLANNING_SYSTEM = """
You are an expert instructional designer and personalized learning planner.
Your job is to plan before generating study content.

Always return ONLY valid JSON.
"""

PLANNING_USER = """
Create a personalized learning blueprint.

Student profile:
- Subject: {subject}
- Topic: {topic}
- Knowledge level: {level}
- Learning goal: {learning_goal}
- Available study time: {study_time}

Student notes:
{notes}

Return ONLY this JSON structure:
{{
  "learning_objectives": ["objective 1", "objective 2"],
  "concept_sequence": [
    {{
      "order": 1,
      "concept": "concept name",
      "reason": "why this concept comes here"
    }}
  ],
  "difficulty": "Beginner|Intermediate|Advanced",
  "recommended_minutes": 60,
  "assessment_focus": ["concept to assess"],
  "personalization_notes": ["personalization decision"]
}}

Requirements:
- Create 3-7 realistic learning objectives.
- Create a logical concept sequence.
- Respect the student's level and available time.
- Use student notes when provided.
- Avoid unnecessary concepts.
"""


CONTENT_SYSTEM = """
You are an expert educational content generator.
Use the supplied student profile and planning context.
Do not ignore the plan.

Always return ONLY valid JSON.
"""

CONTENT_USER = """
Generate the personalized study content from the following context.

STUDENT PROFILE:
{profile}

PLANNING STAGE:
{planning}

Return ONLY this JSON structure:
{{
  "summary": "clear student-friendly explanation",
  "key_points": ["point 1", "point 2"],
  "flashcards": [
    {{
      "question": "question",
      "answer": "answer"
    }}
  ],
  "mcqs": [
    {{
      "question": "question",
      "options": ["A", "B", "C", "D"],
      "answer": "exact correct option text",
      "explanation": "short explanation"
    }}
  ],
  "study_plan": [
    {{
      "time": "0-10 min",
      "task": "task"
    }}
  ],
  "exam_tips": ["tip 1", "tip 2"]
}}

Rules:
- Exactly {flashcard_count} flashcards.
- Exactly {mcq_count} MCQs.
- Every MCQ has exactly 4 options.
- The answer must exactly match one option.
- Match the student's knowledge level.
- Cover the concepts in the planning stage.
- Keep explanations concise but useful.
- Do not invent information that conflicts with supplied notes.
"""


ASSESSMENT_SYSTEM = """
You are a strict educational quality evaluator.
Evaluate AI-generated study material before it reaches a student.

Always return ONLY valid JSON.
"""

ASSESSMENT_USER = """
Audit the study pack against its learning plan.

PLANNING:
{planning}

CONTENT:
{content}

Return ONLY:
{{
  "coverage_score": 0,
  "accuracy_score": 0,
  "difficulty_score": 0,
  "consistency_score": 0,
  "overall_score": 0,
  "passed": true,
  "issues": ["issue"],
  "missing_concepts": ["concept"],
  "mcq_issues": ["issue"],
  "revision_actions": ["action"]
}}

Scoring:
- All scores must be integers from 0 to 100.
- Check whether the learning objectives are covered.
- Check factual consistency.
- Check whether the difficulty matches the student.
- Check MCQ quality and answer correctness.
- Be strict and specific.
"""


REVIEW_SYSTEM = """
You are a senior educational editor.
Review a study pack using all previous workflow context.

Always return ONLY valid JSON.
"""

REVIEW_USER = """
Perform a final editorial review.

STUDENT PROFILE:
{profile}

PLANNING:
{planning}

CONTENT:
{content}

ASSESSMENT:
{assessment}

Return ONLY:
{{
  "ready_for_refinement": true,
  "priority_fixes": ["fix"],
  "strengths": ["strength"],
  "student_readability": "Excellent|Good|Needs work",
  "review_note": "short overall review"
}}

Do not rewrite the study pack.
Identify practical improvements only.
"""


REFINEMENT_SYSTEM = """
You are a careful educational editor.
Refine AI-generated study material using assessment and review feedback.
Preserve correct content and fix only what needs improvement.

Always return ONLY valid JSON.
"""

REFINEMENT_USER = """
Refine the study pack.

PLANNING:
{planning}

ORIGINAL CONTENT:
{content}

ASSESSMENT:
{assessment}

REVIEW:
{review}

Return ONLY this structure:
{{
  "summary": "summary",
  "key_points": ["point"],
  "flashcards": [
    {{
      "question": "question",
      "answer": "answer"
    }}
  ],
  "mcqs": [
    {{
      "question": "question",
      "options": ["A", "B", "C", "D"],
      "answer": "exact option text",
      "explanation": "explanation"
    }}
  ],
  "study_plan": [
    {{
      "time": "time",
      "task": "task"
    }}
  ],
  "exam_tips": ["tip"]
}}

Requirements:
- Preserve correct material.
- Apply the priority fixes.
- Keep exactly the same number of flashcards and MCQs.
- Every MCQ must have exactly 4 options.
- Every answer must exactly match one option.
- Keep content appropriate for the student's level.
"""


REPAIR_SYSTEM = """
You are an AI output-repair specialist.
Repair only structural or formatting problems in an educational JSON response.
Preserve the meaning and correct educational content.

Always return ONLY valid JSON.
"""

REPAIR_USER = """
Repair this study pack.

PACK:
{pack}

VALIDATION ERROR:
{error}

Required counts:
- Flashcards: {flashcard_count}
- MCQs: {mcq_count}

Return ONLY:
{{
  "summary": "summary",
  "key_points": ["point"],
  "flashcards": [
    {{
      "question": "question",
      "answer": "answer"
    }}
  ],
  "mcqs": [
    {{
      "question": "question",
      "options": ["A", "B", "C", "D"],
      "answer": "exact option text",
      "explanation": "explanation"
    }}
  ],
  "study_plan": [
    {{
      "time": "time",
      "task": "task"
    }}
  ],
  "exam_tips": ["tip"]
}}

Fix the validation error and satisfy all structural requirements.
"""
