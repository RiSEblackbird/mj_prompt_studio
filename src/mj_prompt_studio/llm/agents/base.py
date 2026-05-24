from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSpec:
    name: str
    responsibility: str
    default_reasoning: str


AGENT_NAMES = (
    "IntentIntakeAgent",
    "VocabularyAgent",
    "PromptCompilerAgent",
    "PromptDoctorAgent",
    "ParameterAdvisorAgent",
    "ReferenceAnalyzerAgent",
    "ResultReviewAgent",
    "MatrixPlannerAgent",
    "FinalAuditorAgent",
)
