from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, StrictBool, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from .chat_routes import _serialize_channel, _serialize_message
from .experiment_routes import _serialize_experiment
from .models import User
from .project_routes import serialize_project
from .schemas import (
    ChatChannelRead,
    ChatMessageRead,
    ExperimentRead,
    ExperimentStepRunRead,
    ProjectRead,
    WorkflowRead,
)
from .services import lookup as lookup_service
from .workflow_routes import _serialize_workflow


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyInput(ToolInput):
    pass


class IdentifierInput(ToolInput):
    id: str = Field(min_length=1)


class GetProjectInput(ToolInput):
    project_id: str = Field(min_length=1)


class GetWorkflowInput(ToolInput):
    workflow_id: str = Field(min_length=1)


class ListWorkflowsInput(ToolInput):
    tag: Optional[str] = Field(default=None, min_length=1)
    library_state: Optional[str] = Field(default=None, min_length=1)
    visibility: Optional[str] = Field(default=None, min_length=1)
    project_id: Optional[str] = Field(default=None, min_length=1)


class GetExperimentInput(ToolInput):
    experiment_id: str = Field(min_length=1)


class ListExperimentsInput(ToolInput):
    project_id: Optional[str] = Field(default=None, min_length=1)


class GetExperimentRunStepInput(ToolInput):
    experiment_id: str = Field(min_length=1)
    workflow_run_id: str = Field(min_length=1)
    step_run_id: str = Field(min_length=1)


class SearchExperimentNotesInput(ToolInput):
    query: str = Field(min_length=1)
    project_id: Optional[str] = Field(default=None, min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class ListChannelMessagesInput(ToolInput):
    channel_id: str = Field(min_length=1)
    limit: int = Field(default=200, ge=1, le=500)


class CreateNoteInput(ToolInput):
    channel_id: str = Field(min_length=1)
    body: str = Field(min_length=1)
    referenced_workflow_id: Optional[str] = Field(default=None, min_length=1)
    referenced_experiment_id: Optional[str] = Field(default=None, min_length=1)


class ToolError(BaseModel):
    code: str
    message: str
    details: Optional[list[dict[str, Any]]] = None


class ToolInvocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: StrictBool = False


class ToolInvocationResponse(BaseModel):
    tool_name: str
    ok: bool
    data: Any = None
    error: Optional[ToolError] = None


class ToolDefinitionRead(BaseModel):
    name: str
    description: str
    status: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permission: str
    side_effect: str
    confirmation_required: bool


class UnavailableToolRead(BaseModel):
    name: str
    reason: str


class AgentToolCatalogRead(BaseModel):
    contract_version: str = "1.0.0"
    execution_status: str = "enabled"
    tools: list[ToolDefinitionRead]
    unavailable_tools: list[UnavailableToolRead]


ToolHandler = Callable[[Session, User, BaseModel], Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    output_adapter: TypeAdapter[Any]
    permission: str
    side_effect: str
    confirmation_required: bool
    handler: ToolHandler


def _get_project(db: Session, _: User, payload: GetProjectInput) -> ProjectRead:
    return serialize_project(db, lookup_service.get_project(db, payload.project_id))


def _list_projects(db: Session, _: User, __: EmptyInput) -> list[ProjectRead]:
    return [serialize_project(db, project) for project in lookup_service.list_projects(db)]


def _get_workflow(db: Session, _: User, payload: GetWorkflowInput) -> WorkflowRead:
    return _serialize_workflow(db, lookup_service.get_workflow(db, payload.workflow_id))


def _list_workflows(db: Session, _: User, payload: ListWorkflowsInput) -> list[WorkflowRead]:
    workflows = lookup_service.list_workflows(
        db,
        tag=payload.tag,
        library_state=payload.library_state,
        visibility=payload.visibility,
        project_id=payload.project_id,
    )
    return [_serialize_workflow(db, workflow) for workflow in workflows]


def _get_experiment(db: Session, _: User, payload: GetExperimentInput) -> ExperimentRead:
    return _serialize_experiment(db, lookup_service.get_experiment(db, payload.experiment_id))


def _list_experiments(db: Session, _: User, payload: ListExperimentsInput) -> list[ExperimentRead]:
    return [_serialize_experiment(db, experiment) for experiment in lookup_service.list_experiments(db, payload.project_id)]


def _get_experiment_run_step(db: Session, user: User, payload: GetExperimentRunStepInput) -> ExperimentStepRunRead:
    experiment = _get_experiment(db, user, GetExperimentInput(experiment_id=payload.experiment_id))
    for workflow_run in experiment.workflow_runs:
        if workflow_run.id == payload.workflow_run_id:
            for step_run in workflow_run.step_runs:
                if step_run.id == payload.step_run_id:
                    return step_run
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment step run not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment workflow run not found")


def _search_experiment_notes(db: Session, user: User, payload: SearchExperimentNotesInput) -> list[ExperimentRead]:
    experiments = _list_experiments(db, user, ListExperimentsInput(project_id=payload.project_id))
    needle = payload.query.casefold()
    return [experiment for experiment in experiments if needle in experiment.notes.casefold()][: payload.limit]


def _list_chat_channels(db: Session, user: User, _: EmptyInput) -> list[ChatChannelRead]:
    return [_serialize_channel(db, channel) for channel in lookup_service.list_channels(db, user)]


def _list_channel_messages(db: Session, user: User, payload: ListChannelMessagesInput) -> list[ChatMessageRead]:
    messages = lookup_service.list_channel_messages(db, user, payload.channel_id, payload.limit)
    return [_serialize_message(db, message) for message in messages]


def _create_note(db: Session, user: User, payload: CreateNoteInput) -> ChatMessageRead:
    message = lookup_service.create_channel_message(
        db,
        user,
        channel_id=payload.channel_id,
        body=payload.body,
        referenced_workflow_id=payload.referenced_workflow_id,
        referenced_experiment_id=payload.referenced_experiment_id,
    )
    return _serialize_message(db, message)


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "get_project": ToolDefinition("get_project", "Retrieve one project by id.", GetProjectInput, TypeAdapter(ProjectRead), "read; preserve backend project visibility behavior", "none", False, _get_project),
    "list_projects": ToolDefinition("list_projects", "List projects in the existing backend order.", EmptyInput, TypeAdapter(list[ProjectRead]), "read; preserve backend project visibility behavior", "none", False, _list_projects),
    "get_workflow": ToolDefinition("get_workflow", "Retrieve one workflow with steps and branches.", GetWorkflowInput, TypeAdapter(WorkflowRead), "read; preserve backend workflow visibility behavior", "none", False, _get_workflow),
    "list_workflows": ToolDefinition("list_workflows", "List workflows with supported backend filters.", ListWorkflowsInput, TypeAdapter(list[WorkflowRead]), "read; preserve backend workflow visibility behavior", "none", False, _list_workflows),
    "get_experiment": ToolDefinition("get_experiment", "Retrieve one experiment with workflow and step-run snapshots.", GetExperimentInput, TypeAdapter(ExperimentRead), "read; preserve backend experiment visibility behavior", "none", False, _get_experiment),
    "list_experiments": ToolDefinition("list_experiments", "List experiments, optionally for one project.", ListExperimentsInput, TypeAdapter(list[ExperimentRead]), "read; preserve backend experiment visibility behavior", "none", False, _list_experiments),
    "get_experiment_run_step": ToolDefinition("get_experiment_run_step", "Retrieve a nested step run from one experiment.", GetExperimentRunStepInput, TypeAdapter(ExperimentStepRunRead), "read; select only from the returned parent experiment", "none", False, _get_experiment_run_step),
    "search_experiment_notes": ToolDefinition("search_experiment_notes", "Case-insensitively search existing experiment notes.", SearchExperimentNotesInput, TypeAdapter(list[ExperimentRead]), "read; filter only notes returned by the existing experiment listing", "none", False, _search_experiment_notes),
    "list_chat_channels": ToolDefinition("list_chat_channels", "List channels scoped to the authenticated user's lab.", EmptyInput, TypeAdapter(list[ChatChannelRead]), "read; backend constrains channels to the actor's lab_id", "none", False, _list_chat_channels),
    "list_channel_messages": ToolDefinition("list_channel_messages", "List messages in one lab-scoped channel.", ListChannelMessagesInput, TypeAdapter(list[ChatMessageRead]), "read; backend verifies channel lab scope", "none", False, _list_channel_messages),
    "create_note": ToolDefinition("create_note", "Create an auditable chat-message note in one channel.", CreateNoteInput, TypeAdapter(ChatMessageRead), "write; backend resolves actor, verifies lab scope, and validates references", "creates one ChatMessage; never updates embedded experiment or workflow notes", True, _create_note),
}


UNAVAILABLE_TOOLS = [
    UnavailableToolRead(name="get_sample", reason="No Sample entity, route, or service exists."),
    UnavailableToolRead(name="list_samples", reason="No Sample entity, route, or service exists."),
    UnavailableToolRead(name="get_spectrum", reason="No Spectrum entity, spectral-file representation, route, or service exists."),
    UnavailableToolRead(name="compare_spectra", reason="No spectra or comparison backend logic exists."),
    UnavailableToolRead(name="get_peak_assignments", reason="No Peak or Assignment entity, route, or service exists."),
    UnavailableToolRead(name="find_residue", reason="No Protein, sequence, or Residue representation exists."),
    UnavailableToolRead(name="get_residue_shifts", reason="No Residue or chemical-shift representation exists."),
    UnavailableToolRead(name="calculate_chemical_shift_perturbation", reason="No chemical-shift data or calculation backend logic exists."),
]


def catalog() -> AgentToolCatalogRead:
    return AgentToolCatalogRead(
        tools=[
            ToolDefinitionRead(
                name=tool.name,
                description=tool.description,
                status="supported",
                input_schema=tool.input_model.model_json_schema(),
                output_schema=tool.output_adapter.json_schema(),
                permission=tool.permission,
                side_effect=tool.side_effect,
                confirmation_required=tool.confirmation_required,
            )
            for tool in TOOL_REGISTRY.values()
        ],
        unavailable_tools=UNAVAILABLE_TOOLS,
    )


def invoke(db: Session, user: User, tool_name: str, request: ToolInvocationRequest) -> ToolInvocationResponse:
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        unavailable = next((item for item in UNAVAILABLE_TOOLS if item.name == tool_name), None)
        if unavailable is not None:
            raise ToolInvocationException(501, "tool_unavailable", unavailable.reason)
        raise ToolInvocationException(404, "tool_not_found", "The requested tool is not registered.")
    try:
        payload = tool.input_model.model_validate(request.arguments)
    except ValidationError as error:
        raise ToolInvocationException(
            422,
            "invalid_input",
            "Tool arguments do not match the input schema.",
            [{"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]} for item in error.errors()],
        ) from error
    if tool.confirmation_required and not request.confirmed:
        raise ToolInvocationException(409, "confirmation_required", "This tool requires confirmed: true before it can write data.")
    try:
        data = tool.handler(db, user, payload)
        return ToolInvocationResponse(tool_name=tool.name, ok=True, data=tool.output_adapter.dump_python(data, mode="json"))
    except HTTPException as error:
        code = "not_found" if error.status_code == 404 else "forbidden" if error.status_code == 403 else "invalid_request"
        raise ToolInvocationException(error.status_code, code, str(error.detail)) from error
    except Exception as error:
        raise ToolInvocationException(500, "tool_execution_failed", "The tool could not complete its operation.") from error


class ToolInvocationException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[list[dict[str, Any]]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def error_response(tool_name: str, error: ToolInvocationException) -> ToolInvocationResponse:
    return ToolInvocationResponse(
        tool_name=tool_name,
        ok=False,
        error=ToolError(code=error.code, message=error.message, details=error.details),
    )
