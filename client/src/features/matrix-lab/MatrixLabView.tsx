import { Clipboard, Download, Grid3X3, Sparkles } from "lucide-react";
import { useState } from "react";

import type { MatrixPlan, MatrixVariant } from "../../shared/types/api";

interface MatrixLabViewProps {
  plan: MatrixPlan | null;
  variants: MatrixVariant[];
  onPlan: (objective: string) => void;
  onGenerate: () => void;
  onCopySelected: (variant: MatrixVariant | null) => void;
  onCopyAll: () => void;
  onExportCsv: () => void;
  onExportMarkdown: () => void;
}

export function MatrixLabView({
  plan,
  variants,
  onPlan,
  onGenerate,
  onCopySelected,
  onCopyAll,
  onExportCsv,
  onExportMarkdown
}: MatrixLabViewProps) {
  const [objective, setObjective] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = variants.find((variant) => variant.id === selectedId) ?? null;

  return (
    <section className="workspace-pane" aria-label="Matrix Lab">
      <div className="section-header">
        <h1>Matrix Lab</h1>
        <div className="toolbar-actions">
          <button type="button" onClick={() => onPlan(objective)}>
            <Sparkles size={16} /> AI Plan
          </button>
          <button type="button" className="secondary" onClick={onGenerate} disabled={!plan}>
            <Grid3X3 size={16} /> Generate
          </button>
        </div>
      </div>
      <label className="field full">
        <span>Objective</span>
        <textarea value={objective} onChange={(event) => setObjective(event.currentTarget.value)} />
      </label>
      {plan && (
        <section className="plain-panel">
          <h2>{plan.objective}</h2>
          <div className="axis-grid">
            {plan.axes.map((axis) => (
              <div key={axis.name}>
                <strong>{axis.name}</strong>
                <span>{axis.values.map(String).join(", ")}</span>
              </div>
            ))}
          </div>
        </section>
      )}
      <div className="toolbar-actions">
        <button type="button" className="secondary" onClick={() => onCopySelected(selected)}>
          <Clipboard size={16} /> Selected
        </button>
        <button type="button" className="secondary" onClick={onCopyAll}>
          <Clipboard size={16} /> All
        </button>
        <button type="button" className="secondary" onClick={onExportCsv}>
          <Download size={16} /> CSV
        </button>
        <button type="button" className="secondary" onClick={onExportMarkdown}>
          <Download size={16} /> Markdown
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Prompt</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((variant) => (
              <tr
                key={variant.id}
                className={variant.id === selectedId ? "selected" : ""}
                onClick={() => setSelectedId(variant.id)}
              >
                <td>{variant.index}</td>
                <td>{variant.prompt}</td>
                <td>{variant.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
