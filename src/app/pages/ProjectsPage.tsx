import { useEffect, useMemo, useState } from "react";
import { FolderOpen, Plus, Search, Trash2, UserCog, X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import ConfirmDialog from "../components/ConfirmDialog";
import {
  createProject,
  deleteProject,
  fetchLabMembers,
  fetchProject,
  fetchProjects,
  updateProject,
  type LabMemberRecord,
  type ProjectMemberRecord,
  type ProjectRecord,
} from "../api";

const STATUS_CFG: Record<string, { label: string; text: string; bg: string }> = {
  active: { label: "ACTIVE", text: "text-[#00c9a7]", bg: "bg-[#00c9a7]/10 border-[#00c9a7]/25" },
  complete: { label: "COMPLETE", text: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/25" },
  paused: { label: "PAUSED", text: "text-amber-400", bg: "bg-amber-400/10 border-amber-400/25" },
  archived: { label: "ARCHIVED", text: "text-slate-500", bg: "bg-transparent border-slate-700/30" },
};

const FILTERS = ["ALL", "ACTIVE", "COMPLETE", "PAUSED", "ARCHIVED"] as const;

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [labMembers, setLabMembers] = useState<LabMemberRecord[]>([]);
  const [filter, setFilter] = useState<typeof FILTERS[number]>("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [newOpen, setNewOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ProjectRecord | null>(null);
  const [form, setForm] = useState({ title: "", code: "", description: "", tags: "" });
  const [detailForm, setDetailForm] = useState<{
    id: string;
    title: string;
    code: string;
    description: string;
    status: string;
    tags: string;
    members: ProjectMemberRecord[];
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      try {
        setLoading(true);
        setError(null);
        const [nextProjects, nextLabMembers] = await Promise.all([fetchProjects(), fetchLabMembers()]);
        if (!cancelled) {
          setProjects(nextProjects);
          setLabMembers(nextLabMembers);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load projects");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProjects();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    return projects.filter((project) => {
      const matchFilter = filter === "ALL" || project.status === filter.toLowerCase();
      const haystack = `${project.title} ${project.code} ${project.ownerDisplayName ?? ""}`.toLowerCase();
      const matchSearch = !search || haystack.includes(search.toLowerCase());
      return matchFilter && matchSearch;
    });
  }, [filter, projects, search]);

  const addProject = async () => {
    if (!form.title || !form.code) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const project = await createProject({
        title: form.title,
        code: form.code,
        description: form.description,
        tags: form.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      });
      setProjects((current) => [project, ...current]);
      setForm({ title: "", code: "", description: "", tags: "" });
      setNewOpen(false);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to create project");
    } finally {
      setSaving(false);
    }
  };

  const openProjectDetail = async (projectId: string) => {
    try {
      setDetailLoading(true);
      setError(null);
      const project = await fetchProject(projectId);
      setDetailForm({
        id: project.id,
        title: project.title,
        code: project.code,
        description: project.description,
        status: project.status,
        tags: project.tags.join(", "),
        members: project.members,
      });
      setDetailOpen(true);
    } catch (detailError) {
      setError(detailError instanceof Error ? detailError.message : "Failed to load project detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const saveProjectDetail = async () => {
    if (!detailForm) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const updated = await updateProject(detailForm.id, {
        title: detailForm.title,
        description: detailForm.description,
        status: detailForm.status,
        tags: detailForm.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        members: detailForm.members.map((member) => ({
          userId: member.userId,
          projectRole: member.projectRole,
        })),
      });
      setProjects((current) => current.map((project) => (project.id === updated.id ? updated : project)));
      setDetailForm({
        id: updated.id,
        title: updated.title,
        code: updated.code,
        description: updated.description,
        status: updated.status,
        tags: updated.tags.join(", "),
        members: updated.members,
      });
      setDetailOpen(false);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update project");
    } finally {
      setSaving(false);
    }
  };

  const confirmDeleteProject = async () => {
    if (!deleteTarget) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await deleteProject(deleteTarget.id);
      setProjects((current) => current.filter((project) => project.id !== deleteTarget.id));
      if (detailForm?.id === deleteTarget.id) {
        setDetailOpen(false);
        setDetailForm(null);
      }
      setDeleteTarget(null);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete project");
    } finally {
      setSaving(false);
    }
  };

  const availableMembers = detailForm
    ? labMembers.filter((member) => !detailForm.members.some((projectMember) => projectMember.userId === member.id))
    : [];

  const inputCls =
    "w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50";

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">LAB NOTEBOOK</div>
          <h1 className="text-xl font-mono font-semibold text-foreground">Projects</h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1">
            {projects.length} total · {projects.filter((project) => project.status === "active").length} active
          </p>
        </div>
        <button
          onClick={() => setNewOpen(true)}
          className="flex items-center gap-2 bg-[#00c9a7] hover:bg-[#00b899] text-[#080c12] text-[10px] font-mono font-semibold px-3 py-2 rounded-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          NEW PROJECT
        </button>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Projects API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="flex items-center gap-1">
          {FILTERS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setFilter(item)}
              className={`text-[9px] font-mono px-2.5 py-1 rounded-sm border transition-colors ${
                filter === item
                  ? "bg-[#00c9a7]/10 border-[#00c9a7]/25 text-[#00c9a7]"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
        <div className="relative ml-auto">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
          <input
            className="bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm pl-7 pr-3 py-1.5 w-48 focus:outline-none focus:border-[#00c9a7]/50 placeholder:text-muted-foreground/40"
            placeholder="Search projects..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="border border-border rounded-sm bg-card px-4 py-5 text-[11px] font-mono text-muted-foreground">
          Loading projects...
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <FolderOpen className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
          <div className="text-[11px] font-mono text-muted-foreground">No projects match your filter</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {filtered.map((project) => {
            const status = STATUS_CFG[project.status] ?? STATUS_CFG.active;
            return (
              <div
                key={project.id}
                className="border border-border bg-card rounded-sm p-4 hover:bg-secondary transition-colors flex flex-col gap-3 cursor-pointer"
                onClick={() => void openProjectDetail(project.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-[11px] font-mono text-foreground font-medium leading-snug">{project.title}</div>
                    <div className="text-[9px] font-mono text-muted-foreground mt-0.5">
                      {project.code} · Owner: {project.ownerDisplayName ?? "Unassigned"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        setDeleteTarget(project);
                      }}
                      className="flex h-6 w-6 items-center justify-center rounded-sm border border-transparent text-muted-foreground transition-colors hover:border-red-400/30 hover:bg-red-500/10 hover:text-red-300"
                      aria-label={`Delete project ${project.title}`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                    <span className={`flex-shrink-0 text-[8px] font-mono tracking-wider border px-1.5 py-0.5 rounded-sm ${status.bg} ${status.text}`}>
                      {status.label}
                    </span>
                  </div>
                </div>

                <p className="text-[10px] font-mono text-muted-foreground leading-relaxed line-clamp-3">
                  {project.description || "No description yet."}
                </p>

                <div className="flex flex-wrap gap-1">
                  {project.tags.map((tag) => (
                    <span key={tag} className="text-[8px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded-sm">
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="pt-2 border-t border-border">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-3 text-[9px] font-mono text-muted-foreground">
                      <span>{project.experimentCount} experiment{project.experimentCount !== 1 ? "s" : ""}</span>
                      <span>{project.workflowCount} workflow run{project.workflowCount !== 1 ? "s" : ""}</span>
                    </div>
                    <span className="text-[10px] font-mono text-foreground font-semibold">{project.progressPercent}%</span>
                  </div>
                  <div className="h-1 bg-border rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${project.status === "complete" ? "bg-emerald-400" : "bg-[#00c9a7]"}`}
                      style={{ width: `${project.progressPercent}%` }}
                    />
                  </div>
                  <div className="text-[9px] font-mono text-muted-foreground mt-1.5">
                    Updated {project.updatedAt.slice(0, 10)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Dialog.Root open={newOpen} onOpenChange={setNewOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[440px] max-w-[95vw] bg-background border border-border rounded-sm shadow-2xl p-5"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs font-mono text-foreground font-medium">NEW PROJECT</div>
              <button type="button" onClick={() => setNewOpen(false)}>
                <X className="w-3.5 h-3.5 text-muted-foreground" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">PROJECT NAME *</div>
                <input
                  className={inputCls}
                  placeholder="e.g. ANC2 Crystallography"
                  value={form.title}
                  onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                />
              </div>
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">PROJECT CODE *</div>
                <input
                  className={inputCls}
                  placeholder="e.g. XRAY-2026-08"
                  value={form.code}
                  onChange={(event) => setForm((current) => ({ ...current, code: event.target.value }))}
                />
              </div>
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">DESCRIPTION</div>
                <textarea
                  className={inputCls + " min-h-[64px] resize-none"}
                  placeholder="Brief protocol description..."
                  value={form.description}
                  onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                />
              </div>
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">TAGS (comma-separated)</div>
                <input
                  className={inputCls}
                  placeholder="protein, NMR, structural"
                  value={form.tags}
                  onChange={(event) => setForm((current) => ({ ...current, tags: event.target.value }))}
                />
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setNewOpen(false)}
                  className="flex-1 text-[10px] font-mono text-muted-foreground border border-border rounded-sm py-1.5 hover:bg-secondary transition-colors"
                >
                  CANCEL
                </button>
                <button
                  type="button"
                  disabled={!form.title || !form.code || saving}
                  onClick={() => void addProject()}
                  className="flex-1 text-[10px] font-mono text-[#080c12] bg-[#00c9a7] hover:bg-[#00b899] disabled:opacity-40 rounded-sm py-1.5 font-semibold transition-colors"
                >
                  {saving ? "CREATING..." : "CREATE PROJECT"}
                </button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <Dialog.Root open={detailOpen} onOpenChange={setDetailOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content
            className="fixed top-1/2 left-1/2 z-50 max-h-[88vh] w-[760px] max-w-[95vw] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-sm border border-border bg-background p-5 shadow-2xl"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground">PROJECT DETAIL</div>
                <div className="text-sm font-mono font-medium text-foreground">
                  {detailLoading ? "Loading..." : detailForm?.title ?? "Project"}
                </div>
              </div>
              <button type="button" onClick={() => setDetailOpen(false)}>
                <X className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            </div>

            {detailForm && !detailLoading && (
              <div className="space-y-5">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <div className="mb-1 text-[9px] font-mono tracking-widest text-muted-foreground">PROJECT NAME</div>
                    <input
                      className={inputCls}
                      value={detailForm.title}
                      onChange={(event) =>
                        setDetailForm((current) => current ? { ...current, title: event.target.value } : current)
                      }
                    />
                  </div>
                  <div>
                    <div className="mb-1 text-[9px] font-mono tracking-widest text-muted-foreground">PROJECT CODE</div>
                    <input className={inputCls} value={detailForm.code} disabled />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
                  <div>
                    <div className="mb-1 text-[9px] font-mono tracking-widest text-muted-foreground">DESCRIPTION / NOTES</div>
                    <textarea
                      className={inputCls + " min-h-[110px] resize-none"}
                      value={detailForm.description}
                      onChange={(event) =>
                        setDetailForm((current) => current ? { ...current, description: event.target.value } : current)
                      }
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="mb-1 text-[9px] font-mono tracking-widest text-muted-foreground">STATUS</div>
                      <select
                        className={inputCls}
                        value={detailForm.status}
                        onChange={(event) =>
                          setDetailForm((current) => current ? { ...current, status: event.target.value } : current)
                        }
                      >
                        <option value="active">active</option>
                        <option value="complete">complete</option>
                        <option value="paused">paused</option>
                        <option value="archived">archived</option>
                      </select>
                    </div>
                    <div>
                      <div className="mb-1 text-[9px] font-mono tracking-widest text-muted-foreground">TAGS</div>
                      <input
                        className={inputCls}
                        value={detailForm.tags}
                        onChange={(event) =>
                          setDetailForm((current) => current ? { ...current, tags: event.target.value } : current)
                        }
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-sm border border-border bg-card p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <UserCog className="h-3.5 w-3.5 text-[#00c9a7]" />
                    <div className="text-[10px] font-mono text-foreground">PROJECT ACCESS</div>
                  </div>
                  <div className="space-y-2">
                    {detailForm.members.map((member) => (
                      <div key={member.userId} className="grid grid-cols-[minmax(0,1fr)_130px_32px] gap-2 rounded-sm border border-border bg-background px-3 py-2">
                        <div className="min-w-0">
                          <div className="truncate text-[10px] font-mono text-foreground">{member.displayName}</div>
                          <div className="truncate text-[8px] font-mono text-muted-foreground">
                            {member.email} · {member.labRole}
                          </div>
                        </div>
                        <select
                          disabled={member.projectRole === "owner"}
                          className={inputCls + " h-[30px]"}
                          value={member.projectRole}
                          onChange={(event) =>
                            setDetailForm((current) =>
                              current
                                ? {
                                    ...current,
                                    members: current.members.map((currentMember) =>
                                      currentMember.userId === member.userId
                                        ? { ...currentMember, projectRole: event.target.value }
                                        : currentMember,
                                    ),
                                  }
                                : current
                            )
                          }
                        >
                          <option value="owner">owner</option>
                          <option value="editor">editor</option>
                          <option value="commenter">commenter</option>
                          <option value="viewer">viewer</option>
                        </select>
                        <button
                          type="button"
                          disabled={member.projectRole === "owner"}
                          onClick={() =>
                            setDetailForm((current) =>
                              current
                                ? {
                                    ...current,
                                    members: current.members.filter((currentMember) => currentMember.userId !== member.userId),
                                  }
                                : current
                            )
                          }
                          className="flex h-[30px] items-center justify-center rounded-sm border border-transparent text-muted-foreground transition-colors hover:border-red-400/30 hover:bg-red-500/10 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-30"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>

                  {availableMembers.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-3">
                      <select
                        className={inputCls + " max-w-[280px]"}
                        defaultValue=""
                        onChange={(event) => {
                          const userId = event.target.value;
                          if (!userId) {
                            return;
                          }
                          const member = labMembers.find((candidate) => candidate.id === userId);
                          if (!member) {
                            return;
                          }
                          setDetailForm((current) =>
                            current
                              ? {
                                  ...current,
                                  members: [
                                    ...current.members,
                                    {
                                      userId: member.id,
                                      displayName: member.displayName,
                                      email: member.email,
                                      labRole: member.role,
                                      projectRole: "viewer",
                                    },
                                  ],
                                }
                              : current
                          );
                          event.target.value = "";
                        }}
                      >
                        <option value="">Add lab member...</option>
                        {availableMembers.map((member) => (
                          <option key={member.id} value={member.id}>
                            {member.displayName} · {member.role}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() =>
                      setDeleteTarget(
                        projects.find((project) => project.id === detailForm.id) ?? {
                          id: detailForm.id,
                          title: detailForm.title,
                          code: detailForm.code,
                          description: detailForm.description,
                          status: detailForm.status,
                          tags: detailForm.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
                          ownerDisplayName: undefined,
                          experimentCount: 0,
                          workflowCount: 0,
                          progressPercent: 0,
                          members: detailForm.members,
                          createdAt: "",
                          updatedAt: "",
                        },
                      )
                    }
                    className="flex items-center gap-2 rounded-sm border border-red-400/25 bg-red-500/10 px-3 py-1.5 text-[10px] font-mono text-red-300 transition-colors hover:bg-red-500/15"
                  >
                    <Trash2 className="h-3 w-3" />
                    DELETE PROJECT
                  </button>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setDetailOpen(false)}
                      className="rounded-sm border border-border px-3 py-1.5 text-[10px] font-mono text-muted-foreground transition-colors hover:bg-secondary"
                    >
                      CLOSE
                    </button>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void saveProjectDetail()}
                      className="rounded-sm border border-[#00c9a7] bg-[#00c9a7] px-3 py-1.5 text-[10px] font-mono font-semibold text-[#080c12] transition-colors hover:bg-[#00b899] disabled:opacity-40"
                    >
                      {saving ? "SAVING..." : "SAVE PROJECT"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete project?"
        description={
          deleteTarget
            ? `Delete ${deleteTarget.title}. This removes the project record and its local association data. This cannot be undone.`
            : ""
        }
        confirmLabel="DELETE PROJECT"
        busy={saving}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
          }
        }}
        onConfirm={() => void confirmDeleteProject()}
      />
    </div>
  );
}
