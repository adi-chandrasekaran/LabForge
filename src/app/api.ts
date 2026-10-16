import type { AttachmentRecord, IOItem, Param, StepStatus, WorkflowStep } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://127.0.0.1:8000/api/v1";
const API_ROOT = API_BASE.replace(/\/api\/v1$/, "");
const SYNC_REFRESH_EVENT = "nmr-lab-sync-refresh";

export interface WorkflowDraftRecord {
  id: string;
  operation: string;
  payload: Record<string, unknown>;
  status: "pending" | "confirmed" | "expired" | "stale" | "failed";
  expiresAt: string;
  createdAt: string;
  decidedAt?: string | null;
  failureDetail?: string | null;
}

export interface AgentToolCallRecord { id: string; sequence: number; toolName: string; arguments: Record<string, unknown>; result?: Record<string, unknown> | null; status: string; errorMessage?: string | null; }
export interface AgentRunRecord { id: string; userRequest: string; status: string; finalAnswer?: string | null; dataAvailability?: string | null; failureCode?: string | null; failureDetail?: string | null; toolCalls: AgentToolCallRecord[]; }
export interface AgentStatusRecord { available: boolean; provider: string; model: string; detail: string; }
export interface AgentProviderDiagnosticRecord { ok: boolean; provider: string; model: string; code?: string | null; detail: string; }
export interface NMRImportFormatRecord { entityType: string; requiredColumns: string[]; optionalColumns: string[]; listSeparator?: string | null; }
export interface NMRImportErrorRecord { row: number; field?: string | null; message: string; }
export interface NMRImportResultRecord { entityType: string; dryRun: boolean; totalRows: number; validRows: number; importedCount: number; importedIds: string[]; errors: NMRImportErrorRecord[]; }
export interface NMRProteinRecord { id: string; name: string; constructName: string; sequence: string; isotopeLabels: string[]; residueCount: number; }
export interface NMRSampleRecord { id: string; name: string; sampleType: string; concentrationValue?: number | null; concentrationUnit?: string | null; buffer: string; ph?: number | null; proteinIds: string[]; ligandIds: string[]; }
export interface NMRLigandRecord { id: string; name: string; identifier: string; molecularFormula: string; molecularWeightDa?: number | null; }
export interface NMRSpectrumRecord { id: string; name: string; sampleId?: string | null; experimentType: string; nuclei: string[]; spectrometerFrequencyMhz?: number | null; temperatureK?: number | null; status: string; peakCount: number; }
export interface NMRResidueRecord { id: string; proteinId: string; sequenceNumber: number; insertionCode: string; residueName: string; oneLetterCode: string; notes: string; }
export interface NMRPeakRecord { id: string; spectrumId: string; label: string; positionsPpm: number[]; intensity?: number | null; volume?: number | null; assignmentCount: number; }
export interface NMRAssignmentRecord { id: string; peakId: string; residueId: string; atomNames: string[]; confidence?: number | null; status: string; notes: string; }
export interface NMRChemicalShiftRecord { id: string; spectrumId: string; residueId: string; peakId?: string | null; atomName: string; nucleus: string; valuePpm: number; uncertaintyPpm?: number | null; }
export interface NMRShiftDeltaRecord { residueId: string; sequenceNumber: number; residueName: string; atomName: string; nucleus: string; referencePpm: number; comparisonPpm: number; deltaPpm: number; }
export interface NMRSpectrumComparisonRecord { matchedShiftCount: number; referenceOnlyCount: number; comparisonOnlyCount: number; deltas: NMRShiftDeltaRecord[]; }
export interface NMRResiduePerturbationRecord { residueId: string; sequenceNumber: number; residueName: string; matchedAtoms: string[]; componentDeltasPpm: Record<string, number>; perturbationPpm: number; }
export interface NMRCSPRecord { formula: string; nucleusWeights: Record<string, number>; residueCount: number; residues: NMRResiduePerturbationRecord[]; }

interface ApiUser {
  id: string;
  email: string;
  display_name: string;
  role: string;
  lab_id: string;
  created_at: string;
}

interface ApiProject {
  id: string;
  title: string;
  code: string;
  description: string;
  owner_id?: string | null;
  status: string;
  tags: string[];
  owner_display_name?: string | null;
  experiment_count: number;
  workflow_count: number;
  progress_percent: number;
  members: ApiProjectMember[];
  created_at: string;
  updated_at: string;
}

interface ApiProjectMember {
  user_id: string;
  display_name: string;
  email: string;
  lab_role: string;
  project_role: string;
}

interface ApiWorkflowMember {
  user_id: string;
  display_name: string;
  email: string;
  lab_role: string;
  workflow_role: string;
}

interface ApiLabMember {
  id: string;
  email: string;
  display_name: string;
  role: string;
  lab_id: string;
  created_at: string;
}

interface ApiExternalDocSummary {
  slug: string;
  title: string;
  updated_at: string;
}

interface ApiExternalDoc extends ApiExternalDocSummary {
  content: string;
}

interface ApiActivityItem {
  occurred_at: string;
  message: string;
  type: string;
  context: string;
}

interface ApiHomeSummary {
  user_display_name: string;
  active_experiment_count: number;
  protocol_count: number;
  project_count: number;
  completed_experiment_count: number;
  recent_projects: ApiProject[];
  recent_activity: ApiActivityItem[];
}

interface ApiSyncStatus {
  app_mode: string;
  database_backend: string;
  auth_backend: string;
  storage_backend: string;
  local_status: string;
  pending_changes: number;
  last_local_write_at?: string | null;
  last_sync_attempt_at?: string | null;
  last_sync_success_at?: string | null;
  last_error?: string | null;
  last_operation?: string | null;
  hosted_sync_ready: boolean;
  message: string;
}

interface ApiAIProviderStatus {
  id: string;
  label: string;
  configured: boolean;
  status: string;
  detail: string;
}

interface ApiLocalModelRuntime {
  id: string;
  label: string;
  installed: boolean;
  enabled: boolean;
  status: string;
  detail: string;
}

interface ApiAISettings {
  chat_enabled: boolean;
  workflow_builder_enabled: boolean;
  analysis_modules_enabled: boolean;
  local_models_enabled: boolean;
  api_keys_enabled: boolean;
  supported_api_providers: ApiAIProviderStatus[];
  local_model_runtimes: ApiLocalModelRuntime[];
  notes: string[];
}

interface ApiAnalysisModule {
  id: string;
  name: string;
  status: string;
  category: string;
  description: string;
  input_types: string[];
  output_types: string[];
}

interface ApiMCPTool {
  name: string;
  method: string;
  path: string;
  summary: string;
}

interface ApiMCPManifest {
  server_name: string;
  server_version: string;
  transport: string;
  status: string;
  openapi_url: string;
  tool_count: number;
  tools: ApiMCPTool[];
  notes: string[];
}

interface ApiChatChannel {
  id: string;
  lab_id: string;
  name: string;
  topic: string;
  created_by_id?: string | null;
  message_count: number;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  created_at: string;
  updated_at: string;
}

interface ApiChatMessage {
  id: string;
  channel_id: string;
  lab_id: string;
  author_id?: string | null;
  author_display_name?: string | null;
  body: string;
  referenced_workflow_id?: string | null;
  referenced_workflow_title?: string | null;
  referenced_experiment_id?: string | null;
  referenced_experiment_title?: string | null;
  attachments: ApiAttachment[];
  created_at: string;
  updated_at: string;
}

interface ApiProfileSummary {
  user: ApiUser;
  institution: string;
  lab_name: string;
  focus: string;
  expertise: string[];
  experiment_count: number;
  protocol_count: number;
  project_count: number;
  completed_experiment_count: number;
  recent_activity: ApiActivityItem[];
  monthly_activity: number[];
}

interface ApiIOItem extends Omit<IOItem, "id"> {
  id?: string;
}

interface ApiParam extends Omit<Param, "id"> {
  id?: string;
}

interface ApiWorkflowBranchStep {
  id: string;
  workflow_id: string;
  workflow_branch_id?: string | null;
  parent_step_id?: string | null;
  branch_track_id?: string | null;
  order_index: number;
  label: string;
  sublabel?: string | null;
  status_template: string;
  duration?: string | null;
  procedure_markdown: string;
  inputs: ApiIOItem[];
  parameters: ApiParam[];
  outputs: ApiIOItem[];
  notes: string;
  attachments?: ApiAttachment[];
}

interface ApiAttachment {
  id: string;
  owner_type: string;
  owner_id: string;
  filename: string;
  content_type: string;
  storage_backend: string;
  local_path?: string | null;
  remote_url?: string | null;
  download_url: string;
  created_at: string;
}

interface ApiWorkflowBranch {
  id: string;
  workflow_id: string;
  anchor_step_id: string;
  label: string;
  steps: ApiWorkflowBranchStep[];
}

interface ApiWorkflowStep extends ApiWorkflowBranchStep {
  branch_tracks: ApiWorkflowBranch[];
}

interface ApiWorkflow {
  id: string;
  title: string;
  description: string;
  owner_id?: string | null;
  project_id?: string | null;
  visibility: string;
  library_state: string;
  version: number;
  tags: string[];
  members: ApiWorkflowMember[];
  steps: ApiWorkflowStep[];
  created_at: string;
  updated_at: string;
}

interface ApiExperimentStepRun {
  id: string;
  experiment_workflow_run_id: string;
  source_workflow_step_id: string;
  order_index: number;
  label: string;
  sublabel?: string | null;
  status: string;
  duration?: string | null;
  procedure_markdown: string;
  inputs: ApiIOItem[];
  parameters: ApiParam[];
  outputs: ApiIOItem[];
  notes: string;
  attachments?: ApiAttachment[];
}

interface ApiExperimentWorkflowRun {
  id: string;
  experiment_id: string;
  source_workflow_id: string;
  workflow_title: string;
  workflow_description: string;
  workflow_version: number;
  order_index: number;
  status: string;
  step_runs: ApiExperimentStepRun[];
}

interface ApiExperiment {
  id: string;
  project_id?: string | null;
  title: string;
  experiment_date: string;
  operator_id?: string | null;
  status: string;
  notes: string;
  workflow_runs: ApiExperimentWorkflowRun[];
}

export interface WorkflowPageData {
  batch1WorkflowId: string;
  batch2WorkflowId: string;
  batch1: WorkflowStep[];
  batch2: WorkflowStep[];
}

export interface UserRecord {
  id: string;
  email: string;
  displayName: string;
  role: string;
  labId: string;
  createdAt: string;
}

export interface ProjectRecord {
  id: string;
  title: string;
  code: string;
  description: string;
  status: string;
  tags: string[];
  ownerDisplayName?: string;
  experimentCount: number;
  workflowCount: number;
  progressPercent: number;
  members: ProjectMemberRecord[];
  createdAt: string;
  updatedAt: string;
}

export interface ProjectMemberRecord {
  userId: string;
  displayName: string;
  email: string;
  labRole: string;
  projectRole: string;
}

export interface LabMemberRecord {
  id: string;
  email: string;
  displayName: string;
  role: string;
  labId: string;
  createdAt: string;
}

export interface WorkflowMemberRecord {
  userId: string;
  displayName: string;
  email: string;
  labRole: string;
  workflowRole: string;
}

export interface WorkflowRecord {
  id: string;
  title: string;
  description: string;
  projectId?: string;
  visibility: string;
  libraryState: string;
  version: number;
  tags: string[];
  members: WorkflowMemberRecord[];
  steps: WorkflowStep[];
  createdAt: string;
  updatedAt: string;
}

export interface ExternalDocSummaryRecord {
  slug: string;
  title: string;
  updatedAt: string;
}

export interface ExternalDocRecord extends ExternalDocSummaryRecord {
  content: string;
}

export interface ActivityItemRecord {
  occurredAt: string;
  message: string;
  type: string;
  context: string;
}

export interface HomeSummaryRecord {
  userDisplayName: string;
  activeExperimentCount: number;
  protocolCount: number;
  projectCount: number;
  completedExperimentCount: number;
  recentProjects: ProjectRecord[];
  recentActivity: ActivityItemRecord[];
}

export interface ProfileSummaryRecord {
  user: UserRecord;
  institution: string;
  labName: string;
  focus: string;
  expertise: string[];
  experimentCount: number;
  protocolCount: number;
  projectCount: number;
  completedExperimentCount: number;
  recentActivity: ActivityItemRecord[];
  monthlyActivity: number[];
}

export interface SyncStatusRecord {
  appMode: string;
  databaseBackend: string;
  authBackend: string;
  storageBackend: string;
  localStatus: string;
  pendingChanges: number;
  lastLocalWriteAt?: string;
  lastSyncAttemptAt?: string;
  lastSyncSuccessAt?: string;
  lastError?: string;
  lastOperation?: string;
  hostedSyncReady: boolean;
  message: string;
}

export interface AIProviderStatusRecord {
  id: string;
  label: string;
  configured: boolean;
  status: string;
  detail: string;
}

export interface LocalModelRuntimeRecord {
  id: string;
  label: string;
  installed: boolean;
  enabled: boolean;
  status: string;
  detail: string;
}

export interface AISettingsRecord {
  chatEnabled: boolean;
  workflowBuilderEnabled: boolean;
  analysisModulesEnabled: boolean;
  localModelsEnabled: boolean;
  apiKeysEnabled: boolean;
  supportedApiProviders: AIProviderStatusRecord[];
  localModelRuntimes: LocalModelRuntimeRecord[];
  notes: string[];
}

export interface AnalysisModuleRecord {
  id: string;
  name: string;
  status: string;
  category: string;
  description: string;
  inputTypes: string[];
  outputTypes: string[];
}

export interface MCPToolRecord {
  name: string;
  method: string;
  path: string;
  summary: string;
}

export interface MCPManifestRecord {
  serverName: string;
  serverVersion: string;
  transport: string;
  status: string;
  openapiUrl: string;
  toolCount: number;
  tools: MCPToolRecord[];
  notes: string[];
}

export interface ChatChannelRecord {
  id: string;
  labId: string;
  name: string;
  topic: string;
  createdById?: string;
  messageCount: number;
  lastMessagePreview?: string;
  lastMessageAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessageRecord {
  id: string;
  channelId: string;
  labId: string;
  authorId?: string;
  authorDisplayName?: string;
  body: string;
  referencedWorkflowId?: string;
  referencedWorkflowTitle?: string;
  referencedExperimentId?: string;
  referencedExperimentTitle?: string;
  attachments: AttachmentRecord[];
  createdAt: string;
  updatedAt: string;
}

export interface ReferenceOptionRecord {
  id: string;
  label: string;
}

export interface ExperimentWorkflowRun {
  id: string;
  sourceWorkflowId: string;
  workflowTitle: string;
  workflowDescription: string;
  workflowVersion: number;
  orderIndex: number;
  status: StepStatus;
  stepRuns: WorkflowStep[];
}

export interface ExperimentRecord {
  id: string;
  projectId?: string;
  title: string;
  experimentDate: string;
  operatorId?: string;
  status: StepStatus;
  notes: string;
  workflowRuns: ExperimentWorkflowRun[];
}

function toStepStatus(value: string): StepStatus {
  if (value === "complete" || value === "running" || value === "error") {
    return value;
  }
  return "pending";
}

function normalizeItems(items: ApiIOItem[]): IOItem[] {
  return items.map((item, index) => ({
    id: item.id || `${item.name}-${index}`,
    name: item.name,
    type: item.type,
    value: item.value,
    unit: item.unit,
    note: item.note,
  }));
}

function normalizeParams(params: ApiParam[]): Param[] {
  return params.map((param, index) => ({
    id: param.id || `${param.label}-${index}`,
    label: param.label,
    value: param.value,
  }));
}

function normalizeAttachments(attachments: ApiAttachment[] | undefined): AttachmentRecord[] {
  return (attachments ?? []).map((attachment) => ({
    id: attachment.id,
    filename: attachment.filename,
    contentType: attachment.content_type,
    downloadUrl: attachment.download_url.startsWith("http")
      ? attachment.download_url
      : `${API_ROOT}${attachment.download_url}`,
    createdAt: attachment.created_at,
  }));
}

function toUserRecord(user: ApiUser): UserRecord {
  return {
    id: user.id,
    email: user.email,
    displayName: user.display_name,
    role: user.role,
    labId: user.lab_id,
    createdAt: user.created_at,
  };
}

function toProjectRecord(project: ApiProject): ProjectRecord {
  return {
    id: project.id,
    title: project.title,
    code: project.code,
    description: project.description,
    status: project.status,
    tags: project.tags,
    ownerDisplayName: project.owner_display_name ?? undefined,
    experimentCount: project.experiment_count,
    workflowCount: project.workflow_count,
    progressPercent: project.progress_percent,
    members: project.members.map((member) => ({
      userId: member.user_id,
      displayName: member.display_name,
      email: member.email,
      labRole: member.lab_role,
      projectRole: member.project_role,
    })),
    createdAt: project.created_at,
    updatedAt: project.updated_at,
  };
}

function toLabMemberRecord(member: ApiLabMember): LabMemberRecord {
  return {
    id: member.id,
    email: member.email,
    displayName: member.display_name,
    role: member.role,
    labId: member.lab_id,
    createdAt: member.created_at,
  };
}

function toWorkflowRecord(workflow: ApiWorkflow): WorkflowRecord {
  return {
    id: workflow.id,
    title: workflow.title,
    description: workflow.description,
    projectId: workflow.project_id ?? undefined,
    visibility: workflow.visibility,
    libraryState: workflow.library_state,
    version: workflow.version,
    tags: workflow.tags,
    members: workflow.members.map((member) => ({
      userId: member.user_id,
      displayName: member.display_name,
      email: member.email,
      labRole: member.lab_role,
      workflowRole: member.workflow_role,
    })),
    steps: workflow.steps.map(toUiStep),
    createdAt: workflow.created_at,
    updatedAt: workflow.updated_at,
  };
}

function toExternalDocSummaryRecord(doc: ApiExternalDocSummary): ExternalDocSummaryRecord {
  return {
    slug: doc.slug,
    title: doc.title,
    updatedAt: doc.updated_at,
  };
}

function toExternalDocRecord(doc: ApiExternalDoc): ExternalDocRecord {
  return {
    slug: doc.slug,
    title: doc.title,
    updatedAt: doc.updated_at,
    content: doc.content,
  };
}

function toActivityItemRecord(item: ApiActivityItem): ActivityItemRecord {
  return {
    occurredAt: item.occurred_at,
    message: item.message,
    type: item.type,
    context: item.context,
  };
}

function toHomeSummaryRecord(summary: ApiHomeSummary): HomeSummaryRecord {
  return {
    userDisplayName: summary.user_display_name,
    activeExperimentCount: summary.active_experiment_count,
    protocolCount: summary.protocol_count,
    projectCount: summary.project_count,
    completedExperimentCount: summary.completed_experiment_count,
    recentProjects: summary.recent_projects.map(toProjectRecord),
    recentActivity: summary.recent_activity.map(toActivityItemRecord),
  };
}

function toProfileSummaryRecord(summary: ApiProfileSummary): ProfileSummaryRecord {
  return {
    user: toUserRecord(summary.user),
    institution: summary.institution,
    labName: summary.lab_name,
    focus: summary.focus,
    expertise: summary.expertise,
    experimentCount: summary.experiment_count,
    protocolCount: summary.protocol_count,
    projectCount: summary.project_count,
    completedExperimentCount: summary.completed_experiment_count,
    recentActivity: summary.recent_activity.map(toActivityItemRecord),
    monthlyActivity: summary.monthly_activity,
  };
}

function toSyncStatusRecord(status: ApiSyncStatus): SyncStatusRecord {
  return {
    appMode: status.app_mode,
    databaseBackend: status.database_backend,
    authBackend: status.auth_backend,
    storageBackend: status.storage_backend,
    localStatus: status.local_status,
    pendingChanges: status.pending_changes,
    lastLocalWriteAt: status.last_local_write_at ?? undefined,
    lastSyncAttemptAt: status.last_sync_attempt_at ?? undefined,
    lastSyncSuccessAt: status.last_sync_success_at ?? undefined,
    lastError: status.last_error ?? undefined,
    lastOperation: status.last_operation ?? undefined,
    hostedSyncReady: status.hosted_sync_ready,
    message: status.message,
  };
}

function toAiProviderStatusRecord(provider: ApiAIProviderStatus): AIProviderStatusRecord {
  return {
    id: provider.id,
    label: provider.label,
    configured: provider.configured,
    status: provider.status,
    detail: provider.detail,
  };
}

function toLocalModelRuntimeRecord(runtime: ApiLocalModelRuntime): LocalModelRuntimeRecord {
  return {
    id: runtime.id,
    label: runtime.label,
    installed: runtime.installed,
    enabled: runtime.enabled,
    status: runtime.status,
    detail: runtime.detail,
  };
}

function toAiSettingsRecord(settings: ApiAISettings): AISettingsRecord {
  return {
    chatEnabled: settings.chat_enabled,
    workflowBuilderEnabled: settings.workflow_builder_enabled,
    analysisModulesEnabled: settings.analysis_modules_enabled,
    localModelsEnabled: settings.local_models_enabled,
    apiKeysEnabled: settings.api_keys_enabled,
    supportedApiProviders: settings.supported_api_providers.map(toAiProviderStatusRecord),
    localModelRuntimes: settings.local_model_runtimes.map(toLocalModelRuntimeRecord),
    notes: settings.notes,
  };
}

function toAnalysisModuleRecord(module: ApiAnalysisModule): AnalysisModuleRecord {
  return {
    id: module.id,
    name: module.name,
    status: module.status,
    category: module.category,
    description: module.description,
    inputTypes: module.input_types,
    outputTypes: module.output_types,
  };
}

function toMcpToolRecord(tool: ApiMCPTool): MCPToolRecord {
  return {
    name: tool.name,
    method: tool.method,
    path: tool.path,
    summary: tool.summary,
  };
}

function toMcpManifestRecord(manifest: ApiMCPManifest): MCPManifestRecord {
  return {
    serverName: manifest.server_name,
    serverVersion: manifest.server_version,
    transport: manifest.transport,
    status: manifest.status,
    openapiUrl: manifest.openapi_url,
    toolCount: manifest.tool_count,
    tools: manifest.tools.map(toMcpToolRecord),
    notes: manifest.notes,
  };
}

function toChatChannelRecord(channel: ApiChatChannel): ChatChannelRecord {
  return {
    id: channel.id,
    labId: channel.lab_id,
    name: channel.name,
    topic: channel.topic,
    createdById: channel.created_by_id ?? undefined,
    messageCount: channel.message_count,
    lastMessagePreview: channel.last_message_preview ?? undefined,
    lastMessageAt: channel.last_message_at ?? undefined,
    createdAt: channel.created_at,
    updatedAt: channel.updated_at,
  };
}

function toChatMessageRecord(message: ApiChatMessage): ChatMessageRecord {
  return {
    id: message.id,
    channelId: message.channel_id,
    labId: message.lab_id,
    authorId: message.author_id ?? undefined,
    authorDisplayName: message.author_display_name ?? undefined,
    body: message.body,
    referencedWorkflowId: message.referenced_workflow_id ?? undefined,
    referencedWorkflowTitle: message.referenced_workflow_title ?? undefined,
    referencedExperimentId: message.referenced_experiment_id ?? undefined,
    referencedExperimentTitle: message.referenced_experiment_title ?? undefined,
    attachments: normalizeAttachments(message.attachments),
    createdAt: message.created_at,
    updatedAt: message.updated_at,
  };
}

function toUiStep(
  step: ApiWorkflowStep | ApiWorkflowBranchStep | ApiExperimentStepRun,
  options?: { statusField?: "status" | "status_template" },
): WorkflowStep {
  const statusField = options?.statusField ?? ("status" in step ? "status" : "status_template");
  const branchTracks = "branch_tracks" in step && step.branch_tracks.length > 0
    ? step.branch_tracks.map((branchTrack) => ({
        id: branchTrack.id,
        label: branchTrack.label,
        steps: branchTrack.steps.map(toUiStep),
      }))
    : undefined;

  return {
    id: step.id,
    index: step.order_index,
    label: step.label,
    sublabel: step.sublabel || undefined,
    status: toStepStatus(step[statusField]),
    duration: step.duration || undefined,
    procedureMarkdown: step.procedure_markdown || "",
    inputs: normalizeItems(step.inputs),
    parameters: normalizeParams(step.parameters),
    outputs: normalizeItems(step.outputs),
    notes: step.notes || undefined,
    attachments: normalizeAttachments(step.attachments),
    branchTracks,
  };
}

function toStepPayload(step: WorkflowStep) {
  return {
    label: step.label,
    sublabel: step.sublabel || null,
    status_template: step.status,
    duration: step.duration || null,
    procedure_markdown: step.procedureMarkdown || "",
    inputs: step.inputs.map(({ id, ...item }) => item),
    parameters: step.parameters.map(({ id, ...param }) => param),
    outputs: step.outputs.map(({ id, ...item }) => item),
    notes: step.notes || "",
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const method = init?.method?.toUpperCase() ?? "GET";
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const raw = await response.text();
    let message = raw;
    try {
      const payload = JSON.parse(raw) as { message?: string; detail?: string | Array<{ msg?: string }>; code?: string };
      if (typeof payload.message === "string") message = payload.message;
      else if (typeof payload.detail === "string") message = payload.detail;
      else if (Array.isArray(payload.detail)) message = payload.detail.map(item => item.msg).filter(Boolean).join(" ");
      if (payload.code && message) message = `${message} (${payload.code.replaceAll("_", " ")})`;
    } catch {
      // Keep a non-JSON response body as the best available diagnostic.
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    if (typeof window !== "undefined" && method !== "GET") {
      window.dispatchEvent(new Event(SYNC_REFRESH_EVENT));
    }
    return undefined as T;
  }
  const payload = await response.json() as T;
  if (typeof window !== "undefined" && method !== "GET") {
    window.dispatchEvent(new Event(SYNC_REFRESH_EVENT));
  }
  return payload;
}

type ApiWorkflowDraft = {
  id: string; operation: string; payload: Record<string, unknown>; status: WorkflowDraftRecord["status"];
  expires_at: string; created_at: string; decided_at?: string | null; failure_detail?: string | null;
};

function toWorkflowDraftRecord(draft: ApiWorkflowDraft): WorkflowDraftRecord {
  return { id: draft.id, operation: draft.operation, payload: draft.payload, status: draft.status,
    expiresAt: draft.expires_at, createdAt: draft.created_at, decidedAt: draft.decided_at, failureDetail: draft.failure_detail };
}

export async function fetchWorkflowDrafts(): Promise<WorkflowDraftRecord[]> {
  return (await request<ApiWorkflowDraft[]>("/agent/workflow-drafts")).map(toWorkflowDraftRecord);
}

export async function confirmWorkflowDraft(draftId: string): Promise<WorkflowDraftRecord> {
  return toWorkflowDraftRecord(await request<ApiWorkflowDraft>(`/agent/workflow-drafts/${draftId}/confirm`, { method: "POST" }));
}

type ApiAgentRun = { id: string; user_request: string; status: string; final_answer?: string | null; data_availability?: string | null; failure_code?: string | null; failure_detail?: string | null; tool_calls?: Array<{ id: string; sequence: number; tool_name: string; arguments: Record<string, unknown>; result?: Record<string, unknown> | null; status: string; error_message?: string | null; }> };
function toAgentRun(run: ApiAgentRun): AgentRunRecord { return { id: run.id, userRequest: run.user_request, status: run.status, finalAnswer: run.final_answer, dataAvailability: run.data_availability, failureCode: run.failure_code, failureDetail: run.failure_detail, toolCalls: (run.tool_calls ?? []).map(call => ({ id: call.id, sequence: call.sequence, toolName: call.tool_name, arguments: call.arguments, result: call.result, status: call.status, errorMessage: call.error_message })) }; }
export async function fetchAgentStatus(): Promise<AgentStatusRecord> { return request<AgentStatusRecord>("/agent/status"); }
export async function runAgentProviderDiagnostic(): Promise<AgentProviderDiagnosticRecord> { return request<AgentProviderDiagnosticRecord>("/agent/provider-diagnostic", { method: "POST" }); }
export async function createAgentConversation(title: string): Promise<{ id: string }> { return request<{ id: string }>("/agent/conversations", { method: "POST", body: JSON.stringify({ title }) }); }
export async function runAgentConversation(conversationId: string, message: string): Promise<AgentRunRecord> { return toAgentRun(await request<ApiAgentRun>(`/agent/conversations/${conversationId}/runs`, { method: "POST", body: JSON.stringify({ message }) })); }
export async function fetchAgentRuns(conversationId: string): Promise<AgentRunRecord[]> {
  const runs = await request<ApiAgentRun[]>(`/agent/conversations/${conversationId}/runs`);
  const detailed = await Promise.all(runs.map(run => request<ApiAgentRun>(`/agent/conversations/${conversationId}/runs/${run.id}`)));
  return detailed.map(toAgentRun).reverse();
}

type ApiNMRImportFormat = { entity_type: string; required_columns: string[]; optional_columns: string[]; list_separator?: string | null };
type ApiNMRImportResult = { entity_type: string; dry_run: boolean; total_rows: number; valid_rows: number; imported_count: number; imported_ids: string[]; errors: Array<{ row: number; field?: string | null; message: string }> };
function toNMRImportResult(value: ApiNMRImportResult): NMRImportResultRecord { return { entityType: value.entity_type, dryRun: value.dry_run, totalRows: value.total_rows, validRows: value.valid_rows, importedCount: value.imported_count, importedIds: value.imported_ids, errors: value.errors }; }
export async function fetchNMRImportFormats(): Promise<NMRImportFormatRecord[]> { return (await request<ApiNMRImportFormat[]>("/nmr/imports")).map(value => ({ entityType: value.entity_type, requiredColumns: value.required_columns, optionalColumns: value.optional_columns, listSeparator: value.list_separator })); }
export async function uploadNMRImport(entityType: string, file: File, dryRun: boolean): Promise<NMRImportResultRecord> { const body = new FormData(); body.append("file", file); return toNMRImportResult(await request<ApiNMRImportResult>(`/nmr/imports/${entityType}?dry_run=${dryRun}`, { method: "POST", body })); }
export async function fetchNMRProteins(): Promise<NMRProteinRecord[]> { return (await request<Array<{ id: string; name: string; construct_name: string; sequence: string; isotope_labels: string[]; residue_count: number }>>("/nmr/proteins")).map(value => ({ id: value.id, name: value.name, constructName: value.construct_name, sequence: value.sequence, isotopeLabels: value.isotope_labels, residueCount: value.residue_count })); }
export async function fetchNMRSamples(): Promise<NMRSampleRecord[]> { return (await request<Array<{ id: string; name: string; sample_type: string; concentration_value?: number | null; concentration_unit?: string | null; buffer: string; ph?: number | null; protein_ids: string[]; ligand_ids: string[] }>>("/nmr/samples")).map(value => ({ id: value.id, name: value.name, sampleType: value.sample_type, concentrationValue: value.concentration_value, concentrationUnit: value.concentration_unit, buffer: value.buffer, ph: value.ph, proteinIds: value.protein_ids, ligandIds: value.ligand_ids })); }
export async function fetchNMRLigands(): Promise<NMRLigandRecord[]> { return (await request<Array<{ id: string; name: string; identifier: string; molecular_formula: string; molecular_weight_da?: number | null }>>("/nmr/ligands")).map(value => ({ id: value.id, name: value.name, identifier: value.identifier, molecularFormula: value.molecular_formula, molecularWeightDa: value.molecular_weight_da })); }
export async function fetchNMRSpectra(): Promise<NMRSpectrumRecord[]> { return (await request<Array<{ id: string; name: string; sample_id?: string | null; experiment_type: string; nuclei: string[]; spectrometer_frequency_mhz?: number | null; temperature_k?: number | null; status: string; peak_count: number }>>("/nmr/spectra")).map(value => ({ id: value.id, name: value.name, sampleId: value.sample_id, experimentType: value.experiment_type, nuclei: value.nuclei, spectrometerFrequencyMhz: value.spectrometer_frequency_mhz, temperatureK: value.temperature_k, status: value.status, peakCount: value.peak_count })); }
export async function fetchNMRResidues(proteinId: string): Promise<NMRResidueRecord[]> { return (await request<Array<{ id: string; protein_id: string; sequence_number: number; insertion_code: string; residue_name: string; one_letter_code: string; notes: string }>>(`/nmr/residues?protein_id=${encodeURIComponent(proteinId)}`)).map(value => ({ id: value.id, proteinId: value.protein_id, sequenceNumber: value.sequence_number, insertionCode: value.insertion_code, residueName: value.residue_name, oneLetterCode: value.one_letter_code, notes: value.notes })); }
export async function fetchNMRPeaks(spectrumId: string): Promise<NMRPeakRecord[]> { return (await request<Array<{ id: string; spectrum_id: string; label: string; positions_ppm: number[]; intensity?: number | null; volume?: number | null; assignment_count: number }>>(`/nmr/peaks?spectrum_id=${encodeURIComponent(spectrumId)}`)).map(value => ({ id: value.id, spectrumId: value.spectrum_id, label: value.label, positionsPpm: value.positions_ppm, intensity: value.intensity, volume: value.volume, assignmentCount: value.assignment_count })); }
export async function fetchNMRAssignments(peakId: string): Promise<NMRAssignmentRecord[]> { return (await request<Array<{ id: string; peak_id: string; residue_id: string; atom_names: string[]; confidence?: number | null; status: string; notes: string }>>(`/nmr/assignments?peak_id=${encodeURIComponent(peakId)}`)).map(value => ({ id: value.id, peakId: value.peak_id, residueId: value.residue_id, atomNames: value.atom_names, confidence: value.confidence, status: value.status, notes: value.notes })); }
export async function fetchNMRChemicalShifts(spectrumId: string): Promise<NMRChemicalShiftRecord[]> { return (await request<Array<{ id: string; spectrum_id: string; residue_id: string; peak_id?: string | null; atom_name: string; nucleus: string; value_ppm: number; uncertainty_ppm?: number | null }>>(`/nmr/chemical-shifts?spectrum_id=${encodeURIComponent(spectrumId)}`)).map(value => ({ id: value.id, spectrumId: value.spectrum_id, residueId: value.residue_id, peakId: value.peak_id, atomName: value.atom_name, nucleus: value.nucleus, valuePpm: value.value_ppm, uncertaintyPpm: value.uncertainty_ppm })); }
export async function compareNMRSpectra(referenceSpectrumId: string, comparisonSpectrumId: string): Promise<NMRSpectrumComparisonRecord> {
  const value = await request<{ matched_shift_count: number; reference_only_count: number; comparison_only_count: number; deltas: Array<{ residue_id: string; sequence_number: number; residue_name: string; atom_name: string; nucleus: string; reference_ppm: number; comparison_ppm: number; delta_ppm: number }> }>("/nmr/analyses/compare-spectra", { method: "POST", body: JSON.stringify({ reference_spectrum_id: referenceSpectrumId, comparison_spectrum_id: comparisonSpectrumId }) });
  return { matchedShiftCount: value.matched_shift_count, referenceOnlyCount: value.reference_only_count, comparisonOnlyCount: value.comparison_only_count, deltas: value.deltas.map(item => ({ residueId: item.residue_id, sequenceNumber: item.sequence_number, residueName: item.residue_name, atomName: item.atom_name, nucleus: item.nucleus, referencePpm: item.reference_ppm, comparisonPpm: item.comparison_ppm, deltaPpm: item.delta_ppm })) };
}
export async function calculateNMRCSP(referenceSpectrumId: string, comparisonSpectrumId: string, nucleusWeights: Record<string, number>): Promise<NMRCSPRecord> {
  const value = await request<{ formula: string; nucleus_weights: Record<string, number>; residue_count: number; residues: Array<{ residue_id: string; sequence_number: number; residue_name: string; matched_atoms: string[]; component_deltas_ppm: Record<string, number>; perturbation_ppm: number }> }>("/nmr/analyses/chemical-shift-perturbation", { method: "POST", body: JSON.stringify({ reference_spectrum_id: referenceSpectrumId, comparison_spectrum_id: comparisonSpectrumId, nucleus_weights: nucleusWeights }) });
  return { formula: value.formula, nucleusWeights: value.nucleus_weights, residueCount: value.residue_count, residues: value.residues.map(item => ({ residueId: item.residue_id, sequenceNumber: item.sequence_number, residueName: item.residue_name, matchedAtoms: item.matched_atoms, componentDeltasPpm: item.component_deltas_ppm, perturbationPpm: item.perturbation_ppm })) };
}

function toWorkflowPageData(workflows: ApiWorkflow[]): WorkflowPageData {
  const batch1 = workflows.find((workflow) => workflow.title === "ANC2 Batch 1");
  const batch2 = workflows.find((workflow) => workflow.title === "ANC2 Batch 2");
  if (!batch1 || !batch2) {
    throw new Error("ANC2 workflow seeds are missing");
  }

  return {
    batch1WorkflowId: batch1.id,
    batch2WorkflowId: batch2.id,
    batch1: batch1.steps.map(toUiStep),
    batch2: batch2.steps.map(toUiStep),
  };
}

export async function fetchAnc2WorkflowPageData(): Promise<WorkflowPageData> {
  const workflows = await request<ApiWorkflow[]>("/workflows?tag=anc2");
  return toWorkflowPageData(workflows);
}

export async function fetchWorkflows(filters?: {
  tag?: string;
  libraryState?: string;
  visibility?: string;
  projectId?: string;
}): Promise<WorkflowRecord[]> {
  const params = new URLSearchParams();
  if (filters?.tag) params.set("tag", filters.tag);
  if (filters?.libraryState) params.set("library_state", filters.libraryState);
  if (filters?.visibility) params.set("visibility", filters.visibility);
  if (filters?.projectId) params.set("project_id", filters.projectId);
  const query = params.toString();
  const workflows = await request<ApiWorkflow[]>(`/workflows${query ? `?${query}` : ""}`);
  return workflows.map(toWorkflowRecord);
}

export async function fetchWorkflow(workflowId: string): Promise<WorkflowRecord> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}`);
  return toWorkflowRecord(workflow);
}

export async function fetchCurrentUser(): Promise<UserRecord> {
  const user = await request<ApiUser>("/me");
  return toUserRecord(user);
}

export async function fetchProjects(): Promise<ProjectRecord[]> {
  const projects = await request<ApiProject[]>("/projects");
  return projects.map(toProjectRecord);
}

export async function fetchProject(projectId: string): Promise<ProjectRecord> {
  const project = await request<ApiProject>(`/projects/${projectId}`);
  return toProjectRecord(project);
}

export async function createProject(payload: {
  title: string;
  code: string;
  description: string;
  status?: string;
  tags: string[];
}): Promise<ProjectRecord> {
  const project = await request<ApiProject>("/projects", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      code: payload.code,
      description: payload.description,
      status: payload.status ?? "active",
      tags: payload.tags,
    }),
  });
  return toProjectRecord(project);
}

export async function createWorkflow(payload: {
  title: string;
  description?: string;
  projectId?: string;
  visibility?: string;
  libraryState?: string;
  version?: number;
  tags?: string[];
  members?: Array<{ userId: string; workflowRole: string }>;
}): Promise<WorkflowRecord> {
  const workflow = await request<ApiWorkflow>("/workflows", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description ?? "",
      project_id: payload.projectId ?? null,
      visibility: payload.visibility ?? "private",
      library_state: payload.libraryState ?? "draft",
      version: payload.version ?? 1,
      tags: payload.tags ?? [],
      members: payload.members?.map((member) => ({
        user_id: member.userId,
        role: member.workflowRole,
      })),
    }),
  });
  return toWorkflowRecord(workflow);
}

export async function updateProject(
  projectId: string,
  payload: {
    title?: string;
    description?: string;
    status?: string;
    tags?: string[];
    members?: Array<{ userId: string; projectRole: string }>;
  },
): Promise<ProjectRecord> {
  const project = await request<ApiProject>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      status: payload.status,
      tags: payload.tags,
      members: payload.members?.map((member) => ({
        user_id: member.userId,
        role: member.projectRole,
      })),
    }),
  });
  return toProjectRecord(project);
}

export async function deleteProject(projectId: string): Promise<void> {
  await request<void>(`/projects/${projectId}`, {
    method: "DELETE",
  });
}

export async function fetchLabMembers(): Promise<LabMemberRecord[]> {
  const members = await request<ApiLabMember[]>("/users/lab-members");
  return members.map(toLabMemberRecord);
}

export async function fetchExternalDocs(): Promise<ExternalDocSummaryRecord[]> {
  const docs = await request<ApiExternalDocSummary[]>("/docs");
  return docs.map(toExternalDocSummaryRecord);
}

export async function fetchExternalDoc(slug: string): Promise<ExternalDocRecord> {
  const doc = await request<ApiExternalDoc>(`/docs/${slug}`);
  return toExternalDocRecord(doc);
}

export async function fetchHomeSummary(): Promise<HomeSummaryRecord> {
  const summary = await request<ApiHomeSummary>("/dashboard/home");
  return toHomeSummaryRecord(summary);
}

export async function fetchProfileSummary(): Promise<ProfileSummaryRecord> {
  const summary = await request<ApiProfileSummary>("/profile/summary");
  return toProfileSummaryRecord(summary);
}

export async function fetchSyncStatus(): Promise<SyncStatusRecord> {
  const status = await request<ApiSyncStatus>("/sync/status");
  return toSyncStatusRecord(status);
}

export async function pushSyncStatus(): Promise<SyncStatusRecord> {
  const status = await request<ApiSyncStatus>("/sync/push", {
    method: "POST",
  });
  return toSyncStatusRecord(status);
}

export async function fetchAISettings(): Promise<AISettingsRecord> {
  const settings = await request<ApiAISettings>("/ai/settings");
  return toAiSettingsRecord(settings);
}

export async function fetchAnalysisModules(): Promise<AnalysisModuleRecord[]> {
  const modules = await request<ApiAnalysisModule[]>("/analysis/modules");
  return modules.map(toAnalysisModuleRecord);
}

export async function fetchMcpManifest(): Promise<MCPManifestRecord> {
  const manifest = await request<ApiMCPManifest>("/mcp/manifest");
  return toMcpManifestRecord(manifest);
}

export { SYNC_REFRESH_EVENT };

export async function fetchChatChannels(): Promise<ChatChannelRecord[]> {
  const channels = await request<ApiChatChannel[]>("/channels");
  return channels.map(toChatChannelRecord);
}

export async function deleteChatChannel(channelId: string): Promise<void> {
  await request<void>(`/channels/${channelId}`, {
    method: "DELETE",
  });
}

export async function createChatChannel(payload: {
  name: string;
  topic?: string;
}): Promise<ChatChannelRecord> {
  const channel = await request<ApiChatChannel>("/channels", {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      topic: payload.topic ?? "",
    }),
  });
  return toChatChannelRecord(channel);
}

export async function fetchChatMessages(channelId: string): Promise<ChatMessageRecord[]> {
  const messages = await request<ApiChatMessage[]>(`/channels/${channelId}/messages`);
  return messages.map(toChatMessageRecord);
}

export async function createChatMessage(
  channelId: string,
  payload: {
    body: string;
    referencedWorkflowId?: string;
    referencedExperimentId?: string;
  },
): Promise<ChatMessageRecord> {
  const message = await request<ApiChatMessage>(`/channels/${channelId}/messages`, {
    method: "POST",
    body: JSON.stringify({
      body: payload.body,
      referenced_workflow_id: payload.referencedWorkflowId ?? null,
      referenced_experiment_id: payload.referencedExperimentId ?? null,
    }),
  });
  return toChatMessageRecord(message);
}

export async function deleteChatMessage(channelId: string, messageId: string): Promise<void> {
  await request<void>(`/channels/${channelId}/messages/${messageId}`, {
    method: "DELETE",
  });
}

export async function uploadChatMessageAttachment(
  channelId: string,
  messageId: string,
  file: File,
): Promise<AttachmentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  const attachment = await request<ApiAttachment>(`/channels/${channelId}/messages/${messageId}/attachments`, {
    method: "POST",
    body: formData,
  });
  return normalizeAttachments([attachment])[0];
}

export async function fetchWorkflowReferenceOptions(): Promise<ReferenceOptionRecord[]> {
  const workflows = await fetchWorkflows();
  return workflows.map((workflow) => ({
    id: workflow.id,
    label: workflow.title,
  }));
}

export async function fetchExperimentReferenceOptions(): Promise<ReferenceOptionRecord[]> {
  const experiments = await request<ApiExperiment[]>("/experiments");
  return experiments.map((experiment) => ({
    id: experiment.id,
    label: experiment.title,
  }));
}

function toExperimentRecord(experiment: ApiExperiment): ExperimentRecord {
  return {
    id: experiment.id,
    projectId: experiment.project_id ?? undefined,
    title: experiment.title,
    experimentDate: experiment.experiment_date,
    operatorId: experiment.operator_id ?? undefined,
    status: toStepStatus(experiment.status),
    notes: experiment.notes,
    workflowRuns: experiment.workflow_runs.map((workflowRun) => ({
      id: workflowRun.id,
      sourceWorkflowId: workflowRun.source_workflow_id,
      workflowTitle: workflowRun.workflow_title,
      workflowDescription: workflowRun.workflow_description,
      workflowVersion: workflowRun.workflow_version,
      orderIndex: workflowRun.order_index,
      status: toStepStatus(workflowRun.status),
      stepRuns: workflowRun.step_runs.map((stepRun) => toUiStep(stepRun, { statusField: "status" })),
    })),
  };
}

export async function fetchProjectExperiments(projectId: string): Promise<ExperimentRecord[]> {
  const experiments = await request<ApiExperiment[]>(`/experiments?project_id=${encodeURIComponent(projectId)}`);
  return experiments.map(toExperimentRecord);
}

export async function instantiateExperiment(payload: {
  projectId: string;
  title: string;
  experimentDate: string;
  workflowIds: string[];
  notes?: string;
}): Promise<ExperimentRecord> {
  const experiment = await request<ApiExperiment>("/experiments/instantiate", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      title: payload.title,
      experiment_date: payload.experimentDate,
      workflow_ids: payload.workflowIds,
      notes: payload.notes ?? "",
    }),
  });
  return toExperimentRecord(experiment);
}

export async function deleteExperiment(experimentId: string): Promise<void> {
  await request<void>(`/experiments/${experimentId}`, {
    method: "DELETE",
  });
}

export async function updateExperimentStepRun(
  experimentId: string,
  workflowRunId: string,
  step: WorkflowStep,
): Promise<ExperimentRecord> {
  const experiment = await request<ApiExperiment>(
    `/experiments/${experimentId}/workflow-runs/${workflowRunId}/steps/${step.id}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        label: step.label,
        sublabel: step.sublabel || null,
        status: step.status,
        duration: step.duration || null,
        procedure_markdown: step.procedureMarkdown || "",
        inputs: step.inputs.map(({ id, ...item }) => item),
        parameters: step.parameters.map(({ id, ...param }) => param),
        outputs: step.outputs.map(({ id, ...item }) => item),
        notes: step.notes || "",
      }),
    },
  );
  return toExperimentRecord(experiment);
}

export async function uploadWorkflowStepAttachment(
  workflowId: string,
  stepId: string,
  file: File,
): Promise<AttachmentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  const attachment = await request<ApiAttachment>(`/workflows/${workflowId}/steps/${stepId}/attachments`, {
    method: "POST",
    body: formData,
  });
  return normalizeAttachments([attachment])[0];
}

export async function uploadExperimentStepRunAttachment(
  experimentId: string,
  workflowRunId: string,
  stepRunId: string,
  file: File,
): Promise<AttachmentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  const attachment = await request<ApiAttachment>(
    `/experiments/${experimentId}/workflow-runs/${workflowRunId}/steps/${stepRunId}/attachments`,
    {
      method: "POST",
      body: formData,
    },
  );
  return normalizeAttachments([attachment])[0];
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  await request<void>(`/attachments/${attachmentId}`, {
    method: "DELETE",
  });
}

export async function createMainWorkflowStep(
  workflowId: string,
  afterStepId: string | null,
  payload: WorkflowStep,
): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/steps`, {
    method: "POST",
    body: JSON.stringify({
      after_step_id: afterStepId,
      ...toStepPayload(payload),
    }),
  });
  return workflow.steps.map(toUiStep);
}

export async function updateWorkflowStep(workflowId: string, step: WorkflowStep): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/steps/${step.id}`, {
    method: "PATCH",
    body: JSON.stringify(toStepPayload(step)),
  });
  return workflow.steps.map(toUiStep);
}

export async function deleteWorkflowStep(workflowId: string, stepId: string): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/steps/${stepId}`, {
    method: "DELETE",
  });
  return workflow.steps.map(toUiStep);
}

export async function createWorkflowBranch(
  workflowId: string,
  anchorStepId: string,
  label: string,
): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/branches`, {
    method: "POST",
    body: JSON.stringify({ anchor_step_id: anchorStepId, label }),
  });
  return workflow.steps.map(toUiStep);
}

export async function deleteWorkflowBranch(workflowId: string, branchId: string): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/branches/${branchId}`, {
    method: "DELETE",
  });
  return workflow.steps.map(toUiStep);
}

export async function createWorkflowBranchStep(
  workflowId: string,
  branchId: string,
  payload: WorkflowStep,
): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/branches/${branchId}/steps`, {
    method: "POST",
    body: JSON.stringify(toStepPayload(payload)),
  });
  return workflow.steps.map(toUiStep);
}

export async function insertStandardizedWorkflow(
  workflowId: string,
  payload: {
    standardizedWorkflowId: string;
    afterStepId?: string | null;
    anchorStepId?: string | null;
    branchLabel?: string | null;
  },
): Promise<WorkflowStep[]> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/insert-standardized`, {
    method: "POST",
    body: JSON.stringify({
      standardized_workflow_id: payload.standardizedWorkflowId,
      after_step_id: payload.afterStepId ?? null,
      anchor_step_id: payload.anchorStepId ?? null,
      branch_label: payload.branchLabel ?? null,
    }),
  });
  return workflow.steps.map(toUiStep);
}

export async function standardizeWorkflow(
  workflowId: string,
  payload: {
    title: string;
    description?: string;
    tags?: string[];
  },
): Promise<WorkflowRecord> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/standardize`, {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description ?? "",
      tags: payload.tags ?? [],
    }),
  });
  return toWorkflowRecord(workflow);
}

export async function updateWorkflow(
  workflowId: string,
  payload: {
    title?: string;
    description?: string;
    visibility?: string;
    libraryState?: string;
    version?: number;
    projectId?: string | null;
    tags?: string[];
    members?: Array<{ userId: string; workflowRole: string }>;
  },
): Promise<WorkflowRecord> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      visibility: payload.visibility,
      library_state: payload.libraryState,
      version: payload.version,
      project_id: payload.projectId,
      tags: payload.tags,
      members: payload.members?.map((member) => ({
        user_id: member.userId,
        role: member.workflowRole,
      })),
    }),
  });
  return toWorkflowRecord(workflow);
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  await request<void>(`/workflows/${workflowId}`, {
    method: "DELETE",
  });
}

export async function publishWorkflow(workflowId: string): Promise<WorkflowRecord> {
  const workflow = await request<ApiWorkflow>(`/workflows/${workflowId}/publish`, {
    method: "POST",
  });
  return toWorkflowRecord(workflow);
}
