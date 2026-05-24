from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

JsonDict = dict[str, Any]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PromptBriefModel(StrictModel):
    intent: str
    subject: str
    prompt_blocks: JsonDict
    suggested_parameters: JsonDict
    missing_decisions: list[JsonDict]


class VocabularyModel(StrictModel):
    suggestions: list[JsonDict]
    patches: list[JsonDict]


class PromptDoctorModel(StrictModel):
    summary: str
    issues: list[JsonDict]
    patches: list[JsonDict]
    next_actions: list[str]


class ParameterAdvisorModel(StrictModel):
    profile_name: str
    parameters: JsonDict
    rationale: list[str]


class ReferenceAnalysisModel(StrictModel):
    summary: str
    colors: list[str]
    lighting: str
    composition: str
    material_texture: str
    suggested_mode: str
    extracted_vocabulary: list[str]
    confidence: float


class MatrixPlanModel(StrictModel):
    objective: str
    fixed_conditions: JsonDict
    axes: list[JsonDict]
    evaluation_points: list[str]


class ResultReviewModel(StrictModel):
    scores: JsonDict
    strengths: list[str]
    issues: list[str]
    next_prompt_candidates: list[str]
    ai_summary: str


class FinalAuditModel(StrictModel):
    approved: bool
    summary: str
    warnings: list[str]
    patches: list[JsonDict]


class PromptCompileModel(StrictModel):
    compiled_prompt: str
    rationale: list[str]


def schema(name: str, required: list[str], properties: JsonDict) -> JsonDict:
    return {
        "type": "json_schema",
        "name": name,
        "strict": True,
        "schema": {
            "type": "object",
            "required": required,
            "properties": properties,
            "additionalProperties": False,
        },
    }


PROMPT_BRIEF_SCHEMA = schema(
    "prompt_brief",
    ["intent", "subject", "prompt_blocks", "suggested_parameters", "missing_decisions"],
    {
        "intent": {"type": "string"},
        "subject": {"type": "string"},
        "prompt_blocks": {"type": "object"},
        "suggested_parameters": {"type": "object"},
        "missing_decisions": {"type": "array", "items": {"type": "object"}},
    },
)

VOCABULARY_SCHEMA = schema(
    "vocabulary_suggestions",
    ["suggestions", "patches"],
    {
        "suggestions": {"type": "array", "items": {"type": "object"}},
        "patches": {"type": "array", "items": {"type": "object"}},
    },
)

PROMPT_DOCTOR_SCHEMA = schema(
    "prompt_doctor",
    ["summary", "issues", "patches", "next_actions"],
    {
        "summary": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "object"}},
        "patches": {"type": "array", "items": {"type": "object"}},
        "next_actions": {"type": "array", "items": {"type": "string"}},
    },
)

PARAMETER_ADVISOR_SCHEMA = schema(
    "parameter_advisor",
    ["profile_name", "parameters", "rationale"],
    {
        "profile_name": {"type": "string"},
        "parameters": {"type": "object"},
        "rationale": {"type": "array", "items": {"type": "string"}},
    },
)

REFERENCE_ANALYSIS_SCHEMA = schema(
    "reference_analysis",
    [
        "summary",
        "colors",
        "lighting",
        "composition",
        "material_texture",
        "suggested_mode",
        "extracted_vocabulary",
        "confidence",
    ],
    {
        "summary": {"type": "string"},
        "colors": {"type": "array", "items": {"type": "string"}},
        "lighting": {"type": "string"},
        "composition": {"type": "string"},
        "material_texture": {"type": "string"},
        "suggested_mode": {"type": "string"},
        "extracted_vocabulary": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
)

MATRIX_PLAN_SCHEMA = schema(
    "matrix_plan",
    ["objective", "fixed_conditions", "axes", "evaluation_points"],
    {
        "objective": {"type": "string"},
        "fixed_conditions": {"type": "object"},
        "axes": {"type": "array", "items": {"type": "object"}},
        "evaluation_points": {"type": "array", "items": {"type": "string"}},
    },
)

RESULT_REVIEW_SCHEMA = schema(
    "result_review",
    ["scores", "strengths", "issues", "next_prompt_candidates", "ai_summary"],
    {
        "scores": {"type": "object"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "issues": {"type": "array", "items": {"type": "string"}},
        "next_prompt_candidates": {"type": "array", "items": {"type": "string"}},
        "ai_summary": {"type": "string"},
    },
)

FINAL_AUDIT_SCHEMA = schema(
    "final_audit",
    ["approved", "summary", "warnings", "patches"],
    {
        "approved": {"type": "boolean"},
        "summary": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "patches": {"type": "array", "items": {"type": "object"}},
    },
)

PROMPT_COMPILER_SCHEMA = schema(
    "prompt_compile",
    ["compiled_prompt", "rationale"],
    {
        "compiled_prompt": {"type": "string"},
        "rationale": {"type": "array", "items": {"type": "string"}},
    },
)

SCHEMAS: dict[str, JsonDict] = {
    "IntentIntakeAgent": PROMPT_BRIEF_SCHEMA,
    "VocabularyAgent": VOCABULARY_SCHEMA,
    "PromptCompilerAgent": PROMPT_COMPILER_SCHEMA,
    "PromptDoctorAgent": PROMPT_DOCTOR_SCHEMA,
    "ParameterAdvisorAgent": PARAMETER_ADVISOR_SCHEMA,
    "ReferenceAnalyzerAgent": REFERENCE_ANALYSIS_SCHEMA,
    "MatrixPlannerAgent": MATRIX_PLAN_SCHEMA,
    "ResultReviewAgent": RESULT_REVIEW_SCHEMA,
    "FinalAuditorAgent": FINAL_AUDIT_SCHEMA,
}

MODELS: dict[str, type[BaseModel]] = {
    "IntentIntakeAgent": PromptBriefModel,
    "VocabularyAgent": VocabularyModel,
    "PromptCompilerAgent": PromptCompileModel,
    "PromptDoctorAgent": PromptDoctorModel,
    "ParameterAdvisorAgent": ParameterAdvisorModel,
    "ReferenceAnalyzerAgent": ReferenceAnalysisModel,
    "MatrixPlannerAgent": MatrixPlanModel,
    "ResultReviewAgent": ResultReviewModel,
    "FinalAuditorAgent": FinalAuditModel,
}


def validate_schema_payload(agent_name: str, payload: JsonDict) -> None:
    schema_config = SCHEMAS[agent_name]["schema"]
    required = schema_config["required"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"{agent_name} response is missing required keys: {', '.join(missing)}")
    MODELS[agent_name].model_validate(payload)


def schema_for_agent(agent_name: str) -> JsonDict:
    if agent_name not in SCHEMAS:
        raise KeyError(f"Unknown LLM agent: {agent_name}")
    return SCHEMAS[agent_name]
