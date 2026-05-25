import { Stethoscope } from "lucide-react";

import type { PromptPatch, ValidationReport } from "../../shared/types/api";

interface PromptDoctorPanelProps {
  validationReport: ValidationReport | null;
  patches: PromptPatch[];
  onRun: () => void;
  onApplyPatch: (patch: PromptPatch) => void;
}

export function PromptDoctorPanel({
  validationReport,
  patches,
  onRun,
  onApplyPatch
}: PromptDoctorPanelProps) {
  return (
    <section className="inspector-section" aria-label="Prompt Doctor">
      <div className="panel-title-row">
        <h2>Prompt Doctor</h2>
        <button
          type="button"
          className="icon-button"
          onClick={onRun}
          title="Run Prompt Doctor"
          aria-label="Run Prompt Doctor"
        >
          <Stethoscope size={16} />
        </button>
      </div>
      <ul className="compact-list">
        {(validationReport?.issues ?? []).map((issue) => (
          <li key={`${issue.code}-${issue.field_path ?? ""}`}>
            <strong>{issue.severity}</strong> {issue.message}
          </li>
        ))}
        {!validationReport?.issues.length && <li>Validation issue はありません。</li>}
      </ul>
      {patches.length > 0 && (
        <div className="patch-list">
          {patches.map((patch) => (
            <button
              type="button"
              className="patch-item"
              key={`${patch.field_path}-${patch.reason}`}
              onClick={() => onApplyPatch(patch)}
            >
              <span>{patch.reason}</span>
              <small>
                {patch.field_path} / confidence {Math.round(patch.confidence * 100)}%
              </small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
