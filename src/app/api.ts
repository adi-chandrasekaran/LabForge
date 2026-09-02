import type { AttachmentRecord, IOItem, Param, StepStatus, WorkflowStep } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://127.0.0.1:8000/api/v1";
const API_ROOT = API_BASE.replace(/\/api\/v1$/, "");
const SYNC_REFRESH_EVENT = "nmr-lab-sync-refresh";

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
    const message = await response.text();
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
