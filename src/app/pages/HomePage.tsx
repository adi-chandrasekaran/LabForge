import { useEffect, useState } from "react";
import { Link } from "react-router";
import { GitBranch, FolderOpen, Calculator, FlaskConical, CheckCircle2, Play, ArrowRight, Beaker } from "lucide-react";
import { fetchHomeSummary, type HomeSummaryRecord } from "../api";

const STATUS_DOT: Record<string, string> = {
  running: "bg-[#00c9a7] animate-pulse",
  complete: "bg-emerald-400",
  pending: "bg-slate-600",
  planned: "bg-slate-600",
  blocked: "bg-amber-400",
  error: "bg-red-400",
  active: "bg-[#00c9a7] animate-pulse",
};

const STATUS_TEXT: Record<string, string> = {
  running: "text-[#00c9a7]",
  complete: "text-emerald-400",
  pending: "text-slate-500",
  planned: "text-slate-500",
  blocked: "text-amber-400",
  error: "text-red-400",
  active: "text-[#00c9a7]",
};

const QUICK_TOOLS = [
  { to: "/workflow", icon: GitBranch, label: "WORKFLOW", sub: "View & edit protocols" },
  { to: "/calculator", icon: Calculator, label: "CALCULATOR", sub: "Molarity & dilution" },
  { to: "/projects", icon: FolderOpen, label: "PROJECTS", sub: "Manage experiments" },
];

export default function HomePage() {
  const [summary, setSummary] = useState<HomeSummaryRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const nextSummary = await fetchHomeSummary();
        if (!cancelled) {
          setSummary(nextSummary);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = summary?.userDisplayName.split(",")[0] ?? "Chen";

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="mb-8">
        <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">
          {new Date().toISOString().slice(0, 10)} · LAB NOTEBOOK
        </div>
        <h1 className="text-xl font-mono font-semibold text-foreground">{greeting}, {firstName}.</h1>
        <p className="text-[11px] font-mono text-muted-foreground mt-1">
          {summary ? `${summary.activeExperimentCount} experiment${summary.activeExperimentCount !== 1 ? "s" : ""} active · ${summary.recentActivity.length} recent update${summary.recentActivity.length !== 1 ? "s" : ""}` : "Loading dashboard..."}
        </p>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Dashboard API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {[
          { label: "ACTIVE EXPS", value: summary?.activeExperimentCount ?? 0, icon: Play, color: "text-[#00c9a7]" },
          { label: "PROTOCOLS", value: summary?.protocolCount ?? 0, icon: FlaskConical, color: "text-violet-400" },
          { label: "PROJECTS", value: summary?.projectCount ?? 0, icon: Beaker, color: "text-sky-400" },
          { label: "COMPLETED", value: summary?.completedExperimentCount ?? 0, icon: CheckCircle2, color: "text-emerald-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="border border-border bg-card rounded-sm px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9px] font-mono tracking-widest text-muted-foreground">{label}</span>
              <Icon className={`w-3.5 h-3.5 ${color}`} />
            </div>
            <div className={`text-2xl font-mono font-semibold ${color}`}>{loading ? "—" : value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground">RECENT PROJECTS</div>
            <Link to="/projects" className="text-[9px] font-mono text-[#00c9a7] hover:text-[#00b899] flex items-center gap-1 transition-colors">
              VIEW ALL <ArrowRight className="w-2.5 h-2.5" />
            </Link>
          </div>
          {loading ? (
            <div className="border border-border bg-card rounded-sm px-4 py-5 text-[11px] font-mono text-muted-foreground">
              Loading projects...
            </div>
          ) : summary && summary.recentProjects.length > 0 ? (
            <div className="space-y-2">
              {summary.recentProjects.map((project) => (
                <div key={project.id} className="border border-border bg-card rounded-sm px-4 py-3 hover:bg-secondary transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-mono text-foreground font-medium">{project.title}</span>
                        <span className="text-[9px] font-mono text-muted-foreground">{project.code}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <div className="flex items-center gap-1">
                          <div className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[project.status] ?? STATUS_DOT.pending}`} />
                          <span className={`text-[9px] font-mono ${STATUS_TEXT[project.status] ?? STATUS_TEXT.pending}`}>{project.status.toUpperCase()}</span>
                        </div>
                        <span className="text-[9px] font-mono text-muted-foreground">Owner: {project.ownerDisplayName ?? "Unassigned"}</span>
                        <span className="text-[9px] font-mono text-muted-foreground">{project.updatedAt.slice(0, 10)}</span>
                      </div>
                      <div className="flex gap-1.5 mt-2 flex-wrap">
                        {project.tags.map((tag) => (
                          <span key={tag} className="text-[8px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm tracking-wider">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="text-xs font-mono font-semibold text-foreground">{project.progressPercent}%</div>
                      <div className="w-16 h-1 bg-border rounded-full mt-1 overflow-hidden">
                        <div className="h-full bg-[#00c9a7] rounded-full" style={{ width: `${project.progressPercent}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="border border-border bg-card rounded-sm px-4 py-5 text-[11px] font-mono text-muted-foreground">
              No projects yet.
            </div>
          )}

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

        <div>
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">RECENT ACTIVITY</div>
          <div className="border border-border bg-card rounded-sm overflow-hidden">
            {loading ? (
              <div className="px-4 py-5 text-[11px] font-mono text-muted-foreground">Loading activity...</div>
            ) : summary && summary.recentActivity.length > 0 ? (
              summary.recentActivity.map((activity, index) => (
                <div key={`${activity.occurredAt}-${index}`} className={`px-4 py-3 flex items-start gap-3 ${index < summary.recentActivity.length - 1 ? "border-b border-border" : ""}`}>
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${STATUS_DOT[activity.type] ?? STATUS_DOT.pending}`} />
                  <div className="min-w-0 flex-1">
                    <div className="text-[10px] font-mono text-foreground leading-snug">{activity.message}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[9px] font-mono text-muted-foreground">{activity.occurredAt.slice(0, 10)}</span>
                      <span className="text-[9px] font-mono text-muted-foreground/50">{activity.context}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-5 text-[11px] font-mono text-muted-foreground">No recent activity yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
