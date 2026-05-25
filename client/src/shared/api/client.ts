import type {
  AgentJobResponse,
  DocumentResponse,
  JsonObject,
  LLMFeatureProfile,
  LLMJob,
  MatrixPlan,
  MatrixVariant,
  PromptBlocks,
  PromptDocument,
  PromptParameters,
  PromptPatch,
  ReferenceAsset,
  ResultImage,
  ResultReview,
  RuntimeSettingsPublic,
  WorkspaceResponse
} from "../types/api";

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly kind: "http" | "network" | "schema",
    readonly status?: number
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

const API_BASE = import.meta.env.VITE_MJPS_API_BASE ?? "";

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init.headers
      }
    });
    if (!response.ok) {
      const message = await errorMessage(response);
      throw new ApiClientError(message, "http", response.status);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError("ローカルAPIへ接続できません。", "network");
  }
}

async function requestText(path: string, init: RequestInit = {}): Promise<string> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });
  if (!response.ok) {
    const message = await errorMessage(response);
    throw new ApiClientError(message, "http", response.status);
  }
  return response.text();
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    return response.statusText;
  }
  return response.statusText;
}

export interface SaveDocumentPayload {
  user_brief: string;
  blocks: PromptBlocks;
  parameters: PromptParameters;
  notes: string;
  tags: string[];
}

export const api = {
  workspace: () => requestJson<WorkspaceResponse>("/api/workspace"),
  jobs: () => requestJson<{ jobs: LLMJob[] }>("/api/jobs"),
  job: (jobId: string) => requestJson<{ job: LLMJob }>(`/api/jobs/${jobId}`),
  cancelJob: (jobId: string) =>
    requestJson<{ cancelled: boolean }>(`/api/jobs/${jobId}/cancel`, { method: "POST" }),
  retryJob: (jobId: string) =>
    requestJson<{ job: LLMJob }>(`/api/jobs/${jobId}/retry`, { method: "POST" }),
  createProject: (name: string, title: string) =>
    requestJson<{ project: WorkspaceResponse["project"]; document: PromptDocument }>(
      "/api/projects",
      { method: "POST", body: JSON.stringify({ name, title }) }
    ),
  openProject: (projectId: string) =>
    requestJson<{ project: WorkspaceResponse["project"]; document: PromptDocument }>(
      `/api/projects/${projectId}/open`,
      { method: "POST" }
    ),
  saveBlocks: (documentId: string, payload: SaveDocumentPayload) =>
    requestJson<DocumentResponse>(`/api/prompt-documents/${documentId}/blocks`, {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  compile: (documentId: string, payload: SaveDocumentPayload) =>
    requestJson<DocumentResponse>(`/api/prompt-documents/${documentId}/compile`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  applyPatch: (documentId: string, patch: PromptPatch) =>
    requestJson<DocumentResponse>(`/api/prompt-documents/${documentId}/patches/apply`, {
      method: "POST",
      body: JSON.stringify({ patch, confirmed: true })
    }),
  undo: (documentId: string) =>
    requestJson<DocumentResponse>(`/api/prompt-documents/${documentId}/undo`, {
      method: "POST"
    }),
  redo: (documentId: string) =>
    requestJson<DocumentResponse>(`/api/prompt-documents/${documentId}/redo`, {
      method: "POST"
    }),
  revisions: (documentId: string) =>
    requestJson<{ revisions: JsonObject[] }>(`/api/prompt-documents/${documentId}/revisions`),
  intentIntake: (documentId: string, brief: string) =>
    requestJson<AgentJobResponse>("/api/agents/intent-intake", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, brief })
    }),
  vocabulary: (payload: {
    text: string;
    mode?: string;
    field_name?: string;
    source_text?: string;
  }) =>
    requestJson<AgentJobResponse>("/api/agents/vocabulary", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  compileReview: (documentId: string) =>
    requestJson<AgentJobResponse>("/api/agents/compile-review", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId })
    }),
  promptDoctor: (documentId: string) =>
    requestJson<AgentJobResponse>("/api/agents/prompt-doctor", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId })
    }),
  parameterAdvisor: (documentId: string, objective: string) =>
    requestJson<AgentJobResponse>("/api/agents/parameter-advisor", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, objective })
    }),
  referenceAnalyzer: (referenceId: string) =>
    requestJson<AgentJobResponse>("/api/agents/reference-analyzer", {
      method: "POST",
      body: JSON.stringify({ reference_id: referenceId })
    }),
  matrixPlan: (objective: string) =>
    requestJson<AgentJobResponse>("/api/matrix/plan", {
      method: "POST",
      body: JSON.stringify({ objective })
    }),
  matrixGenerate: (projectId: string, plan: MatrixPlan, basePrompt: string) =>
    requestJson<{ variants: MatrixVariant[] }>("/api/matrix/generate", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, plan, base_prompt: basePrompt })
    }),
  matrixCsv: (variants: MatrixVariant[]) =>
    requestText("/api/matrix/export/csv", {
      method: "POST",
      body: JSON.stringify({ variants })
    }),
  matrixMarkdown: (plan: MatrixPlan, variants: MatrixVariant[]) =>
    requestText("/api/matrix/export/markdown", {
      method: "POST",
      body: JSON.stringify({ plan, variants })
    }),
  uploadReference: (projectId: string, file: File) => {
    const form = new FormData();
    form.set("file", file);
    return requestJson<{ reference: ReferenceAsset }>(
      `/api/projects/${projectId}/references/upload`,
      { method: "POST", body: form }
    );
  },
  updateReferenceTags: (referenceId: string, tags: string[]) =>
    requestJson<{ reference: ReferenceAsset }>(`/api/references/${referenceId}/tags`, {
      method: "PUT",
      body: JSON.stringify({ tags })
    }),
  deleteReference: async (referenceId: string) => {
    const response = await fetch(`${API_BASE}/api/references/${referenceId}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      throw new ApiClientError(await errorMessage(response), "http", response.status);
    }
  },
  uploadResult: (documentId: string, file: File) => {
    const form = new FormData();
    form.set("file", file);
    return requestJson<{ result_image: ResultImage }>(
      `/api/prompt-documents/${documentId}/results/upload`,
      { method: "POST", body: form }
    );
  },
  resultReview: (resultImageId: string) =>
    requestJson<AgentJobResponse>(`/api/results/${resultImageId}/review`, {
      method: "POST"
    }),
  resultReviews: (resultImageId: string) =>
    requestJson<{ reviews: ResultReview[] }>(`/api/results/${resultImageId}/reviews`),
  compareResults: (projectId: string) =>
    requestJson<{ lines: string[] }>("/api/results/compare", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId })
    }),
  finalAudit: (documentId: string) =>
    requestJson<AgentJobResponse>("/api/agents/final-audit", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId })
    }),
  settings: () => requestJson<{ settings: RuntimeSettingsPublic }>("/api/settings"),
  saveProfiles: (profiles: Record<string, LLMFeatureProfile>) =>
    requestJson<{ settings: RuntimeSettingsPublic }>("/api/settings/llm-profiles", {
      method: "PUT",
      body: JSON.stringify({ profiles })
    }),
  saveResponseStorage: (responseStorage: "normal" | "privacy") =>
    requestJson<{ settings: RuntimeSettingsPublic }>("/api/settings/response-storage", {
      method: "PUT",
      body: JSON.stringify({ response_storage: responseStorage })
    }),
  setSessionApiKey: (apiKey: string) =>
    requestJson<{ settings: RuntimeSettingsPublic }>("/api/settings/session-api-key", {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey })
    }),
  persistApiKey: (apiKey: string) =>
    requestJson<{ persisted: boolean; settings: RuntimeSettingsPublic }>(
      "/api/settings/persist-api-key",
      { method: "POST", body: JSON.stringify({ api_key: apiKey }) }
    ),
  connectionTest: () =>
    requestJson<{ ok: boolean }>("/api/settings/connection-test", { method: "POST" }),
  exportFile: (
    documentId: string,
    mode: "prompt" | "markdown_record" | "json_snapshot" | "matrix_csv" | "matrix_markdown",
    matrixPlan?: MatrixPlan,
    matrixVariants: MatrixVariant[] = []
  ) =>
    requestText("/api/exports/file", {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
        mode,
        matrix_plan: matrixPlan,
        matrix_variants: matrixVariants
      })
    })
};
