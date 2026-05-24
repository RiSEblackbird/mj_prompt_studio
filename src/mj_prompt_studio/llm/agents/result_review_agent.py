from mj_prompt_studio.llm.agents.base import AgentSpec

SPEC = AgentSpec(
    "ResultReviewAgent", "手動取り込み結果と元プロンプトを比較し改善案を返す。", "high"
)
