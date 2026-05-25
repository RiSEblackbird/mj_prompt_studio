import { BrainCircuit } from "lucide-react";

import type { JsonObject, PromptDocument } from "../../shared/types/api";

interface AIInspectorProps {
  document: PromptDocument;
  agentResult: JsonObject | null;
}

export function AIInspector({ document, agentResult }: AIInspectorProps) {
  const missingDecisions = readStringList(agentResult, "missing_decisions");
  const nextActions = readStringList(agentResult, "next_actions");
  return (
    <section className="inspector-section" aria-label="AI Inspector">
      <div className="panel-title-row">
        <h2>AI Inspector</h2>
        <BrainCircuit size={16} />
      </div>
      <dl className="meta-list">
        <div>
          <dt>Last Agent</dt>
          <dd>{document.llm_context.last_agent ?? "None"}</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{document.llm_context.model}</dd>
        </div>
      </dl>
      <h3>Missing Decisions</h3>
      <ul className="compact-list">
        {missingDecisions.map((item) => (
          <li key={item}>{item}</li>
        ))}
        {missingDecisions.length === 0 && <li>なし</li>}
      </ul>
      <h3>Next Actions</h3>
      <ul className="compact-list">
        {nextActions.map((item) => (
          <li key={item}>{item}</li>
        ))}
        {nextActions.length === 0 && <li>なし</li>}
      </ul>
    </section>
  );
}

function readStringList(source: JsonObject | null, key: string): string[] {
  const value = source?.[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => {
    if (typeof item === "string") {
      return item;
    }
    if (typeof item === "object" && item !== null && "question" in item) {
      return String(item.question);
    }
    return String(item);
  });
}
