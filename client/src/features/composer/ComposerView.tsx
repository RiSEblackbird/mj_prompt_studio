import { Clipboard, Save, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { PromptBlocks, PromptDocument, PromptParameters } from "../../shared/types/api";
import {
  blockLabels,
  blockOrder,
  inputToTextList,
  previewFromBlocks,
  textListToInput
} from "../../shared/utils/prompt";

interface ComposerViewProps {
  document: PromptDocument;
  onSave: (payload: ComposerPayload) => void;
  onCompile: (payload: ComposerPayload) => void;
  onBrief: (brief: string) => void;
  onFieldAssist: (mode: string, field: keyof PromptBlocks, text: string) => void;
  onAutoSuggest: (sourceText: string) => void;
  onCopyPrompt: () => void;
}

export interface ComposerPayload {
  user_brief: string;
  blocks: PromptBlocks;
  parameters: PromptParameters;
  notes: string;
  tags: string[];
}

const assistModes = ["AI補完", "候補", "専門語化", "短縮", "説明"];

export function ComposerView({
  document,
  onSave,
  onCompile,
  onBrief,
  onFieldAssist,
  onAutoSuggest,
  onCopyPrompt
}: ComposerViewProps) {
  const [brief, setBrief] = useState(document.user_brief);
  const [blocks, setBlocks] = useState<PromptBlocks>(document.blocks);

  useEffect(() => {
    setBrief(document.user_brief);
    setBlocks(document.blocks);
  }, [document.id, document.user_brief, document.blocks]);

  const preview = useMemo(() => previewFromBlocks(blocks), [blocks]);

  useEffect(() => {
    if (preview.trim().length < 16) {
      return;
    }
    const timer = window.setTimeout(() => onAutoSuggest(preview), 1000);
    return () => window.clearTimeout(timer);
  }, [onAutoSuggest, preview]);

  const payload = (): ComposerPayload => ({
    user_brief: brief,
    blocks,
    parameters: document.parameters,
    notes: document.notes,
    tags: document.tags
  });

  return (
    <section className="workspace-pane" aria-label="Composer">
      <div className="section-header">
        <h1>Composer</h1>
        <div className="toolbar-actions">
          <button type="button" className="secondary" onClick={() => onSave(payload())}>
            <Save size={16} /> 保存
          </button>
          <button type="button" onClick={() => onCompile(payload())}>
            <Wand2 size={16} /> Compile
          </button>
        </div>
      </div>

      <div className="composer-grid">
        <label className="field full">
          <span>AI Brief</span>
          <textarea
            value={brief}
            onChange={(event) => setBrief(event.currentTarget.value)}
            rows={4}
          />
        </label>
        <button type="button" className="inline-command" onClick={() => onBrief(brief)}>
          <Sparkles size={16} /> AI Brief から構造化
        </button>

        {blockOrder.map((field) => {
          const value = blocks[field];
          const textValue = Array.isArray(value) ? textListToInput(value) : value;
          return (
            <div className="block-editor" key={field}>
              <label className="field">
                <span>{blockLabels[field]}</span>
                <textarea
                  value={textValue}
                  onChange={(event) => {
                    const nextValue =
                      field === "text_in_image"
                        ? inputToTextList(event.currentTarget.value)
                        : event.currentTarget.value;
                    setBlocks({ ...blocks, [field]: nextValue });
                  }}
                  rows={field === "notes" ? 3 : 2}
                />
              </label>
              <div className="assist-row" aria-label={`${blockLabels[field]} assist`}>
                {assistModes.map((mode) => (
                  <button
                    type="button"
                    className="tiny"
                    key={mode}
                    onClick={() => onFieldAssist(mode, field, textValue)}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="preview-columns">
        <section className="plain-panel" aria-label="Live Preview">
          <h2>Live Preview</h2>
          <p>{preview || "未入力"}</p>
        </section>
        <section className="plain-panel" aria-label="Compiled Prompt">
          <div className="panel-title-row">
            <h2>Compiled Prompt</h2>
            <button type="button" className="icon-button" onClick={onCopyPrompt} title="Copy">
              <Clipboard size={16} />
            </button>
          </div>
          <p>{document.compiled_prompt || "未生成"}</p>
        </section>
      </div>
    </section>
  );
}
