import { Users, MessageSquare, Construction } from "lucide-react";

export default function TeamsPage() {
  return (
    <div className="min-h-full bg-background flex items-center justify-center px-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="text-center max-w-sm">
        <div className="w-14 h-14 rounded-sm border border-amber-400/30 bg-amber-400/10 flex items-center justify-center mx-auto mb-5">
          <Users className="w-6 h-6 text-amber-400" />
        </div>
        <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-2">COMING SOON</div>
        <h1 className="text-lg font-mono font-semibold text-foreground mb-3">Teams & Chats</h1>
        <p className="text-[10px] font-mono text-muted-foreground leading-relaxed mb-6">
          Collaborate with your lab members in real-time. Share protocols, annotate experiments, and discuss results — all in one place.
        </p>
        <div className="space-y-2 text-left">
          {[
            "Lab member directory",
            "Protocol discussion threads",
            "Experiment annotation sharing",
            "Real-time notifications",
            "Direct messaging",
          ].map(f => (
            <div key={f} className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-amber-400/60" />
              <span className="text-[10px] font-mono text-muted-foreground">{f}</span>
            </div>
          ))}
        </div>
        <div className="mt-6 border border-amber-400/20 bg-amber-400/5 rounded-sm px-4 py-2.5">
          <div className="text-[9px] font-mono text-amber-400 tracking-wider">PLACEHOLDER · IN DEVELOPMENT</div>
        </div>
      </div>
    </div>
  );
}
