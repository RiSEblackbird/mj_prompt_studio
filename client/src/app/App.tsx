import {
  Download,
  FilePenLine,
  FolderOpen,
  Grid3X3,
  Images,
  Library,
  PenLine,
  Plus,
  RotateCcw,
  ScanSearch,
  Settings,
  Sparkles,
  Undo2
} from "lucide-react";
import { ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AIInspector } from "../features/ai-inspector/AIInspector";
import { ComposerPayload, ComposerView } from "../features/composer/ComposerView";
import { ParameterInspector } from "../features/composer/ParameterInspector";
import { FreeEditorView } from "../features/free-editor/FreeEditorView";
import { JobsPanel } from "../features/jobs/JobsPanel";
import { MatrixLabView } from "../features/matrix-lab/MatrixLabView";
import { PromptDoctorPanel } from "../features/prompt-doctor/PromptDoctorPanel";
import { ReferenceLibraryView } from "../features/reference-library/ReferenceLibraryView";
import { ResultReviewView } from "../features/result-review/ResultReviewView";
import { SettingsView } from "../features/settings/SettingsView";
import { api, ApiClientError } from "../shared/api/client";
import { ConfirmDialog } from "../shared/components/ConfirmDialog";
import type {
  JsonObject,
  JsonValue,
  LLMJob,
  MatrixPlan,
  MatrixVariant,
  PromptDocument,
  PromptParameters,
  PromptPatch,
  ReferenceAsset,
  ResultImage,
  ResultReview,
  RuntimeSettingsPublic,
  WorkspaceResponse
} from "../shared/types/api";
import { copyText, downloadText } from "../shared/utils/clipboard";
import "./styles.css";

type TabId =
  | "composer"
  | "free-editor"
  | "matrix-lab"
  | "reference-library"
  | "result-review"
  | "settings";

type PendingConfirm =
  | { kind: "patch"; patch: PromptPatch }
  | { kind: "parameters"; payload: JsonObject }
  | { kind: "delete-reference"; reference: ReferenceAsset };

const tabs: { id: TabId; label: string; icon: ReactNode }[] = [
  { id: "composer", label: "Composer", icon: <PenLine size={15} /> },
  { id: "free-editor", label: "Free Editor", icon: <FilePenLine size={15} /> },
  { id: "matrix-lab", label: "Matrix Lab", icon: <Grid3X3 size={15} /> },
  { id: "reference-library", label: "Reference Library", icon: <Images size={15} /> },
  { id: "result-review", label: "Result Review", icon: <ScanSearch size={15} /> },
  { id: "settings", label: "Settings", icon: <Settings size={15} /> }
];

export function App() {
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [document, setDocument] = useState<PromptDocument | null>(null);
  const [parameters, setParameters] = useState<PromptParameters | null>(null);
  const [references, setReferences] = useState<ReferenceAsset[]>([]);
  const [resultImages, setResultImages] = useState<ResultImage[]>([]);
  const [jobs, setJobs] = useState<LLMJob[]>([]);
  const [settings, setSettings] = useState<RuntimeSettingsPublic | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("composer");
  const [agentResult, setAgentResult] = useState<JsonObject | null>(null);
  const [pendingPatches, setPendingPatches] = useState<PromptPatch[]>([]);
  const [matrixPlan, setMatrixPlan] = useState<MatrixPlan | null>(null);
  const [matrixVariants, setMatrixVariants] = useState<MatrixVariant[]>([]);
  const [latestReview, setLatestReview] = useState<ResultReview | null>(null);
  const [comparisonLines, setComparisonLines] = useState<string[]>([]);
  const [auditResult, setAuditResult] = useState<JsonObject | null>(null);
  const [freeEditorResult, setFreeEditorResult] = useState({ result: "", detail: "" });
  const [pendingConfirm, setPendingConfirm] = useState<PendingConfirm | null>(null);
  const [status, setStatus] = useState("起動中");
  const [manualCopy, setManualCopy] = useState<string | null>(null);
  const [latestAutoSuggestionText, setLatestAutoSuggestionText] = useState("");
  const handledJobs = useRef<Set<string>>(new Set());

  const loadWorkspace = useCallback(async () => {
    const next = await api.workspace();
    setWorkspace(next);
    setDocument(next.document);
    setParameters(next.document.parameters);
    setReferences(next.references);
    setResultImages(next.result_images);
    setSettings(next.settings);
    setJobs(next.jobs);
    setStatus("保存済み");
  }, []);

  useEffect(() => {
    loadWorkspace().catch((error: unknown) => setStatus(errorToMessage(error)));
  }, [loadWorkspace]);

  const refreshJobs = useCallback(async () => {
    const response = await api.jobs();
    setJobs(response.jobs);
    response.jobs.forEach((job) => {
      if (job.status === "succeeded" && !handledJobs.current.has(job.id)) {
        handledJobs.current.add(job.id);
        handleJobCompletion(job);
      }
      if (job.status === "failed" && !handledJobs.current.has(job.id)) {
        handledJobs.current.add(job.id);
        setStatus(job.error_message ?? "Job failed");
      }
    });
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      refreshJobs().catch((error: unknown) => setStatus(errorToMessage(error)));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [refreshJobs]);

  const savePayload = useCallback(
    (payload: ComposerPayload): ComposerPayload => ({
      ...payload,
      parameters: parameters ?? payload.parameters
    }),
    [parameters]
  );

  const updateDocument = (next: PromptDocument) => {
    setDocument(next);
    setParameters(next.parameters);
    setWorkspace((current) => (current ? { ...current, document: next } : current));
  };

  const handleJobCompletion = (job: LLMJob) => {
    const output = job.output_json;
    if (!output) {
      return;
    }
    setAgentResult(output);
    if (job.agent_name === "IntentIntakeAgent") {
      const nextDocument = readObject(output.document);
      if (nextDocument) {
        updateDocument(nextDocument as unknown as PromptDocument);
      }
      const agent = readObject(output.agent);
      if (agent) {
        setAgentResult(agent);
      }
      loadWorkspace().catch(() => undefined);
      return;
    }
    if (job.agent_name === "VocabularyAgent") {
      if (output.target === "free_editor") {
        setFreeEditorResult({
          result: String(output.transformed ?? ""),
          detail: String(output.detail ?? "")
        });
        return;
      }
      if (
        output.target === "auto_suggestion" &&
        String(output.source_text ?? "") !== latestAutoSuggestionText
      ) {
        return;
      }
      setPendingPatches(readPatches(output.patches));
      return;
    }
    if (job.agent_name === "PromptDoctorAgent") {
      setPendingPatches(readPatches(output.patches));
      return;
    }
    if (job.agent_name === "ParameterAdvisorAgent") {
      setPendingConfirm({ kind: "parameters", payload: output });
      return;
    }
    if (job.agent_name === "MatrixPlannerAgent") {
      const plan = readObject(output.plan);
      if (plan) {
        setMatrixPlan(plan as unknown as MatrixPlan);
      }
      return;
    }
    if (job.agent_name === "ResultReviewAgent") {
      const review = readObject(output.review);
      if (review) {
        setLatestReview(review as unknown as ResultReview);
      }
      loadWorkspace().catch(() => undefined);
      return;
    }
    if (job.agent_name === "FinalAuditorAgent") {
      setAuditResult(output);
      return;
    }
    if (job.agent_name === "ReferenceAnalyzerAgent") {
      loadWorkspace().catch(() => undefined);
    }
  };

  const submitJob = async (work: () => Promise<{ job: LLMJob }>, message: string) => {
    try {
      const response = await work();
      setJobs((current) => [response.job, ...current.filter((job) => job.id !== response.job.id)]);
      setStatus(message);
    } catch (error) {
      setStatus(errorToMessage(error));
    }
  };

  const currentDocument = document;
  const currentSettings = settings;

  const content = useMemo(() => {
    if (!workspace || !currentDocument || !currentSettings || !parameters) {
      return <main className="workspace-pane">Loading</main>;
    }
    if (activeTab === "composer") {
      return (
        <ComposerView
          document={{ ...currentDocument, parameters }}
          onSave={(payload) =>
            api
              .saveBlocks(currentDocument.id, savePayload(payload))
              .then((response) => {
                updateDocument(response.document);
                setStatus("保存済み");
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onCompile={(payload) =>
            api
              .compile(currentDocument.id, savePayload(payload))
              .then((response) => {
                updateDocument(response.document);
                setStatus("Compile 完了");
                return api.compileReview(response.document.id);
              })
              .then((response) => {
                setJobs((current) => [response.job, ...current]);
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onBrief={(brief) =>
            submitJob(
              () => api.intentIntake(currentDocument.id, brief),
              "AI Brief job を作成しました"
            )
          }
          onFieldAssist={(mode, field, text) =>
            submitJob(
              () => api.vocabulary({ text, mode, field_name: field }),
              "Field assist job を作成しました"
            )
          }
          onAutoSuggest={(sourceText) => {
            setLatestAutoSuggestionText(sourceText);
            submitJob(
              () => api.vocabulary({ text: sourceText, mode: "auto", source_text: sourceText }),
              "Auto suggestion job を作成しました"
            );
          }}
          onCopyPrompt={() => handleCopy(currentDocument.compiled_prompt)}
        />
      );
    }
    if (activeTab === "free-editor") {
      return (
        <FreeEditorView
          result={freeEditorResult.result}
          detail={freeEditorResult.detail}
          onTransform={(mode, source, prompt) =>
            submitJob(
              () =>
                api.vocabulary({
                  text: source || prompt,
                  mode: "free_editor",
                  field_name: mode
                }),
              "Free Editor job を作成しました"
            )
          }
        />
      );
    }
    if (activeTab === "matrix-lab") {
      return (
        <MatrixLabView
          plan={matrixPlan}
          variants={matrixVariants}
          onPlan={(objective) =>
            submitJob(() => api.matrixPlan(objective), "Matrix plan job を作成しました")
          }
          onGenerate={() => {
            if (!matrixPlan) {
              setStatus("先に Matrix plan を作成してください");
              return;
            }
            api
              .matrixGenerate(workspace.project.id, matrixPlan, currentDocument.compiled_prompt)
              .then((response) => {
                setMatrixVariants(response.variants);
                setStatus("Matrix variants を生成しました");
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)));
          }}
          onCopySelected={(variant) =>
            variant ? handleCopy(variant.prompt) : setStatus("Variant を選択してください")
          }
          onCopyAll={() => handleCopy(matrixVariants.map((variant) => variant.prompt).join("\n"))}
          onExportCsv={() =>
            api
              .matrixCsv(matrixVariants)
              .then((csv) => {
                downloadText("matrix_variants.csv", csv, "text/csv");
                return handleCopy(csv);
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onExportMarkdown={() => {
            if (!matrixPlan) {
              setStatus("Matrix plan がありません");
              return;
            }
            api
              .matrixMarkdown(matrixPlan, matrixVariants)
              .then((markdown) => {
                downloadText("matrix_variants.md", markdown, "text/markdown");
                return handleCopy(markdown);
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)));
          }}
        />
      );
    }
    if (activeTab === "reference-library") {
      return (
        <ReferenceLibraryView
          references={references}
          onUpload={(file) =>
            api
              .uploadReference(workspace.project.id, file)
              .then((response) => {
                setReferences((current) => [response.reference, ...current]);
                setStatus("参照素材を取り込みました");
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onAnalyze={(referenceId) =>
            submitJob(
              () => api.referenceAnalyzer(referenceId),
              "Reference analysis job を作成しました"
            )
          }
          onSaveTags={(referenceId, tags) =>
            api
              .updateReferenceTags(referenceId, tags)
              .then((response) => {
                setReferences((current) =>
                  current.map((reference) =>
                    reference.id === referenceId ? response.reference : reference
                  )
                );
                setStatus("Tags 保存済み");
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onDelete={(reference) => setPendingConfirm({ kind: "delete-reference", reference })}
          onVocabularyPatch={(vocabulary) =>
            setPendingConfirm({
              kind: "patch",
              patch: {
                field_path: "blocks.style",
                old_value: currentDocument.blocks.style,
                new_value: [currentDocument.blocks.style, vocabulary].filter(Boolean).join(", "),
                reason: "参照素材から抽出した語彙をStyleへ追加",
                confidence: 0.9,
                requires_user_confirmation: true
              }
            })
          }
        />
      );
    }
    if (activeTab === "result-review") {
      return (
        <ResultReviewView
          resultImages={resultImages}
          latestReview={latestReview}
          comparisonLines={comparisonLines}
          auditResult={auditResult}
          onUpload={(file) =>
            api
              .uploadResult(currentDocument.id, file)
              .then((response) => {
                setResultImages((current) => [response.result_image, ...current]);
                setStatus("生成結果画像を取り込みました");
              })
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onReview={(resultImageId) =>
            submitJob(() => api.resultReview(resultImageId), "Result review job を作成しました")
          }
          onCompare={() =>
            api
              .compareResults(workspace.project.id)
              .then((response) => setComparisonLines(response.lines))
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onNextPrompt={(candidate) =>
            setPendingConfirm({
              kind: "patch",
              patch: {
                field_path: "blocks.notes",
                old_value: currentDocument.blocks.notes,
                new_value: candidate,
                reason: "Result Reviewの改善候補をComposerへ戻す",
                confidence: 0.82,
                requires_user_confirmation: true
              }
            })
          }
          onFinalAudit={() =>
            submitJob(() => api.finalAudit(currentDocument.id), "Final audit job を作成しました")
          }
        />
      );
    }
    return (
      <SettingsView
        settings={currentSettings}
        onSessionKey={(apiKey) =>
          api
            .setSessionApiKey(apiKey)
            .then((response) => {
              setSettings(response.settings);
              setStatus("Session API key を適用しました");
            })
            .catch((error: unknown) => setStatus(errorToMessage(error)))
        }
        onPersistKey={(apiKey) =>
          api
            .persistApiKey(apiKey)
            .then((response) => {
              setSettings(response.settings);
              setStatus(response.persisted ? "Keyring 保存済み" : "Session のみに適用しました");
            })
            .catch((error: unknown) => setStatus(errorToMessage(error)))
        }
        onResponseStorage={(mode) =>
          api
            .saveResponseStorage(mode)
            .then((response) => {
              setSettings(response.settings);
              setStatus("Privacy 設定を保存しました");
            })
            .catch((error: unknown) => setStatus(errorToMessage(error)))
        }
        onProfiles={(profiles) =>
          api
            .saveProfiles(profiles)
            .then((response) => {
              setSettings(response.settings);
              setStatus("Feature profiles を保存しました");
            })
            .catch((error: unknown) => setStatus(errorToMessage(error)))
        }
        onConnectionTest={() =>
          api
            .connectionTest()
            .then((response) => setStatus(response.ok ? "Connection OK" : "Connection failed"))
            .catch((error: unknown) => setStatus(errorToMessage(error)))
        }
      />
    );
  }, [
    activeTab,
    agentResult,
    auditResult,
    comparisonLines,
    currentDocument,
    currentSettings,
    freeEditorResult,
    latestReview,
    latestAutoSuggestionText,
    loadWorkspace,
    matrixPlan,
    matrixVariants,
    parameters,
    references,
    resultImages,
    savePayload,
    workspace
  ]);

  if (!workspace || !document || !settings || !parameters) {
    return <div className="boot-screen">MJ Prompt Studio</div>;
  }

  const confirmContent = renderConfirmContent(pendingConfirm);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <strong>MJ Prompt Studio</strong>
          <span>{workspace.project.name}</span>
        </div>
        <div className="toolbar-actions">
          <button
            type="button"
            className="secondary"
            onClick={() => {
              const name = window.prompt("Project name", "New Prompt Project");
              if (name) {
                api
                  .createProject(name, "Untitled Prompt")
                  .then((response) => {
                    setWorkspace({ ...workspace, project: response.project, document: response.document });
                    updateDocument(response.document);
                    setReferences([]);
                    setResultImages([]);
                    setStatus("新規プロジェクトを作成しました");
                  })
                  .catch((error: unknown) => setStatus(errorToMessage(error)));
              }
            }}
          >
            <Plus size={16} /> New
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              api
                .undo(document.id)
                .then((response) => updateDocument(response.document))
                .catch((error: unknown) => setStatus(errorToMessage(error)));
            }}
          >
            <Undo2 size={16} /> Undo
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              api
                .redo(document.id)
                .then((response) => updateDocument(response.document))
                .catch((error: unknown) => setStatus(errorToMessage(error)));
            }}
          >
            <RotateCcw size={16} /> Redo
          </button>
          <button
            type="button"
            onClick={() =>
              api
                .exportFile(document.id, "markdown_record", matrixPlan ?? undefined, matrixVariants)
                .then((content) => {
                  downloadText(`${document.title}.md`, content, "text/markdown");
                  setStatus("Export 完了");
                })
                .catch((error: unknown) => setStatus(errorToMessage(error)))
            }
          >
            <Download size={16} /> Export
          </button>
        </div>
      </header>

      <aside className="left-panel">
        <section>
          <h2>Projects</h2>
          {workspace.projects.map((project) => (
            <button
              type="button"
              className={`nav-row ${project.id === workspace.project.id ? "active" : ""}`}
              key={project.id}
              onClick={() =>
                api
                  .openProject(project.id)
                  .then(() => loadWorkspace())
                  .catch((error: unknown) => setStatus(errorToMessage(error)))
              }
            >
              <FolderOpen size={15} /> {project.name}
            </button>
          ))}
        </section>
        <section>
          <h2>Quick Actions</h2>
          <button type="button" className="nav-row" onClick={() => setActiveTab("composer")}>
            <Sparkles size={15} /> AI Brief
          </button>
          <button
            type="button"
            className="nav-row"
            onClick={() => setActiveTab("reference-library")}
          >
            <Library size={15} /> References
          </button>
          <button type="button" className="nav-row" onClick={() => setActiveTab("settings")}>
            <Settings size={15} /> Settings
          </button>
        </section>
      </aside>

      <nav className="tab-bar" aria-label="Main tabs">
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab.id}
            className={activeTab === tab.id ? "active" : ""}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="main-panel">{content}</main>

      <aside className="right-panel">
        <AIInspector document={document} agentResult={agentResult} />
        <ParameterInspector
          specs={settings.ruleset.parameters}
          parameters={parameters}
          onChange={setParameters}
          onAdvice={() =>
            submitJob(
              () => api.parameterAdvisor(document.id, document.user_brief || document.compiled_prompt),
              "Parameter advisor job を作成しました"
            )
          }
        />
        <PromptDoctorPanel
          validationReport={document.validation_report}
          patches={pendingPatches}
          onRun={() =>
            submitJob(() => api.promptDoctor(document.id), "Prompt Doctor job を作成しました")
          }
          onApplyPatch={(patch) => setPendingConfirm({ kind: "patch", patch })}
        />
      </aside>

      <footer className="bottom-panel">
        <span>{status}</span>
        <JobsPanel
          jobs={jobs}
          onRefresh={() => refreshJobs().catch((error: unknown) => setStatus(errorToMessage(error)))}
          onCancel={(jobId) =>
            api
              .cancelJob(jobId)
              .then(() => refreshJobs())
              .catch((error: unknown) => setStatus(errorToMessage(error)))
          }
          onRetry={(jobId) => {
            handledJobs.current.delete(jobId);
            api
              .retryJob(jobId)
              .then(() => refreshJobs())
              .catch((error: unknown) => setStatus(errorToMessage(error)));
          }}
        />
      </footer>

      <ConfirmDialog
        open={pendingConfirm !== null}
        title="確認"
        onCancel={() => setPendingConfirm(null)}
        onConfirm={() => {
          if (!pendingConfirm) {
            return;
          }
          applyConfirmed(pendingConfirm);
        }}
      >
        {confirmContent}
      </ConfirmDialog>
      <ConfirmDialog
        open={manualCopy !== null}
        title="Manual Copy"
        confirmLabel="閉じる"
        onConfirm={() => setManualCopy(null)}
        onCancel={() => setManualCopy(null)}
      >
        <textarea value={manualCopy ?? ""} readOnly rows={8} />
      </ConfirmDialog>
    </div>
  );

  function handleCopy(text: string): void {
    copyText(text).then((ok) => {
      if (ok) {
        setStatus("コピーしました");
      } else {
        setManualCopy(text);
      }
    });
  }

  function applyConfirmed(confirm: PendingConfirm): void {
    if (!document || !parameters) {
      return;
    }
    if (confirm.kind === "patch") {
      api
        .applyPatch(document.id, confirm.patch)
        .then((response) => {
          updateDocument(response.document);
          setPendingConfirm(null);
          setStatus("Patch を適用しました");
        })
        .catch((error: unknown) => setStatus(errorToMessage(error)));
      return;
    }
    if (confirm.kind === "parameters") {
      const merged = mergeParameters(parameters, readObject(confirm.payload.parameters) ?? {});
      api
        .compile(document.id, {
          user_brief: document.user_brief,
          blocks: document.blocks,
          parameters: merged,
          notes: document.notes,
          tags: document.tags
        })
        .then((response) => {
          updateDocument(response.document);
          setPendingConfirm(null);
          setStatus("Parameter Advisor 提案を適用しました");
        })
        .catch((error: unknown) => setStatus(errorToMessage(error)));
      return;
    }
    api
      .deleteReference(confirm.reference.id)
      .then(() => {
        setReferences((current) =>
          current.filter((reference) => reference.id !== confirm.reference.id)
        );
        setPendingConfirm(null);
        setStatus("参照素材を削除しました");
      })
      .catch((error: unknown) => setStatus(errorToMessage(error)));
  }
}

function renderConfirmContent(confirm: PendingConfirm | null): ReactNode {
  if (!confirm) {
    return null;
  }
  if (confirm.kind === "patch") {
    return (
      <dl className="confirm-grid">
        <div>
          <dt>Reason</dt>
          <dd>{confirm.patch.reason}</dd>
        </div>
        <div>
          <dt>Field</dt>
          <dd>{confirm.patch.field_path}</dd>
        </div>
        <div>
          <dt>Old</dt>
          <dd>{String(confirm.patch.old_value ?? "")}</dd>
        </div>
        <div>
          <dt>New</dt>
          <dd>{String(confirm.patch.new_value ?? "")}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{Math.round(confirm.patch.confidence * 100)}%</dd>
        </div>
      </dl>
    );
  }
  if (confirm.kind === "parameters") {
    return <pre>{JSON.stringify(confirm.payload, null, 2)}</pre>;
  }
  return <p>{confirm.reference.name}</p>;
}

function readObject(value: JsonValue | undefined): JsonObject | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value;
  }
  return null;
}

function readPatches(value: JsonValue | undefined): PromptPatch[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((item) => {
    const object = readObject(item);
    if (!object) {
      return [];
    }
    return [
      {
        field_path: String(object.field_path ?? ""),
        old_value: object.old_value ?? null,
        new_value: object.new_value ?? null,
        reason: String(object.reason ?? ""),
        confidence: Number(object.confidence ?? 0),
        requires_user_confirmation: Boolean(object.requires_user_confirmation ?? true)
      }
    ];
  });
}

function mergeParameters(base: PromptParameters, patch: JsonObject): PromptParameters {
  const next: PromptParameters = { ...base, custom: { ...base.custom } };
  for (const [key, value] of Object.entries(patch)) {
    if (key in next && key !== "custom") {
      if (
        value === null ||
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
      ) {
        Object.assign(next, { [key]: value });
      }
    } else {
      next.custom[key] = value;
    }
  }
  return next;
}

function errorToMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "予期しないエラーが発生しました。";
}
