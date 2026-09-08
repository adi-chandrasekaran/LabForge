import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import type { ProjectRecord, WorkflowRecord } from "../api";

type SortMode = "latest" | "oldest" | "az" | "za";

function ordered<T extends { title: string; updatedAt: string }>(items: T[], mode: SortMode): T[] {
  return [...items].sort((left, right) => {
    if (mode === "az") return left.title.localeCompare(right.title);
    if (mode === "za") return right.title.localeCompare(left.title);
    const time = new Date(left.updatedAt).getTime() - new Date(right.updatedAt).getTime();
    return mode === "oldest" ? time : -time;
  });
}

function SortSelect({ value, onChange, label }: { value: SortMode; onChange: (value: SortMode) => void; label: string }) {
  return <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value as SortMode)} className="rounded border border-[#1b2633] bg-[#080c12] px-2 py-1 text-[10px] text-[#d3dce8]">
    <option value="latest">Latest</option><option value="oldest">Oldest</option><option value="az">A–Z</option><option value="za">Z–A</option>
  </select>;
}

export default function WorkflowTypeNavigator({
  projects, workflows, selectedProjectId, selectedWorkflowId, onSelectProject, onSelectWorkflow, onCreateType, onCreateBatch, typeLabel = "WORKFLOW TYPES", batchLabel = "BATCHES",
}: {
  projects: ProjectRecord[];
  workflows: WorkflowRecord[];
  selectedProjectId: string;
  selectedWorkflowId: string | null;
  onSelectProject: (id: string) => void;
  onSelectWorkflow: (id: string) => void;
  onCreateType: () => void;
  onCreateBatch: () => void;
  typeLabel?: string;
  batchLabel?: string;
}) {
  const [typeSearch, setTypeSearch] = useState("");
  const [batchSearch, setBatchSearch] = useState("");
  const [typeSort, setTypeSort] = useState<SortMode>("latest");
  const [batchSort, setBatchSort] = useState<SortMode>("latest");
  const query = typeSearch.trim().toLowerCase();
  const visibleProjects = useMemo(() => [...projects.filter((project) => {
    if (!query) return true;
    return project.title.toLowerCase().includes(query) || workflows.some((workflow) => workflow.projectId === project.id && workflow.title.toLowerCase().includes(query));
  })].sort((left, right) => {
    if (typeSort === "az") return left.title.localeCompare(right.title);
    if (typeSort === "za") return right.title.localeCompare(left.title);
    const latest = (project: ProjectRecord) => Math.max(new Date(project.updatedAt).getTime(), ...workflows.filter((workflow) => workflow.projectId === project.id).map((workflow) => new Date(workflow.updatedAt).getTime()));
    const difference = latest(left) - latest(right);
    return typeSort === "oldest" ? difference : -difference;
  }), [projects, query, typeSort, workflows]);
  const selectedBatches = useMemo(() => ordered(workflows.filter((workflow) => workflow.projectId === selectedProjectId && workflow.title.toLowerCase().includes(batchSearch.trim().toLowerCase())), batchSort), [batchSearch, batchSort, selectedProjectId, workflows]);

  return <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
    <aside className="rounded border border-[#1b2633] bg-[#0b1118]">
      <div className="flex items-center justify-between border-b border-[#1b2633] px-4 py-3"><span className="text-[10px] font-bold tracking-[0.2em] text-[#52657f]">{typeLabel}</span><button data-testid="workflow-new-type" onClick={onCreateType} className="text-[#00c9a7]" aria-label="New workflow type"><Plus size={16} /></button></div>
      <div className="flex gap-2 p-3"><label className="flex min-w-0 flex-1 items-center gap-2 rounded border border-[#1b2633] px-2"><Search size={13} className="text-[#52657f]" /><input data-testid="workflow-type-search" value={typeSearch} onChange={(event) => setTypeSearch(event.target.value)} placeholder="Filter types" className="min-w-0 flex-1 bg-transparent py-2 text-xs outline-none" /></label><SortSelect label="Sort workflow types" value={typeSort} onChange={setTypeSort} /></div>
      <div className="max-h-64 space-y-1 overflow-y-auto px-2 pb-2">{visibleProjects.map((project) => <button key={project.id} data-testid={`workflow-type-${project.id}`} onClick={() => onSelectProject(project.id)} className={`w-full rounded px-3 py-2 text-left text-xs ${project.id === selectedProjectId ? "bg-[#09211f] text-[#00c9a7]" : "text-[#d3dce8] hover:bg-[#121c27]"}`}><div className="font-bold">{project.title}</div><div className="mt-1 text-[10px] text-[#52657f]">{workflows.filter((workflow) => workflow.projectId === project.id).length} batches</div></button>)}{visibleProjects.length === 0 ? <p className="p-3 text-xs text-[#52657f]">No matching types.</p> : null}</div>
    </aside>
    <aside className="rounded border border-[#1b2633] bg-[#0b1118]">
      <div className="flex items-center justify-between border-b border-[#1b2633] px-4 py-3"><span className="text-[10px] font-bold tracking-[0.2em] text-[#52657f]">{batchLabel}</span><button data-testid="workflow-new-batch" onClick={onCreateBatch} disabled={!selectedProjectId} className="text-[#00c9a7] disabled:opacity-30" aria-label="New batch"><Plus size={16} /></button></div>
      <div className="flex gap-2 p-3"><label className="flex min-w-0 flex-1 items-center gap-2 rounded border border-[#1b2633] px-2"><Search size={13} className="text-[#52657f]" /><input data-testid="workflow-batch-search" value={batchSearch} onChange={(event) => setBatchSearch(event.target.value)} placeholder="Filter batches" className="min-w-0 flex-1 bg-transparent py-2 text-xs outline-none" /></label><SortSelect label="Sort batches" value={batchSort} onChange={setBatchSort} /></div>
      <div className="max-h-64 space-y-1 overflow-y-auto px-2 pb-2">{selectedBatches.map((workflow) => <button key={workflow.id} data-testid={`workflow-batch-${workflow.id}`} onClick={() => onSelectWorkflow(workflow.id)} className={`w-full rounded px-3 py-2 text-left text-xs ${workflow.id === selectedWorkflowId ? "bg-[#09211f] text-[#00c9a7]" : "text-[#d3dce8] hover:bg-[#121c27]"}`}><div className="font-bold">{workflow.title}</div><div className="mt-1 text-[10px] text-[#52657f]">{workflow.steps.length} steps</div></button>)}{selectedBatches.length === 0 ? <p className="p-3 text-xs text-[#52657f]">No matching batches.</p> : null}</div>
    </aside>
  </div>;
}
