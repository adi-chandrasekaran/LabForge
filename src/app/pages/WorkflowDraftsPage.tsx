import { useEffect, useState } from "react";
import { CheckCircle2, ClipboardCheck, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "../components/ui/button";
import { confirmWorkflowDraft, fetchWorkflowDrafts, type WorkflowDraftRecord } from "../api";

const panel = "border border-border rounded-sm bg-card";

export default function WorkflowDraftsPage() {
  const [drafts, setDrafts] = useState<WorkflowDraftRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState<string | null>(null);
  const load = async () => { setLoading(true); try { setDrafts(await fetchWorkflowDrafts()); setError(null); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load workflow drafts."); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  const confirm = async (id: string) => { setConfirming(id); try { await confirmWorkflowDraft(id); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Unable to confirm this draft."); } finally { setConfirming(null); } };
  return <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
    <div className="flex items-start justify-between gap-4 mb-6 flex-wrap"><div><div className="text-[9px] tracking-[0.25em] text-muted-foreground mb-1">AGENT SAFETY REVIEW</div><h1 className="text-xl font-semibold">Workflow change drafts</h1><p className="text-[10px] text-muted-foreground mt-1 max-w-2xl">The assistant can prepare a draft but cannot apply it. Review the exact payload, then explicitly confirm a single pending draft.</p></div><Button variant="outline" size="sm" onClick={() => void load()}><RefreshCw className="w-3 h-3" /> Refresh</Button></div>
    {error && <div className="border border-red-400/25 bg-red-400/10 text-red-200 p-3 text-[10px] mb-4">{error}</div>}
    <div className="border border-emerald-400/20 bg-emerald-400/5 p-3 text-[10px] text-emerald-200 mb-4 flex gap-2"><ShieldCheck className="w-4 h-4 shrink-0" />Confirmation is a human action. Confirmed drafts cannot be applied a second time.</div>
    {loading ? <div className="text-[10px] text-muted-foreground">Loading drafts…</div> : drafts.length === 0 ? <div className={`${panel} p-5 text-[10px] text-muted-foreground`}>No workflow change drafts are waiting for review.</div> : <div className="space-y-3">{drafts.map(draft => <section className={`${panel} p-4`} key={draft.id}><div className="flex items-start justify-between gap-4"><div><div className="flex gap-2 items-center"><ClipboardCheck className="w-4 h-4 text-violet-300" /><span className="text-xs text-foreground">{draft.operation.replaceAll("_", " ")}</span></div><div className="text-[9px] text-muted-foreground mt-2">{draft.id} · created {new Date(draft.createdAt).toLocaleString()}</div></div><div className="text-[9px] uppercase tracking-wider text-violet-300">{draft.status}</div></div><pre className="mt-3 p-3 bg-background border border-border overflow-auto text-[9px] text-muted-foreground">{JSON.stringify(draft.payload, null, 2)}</pre>{draft.failureDetail && <div className="text-[9px] text-red-300 mt-3">{draft.failureDetail}</div>}{draft.status === "pending" && <div className="mt-3 flex justify-end"><Button size="sm" onClick={() => void confirm(draft.id)} disabled={confirming === draft.id}><CheckCircle2 className="w-3 h-3" />{confirming === draft.id ? "Confirming…" : "Confirm and apply"}</Button></div>}</section>)}</div>}
  </div>;
}
