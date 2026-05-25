import { ImagePlus, Search, Sparkles, Trash2 } from "lucide-react";
import { DragEvent, useMemo, useState } from "react";

import type { ReferenceAsset } from "../../shared/types/api";

interface ReferenceLibraryViewProps {
  references: ReferenceAsset[];
  onUpload: (file: File) => void;
  onAnalyze: (referenceId: string) => void;
  onSaveTags: (referenceId: string, tags: string[]) => void;
  onDelete: (reference: ReferenceAsset) => void;
  onVocabularyPatch: (vocabulary: string) => void;
}

export function ReferenceLibraryView({
  references,
  onUpload,
  onAnalyze,
  onSaveTags,
  onDelete,
  onVocabularyPatch
}: ReferenceLibraryViewProps) {
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(references[0]?.id ?? null);
  const selected = references.find((reference) => reference.id === selectedId) ?? references[0];
  const filtered = useMemo(() => {
    const normalized = query.toLowerCase();
    return references.filter((reference) =>
      [reference.name, reference.type, reference.tags.join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    );
  }, [query, references]);

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files.item(0);
    if (file) {
      onUpload(file);
    }
  };

  return (
    <section className="workspace-pane" aria-label="Reference Library">
      <div className="section-header">
        <h1>Reference Library</h1>
        <label className="file-button">
          <ImagePlus size={16} /> Add
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
      <div
        className="drop-zone"
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <Search size={15} />
        <input
          value={query}
          onChange={(event) => setQuery(event.currentTarget.value)}
          placeholder="Search"
        />
      </div>
      <div className="library-grid">
        <div className="item-list">
          {filtered.map((reference) => (
            <button
              type="button"
              className={`asset-list-item ${reference.id === selected?.id ? "active" : ""}`}
              key={reference.id}
              onClick={() => setSelectedId(reference.id)}
            >
              <img src={reference.asset_url} alt="" />
              <span>{reference.name}</span>
              <small>{reference.type}</small>
            </button>
          ))}
        </div>
        {selected && (
          <ReferenceDetail
            reference={selected}
            onAnalyze={onAnalyze}
            onSaveTags={onSaveTags}
            onDelete={onDelete}
            onVocabularyPatch={onVocabularyPatch}
          />
        )}
      </div>
    </section>
  );
}

interface ReferenceDetailProps {
  reference: ReferenceAsset;
  onAnalyze: (referenceId: string) => void;
  onSaveTags: (referenceId: string, tags: string[]) => void;
  onDelete: (reference: ReferenceAsset) => void;
  onVocabularyPatch: (vocabulary: string) => void;
}

function ReferenceDetail({
  reference,
  onAnalyze,
  onSaveTags,
  onDelete,
  onVocabularyPatch
}: ReferenceDetailProps) {
  const [tagText, setTagText] = useState(reference.tags.join(", "));
  return (
    <article className="asset-detail">
      <img className="asset-preview" src={reference.asset_url} alt={reference.name} />
      <div className="panel-title-row">
        <h2>{reference.name}</h2>
        <div className="toolbar-actions">
          <button
            type="button"
            className="icon-button"
            aria-label="Analyze reference"
            title="Analyze reference"
            onClick={() => onAnalyze(reference.id)}
          >
            <Sparkles size={15} />
          </button>
          <button
            type="button"
            className="icon-button danger"
            aria-label="Delete reference"
            title="Delete reference"
            onClick={() => onDelete(reference)}
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>
      <dl className="meta-list">
        <div>
          <dt>Size</dt>
          <dd>
            {reference.image_metadata.width} x {reference.image_metadata.height}
          </dd>
        </div>
        <div>
          <dt>Format</dt>
          <dd>{reference.image_metadata.format_name}</dd>
        </div>
      </dl>
      <div className="swatches">
        {reference.image_metadata.dominant_colors.map((color) => (
          <span key={color} title={color} style={{ background: color }} />
        ))}
      </div>
      <label className="field">
        <span>Tags</span>
        <input value={tagText} onChange={(event) => setTagText(event.currentTarget.value)} />
      </label>
      <button
        type="button"
        className="secondary"
        onClick={() =>
          onSaveTags(
            reference.id,
            tagText
              .split(",")
              .map((tag) => tag.trim())
              .filter(Boolean)
          )
        }
      >
        Tags 保存
      </button>
      <section className="plain-panel">
        <h3>AI Analysis</h3>
        <p>{reference.ai_analysis.summary || "未解析"}</p>
        <div className="button-grid compact">
          {reference.ai_analysis.extracted_vocabulary.map((term) => (
            <button type="button" key={term} onClick={() => onVocabularyPatch(term)}>
              {term}
            </button>
          ))}
        </div>
      </section>
    </article>
  );
}
