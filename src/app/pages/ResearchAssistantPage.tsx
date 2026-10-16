import { useEffect, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, Plus, Send, ShieldCheck, Stethoscope, Wrench } from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import {
  createAgentConversation,
  fetchAgentRuns,
  fetchAgentStatus,
  runAgentConversation,
  runAgentProviderDiagnostic,
  ApiRequestError,
  type AgentProviderDiagnosticRecord,
  type AgentRunRecord,
  type AgentStatusRecord,
} from "../api";

const CONVERSATION_STORAGE_KEY = "nmr-lab-agent-conversation-id";

const diagnosticLabels: Record<AgentProviderDiagnosticRecord["state"], string> = {
  ready: "Provider ready",
  unavailable: "Ollama unavailable",
  configuration_error: "Provider configuration required",
  model_missing: "Ollama model missing",
  provider_error: "Provider issue",
};

export default function ResearchAssistantPage() {
  const [status, setStatus] = useState<AgentStatusRecord | null>(null);
  const [diagnostic, setDiagnostic] = useState<AgentProviderDiagnosticRecord | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [runs, setRuns] = useState<AgentRunRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const providerAvailable = diagnostic?.ok ?? status?.available ?? false;

  useEffect(() => {
    void fetchAgentStatus().then(setStatus).catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to check the provider status."));

    const savedId = window.localStorage.getItem(CONVERSATION_STORAGE_KEY);
    if (!savedId) {
      setRestoring(false);
      return;
    }

    setConversationId(savedId);
    void fetchAgentRuns(savedId)
      .then(setRuns)
      .catch((caught) => {
        if (caught instanceof ApiRequestError && caught.status === 404) {
          window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
          setConversationId(null);
          return;
        }
        setError(caught instanceof Error ? `The saved conversation could not be restored: ${caught.message}` : "The saved conversation could not be restored.");
      })
      .finally(() => setRestoring(false));
  }, []);

  const startNewConversation = () => {
    window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
    setConversationId(null);
    setRuns([]);
    setMessage("");
    setError(null);
  };

  const send = async () => {
    if (!message.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      let id = conversationId;
      if (!id) {
        id = (await createAgentConversation("NMR research assistant")).id;
        setConversationId(id);
        window.localStorage.setItem(CONVERSATION_STORAGE_KEY, id);
      }
      const run = await runAgentConversation(id, message.trim());
      setRuns((current) => [...current, run]);
      setMessage("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The assistant could not complete the request.");
    } finally {
      setBusy(false);
    }
  };

  const diagnose = async () => {
    setDiagnosing(true);
    setDiagnostic(null);
    setError(null);
    try {
      const result = await runAgentProviderDiagnostic();
      setDiagnostic(result);
      setStatus({ available: result.ok, provider: result.provider, model: result.model, detail: result.detail });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The provider diagnostic could not run.");
    } finally {
      setDiagnosing(false);
    }
  };

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="flex justify-between gap-4 mb-6">
        <div>
          <div className="text-[9px] tracking-[0.25em] text-muted-foreground">NMR RESEARCH ASSISTANT</div>
          <h1 className="text-xl font-semibold mt-1">Ask about your LabForge data</h1>
          <p className="text-[10px] text-muted-foreground mt-1">Dataset claims require retrieved evidence. The assistant explicitly reports unavailable NMR data.</p>
        </div>
        <div className="flex items-start gap-2">
          {(conversationId || runs.length > 0) && (
            <Button variant="outline" size="sm" onClick={startNewConversation} disabled={busy || restoring}>
              <Plus className="w-3 h-3" />New conversation
            </Button>
          )}
          <div className={`text-[9px] h-fit border px-3 py-2 ${providerAvailable ? "border-emerald-400/30 text-emerald-300" : "border-amber-400/30 text-amber-300"}`}>
            {status ? `${status.provider} · ${providerAvailable ? "ready" : "unavailable"}` : "checking provider"}
          </div>
        </div>
      </div>

      {status && (
        <div className={`border bg-card p-3 mb-4 flex items-center justify-between gap-3 ${diagnostic ? diagnostic.ok ? "border-emerald-400/30" : "border-amber-400/30" : "border-border"}`}>
          <div className="flex items-start gap-2 text-[10px] text-muted-foreground">
            {diagnostic && (diagnostic.ok ? <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-300" /> : <AlertTriangle className="w-4 h-4 shrink-0 text-amber-300" />)}
            <div>
              {diagnostic && <div className={`font-semibold mb-1 ${diagnostic.ok ? "text-emerald-300" : "text-amber-300"}`}>{diagnosticLabels[diagnostic.state]}</div>}
              <div>{diagnostic?.detail ?? status.detail}</div>
              {diagnostic?.action && <div className="mt-1 text-foreground/80">Next step: {diagnostic.action}</div>}
              {diagnostic?.code && <span className="block mt-1 uppercase tracking-wider">Diagnostic code: {diagnostic.code.replaceAll("_", " ")}</span>}
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => void diagnose()} disabled={diagnosing}>
            <Stethoscope className="w-3 h-3" />{diagnosing ? "Checking…" : "Test provider connection"}
          </Button>
        </div>
      )}

      {error && <div role="alert" className="border border-red-400/25 bg-red-400/10 p-3 mb-4 text-[10px] text-red-200">{error}</div>}

      <div className="space-y-4 mb-4">
        {restoring && <div className="border border-border rounded-sm bg-card p-5 text-[10px] text-muted-foreground">Restoring conversation…</div>}
        {!restoring && runs.length === 0 && (
          <div className="border border-border rounded-sm bg-card p-5 text-[10px] text-muted-foreground">
            <Bot className="w-5 h-5 text-violet-300 mb-2" />
            <div>Try an evidence-backed NMR question:</div>
            <div className="mt-2 space-y-1 text-foreground/80">
              <div>“List my HSQC spectra.”</div>
              <div>“What shifts are stored for residue M1?”</div>
              <div>“Compare two spectra and calculate CSP.”</div>
            </div>
          </div>
        )}
        {runs.map((run) => (
          <section data-testid="agent-run" className="border border-border rounded-sm bg-card p-4" key={run.id}>
            <div className="text-[10px] text-foreground">You: {run.userRequest}</div>
            {run.finalAnswer ? (
              <div className="mt-3 text-[11px] leading-relaxed">
                <div className="mb-1 text-[9px] uppercase tracking-wider text-muted-foreground">Assistant</div>
                <div className="whitespace-pre-wrap">{run.finalAnswer}</div>
              </div>
            ) : (
              <div className="mt-3 text-red-300 text-[10px]">{run.failureDetail ?? "The assistant did not return an answer."}</div>
            )}
            <div className="mt-3 flex items-center gap-2 text-[9px] text-muted-foreground">
              <ShieldCheck className="w-3 h-3" />{run.dataAvailability ?? run.status}
            </div>
            {run.toolCalls.length > 0 && (
              <details className="mt-3 text-[9px] text-muted-foreground">
                <summary className="cursor-pointer flex items-center gap-1"><Wrench className="w-3 h-3" />Evidence and tool audit ({run.toolCalls.length})</summary>
                {run.toolCalls.map((call) => (
                  <pre className="mt-2 p-2 bg-background border border-border overflow-auto" key={call.id}>{call.toolName}{"\n"}{JSON.stringify(call.arguments, null, 2)}{"\n"}{JSON.stringify(call.result, null, 2)}</pre>
                ))}
              </details>
            )}
          </section>
        ))}
      </div>

      <div className="border border-border bg-card p-3">
        <Textarea value={message} onChange={(event) => setMessage(event.target.value)} disabled={busy || restoring} placeholder="Ask a question about your NMR data, projects, workflows, experiments, or notes…" className="min-h-24 text-xs" />
        <div className="mt-2 flex items-center justify-between gap-3">
          <span className="text-[9px] text-muted-foreground">
            {busy ? "Retrieving evidence and running tools…" : providerAvailable ? "Ready for an evidence-backed question." : "Configure a provider to ask questions."}
          </span>
          <Button onClick={() => void send()} disabled={!providerAvailable || busy || restoring || !message.trim()}>
            <Send className="w-3 h-3" />{busy ? "Researching…" : "Ask assistant"}
          </Button>
        </div>
      </div>
    </div>
  );
}
