import { ClipboardCheck, GitCompare, ImagePlus, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import type { JsonObject, ResultImage, ResultReview } from "../../shared/types/api";

interface ResultReviewViewProps {
  resultImages: ResultImage[];
  latestReview: ResultReview | null;
  comparisonLines: string[];
  auditResult: JsonObject | null;
  onUpload: (file: File) => void;
  onReview: (resultImageId: string) => void;
  onCompare: () => void;
  onNextPrompt: (candidate: string) => void;
  onFinalAudit: () => void;
}

export function ResultReviewView({
  resultImages,
  latestReview,
  comparisonLines,
  auditResult,
  onUpload,
  onReview,
  onCompare,
  onNextPrompt,
  onFinalAudit
}: ResultReviewViewProps) {
  const [selectedId, setSelectedId] = useState<string | null>(resultImages[0]?.id ?? null);
  const selected = useMemo(
    () => resultImages.find((image) => image.id === selectedId) ?? resultImages[0],
    [resultImages, selectedId]
  );

  return (
    <section className="workspace-pane" aria-label="Result Review">
      <div className="section-header">
        <h1>Result Review</h1>
        <label className="file-button">
          <ImagePlus size={16} /> Import
          <input
            type="file"
            accept="image/*"
            onChange={(event) => {
              const file = event.currentTarget.files?.item(0);
              if (file) {
                onUpload(file);
              }
            }}
          />
        </label>
      </div>
      <div className="library-grid">
        <div className="item-list">
          {resultImages.map((image) => (
            <button
              type="button"
              className={`asset-list-item ${image.id === selected?.id ? "active" : ""}`}
              key={image.id}
              onClick={() => setSelectedId(image.id)}
            >
              <img src={image.asset_url} alt="" />
              <span>{new Date(image.created_at).toLocaleString()}</span>
            </button>
          ))}
        </div>
        {selected && (
          <article className="asset-detail">
            <img className="asset-preview" src={selected.asset_url} alt="" />
            <div className="toolbar-actions">
              <button type="button" onClick={() => onReview(selected.id)}>
                <Sparkles size={16} /> AI Review
              </button>
              <button type="button" className="secondary" onClick={onCompare}>
                <GitCompare size={16} /> Compare
              </button>
              <button type="button" className="secondary" onClick={onFinalAudit}>
                <ClipboardCheck size={16} /> Final Audit
              </button>
            </div>
            <section className="plain-panel">
              <h2>Source Prompt</h2>
              <p>{selected.prompt_snapshot}</p>
              <pre>{JSON.stringify(selected.parameters_snapshot, null, 2)}</pre>
            </section>
            {latestReview && (
              <section className="plain-panel">
                <h2>AI Review</h2>
                <p>{latestReview.ai_summary}</p>
                <div className="score-grid">
                  {Object.entries(latestReview.scores).map(([key, value]) => (
                    <span key={key}>
                      {key}: {value}
                    </span>
                  ))}
                </div>
                <div className="button-grid compact">
                  {latestReview.next_prompt_candidates.map((candidate) => (
                    <button
                      type="button"
                      key={candidate}
                      onClick={() => onNextPrompt(candidate)}
                    >
                      Next Prompt
                    </button>
                  ))}
                </div>
              </section>
            )}
          </article>
        )}
      </div>
      {comparisonLines.length > 0 && (
        <section className="plain-panel">
          <h2>Comparison</h2>
          <pre>{comparisonLines.join("\n")}</pre>
        </section>
      )}
      {auditResult && (
        <section className="plain-panel">
          <h2>Final Audit</h2>
          <pre>{JSON.stringify(auditResult, null, 2)}</pre>
        </section>
      )}
    </section>
  );
}
