import { useEffect, useMemo, useState } from "react";
import { Bot, BrainCircuit, Cable, FlaskConical, KeyRound, ServerCog } from "lucide-react";
import {
  fetchAISettings,
  fetchAnalysisModules,
  fetchMcpManifest,
  type AISettingsRecord,
  type AnalysisModuleRecord,
  type MCPManifestRecord,
} from "../api";

const panelCls = "border border-border rounded-sm bg-card";

function statusLabel(enabled: boolean) {
  return enabled ? "READY" : "PLACEHOLDER";
}

function formatBool(value: boolean) {
  return value ? "enabled" : "disabled";
}

export default function AIModelPage() {
  const [settings, setSettings] = useState<AISettingsRecord | null>(null);
  const [modules, setModules] = useState<AnalysisModuleRecord[]>([]);
  const [manifest, setManifest] = useState<MCPManifestRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPage() {
      try {
        setLoading(true);
        setError(null);
        const [nextSettings, nextModules, nextManifest] = await Promise.all([
          fetchAISettings(),
          fetchAnalysisModules(),
          fetchMcpManifest(),
        ]);
        if (cancelled) {
          return;
        }
        setSettings(nextSettings);
        setModules(nextModules);
        setManifest(nextManifest);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load AI placeholders");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadPage();
    return () => {
      cancelled = true;
    };
  }, []);

  const toolPreview = useMemo(() => manifest?.tools.slice(0, 6) ?? [], [manifest]);

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">AI SURFACES</div>
          <h1 className="text-xl font-mono font-semibold text-foreground" data-testid="ai-page-title">
            AI Model & MCP
          </h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1 max-w-3xl leading-relaxed">
            PR8 ships real API contracts for future chat, MCP, local models, and analysis modules without faking model execution.
          </p>
        </div>
        <div className="border border-violet-400/20 bg-violet-400/5 rounded-sm px-3 py-2 text-[9px] font-mono text-violet-300">
          PLACEHOLDER ONLY
        </div>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5" data-testid="ai-api-error">
          <div className="text-[10px] font-mono text-red-300">AI API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      {loading && (
        <div className="text-[10px] font-mono text-muted-foreground mb-5" data-testid="ai-loading">
          Loading AI placeholder contracts...
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
        <div className={`${panelCls} p-4`} data-testid="ai-settings-summary">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <Bot className="w-3.5 h-3.5 text-violet-300" />
            AI SETTINGS
          </div>
          <div className="space-y-2 text-[10px] font-mono text-muted-foreground">
            <div className="flex justify-between gap-4"><span>Chat</span><span>{statusLabel(settings?.chatEnabled ?? false)}</span></div>
            <div className="flex justify-between gap-4"><span>Workflow builder</span><span>{statusLabel(settings?.workflowBuilderEnabled ?? false)}</span></div>
            <div className="flex justify-between gap-4"><span>Analysis modules</span><span>{statusLabel(settings?.analysisModulesEnabled ?? false)}</span></div>
            <div className="flex justify-between gap-4"><span>Local models</span><span>{statusLabel(settings?.localModelsEnabled ?? false)}</span></div>
            <div className="flex justify-between gap-4"><span>API keys</span><span>{statusLabel(settings?.apiKeysEnabled ?? false)}</span></div>
          </div>
        </div>

        <div className={`${panelCls} p-4`} data-testid="mcp-summary">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <Cable className="w-3.5 h-3.5 text-[#00c9a7]" />
            MCP MANIFEST
          </div>
          <div className="space-y-2 text-[10px] font-mono text-muted-foreground">
            <div className="flex justify-between gap-4"><span>Server</span><span className="text-foreground">{manifest?.serverName ?? "loading"}</span></div>
            <div className="flex justify-between gap-4"><span>Status</span><span>{manifest?.status ?? "loading"}</span></div>
            <div className="flex justify-between gap-4"><span>Transport</span><span>{manifest?.transport ?? "loading"}</span></div>
            <div className="flex justify-between gap-4"><span>Tool count</span><span data-testid="mcp-tool-count">{manifest?.toolCount ?? 0}</span></div>
          </div>
        </div>

        <div className={`${panelCls} p-4`} data-testid="analysis-summary">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <FlaskConical className="w-3.5 h-3.5 text-amber-300" />
            ANALYSIS REGISTRY
          </div>
          <div className="space-y-2 text-[10px] font-mono text-muted-foreground">
            <div className="flex justify-between gap-4"><span>Registered modules</span><span data-testid="analysis-module-count">{modules.length}</span></div>
            <div className="flex justify-between gap-4"><span>Execution</span><span>disabled</span></div>
            <div className="flex justify-between gap-4"><span>Output persistence</span><span>not started</span></div>
            <div className="flex justify-between gap-4"><span>Agent orchestration</span><span>not started</span></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-4">
        <section className={`${panelCls} p-4`} data-testid="ai-provider-list">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <KeyRound className="w-3.5 h-3.5 text-violet-300" />
            API PROVIDERS
          </div>
          <div className="space-y-3">
            {settings?.supportedApiProviders.map((provider) => (
              <div key={provider.id} className="border border-border rounded-sm bg-background px-3 py-3">
                <div className="flex items-start justify-between gap-3 mb-1">
                  <div className="text-[10px] font-mono text-foreground">{provider.label}</div>
                  <div className="text-[8px] font-mono text-violet-300 uppercase tracking-wider">{provider.status}</div>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground mb-1">
                  Configuration is {formatBool(provider.configured)}.
                </div>
                <div className="text-[9px] font-mono text-muted-foreground leading-relaxed">{provider.detail}</div>
              </div>
            ))}
          </div>
        </section>

        <section className={`${panelCls} p-4`} data-testid="local-runtime-list">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <ServerCog className="w-3.5 h-3.5 text-[#00c9a7]" />
            LOCAL MODEL RUNTIMES
          </div>
          <div className="space-y-3">
            {settings?.localModelRuntimes.map((runtime) => (
              <div key={runtime.id} className="border border-border rounded-sm bg-background px-3 py-3">
                <div className="flex items-start justify-between gap-3 mb-1">
                  <div className="text-[10px] font-mono text-foreground">{runtime.label}</div>
                  <div className="text-[8px] font-mono text-[#00c9a7] uppercase tracking-wider">{runtime.status}</div>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground mb-1">
                  Installed: {runtime.installed ? "yes" : "no"} · Enabled: {runtime.enabled ? "yes" : "no"}
                </div>
                <div className="text-[9px] font-mono text-muted-foreground leading-relaxed">{runtime.detail}</div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] gap-4">
        <section className={`${panelCls} p-4`} data-testid="analysis-module-list">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <BrainCircuit className="w-3.5 h-3.5 text-amber-300" />
            ANALYSIS MODULE PLACEHOLDERS
          </div>
          <div className="space-y-3">
            {modules.map((module) => (
              <div key={module.id} className="border border-border rounded-sm bg-background px-3 py-3">
                <div className="flex items-start justify-between gap-3 mb-1">
                  <div>
                    <div className="text-[10px] font-mono text-foreground">{module.name}</div>
                    <div className="text-[8px] font-mono text-muted-foreground uppercase tracking-wider mt-1">
                      {module.category}
                    </div>
                  </div>
                  <div className="text-[8px] font-mono text-amber-300 uppercase tracking-wider">{module.status}</div>
                </div>
                <div className="text-[9px] font-mono text-muted-foreground leading-relaxed mb-2">{module.description}</div>
                <div className="text-[8px] font-mono text-muted-foreground mb-1">
                  Inputs: {module.inputTypes.join(", ")}
                </div>
                <div className="text-[8px] font-mono text-muted-foreground">
                  Outputs: {module.outputTypes.join(", ")}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className={`${panelCls} p-4`} data-testid="mcp-tool-list">
          <div className="flex items-center gap-2 text-[10px] font-mono text-foreground mb-3">
            <Cable className="w-3.5 h-3.5 text-[#00c9a7]" />
            MCP TOOL PREVIEW
          </div>
          <div className="text-[9px] font-mono text-muted-foreground mb-3 break-all">
            OpenAPI source: {manifest?.openapiUrl ?? "loading"}
          </div>
          <div className="space-y-2 mb-4">
            {toolPreview.map((tool) => (
              <div key={`${tool.method}-${tool.path}`} className="border border-border rounded-sm bg-background px-3 py-2">
                <div className="flex items-center gap-2 text-[9px] font-mono text-foreground">
                  <span className="text-[#00c9a7]">{tool.method}</span>
                  <span className="break-all">{tool.path}</span>
                </div>
                <div className="text-[8px] font-mono text-muted-foreground mt-1 line-clamp-2">{tool.summary}</div>
              </div>
            ))}
          </div>
          <div className="border-t border-border pt-3 space-y-2">
            {manifest?.notes.map((note) => (
              <div key={note} className="text-[9px] font-mono text-muted-foreground leading-relaxed">
                {note}
              </div>
            ))}
            {settings?.notes.map((note) => (
              <div key={note} className="text-[9px] font-mono text-muted-foreground leading-relaxed">
                {note}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
