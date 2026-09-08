from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    database: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    lab_id: str
    created_at: datetime


class IOItem(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    value: Optional[str] = None
    unit: Optional[str] = None
    note: Optional[str] = None


class StepParameter(BaseModel):
    id: Optional[str] = None
    label: str
    value: str


class WorkflowStepBase(BaseModel):
    label: str
    sublabel: Optional[str] = None
    status_template: str = "pending"
    duration: Optional[str] = None
    procedure_markdown: str = ""
    inputs: list[IOItem] = Field(default_factory=list)
    parameters: list[StepParameter] = Field(default_factory=list)
    outputs: list[IOItem] = Field(default_factory=list)
    notes: str = ""


class WorkflowCreate(BaseModel):
    title: str
    description: str = ""
    project_id: Optional[str] = None
    visibility: str = "private"
    library_state: str = "draft"
    version: int = 1
    tags: list[str] = Field(default_factory=list)
    members: Optional[list["WorkflowMemberWrite"]] = None


class WorkflowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None
    visibility: Optional[str] = None
    library_state: Optional[str] = None
    version: Optional[int] = None
    tags: Optional[list[str]] = None
    members: Optional[list["WorkflowMemberWrite"]] = None


class WorkflowStepCreate(WorkflowStepBase):
    after_step_id: Optional[str] = None


class WorkflowStepUpdate(WorkflowStepBase):
    pass


class WorkflowStepReorderRequest(BaseModel):
    ordered_step_ids: list[str]
    branch_id: Optional[str] = None


class WorkflowBranchCreate(BaseModel):
    anchor_step_id: str
    label: str


class WorkflowBranchUpdate(BaseModel):
    label: str


class WorkflowBranchStepCreate(WorkflowStepBase):
    pass


class WorkflowStandardizeRequest(BaseModel):
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    members: Optional[list["WorkflowMemberWrite"]] = None


class WorkflowInsertStandardizedRequest(BaseModel):
    standardized_workflow_id: str
    after_step_id: Optional[str] = None
    anchor_step_id: Optional[str] = None
    branch_label: Optional[str] = None


class WorkflowBranchStepRead(WorkflowStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_branch_id: Optional[str]
    parent_step_id: Optional[str]
    branch_track_id: Optional[str]
    order_index: int
    attachments: list["AttachmentRead"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkflowBranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    anchor_step_id: str
    label: str
    steps: list[WorkflowBranchStepRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkflowStepRead(WorkflowStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_branch_id: Optional[str]
    parent_step_id: Optional[str]
    branch_track_id: Optional[str]
    order_index: int
    attachments: list["AttachmentRead"] = Field(default_factory=list)
    branch_tracks: list[WorkflowBranchRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    owner_id: Optional[str]
    project_id: Optional[str] = None
    visibility: str
    library_state: str
    version: int
    tags: list[str] = Field(default_factory=list)
    members: list["WorkflowMemberRead"] = Field(default_factory=list)
    steps: list[WorkflowStepRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkflowMemberWrite(BaseModel):
    user_id: str
    role: str


class WorkflowMemberRead(BaseModel):
    user_id: str
    display_name: str
    email: str
    lab_role: str
    workflow_role: str


class ChatChannelCreate(BaseModel):
    name: str
    topic: str = ""


class ChatChannelUpdate(BaseModel):
    name: Optional[str] = None
    topic: Optional[str] = None


class ChatChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lab_id: str
    name: str
    topic: str
    created_by_id: Optional[str]
    message_count: int = 0
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    body: str
    referenced_workflow_id: Optional[str] = None
    referenced_experiment_id: Optional[str] = None


class ChatMessageUpdate(BaseModel):
    body: str
    referenced_workflow_id: Optional[str] = None
    referenced_experiment_id: Optional[str] = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    lab_id: str
    author_id: Optional[str]
    author_display_name: Optional[str] = None
    body: str
    referenced_workflow_id: Optional[str] = None
    referenced_workflow_title: Optional[str] = None
    referenced_experiment_id: Optional[str] = None
    referenced_experiment_title: Optional[str] = None
    attachments: list["AttachmentRead"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProjectMemberWrite(BaseModel):
    user_id: str
    role: str


class ProjectMemberRead(BaseModel):
    user_id: str
    display_name: str
    email: str
    lab_role: str
    project_role: str


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    code: str
    description: str
    owner_id: Optional[str]
    status: str
    tags: list[str] = Field(default_factory=list)
    owner_display_name: Optional[str] = None
    experiment_count: int = 0
    workflow_count: int = 0
    progress_percent: int = 0
    members: list[ProjectMemberRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    title: str
    code: str
    description: str = ""
    status: str = "active"
    tags: list[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    members: Optional[list[ProjectMemberWrite]] = None


class LabMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    lab_id: str
    created_at: datetime


class ExperimentCreate(BaseModel):
    project_id: Optional[str] = None
    title: str
    experiment_date: date
    notes: str = ""


class ExperimentInstantiateRequest(BaseModel):
    project_id: Optional[str] = None
    title: str
    experiment_date: date
    workflow_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class ExperimentUpdate(BaseModel):
    title: Optional[str] = None
    experiment_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ExperimentStepRunUpdate(WorkflowStepBase):
    status: str = "planned"


class ExperimentStepRunRead(WorkflowStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_workflow_run_id: str
    source_workflow_step_id: str
    order_index: int
    status: str
    attachments: list["AttachmentRead"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ExperimentWorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    source_workflow_id: str
    workflow_title: str
    workflow_description: str
    workflow_version: int
    order_index: int
    status: str
    step_runs: list[ExperimentStepRunRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str]
    title: str
    experiment_date: date
    operator_id: Optional[str]
    status: str
    notes: str
    workflow_runs: list[ExperimentWorkflowRunRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_type: str
    owner_id: str
    filename: str
    content_type: str
    storage_backend: str
    local_path: Optional[str]
    remote_url: Optional[str]
    download_url: str
    created_at: datetime


class ExternalDocSummaryRead(BaseModel):
    slug: str
    title: str
    updated_at: datetime


class ExternalDocRead(ExternalDocSummaryRead):
    content: str


class ActivityItemRead(BaseModel):
    occurred_at: datetime
    message: str
    type: str
    context: str


class HomeSummaryRead(BaseModel):
    user_display_name: str
    active_experiment_count: int
    protocol_count: int
    project_count: int
    completed_experiment_count: int
    recent_projects: list[ProjectRead] = Field(default_factory=list)
    recent_activity: list[ActivityItemRead] = Field(default_factory=list)


class ProfileSummaryRead(BaseModel):
    user: UserRead
    institution: str
    lab_name: str
    focus: str
    expertise: list[str] = Field(default_factory=list)
    experiment_count: int
    protocol_count: int
    project_count: int
    completed_experiment_count: int
    recent_activity: list[ActivityItemRead] = Field(default_factory=list)
    monthly_activity: list[int] = Field(default_factory=list)


class SyncStatusRead(BaseModel):
    app_mode: str
    database_backend: str
    auth_backend: str
    storage_backend: str
    local_status: str
    pending_changes: int
    last_local_write_at: Optional[datetime] = None
    last_sync_attempt_at: Optional[datetime] = None
    last_sync_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    last_operation: Optional[str] = None
    hosted_sync_ready: bool
    message: str


class AIProviderStatusRead(BaseModel):
    id: str
    label: str
    configured: bool
    status: str
    detail: str


class LocalModelRuntimeRead(BaseModel):
    id: str
    label: str
    installed: bool
    enabled: bool
    status: str
    detail: str


class AISettingsRead(BaseModel):
    chat_enabled: bool
    workflow_builder_enabled: bool
    analysis_modules_enabled: bool
    local_models_enabled: bool
    api_keys_enabled: bool
    supported_api_providers: list[AIProviderStatusRead] = Field(default_factory=list)
    local_model_runtimes: list[LocalModelRuntimeRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AnalysisModuleRead(BaseModel):
    id: str
    name: str
    status: str
    category: str
    description: str
    input_types: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)


class MCPToolRead(BaseModel):
    name: str
    method: str
    path: str
    summary: str


class MCPManifestRead(BaseModel):
    server_name: str
    server_version: str
    transport: str
    status: str
    openapi_url: str
    tool_count: int
    tools: list[MCPToolRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
