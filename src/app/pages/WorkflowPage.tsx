import { useEffect, useMemo, useState } from "react";
import { CornerDownRight, Pencil, Plus, Trash2, X } from "lucide-react";
import ConfirmDialog from "../components/ConfirmDialog";
import {
  createMainWorkflowStep,
  createWorkflowBranchStep,
  createWorkflow,
  createWorkflowBranch,
  deleteWorkflow,
  deleteWorkflowBranch,
  deleteWorkflowStep,
  fetchProjects,
  fetchWorkflows,
  insertStandardizedWorkflow,
  standardizeWorkflow,
  updateWorkflowStep,
  type ProjectRecord,
  type WorkflowRecord,
} from "../api";
import type { BranchTrack, IOItem, Param, StepStatus, WorkflowStep } from "../types";

type AddTarget = { workflowId: string; afterStepId: string | null };
type BranchTarget = { workflowId: string; anchorStepId: string };
type BranchStepTarget = { workflowId: string; branchId: string; branchLabel: string };
type DeleteTarget =
  | { kind: "workflow"; workflowId: string; label: string }
  | { kind: "step"; workflowId: string; stepId: string; label: string }
  | { kind: "branch"; workflowId: string; branchId: string; label: string };

const statusClass: Record<StepStatus, string> = {
  complete: "text-[#00f0b5]",
  running: "text-[#00d7ff]",
  pending: "text-[#60708a]",
  error: "text-[#ff6b6b]",
};

function csv(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function blankStep(label: string, sublabel = ""): WorkflowStep {
  return {
    id: `draft-${Date.now()}`,
    index: 0,
    label,
    sublabel: sublabel || undefined,
    status: "pending",
    duration: "-",
    procedureMarkdown: "",
    inputs: [],
    parameters: [],
    outputs: [],
    notes: "",
  };
}

function emptyDraftStep(): WorkflowStep {
  return blankStep("", "");
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

function StepDraftFields({
  step,
  inputs,
  outputs,
  params,
  onStepChange,
  onInputsChange,
  onOutputsChange,
  onParamsChange,
}: {
  step: WorkflowStep;
  inputs: string;
  outputs: string;
  params: string;
  onStepChange: (step: WorkflowStep) => void;
  onInputsChange: (value: string) => void;
  onOutputsChange: (value: string) => void;
  onParamsChange: (value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Step name
        <input
          data-testid="step-label-input"
          className="mt-2 w-full rounded border border-[#007a6c] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
          value={step.label}
          onChange={(event) => onStepChange({ ...step, label: event.target.value })}
        />
      </label>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Sublabel
        <input
          data-testid="step-sublabel-input"
          className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
          value={step.sublabel ?? ""}
          onChange={(event) => onStepChange({ ...step, sublabel: event.target.value })}
          placeholder="Technique, condition, or short context"
        />
      </label>
      <div className="grid grid-cols-2 gap-2">
        <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
          Status
          <select
            data-testid="step-status-input"
            className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
            value={step.status}
            onChange={(event) => onStepChange({ ...step, status: event.target.value as StepStatus })}
          >
            <option value="pending">pending</option>
            <option value="running">running</option>
            <option value="complete">complete</option>
            <option value="error">error</option>
          </select>
        </label>
        <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
          Duration
          <input
            data-testid="step-duration-input"
            className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
            value={step.duration ?? ""}
            onChange={(event) => onStepChange({ ...step, duration: event.target.value })}
            placeholder="45 min, overnight, 2 hr"
          />
        </label>
      </div>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Procedure
        <textarea
          data-testid="step-procedure-input"
          className="mt-2 min-h-[90px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
          value={step.procedureMarkdown ?? ""}
          onChange={(event) => onStepChange({ ...step, procedureMarkdown: event.target.value })}
          placeholder="Write the exact procedure for this step."
        />
      </label>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Inputs
        <textarea
          data-testid="step-inputs-input"
          className="mt-2 min-h-[80px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]"
          value={inputs}
          onChange={(event) => onInputsChange(event.target.value)}
          placeholder="type | name | value | note"
        />
      </label>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Parameters
        <textarea
          data-testid="step-parameters-input"
          className="mt-2 min-h-[70px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]"
          value={params}
          onChange={(event) => onParamsChange(event.target.value)}
          placeholder="label | value"
        />
      </label>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Outputs
        <textarea
          data-testid="step-outputs-input"
          className="mt-2 min-h-[80px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]"
          value={outputs}
          onChange={(event) => onOutputsChange(event.target.value)}
          placeholder="type | name | value | note"
        />
      </label>
      <label className="block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
        Notes
        <textarea
          data-testid="step-notes-input"
          className="mt-2 min-h-[70px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]"
          value={step.notes ?? ""}
          onChange={(event) => onStepChange({ ...step, notes: event.target.value })}
          placeholder="Expected vs actual outcome, observations, decisions."
        />
      </label>
    </div>
  );
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
    <div className="mx-8 mb-4 rounded border border-[#1b2633] bg-[#080c12] p-5">
      <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.28em] text-[#5c718d]">
        Inner schematic - Step {String(step.index).padStart(2, "0")} / {step.label}
      </div>
      {step.procedureMarkdown ? (
        <div className="mb-5 rounded border border-[#1b2633] bg-[#0d151e] p-3 text-xs leading-relaxed text-[#7d90aa]">
          <div className="mb-1 text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Procedure</div>
          {step.procedureMarkdown}
        </div>
      ) : null}
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
  onToggle,
  onAdd,
  onBranch,
  onEdit,
  onDelete,
  onAddBranchStep,
  onEditBranchStep,
  onDeleteBranchStep,
  onDeleteBranch,
}: {
  step: WorkflowStep;
  expanded: boolean;
  onToggle: () => void;
  onAdd: () => void;
  onBranch: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onAddBranchStep: (branch: BranchTrack) => void;
  onEditBranchStep: (branchStep: WorkflowStep) => void;
  onDeleteBranchStep: (branchStep: WorkflowStep) => void;
  onDeleteBranch: (branch: BranchTrack) => void;
}) {
  return (
    <div className="group relative">
      <div className="absolute -left-3 top-1/2 hidden -translate-y-1/2 flex-col gap-1 group-hover:flex">
        <button className="rounded border border-[#00c9a7]/50 bg-[#0b1a1d] p-1 text-[#00c9a7]" title="Add step" onClick={onAdd}>
          <Plus size={13} />
        </button>
        <button className="rounded border border-[#b88700]/50 bg-[#1b1505] p-1 text-[#ffb000]" title="Diverge branch" onClick={onBranch}>
          <CornerDownRight size={13} />
        </button>
      </div>
      <div
        data-testid={`workflow-step-${step.id}`}
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
        <div className="hidden gap-2 group-hover:flex" onClick={(event) => event.stopPropagation()}>
          <button className="text-[#7d90aa] hover:text-[#00c9a7]" title="Edit step" onClick={onEdit}>
            <Pencil size={14} />
          </button>
          <button className="text-[#7d90aa] hover:text-[#ff6b6b]" title="Delete step" onClick={onDelete}>
            <Trash2 size={14} />
          </button>
        </div>
        <span className="text-[#52657f]">{expanded ? "v" : ">"}</span>
      </div>
      {expanded ? <StepDetail step={step} /> : null}
      {expanded && step.branchTracks?.length ? (
        <div className="ml-8 space-y-3 border-l border-[#9b7500] pl-4">
          {step.branchTracks.map((branch) => (
            <div key={branch.id} className="rounded border border-[#4d3a00] bg-[#111005] p-3">
              <div className="mb-2 flex items-center justify-between text-xs font-bold text-[#ffb000]">
                <span>Branch: {branch.label}</span>
                <div className="flex items-center gap-3">
                  <button className="text-[#00c9a7]" onClick={() => onAddBranchStep(branch)}>
                    + Add branch step
                  </button>
                  <button className="text-[#ff8f8f]" onClick={() => onDeleteBranch(branch)}>
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              {branch.steps.length ? (
                <div className="space-y-2">
                  {branch.steps.map((branchStep) => (
                    <div key={branchStep.id} data-testid={`workflow-branch-step-${branchStep.id}`} className="group/branch flex items-center gap-3 rounded border border-[#1b2633] bg-[#080c12] px-3 py-2 text-xs text-[#d3dce8]">
                      <button className="min-w-0 flex-1 text-left" onClick={() => onEditBranchStep(branchStep)}>
                        {branchStep.label}
                        {branchStep.duration ? <span className="ml-2 text-[#52657f]">{branchStep.duration}</span> : null}
                      </button>
                      <button className="hidden text-[#ff8f8f] group-hover/branch:block" onClick={() => onDeleteBranchStep(branchStep)}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded border border-dashed border-[#3a2d07] p-3 text-center text-xs text-[#52657f]">No steps yet.</div>
              )}
              <div className="mt-2 text-center text-[10px] text-[#52657f]">returns to main flow</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function WorkflowColumn({
  workflow,
  expanded,
  onToggle,
  onAdd,
  onBranch,
  onEdit,
  onAddBranchStep,
  onDeleteStep,
  onDeleteBranchStep,
  onDeleteBranch,
  onDeleteWorkflow,
  onStandardize,
}: {
  workflow: WorkflowRecord;
  expanded: Set<string>;
  onToggle: (stepId: string) => void;
  onAdd: (target: AddTarget) => void;
  onBranch: (target: BranchTarget) => void;
  onEdit: (workflow: WorkflowRecord, step: WorkflowStep) => void;
  onAddBranchStep: (target: BranchStepTarget) => void;
  onDeleteStep: (target: DeleteTarget) => void;
  onDeleteBranchStep: (target: DeleteTarget) => void;
  onDeleteBranch: (target: DeleteTarget) => void;
  onDeleteWorkflow: (target: DeleteTarget) => void;
  onStandardize: (workflow: WorkflowRecord) => void;
}) {
  const done = workflow.steps.filter((step) => step.status === "complete").length;
  const percent = workflow.steps.length ? Math.round((done / workflow.steps.length) * 100) : 0;
  return (
    <section className="space-y-3">
      <div className="rounded border border-[#1b2633] bg-[#0b1118] p-4">
        <div className="text-[10px] uppercase tracking-[0.3em] text-[#52657f]">Experimental workflow</div>
        <div className="mt-2 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#d3dce8]">{workflow.title}</h2>
            <p className="mt-1 text-xs text-[#52657f]">{workflow.description}</p>
          </div>
          <div className="text-right text-xs text-[#52657f]">
            {done}/{workflow.steps.length} done
            <div className="mt-1 text-[#00c9a7]">{percent}%</div>
          </div>
        </div>
        <div className="mt-4 h-1 rounded bg-[#1b2633]">
          <div className="h-1 rounded bg-[#00c9a7]" style={{ width: `${percent}%` }} />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button data-testid={`workflow-add-step-${workflow.id}`} className="rounded border border-[#00c9a7]/50 px-3 py-2 text-[10px] font-bold uppercase text-[#00c9a7]" onClick={() => onAdd({ workflowId: workflow.id, afterStepId: null })}>
            + Add step
          </button>
          <button data-testid={`workflow-standardize-${workflow.id}`} className="rounded border border-[#00c9a7]/50 px-3 py-2 text-[10px] font-bold uppercase text-[#00c9a7]" onClick={() => onStandardize(workflow)}>
            Standardize
          </button>
          <button className="rounded border border-[#ff6b6b]/40 px-3 py-2 text-[10px] font-bold uppercase text-[#ff8f8f]" onClick={() => onDeleteWorkflow({ kind: "workflow", workflowId: workflow.id, label: workflow.title })}>
            Delete workflow
          </button>
        </div>
      </div>
      {workflow.steps.map((step) => (
        <StepCard
          key={step.id}
          step={step}
          expanded={expanded.has(step.id)}
          onToggle={() => onToggle(step.id)}
          onAdd={() => onAdd({ workflowId: workflow.id, afterStepId: step.id })}
          onBranch={() => onBranch({ workflowId: workflow.id, anchorStepId: step.id })}
          onEdit={() => onEdit(workflow, step)}
          onDelete={() => onDeleteStep({ kind: "step", workflowId: workflow.id, stepId: step.id, label: step.label })}
          onAddBranchStep={(branch) => onAddBranchStep({ workflowId: workflow.id, branchId: branch.id, branchLabel: branch.label })}
          onEditBranchStep={(branchStep) => onEdit(workflow, branchStep)}
          onDeleteBranchStep={(branchStep) => onDeleteBranchStep({ kind: "step", workflowId: workflow.id, stepId: branchStep.id, label: branchStep.label })}
          onDeleteBranch={(branch) => onDeleteBranch({ kind: "branch", workflowId: workflow.id, branchId: branch.id, label: branch.label })}
        />
      ))}
      {workflow.steps.length === 0 ? (
        <button className="w-full rounded border border-dashed border-[#1b2633] bg-[#080c12] p-8 text-sm text-[#52657f]" onClick={() => onAdd({ workflowId: workflow.id, afterStepId: null })}>
          Blank workflow - add the first step.
        </button>
      ) : null}
    </section>
  );
}

function AddStepModal({
  target,
  standardized,
  onClose,
  onSubmit,
}: {
  target: AddTarget | null;
  standardized: WorkflowRecord[];
  onClose: () => void;
  onSubmit: (target: AddTarget, payload: { source: "manual" | "standardized"; step: WorkflowStep; standardizedWorkflowId: string }) => void;
}) {
  const [source, setSource] = useState<"manual" | "standardized">("manual");
  const [step, setStep] = useState<WorkflowStep>(() => emptyDraftStep());
  const [inputs, setInputs] = useState("");
  const [outputs, setOutputs] = useState("");
  const [params, setParams] = useState("");
  const [standardizedWorkflowId, setStandardizedWorkflowId] = useState("");

  useEffect(() => {
    if (target) {
      setSource("manual");
      setStep(emptyDraftStep());
      setInputs("");
      setOutputs("");
      setParams("");
      setStandardizedWorkflowId(standardized[0]?.id ?? "");
    }
  }, [target, standardized]);

  if (!target) return null;
  return (
    <div data-testid="add-step-modal" className="fixed inset-0 z-50 grid place-items-center bg-black/70">
      <div className="max-h-[86vh] w-[560px] overflow-y-auto rounded border border-[#1b2633] bg-[#080c12] p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-[0.12em] text-[#d3dce8]">Add new step</h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>
        <label className="mb-3 block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
          Source
          <select data-testid="add-step-source" className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={source} onChange={(event) => setSource(event.target.value as "manual" | "standardized")}>
            <option value="manual">Manual step</option>
            <option value="standardized">Standardized workflow</option>
          </select>
        </label>
        {source === "standardized" ? (
          <label className="mb-3 block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">
            Standardized workflow
            <select data-testid="add-step-standardized-workflow" className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={standardizedWorkflowId} onChange={(event) => setStandardizedWorkflowId(event.target.value)}>
              {standardized.map((workflow) => <option key={workflow.id} value={workflow.id}>{workflow.title}</option>)}
            </select>
          </label>
        ) : (
          <StepDraftFields
            step={step}
            inputs={inputs}
            outputs={outputs}
            params={params}
            onStepChange={setStep}
            onInputsChange={setInputs}
            onOutputsChange={setOutputs}
            onParamsChange={setParams}
          />
        )}
        <div className="mt-4 flex gap-2">
          <button className="flex-1 rounded border border-[#1b2633] py-2 text-xs uppercase text-[#7d90aa]" onClick={onClose}>Cancel</button>
          <button className="flex-1 rounded bg-[#00c9a7] py-2 text-xs font-bold uppercase text-[#080c12]" onClick={() => onSubmit(target, {
            source,
            step: {
              ...step,
              label: step.label.trim(),
              sublabel: step.sublabel?.trim() || undefined,
              inputs: parseItems(inputs),
              outputs: parseItems(outputs),
              parameters: parseParams(params),
            },
            standardizedWorkflowId,
          })}>
            Insert step
          </button>
        </div>
      </div>
    </div>
  );
}

function AddBranchStepModal({
  target,
  onClose,
  onSubmit,
}: {
  target: BranchStepTarget | null;
  onClose: () => void;
  onSubmit: (target: BranchStepTarget, step: WorkflowStep) => void;
}) {
  const [step, setStep] = useState<WorkflowStep>(() => emptyDraftStep());
  const [inputs, setInputs] = useState("");
  const [outputs, setOutputs] = useState("");
  const [params, setParams] = useState("");

  useEffect(() => {
    if (target) {
      setStep(emptyDraftStep());
      setInputs("");
      setOutputs("");
      setParams("");
    }
  }, [target]);

  if (!target) return null;
  return (
    <div data-testid="add-branch-step-modal" className="fixed inset-0 z-50 grid place-items-center bg-black/70">
      <div className="max-h-[86vh] w-[560px] overflow-y-auto rounded border border-[#4d3a00] bg-[#080c12] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-[0.12em] text-[#d3dce8]">Add branch step</h3>
            <p className="mt-1 text-xs text-[#7d90aa]">{target.branchLabel}</p>
          </div>
          <button onClick={onClose}><X size={16} /></button>
        </div>
        <StepDraftFields
          step={step}
          inputs={inputs}
          outputs={outputs}
          params={params}
          onStepChange={setStep}
          onInputsChange={setInputs}
          onOutputsChange={setOutputs}
          onParamsChange={setParams}
        />
        <div className="mt-4 flex gap-2">
          <button className="flex-1 rounded border border-[#1b2633] py-2 text-xs uppercase text-[#7d90aa]" onClick={onClose}>Cancel</button>
          <button className="flex-1 rounded bg-[#9b7500] py-2 text-xs font-bold uppercase text-[#080c12]" onClick={() => onSubmit(target, {
            ...step,
            label: step.label.trim(),
            sublabel: step.sublabel?.trim() || undefined,
            inputs: parseItems(inputs),
            outputs: parseItems(outputs),
            parameters: parseParams(params),
          })}>
            Add branch step
          </button>
        </div>
      </div>
    </div>
  );
}

function BranchModal({
  target,
  standardized,
  onClose,
  onSubmit,
}: {
  target: BranchTarget | null;
  standardized: WorkflowRecord[];
  onClose: () => void;
  onSubmit: (target: BranchTarget, payload: { source: "manual" | "standardized"; label: string; standardizedWorkflowId: string }) => void;
}) {
  const [source, setSource] = useState<"manual" | "standardized">("manual");
  const [label, setLabel] = useState("");
  const [standardizedWorkflowId, setStandardizedWorkflowId] = useState("");
  useEffect(() => {
    if (target) {
      setSource("manual");
      setLabel("");
      setStandardizedWorkflowId(standardized[0]?.id ?? "");
    }
  }, [target, standardized]);
  if (!target) return null;
  return (
    <div data-testid="branch-modal" className="fixed inset-0 z-50 grid place-items-center bg-black/70">
      <div className="w-[440px] rounded border border-[#1b2633] bg-[#080c12] p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-[0.12em] text-[#d3dce8]">Diverge branch</h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>
        <label className="mb-3 block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Source
          <select data-testid="branch-source" className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={source} onChange={(event) => setSource(event.target.value as "manual" | "standardized")}>
            <option value="manual">Manual branch</option>
            <option value="standardized">Standardized workflow</option>
          </select>
        </label>
        <label className="mb-3 block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Branch label
          <input className="mt-2 w-full rounded border border-[#b88700] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Troubleshooting branch" />
        </label>
        {source === "standardized" ? (
          <label className="mb-3 block text-[10px] uppercase tracking-[0.2em] text-[#5c718d]">Standardized workflow
            <select data-testid="branch-standardized-workflow" className="mt-2 w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={standardizedWorkflowId} onChange={(event) => setStandardizedWorkflowId(event.target.value)}>
              {standardized.map((workflow) => <option key={workflow.id} value={workflow.id}>{workflow.title}</option>)}
            </select>
          </label>
        ) : null}
        <div className="mt-4 flex gap-2">
          <button className="flex-1 rounded border border-[#1b2633] py-2 text-xs uppercase text-[#7d90aa]" onClick={onClose}>Cancel</button>
          <button className="flex-1 rounded bg-[#9b7500] py-2 text-xs font-bold uppercase text-[#080c12]" onClick={() => onSubmit(target, { source, label, standardizedWorkflowId })}>
            Create branch
          </button>
        </div>
      </div>
    </div>
  );
}

function EditStepModal({
  editing,
  onClose,
  onSave,
}: {
  editing: { workflow: WorkflowRecord; step: WorkflowStep } | null;
  onClose: () => void;
  onSave: (workflowId: string, step: WorkflowStep) => void;
}) {
  const [step, setStep] = useState<WorkflowStep | null>(null);
  const [inputs, setInputs] = useState("");
  const [outputs, setOutputs] = useState("");
  const [params, setParams] = useState("");
  useEffect(() => {
    if (editing) {
      setStep({ ...editing.step });
      setInputs(itemsToText(editing.step.inputs));
      setOutputs(itemsToText(editing.step.outputs));
      setParams(paramsToText(editing.step.parameters));
    }
  }, [editing]);
  if (!editing || !step) return null;
  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[480px] border-l border-[#1b2633] bg-[#080c12] p-5 shadow-2xl">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-[0.12em] text-[#d3dce8]">Edit step</h3>
        <button onClick={onClose}><X size={16} /></button>
      </div>
      <div className="space-y-3 overflow-y-auto pb-20">
        <input className="w-full rounded border border-[#007a6c] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.label} onChange={(event) => setStep({ ...step, label: event.target.value })} />
        <input className="w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.sublabel ?? ""} onChange={(event) => setStep({ ...step, sublabel: event.target.value })} placeholder="Sublabel" />
        <div className="grid grid-cols-2 gap-2">
          <select className="rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.status} onChange={(event) => setStep({ ...step, status: event.target.value as StepStatus })}>
            <option value="pending">pending</option>
            <option value="running">running</option>
            <option value="complete">complete</option>
            <option value="error">error</option>
          </select>
          <input className="rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.duration ?? ""} onChange={(event) => setStep({ ...step, duration: event.target.value })} placeholder="Duration" />
        </div>
        <textarea className="min-h-[90px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.procedureMarkdown ?? ""} onChange={(event) => setStep({ ...step, procedureMarkdown: event.target.value })} placeholder="Procedure" />
        <textarea className="min-h-[100px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]" value={inputs} onChange={(event) => setInputs(event.target.value)} placeholder="Inputs: type | name | value | note" />
        <textarea className="min-h-[80px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]" value={params} onChange={(event) => setParams(event.target.value)} placeholder="Parameters: label | value" />
        <textarea className="min-h-[100px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-xs text-[#d3dce8]" value={outputs} onChange={(event) => setOutputs(event.target.value)} placeholder="Outputs: type | name | value | note" />
        <textarea className="min-h-[80px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={step.notes ?? ""} onChange={(event) => setStep({ ...step, notes: event.target.value })} placeholder="Notes" />
      </div>
      <div className="absolute bottom-0 left-0 right-0 flex gap-2 border-t border-[#1b2633] bg-[#080c12] p-5">
        <button className="flex-1 rounded border border-[#1b2633] py-2 text-xs uppercase text-[#7d90aa]" onClick={onClose}>Cancel</button>
        <button className="flex-1 rounded bg-[#00c9a7] py-2 text-xs font-bold uppercase text-[#080c12]" onClick={() => onSave(editing.workflow.id, { ...step, inputs: parseItems(inputs), outputs: parseItems(outputs), parameters: parseParams(params) })}>
          Save step
        </button>
      </div>
    </div>
  );
}

function StandardizeModal({
  workflow,
  onClose,
  onSubmit,
}: {
  workflow: WorkflowRecord | null;
  onClose: () => void;
  onSubmit: (workflow: WorkflowRecord, title: string, description: string, tags: string[]) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  useEffect(() => {
    if (workflow) {
      setTitle(`${workflow.title} Standard`);
      setDescription(workflow.description);
      setTags("standardized");
    }
  }, [workflow]);
  if (!workflow) return null;
  return (
    <div data-testid="standardize-modal" className="fixed inset-0 z-50 grid place-items-center bg-black/70">
      <div className="w-[480px] rounded border border-[#1b2633] bg-[#080c12] p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-[0.12em] text-[#d3dce8]">Standardize workflow</h3>
        <input className="mb-3 w-full rounded border border-[#007a6c] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={title} onChange={(event) => setTitle(event.target.value)} />
        <textarea className="mb-3 min-h-[90px] w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={description} onChange={(event) => setDescription(event.target.value)} />
        <input className="w-full rounded border border-[#1b2633] bg-[#121c27] p-2 text-sm text-[#d3dce8]" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="tags, comma, separated" />
        <div className="mt-4 flex gap-2">
          <button className="flex-1 rounded border border-[#1b2633] py-2 text-xs uppercase text-[#7d90aa]" onClick={onClose}>Cancel</button>
          <button className="flex-1 rounded bg-[#00c9a7] py-2 text-xs font-bold uppercase text-[#080c12]" onClick={() => onSubmit(workflow, title, description, csv(tags))}>
            Save standard
          </button>
        </div>
      </div>
    </div>
  );
}

export default function WorkflowPage() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowRecord[]>([]);
  const [standardized, setStandardized] = useState<WorkflowRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");
  const [addTarget, setAddTarget] = useState<AddTarget | null>(null);
  const [branchTarget, setBranchTarget] = useState<BranchTarget | null>(null);
  const [branchStepTarget, setBranchStepTarget] = useState<BranchStepTarget | null>(null);
  const [editing, setEditing] = useState<{ workflow: WorkflowRecord; step: WorkflowStep } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [standardizeTarget, setStandardizeTarget] = useState<WorkflowRecord | null>(null);

  async function loadData() {
    try {
      setError("");
      const [nextProjects, nextWorkflows, nextStandardized] = await Promise.all([
        fetchProjects(),
        fetchWorkflows({ tag: "experimental" }),
        fetchWorkflows({ tag: "standardized", libraryState: "published", visibility: "library" }),
      ]);
      setProjects(nextProjects);
      setWorkflows(nextWorkflows);
      setStandardized(nextStandardized);
      setSelectedProjectId((current) => current || nextProjects[0]?.id || "");
    } catch (event) {
      setError(event instanceof Error ? event.message : "Failed to load workflows");
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const selectedWorkflows = useMemo(
    () => workflows.filter((workflow) => workflow.projectId === selectedProjectId),
    [workflows, selectedProjectId],
  );

  async function ensureWorkflow(project: ProjectRecord) {
    const workflow = await createWorkflow({
      title: `${project.title} Experimental Workflow`,
      description: `Editable experimental workflow for ${project.title}.`,
      projectId: project.id,
      visibility: "private",
      libraryState: "draft",
      tags: ["experimental", ...project.tags],
    });
    setWorkflows((current) => [...current, workflow]);
    setAddTarget({ workflowId: workflow.id, afterStepId: null });
  }

  async function startBlankWorkflow(project: ProjectRecord) {
    const existingBlankWorkflow = selectedWorkflows.find((workflow) => workflow.steps.length === 0);
    if (existingBlankWorkflow) {
      setAddTarget({ workflowId: existingBlankWorkflow.id, afterStepId: null });
      return;
    }
    await ensureWorkflow(project);
  }

  async function replaceWorkflowSteps(workflowId: string, steps: WorkflowStep[]) {
    setWorkflows((current) => current.map((workflow) => (workflow.id === workflowId ? { ...workflow, steps } : workflow)));
  }

  async function handleAdd(target: AddTarget, payload: { source: "manual" | "standardized"; step: WorkflowStep; standardizedWorkflowId: string }) {
    let changed = false;
    if (payload.source === "standardized") {
      const steps = await insertStandardizedWorkflow(target.workflowId, {
        standardizedWorkflowId: payload.standardizedWorkflowId,
        afterStepId: target.afterStepId,
      });
      await replaceWorkflowSteps(target.workflowId, steps);
      changed = true;
    } else if (payload.step.label.trim()) {
      const steps = await createMainWorkflowStep(target.workflowId, target.afterStepId, payload.step);
      await replaceWorkflowSteps(target.workflowId, steps);
      changed = true;
    }
    if (changed) await loadData();
    setAddTarget(null);
  }

  async function handleAddBranchStep(target: BranchStepTarget, step: WorkflowStep) {
    if (!step.label.trim()) return;
    const steps = await createWorkflowBranchStep(target.workflowId, target.branchId, step);
    await replaceWorkflowSteps(target.workflowId, steps);
    await loadData();
    setBranchStepTarget(null);
  }

  async function handleBranch(target: BranchTarget, payload: { source: "manual" | "standardized"; label: string; standardizedWorkflowId: string }) {
    const label = payload.label.trim() || "Troubleshooting branch";
    const steps =
      payload.source === "standardized"
        ? await insertStandardizedWorkflow(target.workflowId, {
            standardizedWorkflowId: payload.standardizedWorkflowId,
            anchorStepId: target.anchorStepId,
            branchLabel: label,
          })
        : await createWorkflowBranch(target.workflowId, target.anchorStepId, label);
    await replaceWorkflowSteps(target.workflowId, steps);
    await loadData();
    setBranchTarget(null);
  }

  async function handleSaveStep(workflowId: string, step: WorkflowStep) {
    const steps = await updateWorkflowStep(workflowId, step);
    await replaceWorkflowSteps(workflowId, steps);
    setEditing(null);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    if (deleteTarget.kind === "workflow") {
      await deleteWorkflow(deleteTarget.workflowId);
      setWorkflows((current) => current.filter((workflow) => workflow.id !== deleteTarget.workflowId));
    }
    if (deleteTarget.kind === "step") {
      const steps = await deleteWorkflowStep(deleteTarget.workflowId, deleteTarget.stepId);
      await replaceWorkflowSteps(deleteTarget.workflowId, steps);
    }
    if (deleteTarget.kind === "branch") {
      const steps = await deleteWorkflowBranch(deleteTarget.workflowId, deleteTarget.branchId);
      await replaceWorkflowSteps(deleteTarget.workflowId, steps);
    }
    setDeleteTarget(null);
  }

  async function handleStandardize(workflow: WorkflowRecord, title: string, description: string, tags: string[]) {
    const created = await standardizeWorkflow(workflow.id, { title, description, tags });
    setStandardized((current) => [created, ...current]);
    setStandardizeTarget(null);
  }

  return (
    <main className="min-h-screen bg-[#080c12] p-8 font-mono text-[#d3dce8]">
      <div className="mx-auto max-w-[1500px]">
        <div className="mb-6 text-[10px] uppercase tracking-[0.3em] text-[#52657f]">Workflow / experimental workflows</div>
        <div className="mb-5 flex flex-wrap gap-2">
          {projects.map((project) => (
            <button
              key={project.id}
              data-testid={`workflow-project-tab-${project.id}`}
              className={`rounded border px-3 py-2 text-xs font-bold uppercase ${
                project.id === selectedProjectId
                  ? "border-[#00c9a7] bg-[#09211f] text-[#00c9a7]"
                  : "border-[#1b2633] bg-[#0b1118] text-[#7d90aa]"
              }`}
              onClick={() => setSelectedProjectId(project.id)}
            >
              {project.title.replace(" Protein Purification", "").replace(" Purification Process And Troubleshooting", "").replace(" Transformation And Culture", "")}
            </button>
          ))}
        </div>
        <div className="mb-8 flex items-start justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-[#52657f]">Workflow schematic</div>
            <h1 className="mt-2 text-2xl font-bold">{selectedProject?.title ?? "Experimental Workflows"}</h1>
            <p className="mt-2 text-sm text-[#52657f]">{selectedProject?.description ?? "Select a project to edit its workflow."}</p>
          </div>
          {selectedProject && selectedWorkflows.every((workflow) => workflow.steps.length === 0) ? (
            <button className="rounded bg-[#00c9a7] px-4 py-3 text-xs font-bold uppercase text-[#080c12]" onClick={() => void startBlankWorkflow(selectedProject)}>
              Create blank workflow
            </button>
          ) : null}
        </div>
        {error ? <div className="mb-6 rounded border border-red-500/40 bg-red-950/30 p-4 text-sm text-red-200">{error}</div> : null}
        <div className={`grid gap-8 ${selectedWorkflows.length > 1 ? "xl:grid-cols-2" : ""}`}>
          {selectedWorkflows.map((workflow) => (
            <WorkflowColumn
              key={workflow.id}
              workflow={workflow}
              expanded={expanded}
              onToggle={(stepId) => setExpanded((current) => {
                const next = new Set(current);
                if (next.has(stepId)) next.delete(stepId);
                else next.add(stepId);
                return next;
              })}
              onAdd={setAddTarget}
              onBranch={setBranchTarget}
              onEdit={(workflowRecord, step) => setEditing({ workflow: workflowRecord, step })}
              onAddBranchStep={setBranchStepTarget}
              onDeleteStep={setDeleteTarget}
              onDeleteBranchStep={setDeleteTarget}
              onDeleteBranch={setDeleteTarget}
              onDeleteWorkflow={setDeleteTarget}
              onStandardize={setStandardizeTarget}
            />
          ))}
        </div>
      </div>
      <AddStepModal target={addTarget} standardized={standardized} onClose={() => setAddTarget(null)} onSubmit={(target, payload) => void handleAdd(target, payload)} />
      <BranchModal target={branchTarget} standardized={standardized} onClose={() => setBranchTarget(null)} onSubmit={(target, payload) => void handleBranch(target, payload)} />
      <AddBranchStepModal target={branchStepTarget} onClose={() => setBranchStepTarget(null)} onSubmit={(target, step) => void handleAddBranchStep(target, step)} />
      <EditStepModal editing={editing} onClose={() => setEditing(null)} onSave={(workflowId, step) => void handleSaveStep(workflowId, step)} />
      <StandardizeModal workflow={standardizeTarget} onClose={() => setStandardizeTarget(null)} onSubmit={(workflow, title, description, tags) => void handleStandardize(workflow, title, description, tags)} />
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Confirm delete"
        description={`Are you sure you want to delete ${deleteTarget?.label ?? "this item"}? This cannot be undone.`}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={() => void handleDelete()}
      />
    </main>
  );
}
