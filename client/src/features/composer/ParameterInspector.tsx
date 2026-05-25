import { SlidersHorizontal, Sparkles } from "lucide-react";

import type { ParameterSpec, PromptParameters } from "../../shared/types/api";

interface ParameterInspectorProps {
  specs: ParameterSpec[];
  parameters: PromptParameters;
  onChange: (parameters: PromptParameters) => void;
  onAdvice: () => void;
}

export function ParameterInspector({
  specs,
  parameters,
  onChange,
  onAdvice
}: ParameterInspectorProps) {
  const updateParameter = (name: string, value: string | number | boolean | null) => {
    if (name in parameters) {
      onChange({ ...parameters, [name]: value });
      return;
    }
    onChange({ ...parameters, custom: { ...parameters.custom, [name]: value } });
  };

  return (
    <section className="inspector-section" aria-label="Parameter Advisor">
      <div className="panel-title-row">
        <h2>Parameter Advisor</h2>
        <button
          type="button"
          className="icon-button"
          onClick={onAdvice}
          title="AI advice"
          aria-label="AI advice"
        >
          <Sparkles size={16} />
        </button>
      </div>
      <div className="parameter-list">
        {specs.map((spec) => (
          <label className="parameter-row" key={spec.name}>
            <span>
              <SlidersHorizontal size={14} /> {spec.display_name}
            </span>
            {renderEditor(spec, valueFor(parameters, spec.name), (value) =>
              updateParameter(spec.name, value)
            )}
          </label>
        ))}
      </div>
    </section>
  );
}

function valueFor(parameters: PromptParameters, name: string): string | number | boolean | null {
  if (name in parameters) {
    return parameters[name as keyof PromptParameters] as string | number | boolean | null;
  }
  const value = parameters.custom[name];
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return value;
  }
  return null;
}

function renderEditor(
  spec: ParameterSpec,
  value: string | number | boolean | null,
  onChange: (value: string | number | boolean | null) => void
) {
  if (spec.kind === "boolean") {
    return (
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(event) => onChange(event.currentTarget.checked)}
      />
    );
  }
  if (spec.kind === "integer" || spec.kind === "number") {
    return (
      <input
        type="number"
        min={spec.minimum ?? undefined}
        max={spec.maximum ?? undefined}
        value={typeof value === "number" || typeof value === "string" ? value : ""}
        onChange={(event) => {
          const next = event.currentTarget.value;
          onChange(next === "" ? null : Number(next));
        }}
      />
    );
  }
  if (spec.kind === "enum") {
    return (
      <select
        value={typeof value === "string" || typeof value === "number" ? value : ""}
        onChange={(event) => onChange(event.currentTarget.value || null)}
      >
        <option value="">未指定</option>
        {spec.choices.map((choice) => (
          <option key={choice} value={choice}>
            {choice}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      value={typeof value === "string" ? value : ""}
      onChange={(event) => onChange(event.currentTarget.value || null)}
    />
  );
}
