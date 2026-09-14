from datetime import date, datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class UserRole(str, Enum):
    professor = "professor"
    post_doc = "post_doc"
    phd = "phd"
    student = "student"
    intern = "intern"


class AccessRole(str, Enum):
    owner = "owner"
    editor = "editor"
    commenter = "commenter"
    viewer = "viewer"


class LibraryState(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class RunStatus(str, Enum):
    planned = "planned"
    running = "running"
    complete = "complete"
    blocked = "blocked"
    error = "error"


class AgentRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default=UserRole.student.value)
    lab_id: Mapped[str] = mapped_column(String, default="local-lab")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent_conversations: Mapped[list["AgentConversation"]] = relationship(back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String, default=AccessRole.viewer.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    visibility: Mapped[str] = mapped_column(String, default="private")
    library_state: Mapped[str] = mapped_column(String, default=LibraryState.draft.value)
    version: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    branches: Mapped[list["WorkflowBranch"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")


class WorkflowMember(Base):
    __tablename__ = "workflow_members"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String, default=AccessRole.viewer.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkflowBranch(Base):
    __tablename__ = "workflow_branches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.id"), index=True)
    anchor_step_id: Mapped[str] = mapped_column(ForeignKey("workflow_steps.id"), index=True)
    label: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow: Mapped[Workflow] = relationship(back_populates="branches")
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="branch",
        cascade="all, delete-orphan",
        foreign_keys="WorkflowStep.workflow_branch_id",
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.id"), index=True)
    workflow_branch_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workflow_branches.id"), nullable=True, index=True)
    parent_step_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workflow_steps.id"), nullable=True)
    branch_track_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String)
    sublabel: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status_template: Mapped[str] = mapped_column(String, default="pending")
    duration: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    procedure_markdown: Mapped[str] = mapped_column(Text, default="")
    inputs: Mapped[list[dict]] = mapped_column(JSON, default=list)
    parameters: Mapped[list[dict]] = mapped_column(JSON, default=list)
    outputs: Mapped[list[dict]] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow: Mapped[Workflow] = relationship(back_populates="steps")
    branch: Mapped[Optional[WorkflowBranch]] = relationship(
        back_populates="steps",
        foreign_keys=[workflow_branch_id],
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, index=True)
    experiment_date: Mapped[date] = mapped_column(Date)
    operator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default=RunStatus.planned.value)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow_runs: Mapped[list["ExperimentWorkflowRun"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ExperimentWorkflowRun(Base):
    __tablename__ = "experiment_workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), index=True)
    source_workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.id"), index=True)
    workflow_title: Mapped[str] = mapped_column(String)
    workflow_description: Mapped[str] = mapped_column(Text, default="")
    workflow_version: Mapped[int] = mapped_column(Integer, default=1)
    order_index: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default=RunStatus.planned.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    experiment: Mapped[Experiment] = relationship(back_populates="workflow_runs")
    step_runs: Mapped[list["ExperimentStepRun"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
    )


class ExperimentStepRun(Base):
    __tablename__ = "experiment_step_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    experiment_workflow_run_id: Mapped[str] = mapped_column(ForeignKey("experiment_workflow_runs.id"), index=True)
    source_workflow_step_id: Mapped[str] = mapped_column(ForeignKey("workflow_steps.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String)
    sublabel: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default=RunStatus.planned.value)
    duration: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    procedure_markdown: Mapped[str] = mapped_column(Text, default="")
    inputs: Mapped[list[dict]] = mapped_column(JSON, default=list)
    parameters: Mapped[list[dict]] = mapped_column(JSON, default=list)
    outputs: Mapped[list[dict]] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow_run: Mapped[ExperimentWorkflowRun] = relationship(back_populates="step_runs")


class ChatChannel(Base):
    __tablename__ = "chat_channels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    lab_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    topic: Mapped[str] = mapped_column(Text, default="")
    created_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("chat_channels.id"), index=True)
    lab_id: Mapped[str] = mapped_column(String, index=True)
    author_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text, default="")
    referenced_workflow_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    referenced_experiment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiments.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel: Mapped[ChatChannel] = relationship(back_populates="messages")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_type: Mapped[str] = mapped_column(String, index=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    storage_backend: Mapped[str] = mapped_column(String, default="local")
    local_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    remote_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pending_changes: Mapped[int] = mapped_column(Integer, default=0)
    last_local_write_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_operation: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String, default="Untitled NMR research conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped[User] = relationship(back_populates="agent_conversations")
    runs: Mapped[list["AgentRun"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("agent_conversations.id"), index=True)
    user_request: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String, default="openai")
    model: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default=AgentRunStatus.pending.value)
    final_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_availability: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_tool_call_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    provider_response_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped["AgentConversation"] = relationship(back_populates="runs")
    tool_calls: Mapped[list["AgentToolCall"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped["AgentRun"] = relationship(back_populates="tool_calls")
