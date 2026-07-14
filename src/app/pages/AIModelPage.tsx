import { BrainCircuit, Sparkles, FlaskConical, FileText, Calculator } from "lucide-react";

const PLANNED = [
  { icon: FlaskConical, title: "Protocol Assistant", desc: "Suggest optimizations and troubleshoot failed steps using a fine-tuned biochemistry model." },
  { icon: FileText, title: "Automated Reporting", desc: "Generate experiment summaries, methods sections, and result narratives from your notebook data." },
  { icon: Calculator, title: "Smart Calculator", desc: "Conversational interface for complex multi-step calculations (dilution series, buffer recipes, yields)." },
  { icon: Sparkles, title: "Anomaly Detection", desc: "Flag unexpected results, yield drops, or equipment drift by comparing against historical runs." },
];

export default function AIModelPage() {
  return (
    <div className="min-h-full bg-background flex items-center justify-center px-7 py-10" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-sm border border-violet-400/30 bg-violet-400/10 flex items-center justify-center mx-auto mb-5">
            <BrainCircuit className="w-6 h-6 text-violet-400" />
          </div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-2">COMING SOON</div>
          <h1 className="text-lg font-mono font-semibold text-foreground mb-3">AI Model</h1>
          <p className="text-[10px] font-mono text-muted-foreground leading-relaxed">
            An AI layer built specifically for lab workflows — trained on biochemistry literature and tuned to your notebook data.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {PLANNED.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="border border-border bg-card rounded-sm p-4">
              <Icon className="w-4 h-4 text-violet-400 mb-2.5" />
              <div className="text-[10px] font-mono text-foreground font-medium mb-1">{title}</div>
              <p className="text-[9px] font-mono text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        <div className="border border-violet-400/20 bg-violet-400/5 rounded-sm px-4 py-2.5 text-center">
          <div className="text-[9px] font-mono text-violet-400 tracking-wider">PLACEHOLDER · IN DEVELOPMENT</div>
        </div>
      </div>
    </div>
  );
}
