import { Link } from "react-router";
import { GitBranch, FolderOpen, Calculator, FlaskConical, Clock, CheckCircle2, Play, ArrowRight, Beaker, TrendingUp } from "lucide-react";

const RECENT_PROJECTS = [
  { id: "p1", name: "ANC2 Purification", code: "PROT-2026-07", status: "running", progress: 38, pi: "Ferretti A.", updated: "2 hr ago", tags: ["protein", "purification"] },
  { id: "p2", name: "BRCA1 Sanger Sequencing", code: "GEN-2026-06", status: "complete", progress: 100, pi: "Chen Y.", updated: "3 days ago", tags: ["sequencing", "PCR"] },
  { id: "p3", name: "p53 Binding Assay", code: "BIND-2026-05", status: "pending", progress: 0, pi: "Lindqvist S.", updated: "1 wk ago", tags: ["binding", "ITC"] },
];

const ACTIVITY = [
  { time: "10:48", msg: "Step 3 (PCR Setup) started", type: "running", exp: "EXP-2024-0711" },
  { time: "10:35", msg: "DNA Extraction completed — yield 4.2 µg/µL", type: "complete", exp: "EXP-2024-0711" },
  { time: "09:05", msg: "Dialysis step started (Batch 1)", type: "running", exp: "ANC2-PURIF-2026" },
  { time: "08:57", msg: "Sample QC passed — A260/A280 = 1.89", type: "complete", exp: "EXP-2024-0711" },
  { time: "Yesterday", msg: "Ni-NTA Elution completed", type: "complete", exp: "ANC2-PURIF-2026" },
];

const STATUS_DOT: Record<string, string> = { running: "bg-[#00c9a7] animate-pulse", complete: "bg-emerald-400", pending: "bg-slate-600" };
const STATUS_TEXT: Record<string, string> = { running: "text-[#00c9a7]", complete: "text-emerald-400", pending: "text-slate-500" };

const QUICK_TOOLS = [
  { to: "/workflow", icon: GitBranch, label: "WORKFLOW", sub: "View & edit protocols" },
  { to: "/calculator", icon: Calculator, label: "CALCULATOR", sub: "Molarity & dilution" },
  { to: "/projects", icon: FolderOpen, label: "PROJECTS", sub: "Manage experiments" },
];

export default function HomePage() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Header */}
      <div className="mb-8">
        <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">
          {new Date().toISOString().slice(0, 10)} · LAB NOTEBOOK
        </div>
        <h1 className="text-xl font-mono font-semibold text-foreground">{greeting}, Chen.</h1>
        <p className="text-[11px] font-mono text-muted-foreground mt-1">1 experiment running · 2 steps due today</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {[
          { label: "ACTIVE EXPS", value: "3", icon: Play, color: "text-[#00c9a7]" },
          { label: "PROTOCOLS", value: "12", icon: FlaskConical, color: "text-violet-400" },
          { label: "SAMPLES", value: "47", icon: Beaker, color: "text-sky-400" },
          { label: "COMPLETED", value: "28", icon: CheckCircle2, color: "text-emerald-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="border border-border bg-card rounded-sm px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9px] font-mono tracking-widest text-muted-foreground">{label}</span>
              <Icon className={`w-3.5 h-3.5 ${color}`} />
            </div>
            <div className={`text-2xl font-mono font-semibold ${color}`}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        {/* Recent Projects */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground">RECENT PROJECTS</div>
            <Link to="/projects" className="text-[9px] font-mono text-[#00c9a7] hover:text-[#00b899] flex items-center gap-1 transition-colors">
              VIEW ALL <ArrowRight className="w-2.5 h-2.5" />
            </Link>
          </div>
          <div className="space-y-2">
            {RECENT_PROJECTS.map(p => (
              <div key={p.id} className="border border-border bg-card rounded-sm px-4 py-3 hover:bg-secondary transition-colors cursor-pointer">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-mono text-foreground font-medium">{p.name}</span>
                      <span className="text-[9px] font-mono text-muted-foreground">{p.code}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex items-center gap-1">
                        <div className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[p.status]}`} />
                        <span className={`text-[9px] font-mono ${STATUS_TEXT[p.status]}`}>{p.status.toUpperCase()}</span>
                      </div>
                      <span className="text-[9px] font-mono text-muted-foreground">PI: {p.pi}</span>
                      <span className="text-[9px] font-mono text-muted-foreground">{p.updated}</span>
                    </div>
                    <div className="flex gap-1.5 mt-2">
                      {p.tags.map(t => (
                        <span key={t} className="text-[8px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm tracking-wider">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <div className="text-xs font-mono font-semibold text-foreground">{p.progress}%</div>
                    <div className="w-16 h-1 bg-border rounded-full mt-1 overflow-hidden">
                      <div className="h-full bg-[#00c9a7] rounded-full" style={{ width: `${p.progress}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Tools */}
          <div className="mt-6">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">QUICK ACCESS</div>
            <div className="grid grid-cols-3 gap-2">
              {QUICK_TOOLS.map(({ to, icon: Icon, label, sub }) => (
                <Link key={to} to={to} className="border border-border bg-card hover:bg-secondary hover:border-[#00c9a7]/30 rounded-sm px-3 py-3 transition-all group">
                  <Icon className="w-4 h-4 text-[#00c9a7] mb-2" />
                  <div className="text-[10px] font-mono text-foreground font-medium">{label}</div>
                  <div className="text-[9px] font-mono text-muted-foreground mt-0.5">{sub}</div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Activity feed */}
        <div>
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">RECENT ACTIVITY</div>
          <div className="border border-border bg-card rounded-sm overflow-hidden">
            {ACTIVITY.map((a, i) => (
              <div key={i} className={`px-4 py-3 flex items-start gap-3 ${i < ACTIVITY.length - 1 ? "border-b border-border" : ""}`}>
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${a.type === "running" ? "bg-[#00c9a7] animate-pulse" : "bg-emerald-400"}`} />
                <div className="min-w-0 flex-1">
                  <div className="text-[10px] font-mono text-foreground leading-snug">{a.msg}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[9px] font-mono text-muted-foreground">{a.time}</span>
                    <span className="text-[9px] font-mono text-muted-foreground/50">{a.exp}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
