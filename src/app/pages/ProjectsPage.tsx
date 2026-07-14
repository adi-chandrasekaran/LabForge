import { useState } from "react";
import { Link } from "react-router";
import { Plus, FolderOpen, GitBranch, CheckCircle2, Clock, AlertTriangle, Search, X, FlaskConical } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";

interface Project {
  id: string;
  name: string;
  code: string;
  pi: string;
  status: "active" | "complete" | "paused" | "archived";
  description: string;
  started: string;
  updated: string;
  progress: number;
  tags: string[];
  samples: number;
  workflows: number;
}

const INITIAL: Project[] = [
  { id: "p1", name: "ANC2 Protein Purification", code: "PROT-2026-07", pi: "Ferretti, A.", status: "active", description: "Comparative purification strategies for ancestral ANC2 protein using native and refolding protocols.", started: "2026-07-01", updated: "2026-07-13", progress: 38, tags: ["protein", "purification", "refolding"], samples: 24, workflows: 2 },
  { id: "p2", name: "BRCA1 Sanger Sequencing", code: "GEN-2026-06", pi: "Chen, Y.", status: "complete", description: "Targeted amplification and Sanger sequencing of BRCA1 exons from FFPE biopsy samples.", started: "2026-06-15", updated: "2026-06-28", progress: 100, tags: ["sequencing", "PCR", "BRCA1"], samples: 12, workflows: 1 },
  { id: "p3", name: "p53-DNA Binding Assay", code: "BIND-2026-05", pi: "Lindqvist, S.", status: "paused", description: "ITC and EMSA characterization of p53 binding to consensus DNA elements.", started: "2026-05-10", updated: "2026-06-01", progress: 62, tags: ["binding", "ITC", "EMSA", "p53"], samples: 8, workflows: 3 },
  { id: "p4", name: "Histone H3 ChIP-seq", code: "EPIG-2026-04", pi: "Okafor, M.", status: "active", description: "Chromatin immunoprecipitation followed by next-generation sequencing for H3K27ac mapping.", started: "2026-04-01", updated: "2026-07-10", progress: 71, tags: ["ChIP-seq", "histone", "epigenetics"], samples: 36, workflows: 1 },
  { id: "p5", name: "NMR Structure of ANC2", code: "NMR-2026-03", pi: "Ferretti, A.", status: "active", description: "Solution NMR structure determination of refolded ANC2 in the presence of DNA.", started: "2026-03-20", updated: "2026-07-12", progress: 45, tags: ["NMR", "structure", "ANC2"], samples: 6, workflows: 1 },
];

const STATUS_CFG: Record<Project["status"], { label: string; dot: string; text: string; bg: string }> = {
  active:   { label: "ACTIVE",   dot: "bg-[#00c9a7] animate-pulse", text: "text-[#00c9a7]",  bg: "bg-[#00c9a7]/10 border-[#00c9a7]/25" },
  complete: { label: "COMPLETE", dot: "bg-emerald-400",             text: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/25" },
  paused:   { label: "PAUSED",   dot: "bg-amber-400",               text: "text-amber-400",  bg: "bg-amber-400/10 border-amber-400/25" },
  archived: { label: "ARCHIVED", dot: "bg-slate-600",               text: "text-slate-500",  bg: "bg-transparent border-slate-700/30" },
};

const FILTERS = ["ALL", "ACTIVE", "COMPLETE", "PAUSED", "ARCHIVED"] as const;

export default function ProjectsPage() {
  const [projects, setProjects] = useState(INITIAL);
  const [filter, setFilter] = useState<typeof FILTERS[number]>("ALL");
  const [search, setSearch] = useState("");
  const [newOpen, setNewOpen] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", pi: "", description: "", tags: "" });

  const filtered = projects.filter(p => {
    const matchFilter = filter === "ALL" || p.status === filter.toLowerCase();
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.code.toLowerCase().includes(search.toLowerCase()) || p.pi.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const addProject = () => {
    if (!form.name) return;
    const newP: Project = {
      id: `p${Date.now()}`, name: form.name, code: form.code || `PROJ-${Date.now().toString().slice(-4)}`,
      pi: form.pi || "—", status: "active", description: form.description,
      started: new Date().toISOString().slice(0, 10), updated: new Date().toISOString().slice(0, 10),
      progress: 0, tags: form.tags.split(",").map(t => t.trim()).filter(Boolean), samples: 0, workflows: 0,
    };
    setProjects(ps => [newP, ...ps]);
    setForm({ name: "", code: "", pi: "", description: "", tags: "" });
    setNewOpen(false);
  };

  const inputCls = "w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50";

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">LAB NOTEBOOK</div>
          <h1 className="text-xl font-mono font-semibold text-foreground">Projects</h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1">{projects.length} total · {projects.filter(p => p.status === "active").length} active</p>
        </div>
        <button
          onClick={() => setNewOpen(true)}
          className="flex items-center gap-2 bg-[#00c9a7] hover:bg-[#00b899] text-[#080c12] text-[10px] font-mono font-semibold px-3 py-2 rounded-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />NEW PROJECT
        </button>
      </div>

      {/* Filter + search */}
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="flex items-center gap-1">
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`text-[9px] font-mono px-2.5 py-1 rounded-sm border transition-colors ${filter === f ? "bg-[#00c9a7]/10 border-[#00c9a7]/25 text-[#00c9a7]" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
              {f}
            </button>
          ))}
        </div>
        <div className="relative ml-auto">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
          <input
            className="bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm pl-7 pr-3 py-1.5 w-48 focus:outline-none focus:border-[#00c9a7]/50 placeholder:text-muted-foreground/40"
            placeholder="Search projects..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Project grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {filtered.map(p => {
          const sc = STATUS_CFG[p.status];
          return (
            <div key={p.id} className="border border-border bg-card rounded-sm p-4 hover:bg-secondary transition-colors flex flex-col gap-3 cursor-pointer">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-[11px] font-mono text-foreground font-medium leading-snug">{p.name}</div>
                  <div className="text-[9px] font-mono text-muted-foreground mt-0.5">{p.code} · PI: {p.pi}</div>
                </div>
                <span className={`flex-shrink-0 text-[8px] font-mono tracking-wider border px-1.5 py-0.5 rounded-sm ${sc.bg} ${sc.text}`}>{sc.label}</span>
              </div>

              <p className="text-[10px] font-mono text-muted-foreground leading-relaxed line-clamp-2">{p.description}</p>

              <div className="flex flex-wrap gap-1">
                {p.tags.map(t => (
                  <span key={t} className="text-[8px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm">{t}</span>
                ))}
              </div>

              <div className="pt-2 border-t border-border">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-3 text-[9px] font-mono text-muted-foreground">
                    <span>{p.samples} samples</span>
                    <span>{p.workflows} workflow{p.workflows !== 1 ? "s" : ""}</span>
                  </div>
                  <span className="text-[10px] font-mono text-foreground font-semibold">{p.progress}%</span>
                </div>
                <div className="h-1 bg-border rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${p.status === "complete" ? "bg-emerald-400" : "bg-[#00c9a7]"}`} style={{ width: `${p.progress}%` }} />
                </div>
                <div className="text-[9px] font-mono text-muted-foreground mt-1.5">Updated {p.updated}</div>
              </div>
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16">
          <FolderOpen className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
          <div className="text-[11px] font-mono text-muted-foreground">No projects match your filter</div>
        </div>
      )}

      {/* New project modal */}
      <Dialog.Root open={newOpen} onOpenChange={setNewOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[440px] max-w-[95vw] bg-background border border-border rounded-sm shadow-2xl p-5"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs font-mono text-foreground font-medium">NEW PROJECT</div>
              <button onClick={() => setNewOpen(false)}><X className="w-3.5 h-3.5 text-muted-foreground" /></button>
            </div>
            <div className="space-y-3">
              {[
                { key: "name", label: "PROJECT NAME *", ph: "e.g. ANC2 Crystallography" },
                { key: "code", label: "PROJECT CODE", ph: "e.g. XRAY-2026-08" },
                { key: "pi", label: "PRINCIPAL INVESTIGATOR", ph: "Last, First" },
                { key: "description", label: "DESCRIPTION", ph: "Brief protocol description..." },
                { key: "tags", label: "TAGS (comma-separated)", ph: "protein, NMR, structural" },
              ].map(({ key, label, ph }) => (
                <div key={key}>
                  <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">{label}</div>
                  {key === "description"
                    ? <textarea className={inputCls + " min-h-[64px] resize-none"} placeholder={ph} value={(form as any)[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
                    : <input className={inputCls} placeholder={ph} value={(form as any)[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
                  }
                </div>
              ))}
              <div className="flex gap-2 pt-1">
                <button onClick={() => setNewOpen(false)} className="flex-1 text-[10px] font-mono text-muted-foreground border border-border rounded-sm py-1.5 hover:bg-secondary transition-colors">CANCEL</button>
                <button disabled={!form.name} onClick={addProject}
                  className="flex-1 text-[10px] font-mono text-[#080c12] bg-[#00c9a7] hover:bg-[#00b899] disabled:opacity-40 rounded-sm py-1.5 font-semibold transition-colors">
                  CREATE PROJECT
                </button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
