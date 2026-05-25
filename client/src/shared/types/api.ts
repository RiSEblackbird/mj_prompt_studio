export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };

export interface ProjectRecord {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface PromptBlocks {
  intent: string;
  subject: string;
  action_state: string;
  environment: string;
  composition: string;
  camera_lens: string;
  lighting: string;
  material_texture: string;
  color_palette: string;
  style: string;
  text_in_image: string[];
  positive_constraints: string;
  notes: string;
}

export interface PromptParameters {
  aspect_ratio: string | null;
  raw: boolean | null;
  stylize: number | null;
  chaos: number | null;
  weird: number | null;
  experimental: number | null;
  tile: boolean | null;
  seed: number | null;
  speed_mode: string | null;
  custom: JsonObject;
}

export interface PromptReferences {
  image_references: string[];
  style_references: string[];
  moodboards: string[];
  personalization_profiles: string[];
}

export interface LLMContext {
  latest_response_id: string | null;
  last_agent: string | null;
  model: string;
  reasoning_effort: string;
  user_vocab_snapshot_id: string | null;
  project_style_profile_id: string | null;
}

export interface ValidationIssue {
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  field_path: string | null;
}

export interface ValidationReport {
  issues: ValidationIssue[];
}

export interface PromptDocument {
  id: string;
  project_id: string;
  title: string;
  ruleset_id: string;
  user_brief: string;
  blocks: PromptBlocks;
  parameters: PromptParameters;
  references: PromptReferences;
  compiled_prompt: string;
  validation_report: ValidationReport | null;
  llm_context: LLMContext;
  notes: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface PromptPatch {
  field_path: string;
  old_value: JsonValue;
  new_value: JsonValue;
  reason: string;
  confidence: number;
  requires_user_confirmation: boolean;
}

export interface ReferenceAnalysis {
  summary: string;
  colors: string[];
  lighting: string;
  composition: string;
  material_texture: string;
  suggested_mode: string;
  extracted_vocabulary: string[];
  confidence: number;
}

export interface ImageMetadata {
  width: number;
  height: number;
  format_name: string;
  file_size_bytes: number;
  dominant_colors: string[];
}

export interface ReferenceAsset {
  id: string;
  project_id: string;
  type: string;
  name: string;
  external_url: string | null;
  tags: string[];
  ai_analysis: ReferenceAnalysis;
  image_metadata: ImageMetadata;
  notes: string;
  created_at: string;
  updated_at: string;
  asset_url: string;
}

export interface ResultImage {
  id: string;
  project_id: string;
  prompt_document_id: string;
  prompt_snapshot: string;
  parameters_snapshot: JsonObject;
  image_metadata: ImageMetadata;
  created_at: string;
  asset_url: string;
}

export interface ResultReview {
  id: string;
  result_image_id: string;
  scores: Record<string, number>;
  strengths: string[];
  issues: string[];
  next_prompt_candidates: string[];
  ai_summary: string;
  reviewer: string;
  created_at: string;
}

export interface MatrixAxis {
  name: string;
  values: JsonValue[];
  description: string;
}

export interface MatrixPlan {
  id: string;
  objective: string;
  fixed_conditions: JsonObject;
  axes: MatrixAxis[];
  evaluation_points: string[];
  max_variants: number;
}

export interface MatrixVariant {
  id: string;
  index: number;
  parameters: JsonObject;
  prompt: string;
  notes: string;
}

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export interface LLMJob {
  id: string;
  agent_name: string;
  model: string;
  reasoning_effort: string;
  status: JobStatus;
  input_snapshot: JsonObject;
  output_json: JsonObject | null;
  error_message: string | null;
  created_at: string;
  finished_at: string | null;
  retry_count: number;
}

export interface ParameterSpec {
  name: string;
  display_name: string;
  kind: "boolean" | "integer" | "number" | "string" | "enum";
  flag: string;
  ui_visible: boolean;
  export_enabled: boolean;
  minimum: number | null;
  maximum: number | null;
  choices: string[];
  description: string;
}

export interface ReferenceModeSpec {
  name: string;
  display_name: string;
  enabled: boolean;
  description: string;
}

export interface RulesetDisplay {
  display_name: string;
  ui_expose_identifier: boolean;
  capabilities: Record<string, boolean>;
  parameters: ParameterSpec[];
  reference_modes: ReferenceModeSpec[];
}

export interface LLMFeatureProfile {
  model: string;
  reasoning_effort: string;
  vocabulary_amount: string;
}

export interface RuntimeSettingsPublic {
  llm_mode: string;
  response_storage: "normal" | "privacy";
  privacy_mode: boolean;
  api_key_configured: boolean;
  feature_profiles: Record<string, LLMFeatureProfile>;
  feature_display_names: Record<string, string>;
  available_models: string[];
  reasoning_efforts: string[];
  vocabulary_amounts: string[];
  vocabulary_amount_labels: Record<string, string>;
  ruleset: RulesetDisplay;
}

export interface WorkspaceResponse {
  project: ProjectRecord;
  document: PromptDocument;
  projects: ProjectRecord[];
  references: ReferenceAsset[];
  result_images: ResultImage[];
  ruleset: RulesetDisplay;
  settings: RuntimeSettingsPublic;
  jobs: LLMJob[];
}

export interface AgentJobResponse {
  job: LLMJob;
}

export interface DocumentResponse {
  document: PromptDocument;
}

export interface ApiErrorPayload {
  detail?: string;
}
