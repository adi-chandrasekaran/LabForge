import { useEffect, useMemo, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { CornerDownRight, Pencil, Plus, Shield, Trash2, Users, X } from "lucide-react";
import ConfirmDialog from "../components/ConfirmDialog";
import WorkflowTypeNavigator from "../components/WorkflowTypeNavigator";
import {
  createMainWorkflowStep,
  createWorkflow,
  createWorkflowBranch,
  deleteWorkflow,
  deleteWorkflowBranch,
  deleteWorkflowStep,
  fetchCurrentUser,
  fetchLabMembers,
  fetchProjects,
  fetchWorkflows,
  publishWorkflow,
  updateWorkflow,
  updateWorkflowStep,
  type LabMemberRecord,
  type ProjectRecord,
  type UserRecord,
  type WorkflowMemberRecord,
  type WorkflowRecord,
} from "../api";
import type { BranchTrack, IOItem, Param, StepStatus, WorkflowStep } from "../types";

type DeleteTarget =
  | { kind: "workflow"; workflowId: string; label: string }
  | { kind: "step"; workflowId: string; stepId: string; label: string }
  | { kind: "branch"; workflowId: string; branchId: string; label: string };

const inputCls =
  "w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50";

const statusClass: Record<StepStatus, string> = {
  complete: "text-[#00f0b5]",
  running: "text-[#00d7ff]",
  pending: "text-[#60708a]",
  error: "text-[#ff6b6b]",
};

function csv(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function itemsToText(items: IOItem[]): string {
  return items.map((item) => [item.type, item.name, item.value ?? "", item.note ?? ""].join(" | ")).join("\n");
}

function paramsToText(params: Param[]): string {
  return params.map((param) => `${param.label} | ${param.value}`).join("\n");
}

function parseItems(text: string): IOItem[] {
  return text
    .split("\n")
    .map((line, index) => {
      const [type = "sample", name = "", value = "", note = ""] = line.split("|").map((part) => part.trim());
      if (!name) return null;
      return {
        id: `item-${index}-${name}`,
        type: type as IOItem["type"],
        name,
        value: value || undefined,
        note: note || undefined,
      };
    })
    .filter(Boolean) as IOItem[];
}

function parseParams(text: string): Param[] {
  return text
    .split("\n")
    .map((line, index) => {
      const [label = "", value = ""] = line.split("|").map((part) => part.trim());
      if (!label) return null;
      return { id: `param-${index}-${label}`, label, value };
    })
    .filter(Boolean) as Param[];
}

function blankStep(): WorkflowStep {
  return {
    id: `draft-${Date.now()}`,
    index: 0,
    label: "",
    status: "pending",
    duration: "",
    procedureMarkdown: "",
    inputs: [],
    parameters: [],
    outputs: [],
    notes: "",
  };
}

function ItemList({ title, items }: { title: string; items: IOItem[] }) {
  return (
    <div>
      <div className="mb-3 border-b border-[#1b2633] pb-2 text-[10px] font-bold uppercase tracking-[0.22em] text-[#5c718d]">
        {title}
      </div>
      <div className="space-y-3">
        {items.length === 0 ? <p className="text-xs text-[#50627b]">No entries yet.</p> : null}
        {items.map((item) => (
          <div key={item.id} className="relative pl-4 text-sm">
            <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-[#00c9a7]" />
            <div className="font-bold text-[#d3dce8]">
              {item.name} {item.value ? <span className="text-[#ffb000]">{item.value}</span> : null}
            </div>
            <div className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-[#52657f]">{item.type}</div>
            {item.note ? <div className="mt-1 text-xs italic text-[#52657f]">{item.note}</div> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function StepDetail({ step }: { step: WorkflowStep }) {
  return (
    <div className="mx-6 mb-4 rounded border border-[#1b2633] bg-[#080c12] p-5">
      <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.28em] text-[#5c718d]">
        Inner schematic - Step {String(step.index).padStart(2, "0")} / {step.label}
      </div>
      <div className="mb-5 rounded border border-[#1b2633] bg-[#0d151e] p-3 text-xs leading-relaxed text-[#7d90aa]">
        <div className="mb-1 text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Procedure</div>
        {step.procedureMarkdown || "No procedure added."}
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_160px_1fr]">
        <ItemList title="Inputs" items={step.inputs} />
        <div className="flex flex-col items-center justify-center gap-3 text-[#00c9a7]">
          <div>-&gt;</div>
          <div className="w-full rounded border border-[#007a6c] bg-[#0b1a1d] p-4 text-center">
            <div className="text-[10px] uppercase tracking-[0.2em] text-[#52657f]">Process</div>
            <div className="mt-2 text-sm font-bold text-[#00c9a7]">{step.label}</div>
            <div className="mt-3 border-t border-[#1b403d] pt-3 text-[10px] uppercase tracking-[0.2em] text-[#52657f]">
              Duration
            </div>
            <div className="text-sm text-[#d3dce8]">{step.duration || "-"}</div>
          </div>
          <div>-&gt;</div>
        </div>
        <ItemList title="Outputs" items={step.outputs} />
      </div>
      {step.parameters.length ? (
        <div className="mt-5 border-t border-[#1b2633] pt-4">
          <div className="mb-2 text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Parameters</div>
          <div className="flex flex-wrap gap-2">
            {step.parameters.map((param) => (
              <span key={param.id} className="rounded border border-[#243242] bg-[#121c27] px-2 py-1 text-[11px] text-[#8da0b8]">
                {param.label}: <b className="text-[#d3dce8]">{param.value}</b>
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {step.notes ? <div className="mt-4 border-t border-[#1b2633] pt-4 text-xs text-[#7d90aa]">{step.notes}</div> : null}
    </div>
  );
}

function StepCard({
  step,
  expanded,
  canEdit,
  onToggle,
  onAdd,
  onBranch,
  onEdit,
  onDelete,
  onDeleteBranch,
}: {
  step: WorkflowStep;
  expanded: boolean;
  canEdit: boolean;
  onToggle: () => void;
  onAdd: () => void;
  onBranch: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onDeleteBranch: (branch: BranchTrack) => void;
}) {
  return (
    <div className="group relative">
      {canEdit ? (
        <div className="absolute -left-3 top-1/2 hidden -translate-y-1/2 flex-col gap-1 group-hover:flex">
          <button className="rounded border border-[#00c9a7]/50 bg-[#0b1a1d] p-1 text-[#00c9a7]" title="Add step" onClick={onAdd}>
            <Plus size={13} />
          </button>
          <button className="rounded border border-[#b88700]/50 bg-[#1b1505] p-1 text-[#ffb000]" title="Diverge branch" onClick={onBranch}>
            <CornerDownRight size={13} />
          </button>
        </div>
      ) : null}
      <div
        className={`flex cursor-pointer items-center gap-4 rounded border bg-[#0b1118] px-4 py-4 ${
          expanded ? "border-[#007a6c] bg-[#09211f]" : "border-[#1b2633]"
        }`}
        onClick={onToggle}
      >
        <span className="text-xs text-[#52657f]">{String(step.index).padStart(2, "0")}</span>
        <span className="h-2 w-2 rounded-full bg-[#00c9a7]" />
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-bold text-[#d3dce8]">
            {step.label} {step.sublabel ? <span className="font-normal text-[#52657f]">{step.sublabel}</span> : null}
            <span className={`ml-2 text-[10px] uppercase ${statusClass[step.status]}`}>{step.status}</span>
          </div>
          <div className="text-xs text-[#52657f]">{step.duration || "-"}</div>
        </div>
        {canEdit ? (
          <div className="hidden gap-2 group-hover:flex" onClick={(event) => event.stopPropagation()}>
            <button className="text-[#7d90aa] hover:text-[#00c9a7]" title="Edit step" onClick={onEdit}>
              <Pencil size={14} />
            </button>
            <button className="text-[#7d90aa] hover:text-[#ff6b6b]" title="Delete step" onClick={onDelete}>
              <Trash2 size={14} />
            </button>
          </div>
        ) : null}
        <span className="text-[#52657f]">{expanded ? "v" : ">"}</span>
      </div>
      {expanded ? <StepDetail step={step} /> : null}
      {expanded && step.branchTracks?.length ? (
        <div className="ml-8 space-y-3 border-l border-[#9b7500] pl-4">
          {step.branchTracks.map((branch) => (
            <div key={branch.id} className="rounded border border-[#4d3a00] bg-[#111005] p-3">
              <div className="mb-2 flex items-center justify-between text-xs font-bold text-[#ffb000]">
                <span>Branch: {branch.label}</span>
                {canEdit ? (
                  <button className="text-[#ff8f8f]" onClick={() => onDeleteBranch(branch)}>
                    <Trash2 size={13} />
                  </button>
                ) : null}
              </div>
              <div className="space-y-2">
                {branch.steps.length ? (
                  branch.steps.map((branchStep) => (
                    <div key={branchStep.id} className="rounded border border-[#2d2509] bg-[#090b0f] px-3 py-2 text-xs text-[#d3dce8]">
                      {branchStep.label}
                      <span className="ml-2 text-[#52657f]">{branchStep.duration || "-"}</span>
                    </div>
                  ))
                ) : (
                  <div className="rounded border border-dashed border-[#2d2509] px-3 py-2 text-xs text-[#52657f]">No branch steps yet.</div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function StandardizedWorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowRecord[]>([]);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [labMembers, setLabMembers] = useState<LabMemberRecord[]>([]);
  const [currentUser, setCurrentUser] = useState<UserRecord | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [expandedStepIds, setExpandedStepIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [metadataOpen, setMetadataOpen] = useState(false);
  const [stepFormOpen, setStepFormOpen] = useState(false);
  const [branchOpen, setBranchOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [metadataForm, setMetadataForm] = useState({
    id: "",
    projectId: "",
    title: "",
    description: "",
    tags: "",
    members: [] as WorkflowMemberRecord[],
  });
  const [stepForm, setStepForm] = useState<{
    workflowId: string;
    stepId?: string;
    afterStepId?: string | null;
    step: WorkflowStep;
  } | null>(null);
  const [branchForm, setBranchForm] = useState({ workflowId: "", anchorStepId: "", label: "" });

  async function loadPage() {
    setLoading(true);
    setError(null);
    try {
      const [nextWorkflows, nextProjects, nextLabMembers, nextUser] = await Promise.all([
        fetchWorkflows({ tag: "standardized", libraryState: "published", visibility: "library" }),
        fetchProjects(),
        fetchLabMembers(),
        fetchCurrentUser(),
      ]);
      setWorkflows(nextWorkflows);
      setProjects(nextProjects);
      setLabMembers(nextLabMembers);
      setCurrentUser(nextUser);
      setSelectedWorkflowId((current) => current ?? nextWorkflows[0]?.id ?? null);
      setSelectedProjectId((current) => current || nextWorkflows[0]?.projectId || nextProjects[0]?.id || "");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load standardized workflows");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPage();
  }, []);

  const selectedWorkflow = useMemo(() => workflows.find((workflow) => workflow.id === selectedWorkflowId && workflow.projectId === selectedProjectId) ?? workflows.find((workflow) => workflow.projectId === selectedProjectId) ?? null, [selectedProjectId, selectedWorkflowId, workflows]);
  const currentWorkflowRole = selectedWorkflow?.members.find((member) => member.userId === currentUser?.id)?.workflowRole;
  const canEdit = currentWorkflowRole === "owner" || currentWorkflowRole === "editor";
  const availableMembers = labMembers.filter((member) => !metadataForm.members.some((workflowMember) => workflowMember.userId === member.id));

  function replaceWorkflow(updated: WorkflowRecord) {
    setWorkflows((current) => current.map((workflow) => (workflow.id === updated.id ? updated : workflow)));
    setSelectedWorkflowId(updated.id);
  }

  function replaceWorkflowSteps(workflowId: string, steps: WorkflowStep[]) {
    setWorkflows((current) =>
      current.map((workflow) => (workflow.id === workflowId ? { ...workflow, steps } : workflow)),
    );
    setSelectedWorkflowId(workflowId);
  }

  function openCreateDialog() {
    setMetadataForm({ id: "", projectId: selectedProjectId, title: "", description: "", tags: "standardized", members: [] });
    setCreateOpen(true);
  }

  function openMetadataDialog(workflow: WorkflowRecord) {
    setMetadataForm({
      id: workflow.id,
      projectId: workflow.projectId ?? "",
      title: workflow.title,
      description: workflow.description,
      tags: workflow.tags.join(", "),
      members: workflow.members,
    });
    setMetadataOpen(true);
  }

  function openStepDialog(workflowId: string, step?: WorkflowStep, afterStepId?: string | null) {
    setStepForm({ workflowId, stepId: step?.id, afterStepId, step: step ? { ...step } : blankStep() });
    setStepFormOpen(true);
  }

  async function handleCreateWorkflow() {
    try {
      setSaving(true);
      setError(null);
      const tags = csv(metadataForm.tags);
      const created = await createWorkflow({
        title: metadataForm.title || "Untitled standardized workflow",
        description: metadataForm.description,
        projectId: metadataForm.projectId,
        tags: tags.includes("standardized") ? tags : ["standardized", ...tags],
        visibility: "library",
        libraryState: "published",
        members: metadataForm.members.map((member) => ({ userId: member.userId, workflowRole: member.workflowRole })),
      });
      setWorkflows((current) => [created, ...current]);
      setSelectedWorkflowId(created.id);
      setCreateOpen(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create standardized workflow");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveMetadata() {
    try {
      setSaving(true);
      setError(null);
      const tags = csv(metadataForm.tags);
      const updated = await updateWorkflow(metadataForm.id, {
        title: metadataForm.title,
        description: metadataForm.description,
        projectId: metadataForm.projectId,
        tags: tags.includes("standardized") ? tags : ["standardized", ...tags],
        members: metadataForm.members.map((member) => ({ userId: member.userId, workflowRole: member.workflowRole })),
      });
      replaceWorkflow(updated);
      setMetadataOpen(false);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update standardized workflow");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveStep() {
    if (!stepForm) return;
    try {
      setSaving(true);
      setError(null);
      const payload = {
        label: stepForm.step.label || "Untitled step",
        sublabel: stepForm.step.sublabel,
        status: stepForm.step.status,
        duration: stepForm.step.duration,
        procedureMarkdown: stepForm.step.procedureMarkdown,
        inputs: stepForm.step.inputs,
        parameters: stepForm.step.parameters,
        outputs: stepForm.step.outputs,
        notes: stepForm.step.notes,
      };
      const updated = stepForm.stepId
        ? await updateWorkflowStep(stepForm.workflowId, { ...stepForm.step, ...payload })
        : await createMainWorkflowStep(stepForm.workflowId, stepForm.afterStepId ?? null, { ...stepForm.step, ...payload });
      replaceWorkflowSteps(stepForm.workflowId, updated);
      setStepFormOpen(false);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save workflow step");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateBranch() {
    try {
      setSaving(true);
      setError(null);
      const updated = await createWorkflowBranch(branchForm.workflowId, branchForm.anchorStepId, branchForm.label || "Troubleshooting branch");
      replaceWorkflowSteps(branchForm.workflowId, updated);
      setBranchOpen(false);
    } catch (branchError) {
      setError(branchError instanceof Error ? branchError.message : "Failed to create branch");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      setSaving(true);
      setError(null);
      if (deleteTarget.kind === "workflow") {
        await deleteWorkflow(deleteTarget.workflowId);
        const nextWorkflows = workflows.filter((workflow) => workflow.id !== deleteTarget.workflowId);
        setWorkflows(nextWorkflows);
        setSelectedWorkflowId(nextWorkflows[0]?.id ?? null);
      } else if (deleteTarget.kind === "step") {
        replaceWorkflowSteps(deleteTarget.workflowId, await deleteWorkflowStep(deleteTarget.workflowId, deleteTarget.stepId));
      } else {
        replaceWorkflowSteps(deleteTarget.workflowId, await deleteWorkflowBranch(deleteTarget.workflowId, deleteTarget.branchId));
      }
      setDeleteTarget(null);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete item");
    } finally {
      setSaving(false);
    }
  }

  async function handleRepublishWorkflow(workflowId: string) {
    try {
      setSaving(true);
      setError(null);
      replaceWorkflow(await publishWorkflow(workflowId));
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : "Failed to publish standardized workflow");
    } finally {
      setSaving(false);
    }
  }

  function updateStepFormStep(updates: Partial<WorkflowStep>) {
    if (!stepForm) return;
    setStepForm({ ...stepForm, step: { ...stepForm.step, ...updates } });
  }

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">WORKFLOW LIBRARY</div>
          <h1 className="text-xl font-mono font-semibold text-foreground">Standardized Workflows</h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1">
            Published, reusable workflows. Owners and editors can update them; viewers and commenters can inspect and reuse them.
          </p>
        </div>
        <button
          type="button"
          data-testid="new-standardized-workflow"
          onClick={openCreateDialog}
          className="rounded-sm bg-[#00c9a7] px-3 py-2 text-[10px] font-mono font-semibold uppercase text-[#080c12] hover:bg-[#00b899]"
        >
          + New Standardized Workflow
        </button>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Standardized workflow API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <WorkflowTypeNavigator
        projects={projects}
        workflows={workflows}
        selectedProjectId={selectedProjectId}
        selectedWorkflowId={selectedWorkflow?.id ?? null}
        onSelectProject={(projectId) => { setSelectedProjectId(projectId); setSelectedWorkflowId(workflows.find((workflow) => workflow.projectId === projectId)?.id ?? null); }}
        onSelectWorkflow={setSelectedWorkflowId}
        onCreateType={() => { window.location.href = "/workflow"; }}
        onCreateBatch={openCreateDialog}
        typeLabel="WORKFLOW TYPES"
        batchLabel="STANDARDIZED WORKFLOWS"
      />

      <div className="mt-5 grid grid-cols-1 gap-5">
        <aside className="hidden border border-border bg-card rounded-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border text-[9px] font-mono tracking-widest text-muted-foreground">
            LIBRARY ENTRIES
          </div>
          {loading ? (
            <div className="px-4 py-5 text-[10px] font-mono text-muted-foreground">Loading standardized workflows...</div>
          ) : workflows.length === 0 ? (
            <div className="px-4 py-5 text-[10px] font-mono text-muted-foreground">No standardized workflows found.</div>
          ) : (
            <div className="p-2 space-y-2">
              {workflows.map((workflow) => {
                const workflowRole = workflow.members.find((member) => member.userId === currentUser?.id)?.workflowRole ?? "viewer";
                return (
                  <button
                    key={workflow.id}
                    type="button"
                    onClick={() => setSelectedWorkflowId(workflow.id)}
                    className={`w-full text-left px-3 py-3 rounded-sm border transition-colors ${
                      selectedWorkflowId === workflow.id
                        ? "bg-[#00c9a7]/10 border-[#00c9a7]/25"
                        : "bg-card border-border hover:bg-secondary/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[11px] font-mono text-foreground">{workflow.title}</div>
                        <div className="mt-1 text-[9px] font-mono text-muted-foreground">
                          v{workflow.version} · {workflow.steps.length} steps
                        </div>
                      </div>
                      <div className="text-[8px] font-mono px-1.5 py-0.5 rounded-sm border border-[#00c9a7]/25 bg-[#00c9a7]/10 text-[#00c9a7]">
                        {workflowRole.toUpperCase()}
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {workflow.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="text-[8px] font-mono px-1.5 py-0.5 rounded-sm border border-border text-muted-foreground">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </aside>

        <section className="border border-border bg-card rounded-sm overflow-hidden">
          {selectedWorkflow ? (
            <>
              <div className="px-5 py-4 border-b border-border flex items-start justify-between gap-4">
                <div>
                  <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">STANDARDIZED WORKFLOW</div>
                  <h2 className="text-lg font-mono font-semibold text-foreground">{selectedWorkflow.title}</h2>
                  <div className="mt-2 text-[10px] font-mono text-muted-foreground">{selectedWorkflow.description}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedWorkflow.tags.map((tag) => (
                      <span key={tag} className="text-[8px] font-mono px-1.5 py-0.5 rounded-sm border border-border text-muted-foreground">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {canEdit ? (
                    <>
                      <button
                        type="button"
                        data-testid="standardized-add-step"
                        onClick={() => openStepDialog(selectedWorkflow.id, undefined, null)}
                        className="rounded-sm border border-[#00c9a7]/25 px-2.5 py-1.5 text-[9px] font-mono text-[#00c9a7]"
                      >
                        + ADD STEP
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleRepublishWorkflow(selectedWorkflow.id)}
                        disabled={saving}
                        className="rounded-sm border border-[#00c9a7]/25 px-2.5 py-1.5 text-[9px] font-mono text-[#00c9a7] disabled:opacity-40"
                      >
                        PUBLISH
                      </button>
                      <button
                        type="button"
                        onClick={() => openMetadataDialog(selectedWorkflow)}
                        className="rounded-sm border border-border px-2.5 py-1.5 text-[9px] font-mono text-muted-foreground hover:text-foreground"
                      >
                        <span className="inline-flex items-center gap-1"><Pencil className="w-3 h-3" />EDIT DETAILS</span>
                      </button>
                      <button
                        type="button"
                        data-testid="standardized-delete-workflow"
                        onClick={() => setDeleteTarget({ kind: "workflow", workflowId: selectedWorkflow.id, label: selectedWorkflow.title })}
                        className="rounded-sm border border-red-400/25 px-2.5 py-1.5 text-[9px] font-mono text-red-300"
                      >
                        <span className="inline-flex items-center gap-1"><Trash2 className="w-3 h-3" />DELETE</span>
                      </button>
                    </>
                  ) : null}
                </div>
              </div>

              <div className="grid grid-cols-1 2xl:grid-cols-[1fr_280px] gap-5 px-5 py-5">
                <div className="space-y-3">
                  {selectedWorkflow.steps.length === 0 ? (
                    <div className="rounded border border-dashed border-[#1b2633] p-8 text-center text-xs text-[#52657f]">
                      No steps yet. {canEdit ? "Add a step to start building this standardized workflow." : ""}
                    </div>
                  ) : null}
                  {selectedWorkflow.steps.map((step) => (
                    <StepCard
                      key={step.id}
                      step={step}
                      expanded={expandedStepIds.has(step.id)}
                      canEdit={canEdit}
                      onToggle={() =>
                        setExpandedStepIds((current) => {
                          const next = new Set(current);
                          if (next.has(step.id)) next.delete(step.id);
                          else next.add(step.id);
                          return next;
                        })
                      }
                      onAdd={() => openStepDialog(selectedWorkflow.id, undefined, step.id)}
                      onBranch={() => {
                        setBranchForm({ workflowId: selectedWorkflow.id, anchorStepId: step.id, label: "" });
                        setBranchOpen(true);
                      }}
                      onEdit={() => openStepDialog(selectedWorkflow.id, step)}
                      onDelete={() => setDeleteTarget({ kind: "step", workflowId: selectedWorkflow.id, stepId: step.id, label: step.label })}
                      onDeleteBranch={(branch) =>
                        setDeleteTarget({ kind: "branch", workflowId: selectedWorkflow.id, branchId: branch.id, label: branch.label })
                      }
                    />
                  ))}
                </div>

                <div className="space-y-4">
                  <div className="border border-border rounded-sm bg-background/60 px-4 py-4">
                    <div className="flex items-center gap-2 text-[9px] font-mono tracking-widest text-muted-foreground mb-3">
                      <Shield className="w-3.5 h-3.5 text-[#00c9a7]" />
                      ACCESS
                    </div>
                    <div className="text-[10px] font-mono text-foreground">
                      Your role: <span className="text-[#00c9a7]">{(currentWorkflowRole ?? "viewer").toUpperCase()}</span>
                    </div>
                    <div className="mt-2 text-[9px] font-mono text-muted-foreground">
                      Owners and editors can modify standardized workflow steps. Viewers and commenters can inspect and reuse.
                    </div>
                  </div>

                  <div className="border border-border rounded-sm bg-background/60 px-4 py-4">
                    <div className="flex items-center gap-2 text-[9px] font-mono tracking-widest text-muted-foreground mb-3">
                      <Users className="w-3.5 h-3.5 text-[#00c9a7]" />
                      MEMBERS
                    </div>
                    <div className="space-y-2">
                      {selectedWorkflow.members.map((member) => (
                        <div key={member.userId} className="rounded-sm border border-border px-3 py-2">
                          <div className="text-[10px] font-mono text-foreground">{member.displayName}</div>
                          <div className="mt-1 text-[8px] font-mono text-muted-foreground">
                            {member.workflowRole.toUpperCase()} · {member.labRole}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="px-5 py-10 text-[10px] font-mono text-muted-foreground">Create or select a standardized workflow.</div>
          )}
        </section>
      </div>

      <WorkflowMetadataDialog
        open={createOpen || metadataOpen}
        onOpenChange={(open) => {
          setCreateOpen(false);
          setMetadataOpen(open && metadataOpen);
        }}
        title={createOpen ? "Create standardized workflow" : "Edit library entry"}
        form={metadataForm}
        setForm={setMetadataForm}
        projects={projects}
        labMembers={labMembers}
        availableMembers={availableMembers}
        saving={saving}
        actionLabel={createOpen ? "CREATE WORKFLOW" : "SAVE WORKFLOW"}
        onSubmit={() => void (createOpen ? handleCreateWorkflow() : handleSaveMetadata())}
      />

      <Dialog.Root open={stepFormOpen} onOpenChange={setStepFormOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/70" />
          <Dialog.Content className="fixed left-1/2 top-1/2 max-h-[88vh] w-[min(820px,92vw)] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-sm border border-border bg-card p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground">STANDARDIZED STEP</div>
                <Dialog.Title className="text-sm font-mono text-foreground mt-1">{stepForm?.stepId ? "Edit step" : "Add step"}</Dialog.Title>
              </div>
              <Dialog.Close className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </Dialog.Close>
            </div>

            {stepForm ? (
              <div className="mt-5 grid grid-cols-1 gap-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">LABEL</label>
                    <input className={inputCls} value={stepForm.step.label} onChange={(event) => updateStepFormStep({ label: event.target.value })} />
                  </div>
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">SUBLABEL</label>
                    <input className={inputCls} value={stepForm.step.sublabel ?? ""} onChange={(event) => updateStepFormStep({ sublabel: event.target.value })} />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">STATUS</label>
                    <select className={inputCls} value={stepForm.step.status} onChange={(event) => updateStepFormStep({ status: event.target.value as StepStatus })}>
                      <option value="pending">pending</option>
                      <option value="running">running</option>
                      <option value="complete">complete</option>
                      <option value="error">error</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">DURATION</label>
                    <input className={inputCls} value={stepForm.step.duration ?? ""} onChange={(event) => updateStepFormStep({ duration: event.target.value })} />
                  </div>
                </div>
                <div>
                  <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">PROCEDURE</label>
                  <textarea className={`${inputCls} min-h-24 resize-none`} value={stepForm.step.procedureMarkdown} onChange={(event) => updateStepFormStep({ procedureMarkdown: event.target.value })} />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">INPUTS</label>
                    <textarea className={`${inputCls} min-h-28 resize-none`} value={itemsToText(stepForm.step.inputs)} onChange={(event) => updateStepFormStep({ inputs: parseItems(event.target.value) })} />
                  </div>
                  <div>
                    <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">OUTPUTS</label>
                    <textarea className={`${inputCls} min-h-28 resize-none`} value={itemsToText(stepForm.step.outputs)} onChange={(event) => updateStepFormStep({ outputs: parseItems(event.target.value) })} />
                  </div>
                </div>
                <div>
                  <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">PARAMETERS</label>
                  <textarea className={`${inputCls} min-h-20 resize-none`} value={paramsToText(stepForm.step.parameters)} onChange={(event) => updateStepFormStep({ parameters: parseParams(event.target.value) })} />
                </div>
                <div>
                  <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">NOTES</label>
                  <textarea className={`${inputCls} min-h-20 resize-none`} value={stepForm.step.notes} onChange={(event) => updateStepFormStep({ notes: event.target.value })} />
                </div>
              </div>
            ) : null}

            <div className="mt-5 flex justify-end gap-2">
              <Dialog.Close className="rounded-sm border border-border px-3 py-2 text-[10px] font-mono text-muted-foreground hover:text-foreground">
                CANCEL
              </Dialog.Close>
              <button
                type="button"
                onClick={() => void handleSaveStep()}
                disabled={saving}
                className="rounded-sm bg-[#00c9a7] px-3 py-2 text-[10px] font-mono font-semibold text-[#080c12] hover:bg-[#00b899] disabled:opacity-60"
              >
                {saving ? "SAVING..." : "SAVE STEP"}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <Dialog.Root open={branchOpen} onOpenChange={setBranchOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/70" />
          <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(420px,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-sm border border-border bg-card p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[9px] font-mono tracking-[0.25em] text-[#ffb000]">DIVERGE BRANCH</div>
                <Dialog.Title className="text-sm font-mono text-foreground mt-1">Add side track</Dialog.Title>
              </div>
              <Dialog.Close className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </Dialog.Close>
            </div>
            <div className="mt-5">
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">BRANCH LABEL</label>
              <input className={inputCls} value={branchForm.label} onChange={(event) => setBranchForm({ ...branchForm, label: event.target.value })} placeholder="e.g. Troubleshooting run" />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Dialog.Close className="rounded-sm border border-border px-3 py-2 text-[10px] font-mono text-muted-foreground hover:text-foreground">
                CANCEL
              </Dialog.Close>
              <button type="button" onClick={() => void handleCreateBranch()} disabled={saving} className="rounded-sm bg-[#9b7500] px-3 py-2 text-[10px] font-mono font-semibold text-[#080c12] disabled:opacity-60">
                CREATE BRANCH
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title={`Delete ${deleteTarget?.kind ?? "item"}?`}
        description={`This will permanently delete "${deleteTarget?.label ?? "this item"}". This cannot be undone.`}
        confirmLabel="Delete"
        busy={saving}
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}

function WorkflowMetadataDialog({
  open,
  onOpenChange,
  title,
  form,
  setForm,
  projects,
  labMembers,
  availableMembers,
  saving,
  actionLabel,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  form: {
    id: string;
    projectId: string;
    title: string;
    description: string;
    tags: string;
    members: WorkflowMemberRecord[];
  };
  setForm: (form: {
    id: string;
    projectId: string;
    title: string;
    description: string;
    tags: string;
    members: WorkflowMemberRecord[];
  }) => void;
  projects: ProjectRecord[];
  labMembers: LabMemberRecord[];
  availableMembers: LabMemberRecord[];
  saving: boolean;
  actionLabel: string;
  onSubmit: () => void;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70" />
        <Dialog.Content data-testid="standardized-metadata-dialog" className="fixed left-1/2 top-1/2 w-[min(720px,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-sm border border-border bg-card p-5 shadow-2xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground">STANDARDIZED WORKFLOW</div>
              <Dialog.Title className="text-sm font-mono text-foreground mt-1">{title}</Dialog.Title>
            </div>
            <Dialog.Close className="text-muted-foreground hover:text-foreground">
              <X className="w-4 h-4" />
            </Dialog.Close>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-4">
            <div>
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">WORKFLOW TYPE</label>
              <select data-testid="standardized-project-select" required className={inputCls} value={form.projectId} onChange={(event) => setForm({ ...form, projectId: event.target.value })}>
                <option value="">Select a type...</option>
                {projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">TITLE</label>
              <input data-testid="standardized-title-input" className={inputCls} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            </div>
            <div>
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">DESCRIPTION</label>
              <textarea data-testid="standardized-description-input" className={`${inputCls} min-h-24 resize-none`} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
            </div>
            <div>
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-1">TAGS</label>
              <input data-testid="standardized-tags-input" className={inputCls} value={form.tags} onChange={(event) => setForm({ ...form, tags: event.target.value })} />
            </div>
            <div>
              <label className="block text-[9px] font-mono tracking-widest text-muted-foreground mb-2">MEMBERS / ACCESS</label>
              <div className="space-y-2">
                {form.members.map((member, index) => (
                  <div key={member.userId} className="grid grid-cols-[1fr_140px_40px] gap-2">
                    <input className={inputCls} value={member.displayName} readOnly />
                    <select
                      className={inputCls}
                      value={member.workflowRole}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          members: form.members.map((currentMember, currentIndex) =>
                            currentIndex === index ? { ...currentMember, workflowRole: event.target.value } : currentMember,
                          ),
                        })
                      }
                    >
                      <option value="owner">owner</option>
                      <option value="editor">editor</option>
                      <option value="commenter">commenter</option>
                      <option value="viewer">viewer</option>
                    </select>
                    <button
                      type="button"
                      className="rounded-sm border border-border text-muted-foreground hover:text-foreground"
                      onClick={() => setForm({ ...form, members: form.members.filter((_, currentIndex) => currentIndex !== index) })}
                    >
                      <X className="w-4 h-4 mx-auto" />
                    </button>
                  </div>
                ))}
                {availableMembers.length > 0 && (
                  <select
                    className={inputCls}
                    defaultValue=""
                    onChange={(event) => {
                      const userId = event.target.value;
                      if (!userId) return;
                      const member = labMembers.find((item) => item.id === userId);
                      if (!member) return;
                      setForm({
                        ...form,
                        members: [
                          ...form.members,
                          {
                            userId: member.id,
                            displayName: member.displayName,
                            email: member.email,
                            labRole: member.role,
                            workflowRole: "viewer",
                          },
                        ],
                      });
                      event.target.value = "";
                    }}
                  >
                    <option value="">Add lab member...</option>
                    {availableMembers.map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.displayName} ({member.role})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          </div>

          <div className="mt-5 flex justify-end gap-2">
            <Dialog.Close className="rounded-sm border border-border px-3 py-2 text-[10px] font-mono text-muted-foreground hover:text-foreground">
              CANCEL
            </Dialog.Close>
              <button
                type="button"
                data-testid="standardized-save-metadata"
                onClick={onSubmit}
                disabled={saving || !form.projectId}
              className="rounded-sm bg-[#00c9a7] px-3 py-2 text-[10px] font-mono font-semibold text-[#080c12] hover:bg-[#00b899] disabled:opacity-60"
            >
              {saving ? "SAVING..." : actionLabel}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
